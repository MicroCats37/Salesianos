"""La siembra de arranque del catálogo: idempotente, aditiva y no destructiva.

GIVEN  una base de datos sin catálogo
WHEN   se ejecuta el comando `seed_catalogo`
THEN   quedan el evento, la edición `PUBLICADA`, las promociones, las
       categorías, las disciplinas, los paquetes, sus precios, vínculos y
       beneficios — y reejecutarlo NO duplica ni borra nada.

GIVEN  un catálogo ya configurado por el operador
WHEN   se ejecuta el comando
THEN   su configuración se PRESERVA: no se pisan precios ni se borran
       vínculos.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §8 (estructura del test de
integración) y §10.5 (prohibido `unittest.mock.patch`).
"""

from datetime import date
from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync
from django.core.management import call_command
from django.core.management.base import CommandError

from modules.eventos.domain.constants import EstadoEdicion
from modules.eventos.domain.models import Edicion, Evento
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
    Promocion,
)
from modules.salesianos_fest.domain.services.flujos.catalogo_flujo import CatalogoFlujo
from modules.salesianos_fest.management.commands.seed_catalogo import (
    ANIO_MAXIMO_PROMOCION,
    ANIO_MINIMO_PROMOCION,
    CATEGORIAS_OFICIALES,
    DISCIPLINAS_OFICIALES,
    PAQUETES_OFICIALES,
)

pytestmark = pytest.mark.django_db


# ── Utilidades ───────────────────────────────────────────────────────────────


def _sembrar(*argumentos):
    """Ejecuta el comando de seed con sus valores por defecto."""
    call_command("seed_catalogo", *argumentos)


def _conteos() -> dict[str, int]:
    """El estado del catálogo sembrado, para comparar dos ejecuciones."""
    return {
        "eventos": Evento.objects.count(),
        "ediciones": Edicion.objects.count(),
        "promociones": Promocion.objects.count(),
        "categorias": Categoria.objects.count(),
        "disciplinas": Disciplina.objects.count(),
        "paquetes": Paquete.objects.count(),
        "precios": PaquetePrecio.objects.count(),
        "vinculos": PaqueteDisciplina.objects.count(),
        "beneficios": PaqueteBeneficio.objects.count(),
    }


def _edicion_operador(estado=EstadoEdicion.PUBLICADA, modulos=("inscripciones",)):
    """Una edición ya existente, creada por el operador."""
    evento = Evento.objects.create(nombre="Salesianos FEST", slug="salesianos-fest")
    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
        estado=estado,
        modulos_habilitados=list(modulos),
    )


# ── El seed deja el catálogo ─────────────────────────────────────────────────


def test_el_seed_deja_el_evento_y_la_edicion_publicada():
    """GIVEN una base de datos vacía
    WHEN  se ejecuta el seed
    THEN  queda el evento raíz y su edición `PUBLICADA` con el módulo
          `inscripciones` habilitado: es lo que resuelve el alcance cuando el
          cliente no manda `edicion_id` (`FR-02` §2.2).
    """
    _sembrar()

    evento = Evento.objects.get(slug="salesianos-fest")
    edicion = Edicion.objects.get(evento=evento, slug="2026")

    assert edicion.estado == EstadoEdicion.PUBLICADA
    assert edicion.modulo_habilitado("inscripciones")


def test_el_seed_deja_el_catalogo_completo_de_la_edicion():
    """GIVEN una base de datos vacía
    WHEN  se ejecuta el seed
    THEN  quedan las disciplinas, los paquetes, sus precios, sus vínculos
          disciplina↔paquete y los beneficios declarados.
    """
    _sembrar()

    edicion = Edicion.objects.get(slug="2026")

    assert Disciplina.objects.filter(edicion=edicion).count() == len(
        DISCIPLINAS_OFICIALES
    )
    assert Paquete.objects.filter(edicion=edicion).count() == len(PAQUETES_OFICIALES)
    assert PaquetePrecio.objects.filter(paquete__edicion=edicion).count() == (
        2 * len(PAQUETES_OFICIALES)
    )
    assert PaqueteDisciplina.objects.filter(paquete__edicion=edicion).count() == sum(
        len(paquete["disciplinas"]) for paquete in PAQUETES_OFICIALES
    )
    assert PaqueteBeneficio.objects.filter(paquete__edicion=edicion).count() == sum(
        len(paquete["beneficios"]) for paquete in PAQUETES_OFICIALES
    )


