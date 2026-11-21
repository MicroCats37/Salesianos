"""La superficie PÚBLICA de los encuentros: lectura, cubos e invariantes.

Change: `partidos-marcadores-competencias` · Batch 1

GIVEN  una edición PUBLICADA con encuentros en distintos estados
WHEN   un ANÓNIMO lee `GET /api/publico/competencias/encuentros`
THEN   responde el envelope congelado con los TRES cubos, el ganador viaja
       como la autoridad —jamás deducido del marcador—, la versión viaja y
       NADA se escribe (`FR-01`, `explore` §5, §9).

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).
"""

import json
from datetime import date, datetime, timedelta

import pytest
from django.test import Client
from django.utils import timezone

from modules.competencias.domain.constants import (
    EstadoCompetencia,
    EstadoEncuentro,
    EstadoRonda,
)
from modules.competencias.domain.models import (
    AuditoriaOperacion,
    Competencia,
    Encuentro,
    Ronda,
)
from modules.eventos.domain.constants import EstadoEdicion

pytestmark = [
    pytest.mark.urls("modules.competencias.tests.urls_competencias"),
    pytest.mark.django_db,
]

RUTA_PUBLICA = "/api/publico/competencias/encuentros"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def instante():
    """Un instante AWARE en la zona horaria del proyecto (`America/Lima`)."""
    return timezone.make_aware(datetime(2027, 3, 14, 10, 0))


@pytest.fixture
def cliente():
    """Cliente HTTP anónimo: sin credencial de sesión."""
    return Client()


@pytest.fixture
def encuentro_programado(db, ronda, equipo_en_cuadro, equipo_2_en_cuadro, instante):
    """Encuentro PROGRAMADO: con participantes y con horario."""
    return Encuentro.objects.create(
        ronda=ronda,
        orden=2,
        estado=EstadoEncuentro.PROGRAMADO,
        participante_1=equipo_en_cuadro,
        participante_2=equipo_2_en_cuadro,
        inicio_programado=instante,
        fin_programado=instante + timedelta(hours=1),
    )


@pytest.fixture
def encuentro_en_vivo(db, ronda, equipo_en_cuadro, equipo_2_en_cuadro, instante):
    """Encuentro EN CURSO: está en juego."""
    return Encuentro.objects.create(
        ronda=ronda,
        orden=3,
        estado=EstadoEncuentro.EN_CURSO,
        participante_1=equipo_en_cuadro,
        participante_2=equipo_2_en_cuadro,
        inicio_programado=instante,
        fin_programado=instante + timedelta(hours=1),
        iniciado_en=instante,
    )


@pytest.fixture
def encuentro_finalizado(db, ronda, equipo_en_cuadro, equipo_2_en_cuadro, instante):
    """Encuentro FINALIZADO con ganador.

    El marcador NO coincide con el ganador a propósito: el puntaje es
    INFORMATIVO y el ganador es el que ocupa el slot. Si algún día alguien
    dedujera el ganador del marcador, este encuentro lo delata.
    """
    return Encuentro.objects.create(
        ronda=ronda,
        orden=4,
        estado=EstadoEncuentro.FINALIZADO,
        participante_1=equipo_en_cuadro,
        participante_2=equipo_2_en_cuadro,
        inicio_programado=instante,
        fin_programado=instante + timedelta(hours=1),
        iniciado_en=instante,
        finalizado_en=instante + timedelta(hours=1),
        puntaje_1=9,
        puntaje_2=4,
        marcador_detalle="Set 1: 9-4",
        ganador=equipo_2_en_cuadro,
    )


@pytest.fixture
def encuentro_cancelado(db, ronda, equipo_en_cuadro, instante):
    """Encuentro CANCELADO: no se publica."""
    return Encuentro.objects.create(
        ronda=ronda,
        orden=5,
        estado=EstadoEncuentro.CANCELADO,
        participante_1=equipo_en_cuadro,
        inicio_programado=instante,
        fin_programado=instante + timedelta(hours=1),
    )


@pytest.fixture
def encuentro_de_competencia_cancelada(db, edicion_publicada, disciplina, categoria):
    """Un encuentro de una competencia CANCELADA: tampoco se publica."""
    competencia = Competencia.objects.create(
        edicion=edicion_publicada,
        disciplina=disciplina,
        categoria=categoria,
        nombre="Vóley Mixto Anulado 2027",
        fecha=date(2027, 3, 16),
        estado=EstadoCompetencia.CANCELADA,
    )
    ronda_cancelada = Ronda.objects.create(
        competencia=competencia,
        etiqueta="Cuartos anulados",
        orden=1,
        estado=EstadoRonda.ACTIVA,
    )
    return Encuentro.objects.create(
        ronda=ronda_cancelada,
        orden=1,
        estado=EstadoEncuentro.PROGRAMADO,
    )


