"""El precio POR PERSONA del alta: cantidad, mínimo comercial y total.

GIVEN  un paquete con su mínimo comercial y su precio unitario vigente
WHEN   se confirma el alta con una cantidad de participantes
THEN   el servidor exige la cantidad mínima, cobra el PRECIO UNITARIO del
       catálogo y congela `cantidad × precio_unitario` en la compra
       (`D-CAT-01`, `RN-C02`).

No hay un máximo global de participantes: el tope de un equipo es el de su
disciplina, que es una regla DEPORTIVA, no comercial.
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.exceptions import (
    CantidadInsuficienteError,
    PrecioCambiadoError,
)
from modules.salesianos_fest.domain.models import Inscripcion
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    EquipoCreateData,
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de inscripciones."""
    return injector.get(InscripcionFlujo)


def _intencion(edicion, paquete, disciplina, persona, promocion, cantidad):
    """La intención de alta con la cantidad indicada."""
    return InscripcionInicialData(
        responsable_id=persona.id,
        edicion_id=edicion.id,
        paquete_id=paquete.id,
        promocion_id=promocion.id,
        cantidad=cantidad,
        equipos=[
            EquipoCreateData(disciplina_id=disciplina.id, nombre="EquipoUno"),
        ],
    )


def test_el_total_es_cantidad_por_precio_unitario(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion,
    categoria,
):
    """GIVEN un paquete con precio unitario de S/ 250.00 y mínimo 10
    WHEN  se confirma el alta de 10 participantes
    THEN  el total congelado es `10 × 250.00`: el precio es POR PERSONA
       (`D-CAT-01`) y el total lo deriva el servidor (`RN-C02`).
    """
    intencion = _intencion(
        edicion_publicada, paquete, disciplina, persona, promocion, 10
    )

    resultado = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert resultado.compra.cantidad == 10
    assert resultado.compra.precio_unitario == Decimal("250.00")
    assert resultado.compra.total == Decimal("2500.00")

    linea = Compra.objects.get().lineas_snapshot[0]
    assert linea["cantidad"] == 10
    assert linea["precio_unitario"] == "250.00"


def test_la_cantidad_debe_alcanzar_el_minimo_comercial(
    flujo, edicion_publicada, paquete, disciplina, persona, precio, promocion
):
    """GIVEN un paquete cuyo mínimo comercial es 10
    WHEN  se confirma el alta de 9 participantes
    THEN  se rechaza con `CANTIDAD_INSUFICIENTE`: el mínimo es del PAQUETE
       (`D-CAT-01`).
    """
    intencion = _intencion(
        edicion_publicada, paquete, disciplina, persona, promocion, 9
    )

    with pytest.raises(CantidadInsuficienteError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0


def test_la_cantidad_minima_se_acepta(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion,
    categoria,
):
    """GIVEN un paquete cuyo mínimo comercial es 10
    WHEN  se confirma el alta de EXACTAMENTE 10 participantes
    THEN  se acepta: el mínimo es un mínimo, no un valor único.
    """
    intencion = _intencion(
        edicion_publicada, paquete, disciplina, persona, promocion, 10
    )

    resultado = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert resultado.compra.cantidad == 10
    assert resultado.inscripcion.cupos_solicitados == 10


def test_no_hay_un_maximo_global_de_participantes(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion,
    categoria,
):
    """GIVEN un paquete sin tope global de participantes
    WHEN  se confirma el alta de 60 participantes
    THEN  se acepta: el tope de un equipo es el de su DISCIPLINA, que es una
       regla deportiva, no comercial (`D-CAT-01`).
    """
    intencion = _intencion(
        edicion_publicada, paquete, disciplina, persona, promocion, 60
    )

    resultado = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert resultado.compra.cantidad == 60
    assert resultado.compra.total == Decimal("15000.00")


def test_un_token_de_cotizacion_vigente_se_acepta(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion,
    categoria,
):
    """GIVEN un alta con el token de concurrencia de la cotización vigente
    WHEN  se confirma
    THEN  se acepta: el catálogo no se movió (`RN-C02`).
    """
    intencion = _intencion(
        edicion_publicada, paquete, disciplina, persona, promocion, 10
    )
    intencion = intencion.model_copy(update={"cotizacion_version": 1})

    resultado = async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert resultado.compra.cantidad == 10


def test_un_token_de_cotizacion_desfasado_se_rechaza(
    flujo,
    edicion_publicada,
    paquete,
    disciplina,
    persona,
    precio,
    promocion,
    categoria,
):
    """GIVEN un alta con el token de una cotización que ya no es la vigente
    WHEN  se confirma
    THEN  se rechaza con `PRECIO_CAMBIADO`: es mejor obligar a cotizar de
       nuevo que cobrar una cantidad que nadie vio (`RN-C02`).
    """
    intencion = _intencion(
        edicion_publicada, paquete, disciplina, persona, promocion, 10
    )
    intencion = intencion.model_copy(update={"cotizacion_version": 99})

    with pytest.raises(PrecioCambiadoError):
        async_to_sync(flujo.crear_inscripcion_inicial)(intencion)

    assert Inscripcion.objects.count() == 0