def test_el_seed_siembra_las_promociones_y_las_categorias_oficiales():
    """GIVEN una base de datos vacía
    WHEN  se ejecuta el seed
    THEN  quedan las promociones GLOBALES (una por año de cohorte) y las
          categorías OFICIALES de la edición, con su rango: sin ellas la
          inscripción no puede derivar su categoría (`D-CAT-05`).
    """
    _sembrar()

    assert Promocion.objects.count() == (
        ANIO_MAXIMO_PROMOCION - ANIO_MINIMO_PROMOCION + 1
    )

    edicion = Edicion.objects.get(slug="2026")
    categorias = Categoria.objects.filter(edicion=edicion)
    assert categorias.count() == len(CATEGORIAS_OFICIALES)
    for datos in CATEGORIAS_OFICIALES:
        categoria = categorias.get(nombre=datos["nombre"])
        assert categoria.promocion_desde == datos["promocion_desde"]
        assert categoria.promocion_hasta == datos["promocion_hasta"]


def test_el_seed_deja_los_precios_unitarios_con_vigencia():
    """GIVEN una base de datos vacía
    WHEN  se ejecuta el seed
    THEN  cada paquete tiene las DOS etapas del catálogo oficial (preventa y
          regular) y al menos una vigente: sin precio vigente un paquete no
          está a la venta (`FL-01` paso 3).

    Los montos son UNITARIOS: el precio de UNA persona (`D-CAT-01`).
    """
    _sembrar()

    for paquete in Paquete.objects.all():
        precios = PaquetePrecio.objects.filter(paquete=paquete)
        assert precios.count() == 2
        assert all(precio.monto > Decimal("0") for precio in precios)
        vigente = (
            precios.filter(vigente_desde__lte=date.today())
            .order_by("-vigente_desde")
            .first()
        )
        assert vigente is not None
        assert vigente.vigente_hasta is None or vigente.vigente_hasta >= date.today()


def test_el_seed_deja_el_minimo_comercial_de_cada_paquete():
    """GIVEN una base de datos vacía
    WHEN  se ejecuta el seed
    THEN  cada paquete declara su mínimo comercial de participantes: es el
          mínimo contra el que el servidor contrasta la cantidad.
    """
    _sembrar()

    for datos in PAQUETES_OFICIALES:
        paquete = Paquete.objects.get(slug=datos["slug"])
        assert paquete.minimo_compra_inicial == datos["minimo_compra_inicial"]


# ── El seed es idempotente ───────────────────────────────────────────────────


def test_el_seed_es_idempotente():
    """GIVEN un catálogo ya sembrado
    WHEN  se ejecuta el seed otra vez
    THEN  no duplica ni una fila: el catálogo queda igual.
    """
    _sembrar()
    antes = _conteos()

    _sembrar()

    assert _conteos() == antes


def test_el_seed_no_crea_un_segundo_precio_en_reejecucion():
    """GIVEN un paquete con sus precios sembrados
    WHEN  se ejecuta el seed otra vez
    THEN  el paquete conserva SUS precios: las vigencias sembradas son
          fechas fijas, no `date.today()`.
    """
    _sembrar()

    _sembrar()

    for paquete in Paquete.objects.all():
        assert PaquetePrecio.objects.filter(paquete=paquete).count() == 2


# ── El seed NO destruye ni pisa lo del operador ─────────────────────────────