@pytest.fixture
def edicion_no_publicada(db, edicion_otra):
    """La SEGUNDA edición, en BORRADOR: su contenido no se publica.

    Sigue siendo la segunda edición PUBLICADA del catálogo si nadie la
    degrada; degradarla deja UNA sola edición publicada, que es la que la
    lectura pública resuelve.
    """
    edicion_otra.estado = EstadoEdicion.BORRADOR
    edicion_otra.save()
    return edicion_otra


@pytest.fixture
def encuentro_de_edicion_no_publicada(
    db,
    edicion_no_publicada,
    disciplina_otra_edicion,
    categoria_otra,
):
    """Un encuentro de una edición que NO está publicada."""
    competencia_ajena = Competencia.objects.create(
        edicion=edicion_no_publicada,
        disciplina=disciplina_otra_edicion,
        categoria=categoria_otra,
        nombre="Vóley Mixto 2028",
        fecha=date(2028, 3, 14),
    )
    ronda_ajena = Ronda.objects.create(
        competencia=competencia_ajena,
        etiqueta="Cuartos 2028",
        orden=1,
        estado=EstadoRonda.ACTIVA,
    )
    return Encuentro.objects.create(
        ronda=ronda_ajena,
        orden=1,
        estado=EstadoEncuentro.PROGRAMADO,
    )


def _cuerpo(respuesta) -> dict:
    """El cuerpo JSON de la respuesta."""
    return json.loads(respuesta.content)


# ── La forma del contrato ───────────────────────────────────────────────────


def test_la_lectura_publica_responde_el_envelope_con_los_tres_cubos(
    cliente,
    edicion_publicada,
    encuentro_programado,
):
    """GIVEN una edición publicada con un encuentro programado."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    cuerpo = _cuerpo(respuesta)
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["data"]["edicion_id"] == str(edicion_publicada.id)
    assert cuerpo["data"]["edicion_nombre"] == edicion_publicada.nombre
    assert set(cuerpo["data"]) == {
        "edicion_id",
        "edicion_nombre",
        "total",
        "en_vivo",
        "proximos",
        "finalizados",
    }


def test_el_encuentro_publico_trae_el_contexto_del_partido(
    cliente,
    edicion_publicada,
    ronda,
    competencia,
    encuentro_programado,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
):
    """GIVEN un encuentro programado con sus dos equipos."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    publicos = _cuerpo(respuesta)["data"]["proximos"]
    assert len(publicos) == 1
    partido = publicos[0]

    # Contexto de COMPETENCIA, RONDA, EQUIPOS, marcador, ganador, versión y
    # tiempos: es lo que necesita la página pública y el resumen de la
    # portada.
    assert partido["id"] == str(encuentro_programado.id)
    assert partido["competencia_id"] == str(competencia.id)
    assert partido["ronda_id"] == str(ronda.id)
    assert partido["ronda_etiqueta"] == ronda.etiqueta
    assert partido["ronda_orden"] == ronda.orden
    assert partido["estado_publico"] == "PROGRAMA"
    assert partido["es_bye"] is False
    assert partido["version"] == encuentro_programado.version
    assert partido["inicio_programado"] is not None
    assert partido["finalizado_en"] is None
    assert [p["equipo_nombre"] for p in partido["participantes"]] == [
        equipo_en_cuadro.equipo.nombre,
        equipo_2_en_cuadro.equipo.nombre,
    ]
    assert partido["participantes"][0]["slot"] == "PARTICIPANTE_1"
    assert partido["participantes"][1]["slot"] == "PARTICIPANTE_2"


def test_el_estado_vacio_devuelve_las_tres_listas_vacias(
    cliente,
    edicion_publicada,
):
    """GIVEN una edición publicada SIN encuentros."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    datos = _cuerpo(respuesta)["data"]
    assert datos["total"] == 0
    assert datos["en_vivo"] == []
    assert datos["proximos"] == []
    assert datos["finalizados"] == []


# ── Los cubos del estado ────────────────────────────────────────────────────


def test_cada_encuentro_se_publica_en_su_cubo(
    cliente,
    edicion_publicada,
    encuentro,
    encuentro_programado,
    encuentro_en_vivo,
    encuentro_finalizado,
):
    """GIVEN un encuentro en cada estado publicable."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    datos = _cuerpo(respuesta)["data"]

    assert [e["id"] for e in datos["en_vivo"]] == [str(encuentro_en_vivo.id)]
    assert [e["id"] for e in datos["finalizados"]] == [str(encuentro_finalizado.id)]
    # El BORRADOR y el PROGRAMADO comparten el cubo "programa".
    assert {e["id"] for e in datos["proximos"]} == {
        str(encuentro.id),
        str(encuentro_programado.id),
    }
    assert datos["total"] == 4
    assert {e["estado_publico"] for e in datos["proximos"]} == {"PROGRAMA"}


