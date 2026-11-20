"""La ampliación: comprar cupos extra para la MISMA inscripción.

GIVEN  una inscripción con un paquete vigente y con precio
WHEN   el responsable pide cupos extra
THEN   se crea una COMPRA SEPARADA y PENDIENTE con el precio congelado por el
       servidor, la capacidad NO cambia hasta que el pago se active, y un
       reintento devuelve la MISMA compra (`FL-04`, `RN-C02`, `RN-I02`,
       `FR-04` I-4).
"""

from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync

from modules.commerce.domain.constants import EstadoCompra, OrigenCompra
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.constants import (
    CausaOperativaCompraCupos,
    CONCEPTO_LINEA_CUPO,
)
from modules.salesianos_fest.domain.exceptions import (
    CompraNoAutorizadaError,
    CupoInvalidoError,
    PaqueteNoVigenteError,
)
from modules.salesianos_fest.domain.models import Inscripcion
from modules.salesianos_fest.domain.schemas.pool_schemas import CompraCuposData
from modules.salesianos_fest.domain.services.flujos.compra_cupos_flujo import (
    CompraCuposFlujo,
)
from modules.salesianos_fest.domain.services.orchestrators.compra_cupos_orchestrator import (
    CompraCuposOrchestrator,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de la compra de cupos."""
    return injector.get(CompraCuposFlujo)


@pytest.fixture
def orchestrator(injector):
    """El orquestador real de la compra de cupos."""
    return injector.get(CompraCuposOrchestrator)


@pytest.fixture
def intencion(inscripcion, precio):
    """La intención de comprar tres cupos extra."""
    return CompraCuposData(inscripcion_id=inscripcion.id, cantidad=3)


def test_la_ampliacion_crea_una_compra_separada_y_pendiente(
    flujo, intencion, inscripcion, paquete, precio
):
    """GIVEN una inscripción con su compra del ALTA
    WHEN  se compran cupos extra
    THEN  se crea una COMPRA NUEVA, PENDIENTE y de origen INSCRIPCION, con su
       propia referencia: la ampliación es un hecho COMERCIAL aparte
       (`FL-04` paso 2).
    """
    resultado = async_to_sync(flujo.comprar_cupos)(intencion)

    assert resultado.causa_operativa == CausaOperativaCompraCupos.COMPRA_CUPOS_CREADA
    assert resultado.cupos_solicitados == 3
    assert Compra.objects.count() == 1

    compra = Compra.objects.get()
    assert compra.origen == OrigenCompra.INSCRIPCION
    assert compra.estado == EstadoCompra.PENDIENTE
    assert compra.persona_id == inscripcion.responsable_id
    assert compra.referencia == f"INSCRIPCION:{inscripcion.id}:EXPANSION:3"


def test_la_ampliacion_congela_el_precio_del_catalogo(
    flujo, intencion, paquete, precio
):
    """GIVEN un paquete con precio de catálogo
    WHEN  se compran tres cupos extra
    THEN  la línea congela ESE precio y el total lo deriva el servidor: el
       cliente NO declara ningún importe (`RN-C02`).
    """
    resultado = async_to_sync(flujo.comprar_cupos)(intencion)

    assert resultado.total == Decimal("750.00")
    assert resultado.moneda == "PEN"

    compra = Compra.objects.get()
    linea = compra.lineas_snapshot[0]
    assert linea["concepto_tipo"] == CONCEPTO_LINEA_CUPO
    assert linea["concepto_id"] == str(paquete.id)
    assert linea["cantidad"] == 3
    assert linea["precio_unitario"] == "250.00"


def test_la_compra_pendiente_no_habilita_cupos(flujo, intencion, inscripcion):
    """GIVEN una compra de cupos extra PENDIENTE
    WHEN  se mira la capacidad de la inscripción
    THEN  la capacidad pagada NO cambia: los cupos se habilitan al activarse
       el pago (`RN-I02`, `QA-I03`).
    """
    async_to_sync(flujo.comprar_cupos)(intencion)

    inscripcion.refresh_from_db()
    assert inscripcion.cupos_pagados == 10
    assert inscripcion.cupos_asignados == 0


def test_un_reintento_devuelve_la_misma_compra(flujo, intencion):
    """GIVEN una compra de cupos extra ya pendiente
    WHEN  se reintenta la misma petición
    THEN  devuelve la MISMA compra y su MISMA orden de pago: no se duplica
       (`FR-04` I-4, `RN-C06`).
    """
    primera = async_to_sync(flujo.comprar_cupos)(intencion)
    segunda = async_to_sync(flujo.comprar_cupos)(intencion)

    assert segunda.causa_operativa == (
        CausaOperativaCompraCupos.COMPRA_CUPOS_REUTILIZADA
    )
    assert segunda.reutilizada is True
    assert segunda.compra_id == primera.compra_id
    assert segunda.orden_pago_id == primera.orden_pago_id
    assert Compra.objects.count() == 1


def test_una_cantidad_invalida_se_rechaza(flujo, inscripcion):
    """GIVEN una cantidad que no está dentro de los límites de dominio
    WHEN  se intenta comprar
    THEN  se rechaza con `CUPO_INVALIDO` (422), el código CONGELADO por el
       ledger para `RT-CM-01`.
    """
    with pytest.raises(CupoInvalidoError):
        async_to_sync(flujo.comprar_cupos)(
            CompraCuposData(inscripcion_id=inscripcion.id, cantidad=0)
        )

    assert Compra.objects.count() == 0


def test_una_cantidad_que_supera_el_tope_se_rechaza(flujo, inscripcion):
    """GIVEN una cantidad por encima del máximo de ampliación
    WHEN  se intenta comprar
    THEN  se rechaza con `CUPO_INVALIDO`: el límite lo declara el servidor
       (`FL-04` paso 2).
    """
    from modules.salesianos_fest.domain.constants import MAX_CUPOS_POR_AMPLIACION

    with pytest.raises(CupoInvalidoError):
        async_to_sync(flujo.comprar_cupos)(
            CompraCuposData(
                inscripcion_id=inscripcion.id,
                cantidad=MAX_CUPOS_POR_AMPLIACION + 1,
            )
        )

    assert Compra.objects.count() == 0


def test_un_paquete_sin_precio_vigente_no_se_amplia(
    flujo, edicion_publicada, persona, paquete_sin_precio, disciplina, promocion
):
    """GIVEN un paquete SIN precio vigente
    WHEN  se intenta ampliar
    THEN  se rechaza con `PAQUETE_NO_VIGENTE` (409): no hay precio de
       reserva inventado (`FL-01` paso 3).
    """
    inscripcion = Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona,
        paquete=paquete_sin_precio,
        promocion=promocion,
        referencia="INS-TEST-SIN-PRECIO",
        cupos_solicitados=5,
    )

    with pytest.raises(PaqueteNoVigenteError):
        async_to_sync(flujo.comprar_cupos)(
            CompraCuposData(inscripcion_id=inscripcion.id, cantidad=2)
        )

    assert Compra.objects.count() == 0


def test_un_paquete_retirado_no_se_amplia(
    flujo, edicion_publicada, persona, paquete_retirado, disciplina, promocion
):
    """GIVEN un paquete RETIRADO
    WHEN  se intenta ampliar
    THEN  se rechaza con `PAQUETE_NO_VIGENTE` (409).
    """
    inscripcion = Inscripcion.objects.create(
        edicion=edicion_publicada,
        responsable=persona,
        paquete=paquete_retirado,
        promocion=promocion,
        referencia="INS-TEST-RETIRADO",
        cupos_solicitados=5,
    )

    with pytest.raises(PaqueteNoVigenteError):
        async_to_sync(flujo.comprar_cupos)(
            CompraCuposData(inscripcion_id=inscripcion.id, cantidad=2)
        )

    assert Compra.objects.count() == 0


def test_un_actor_ajeno_no_compra_cupos(
    orchestrator, inscripcion, usuario_ajeno
):
    """GIVEN una cuenta que NO es la responsable de la inscripción
    WHEN  intenta comprar cupos extra
    THEN  se rechaza con `COMPRA_NO_AUTORIZADA` (403), el código CONGELADO
       por el ledger para `RT-CM-01`.
    """
    with pytest.raises(CompraNoAutorizadaError):
        async_to_sync(orchestrator.comprar_cupos)(
            usuario_ajeno,
            inscripcion.id,
            CompraCuposData(cantidad=3),
        )

    assert Compra.objects.count() == 0


def test_el_responsable_compra_cupos_extra(
    orchestrator, inscripcion, usuario_responsable, precio
):
    """GIVEN la cuenta responsable de la inscripción
    WHEN  compra cupos extra
    THEN  la compra se crea y la capacidad sigue intacta hasta el pago.
    """
    resultado = async_to_sync(orchestrator.comprar_cupos)(
        usuario_responsable,
        inscripcion.id,
        CompraCuposData(cantidad=3),
    )

    assert resultado.cupos_solicitados == 3
    assert resultado.cupos_pagados == 10
    assert resultado.cupos_disponibles == 10
    assert Compra.objects.count() == 1


def test_una_inscripcion_inexistente_se_rechaza(flujo):
    """GIVEN un identificador de inscripción que no existe
    WHEN  se intenta ampliar
    THEN  se rechaza con `INSCRIPCION_NO_ENCONTRADA` (404).
    """
    from uuid import uuid4

    from modules.salesianos_fest.domain.exceptions import (
        InscripcionNoEncontradaError,
    )

    with pytest.raises(InscripcionNoEncontradaError):
        async_to_sync(flujo.comprar_cupos)(
            CompraCuposData(inscripcion_id=uuid4(), cantidad=1)
        )