def test_el_seed_preserva_el_precio_configurado_por_el_operador():
    """GIVEN un paquete cuyo precio ya fue configurado por el operador
    WHEN  se ejecuta el seed
    THEN  el precio se preserva: el seed no crea otro ni lo modifica.
    """
    edicion = _edicion_operador()
    paquete = Paquete.objects.create(
        edicion=edicion,
        nombre="Paquete del operador",
        slug="paquete-operador",
        minimo_compra_inicial=5,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        monto=Decimal("99.00"),
        vigente_desde=date(2026, 1, 1),
    )

    _sembrar()

    precios = PaquetePrecio.objects.filter(paquete=paquete)
    assert precios.count() == 1
    assert precios.first().monto == Decimal("99.00")


def test_el_seed_no_borra_los_vinculos_del_operador():
    """GIVEN un vínculo disciplina↔paquete añadido por el operador
    WHEN  se ejecuta el seed
    THEN  el vínculo sigue ahí: el seed sólo AGREGA, nunca borra.
    """
    _sembrar()
    edicion = Edicion.objects.get(slug="2026")
    paquete = Paquete.objects.get(edicion=edicion, slug="reencuentro-fiesta")
    disciplina = Disciplina.objects.get(edicion=edicion, slug="basquet-masculino")
    PaqueteDisciplina.objects.filter(paquete=paquete, disciplina=disciplina).delete()
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    vinculos = PaqueteDisciplina.objects.count()

    _sembrar()

    assert PaqueteDisciplina.objects.count() == vinculos
    assert PaqueteDisciplina.objects.filter(
        paquete=paquete,
        disciplina=disciplina,
    ).exists()


def test_el_seed_publica_una_edicion_que_estaba_en_borrador():
    """GIVEN una edición del operador en `BORRADOR`
    WHEN  se ejecuta el seed
    THEN  la publica y le habilita el módulo `inscripciones`: el catálogo
          tiene que ser resoluble sin que el frontend elija edición.
    """
    edicion = _edicion_operador(
        estado=EstadoEdicion.BORRADOR,
        modulos=(),
    )

    _sembrar()

    edicion.refresh_from_db()
    assert edicion.estado == EstadoEdicion.PUBLICADA
    assert edicion.modulo_habilitado("inscripciones")


def test_el_seed_falla_si_ya_hay_otra_edicion_publicada():
    """GIVEN otra edición ya `PUBLICADA` (el alcance sería ambiguo)
    WHEN  se ejecuta el seed
    THEN  falla con un mensaje explícito y NO siembra nada: un catálogo
          ambiguo no es un catálogo servible (`FR-02` §2.2, nivel 3).
    """
    evento = Evento.objects.create(nombre="Otro FEST", slug="otro-fest")
    Edicion.objects.create(
        evento=evento,
        nombre="Otro FEST 2026",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=["inscripciones"],
    )

    with pytest.raises(CommandError):
        _sembrar()

    assert Paquete.objects.count() == 0
    assert Disciplina.objects.count() == 0


# ── El catálogo sembrado es servible ─────────────────────────────────────────


def test_el_catalogo_sembrado_es_servible_sin_seleccion_de_edicion(injector):
    """GIVEN un catálogo sembrado
    WHEN  se consulta el catálogo SIN `edicion_id`
    THEN  devuelve los paquetes de la edición publicada: el frontend no
          necesita elegir edición para ver el catálogo.
    """
    _sembrar()
    flujo = injector.get(CatalogoFlujo)

    resultado = async_to_sync(flujo.listar_paquetes)(None)

    assert len(resultado.paquetes) == len(PAQUETES_OFICIALES)
    assert all(paquete.precio.monto > Decimal("0") for paquete in resultado.paquetes)
    assert all(paquete.disciplinas for paquete in resultado.paquetes)


def test_el_dry_run_no_deja_ninguna_fila_escrita():
    """GIVEN una base de datos vacía
    WHEN  se ejecuta el seed con `--dry-run`
    THEN  no queda ninguna fila escrita.
    """
    _sembrar("--dry-run")

    assert _conteos() == {
        "eventos": 0,
        "ediciones": 0,
        "promociones": 0,
        "categorias": 0,
        "disciplinas": 0,
        "paquetes": 0,
        "precios": 0,
        "vinculos": 0,
        "beneficios": 0,
    }