def test_un_encuentro_cancelado_no_se_publica(
    cliente,
    edicion_publicada,
    encuentro_cancelado,
):
    """GIVEN un encuentro cancelado."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    datos = _cuerpo(respuesta)["data"]
    assert datos["total"] == 0
    assert datos["en_vivo"] == []
    assert datos["proximos"] == []
    assert datos["finalizados"] == []


def test_los_encuentros_de_una_competencia_cancelada_no_se_publican(
    cliente,
    edicion_publicada,
    encuentro_de_competencia_cancelada,
):
    """GIVEN un encuentro de una competencia CANCELADA."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    datos = _cuerpo(respuesta)["data"]
    assert datos["total"] == 0
    assert datos["proximos"] == []


def test_los_encuentros_de_una_edicion_no_publicada_no_se_publican(
    cliente,
    edicion_publicada,
    edicion_no_publicada,
    encuentro_de_edicion_no_publicada,
):
    """GIVEN un encuentro de una edición que NO está publicada."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    datos = _cuerpo(respuesta)["data"]
    assert datos["edicion_id"] == str(edicion_publicada.id)
    assert datos["total"] == 0
    assert datos["proximos"] == []


# ── La invariante del ganador ───────────────────────────────────────────────


def test_el_ganador_viaja_como_la_autoridad_y_no_se_deduce_del_marcador(
    cliente,
    edicion_publicada,
    encuentro_finalizado,
    equipo_en_cuadro,
    equipo_2_en_cuadro,
):
    """GIVEN un encuentro con marcador 9-4 y ganador en el SEGUNDO slot."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    partido = _cuerpo(respuesta)["data"]["finalizados"][0]

    # El marcador es informativo: 9 a 4.
    assert partido["puntaje_1"] == 9
    assert partido["puntaje_2"] == 4
    # El ganador es el que ocupa el slot, NO el que va ganando.
    assert partido["ganador_equipo_id"] == str(equipo_2_en_cuadro.equipo_id)
    assert partido["ganador_equipo_nombre"] == equipo_2_en_cuadro.equipo.nombre
    assert partido["ganador_equipo_id"] != str(equipo_en_cuadro.equipo_id)


def test_un_encuentro_sin_ganador_no_inventa_uno(
    cliente,
    edicion_publicada,
    encuentro_en_vivo,
):
    """GIVEN un encuentro en juego: todavía no hay ganador."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    partido = _cuerpo(respuesta)["data"]["en_vivo"][0]
    assert partido["ganador_equipo_id"] is None
    assert partido["ganador_equipo_nombre"] is None


# ── La lectura NO escribe ───────────────────────────────────────────────────


def test_la_lectura_publica_no_escribe_nada(
    cliente,
    edicion_publicada,
    encuentro_programado,
    encuentro_en_vivo,
    encuentro_finalizado,
):
    """GIVEN una edición con encuentros."""
    encuentros_antes = list(
        Encuentro.objects.order_by("id").values(
            "id",
            "estado",
            "version",
            "puntaje_1",
            "puntaje_2",
            "ganador_id",
        )
    )
    total_antes = Encuentro.objects.count()
    competencias_antes = Competencia.objects.count()

    # WHEN un anónimo lee la superficie pública.
    respuesta = cliente.get(RUTA_PUBLICA)

    # THEN la respuesta es correcta y NADA cambió.
    assert respuesta.status_code == 200
    assert Encuentro.objects.count() == total_antes
    assert Competencia.objects.count() == competencias_antes
    assert list(
        Encuentro.objects.order_by("id").values(
            "id",
            "estado",
            "version",
            "puntaje_1",
            "puntaje_2",
            "ganador_id",
        )
    ) == encuentros_antes
    # Y no deja acta de ninguna operación.
    assert AuditoriaOperacion.objects.count() == 0


# ── La frontera ─────────────────────────────────────────────────────────────


def test_la_lectura_publica_es_anonima(cliente, edicion_publicada, encuentro_programado):
    """GIVEN una petición SIN credencial de sesión."""
    respuesta = cliente.get(RUTA_PUBLICA)

    assert respuesta.status_code == 200
    assert _cuerpo(respuesta)["success"] is True


def test_las_rutas_de_competencias_siguen_protegidas(cliente, edicion_publicada):
    """GIVEN una petición anónima · WHEN llama a la superficie administrativa."""
    lectura = cliente.get("/api/competencias")
    escritura = cliente.post("/api/competencias", data={}, content_type="application/json")

    # THEN la autenticación se exige ANTES que el permiso: 401.
    assert lectura.status_code == 401
    assert escritura.status_code == 401
    assert _cuerpo(lectura)["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_la_escritura_de_competencias_sigue_exigiendo_capacidad(
    db,
    cliente,
    edicion_publicada,
    usuario_ajeno,
):
    """GIVEN una cuenta NORMAL · WHEN escribe en la superficie administrativa."""
    from ninja_jwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(usuario_ajeno).access_token)
    respuesta = cliente.post(
        "/api/competencias",
        data={},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert respuesta.status_code == 403
    assert _cuerpo(respuesta)["error"]["code"] == "ACTION_NOT_ALLOWED"
