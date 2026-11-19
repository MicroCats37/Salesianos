"""`EdicionPresenter`: result de dominio → schema HTTP.

GIVEN  un result de dominio
WHEN   lo proyecta el presenter
THEN   el wrapper HTTP sale tipado y con el estado real de los módulos.
"""

from datetime import date, datetime
from uuid import uuid4

from modules.eventos.domain.results.edicion_result import (
    EdicionActualResult,
    EdicionResult,
)
from modules.eventos.presentation.presenters.edicion_presenter import EdicionPresenter


def _result() -> EdicionResult:
    """Result de dominio con un identificador y una marca de tiempo fijos."""
    identificador = uuid4()
    momento = datetime(2026, 1, 1, 12, 0, 0)
    return EdicionResult(
        id=identificador,
        evento_id=uuid4(),
        evento_nombre="Salesianos FEST",
        evento_slug="salesianos-fest",
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
        estado="PUBLICADA",
        modulos_habilitados=["inscripciones", "pases"],
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        created_at=momento,
        updated_at=momento,
    )


def test_present_proyecta_los_campos_del_wrapper():
    resultado = _result()

    wrapper = EdicionPresenter.present(resultado)

    assert wrapper.id == resultado.id
    assert wrapper.evento_nombre == "Salesianos FEST"
    assert wrapper.nombre == "Salesianos FEST 2026"
    assert wrapper.anio == 2026
    assert wrapper.estado == "PUBLICADA"
    assert wrapper.modulos_habilitados == ["inscripciones", "pases"]
    assert wrapper.fecha_inicio == date(2026, 11, 15)


def test_present_actual_lista_los_cinco_modulos_logicos():
    resultado = EdicionActualResult(
        edicion=_result(),
        modulos=[
            {"clave": "inscripciones", "nombre": "Inscripciones deportivas", "habilitado": True},
            {"clave": "pases", "nombre": "Pases / beneficios", "habilitado": True},
            {"clave": "marketplace", "nombre": "Marketplace", "habilitado": False},
            {"clave": "competencias", "nombre": "Competencias", "habilitado": False},
            {"clave": "patrocinadores", "nombre": "Patrocinadores", "habilitado": False},
        ],
    )

    wrapper = EdicionPresenter.present_actual(resultado)

    assert len(wrapper.modulos) == 5
    assert [modulo.clave for modulo in wrapper.modulos] == [
        "inscripciones",
        "pases",
        "marketplace",
        "competencias",
        "patrocinadores",
    ]
    assert [modulo.habilitado for modulo in wrapper.modulos] == [
        True,
        True,
        False,
        False,
        False,
    ]


def test_present_actual_no_oculta_los_modulos_deshabilitados():
    """Un módulo apagado es INFORMACIÓN: aparece con `habilitado = False`."""
    resultado = EdicionActualResult(
        edicion=_result(),
        modulos=[
            {"clave": "inscripciones", "nombre": "Inscripciones deportivas", "habilitado": True},
            {"clave": "pases", "nombre": "Pases / beneficios", "habilitado": False},
            {"clave": "marketplace", "nombre": "Marketplace", "habilitado": False},
            {"clave": "competencias", "nombre": "Competencias", "habilitado": False},
            {"clave": "patrocinadores", "nombre": "Patrocinadores", "habilitado": False},
        ],
    )

    wrapper = EdicionPresenter.present_actual(resultado)

    deshabilitados = [m.clave for m in wrapper.modulos if not m.habilitado]
    assert deshabilitados == ["pases", "marketplace", "competencias", "patrocinadores"]


def test_el_presenter_no_consulta_la_base_de_datos():
    """El presenter es un transformador puro: no toca el ORM.

    Se comprueba que el presenter funciona con un result construido a mano
    (sin ninguna fila en la base de datos).
    """
    wrapper = EdicionPresenter.present(_result())

    assert wrapper.slug == "2026"
