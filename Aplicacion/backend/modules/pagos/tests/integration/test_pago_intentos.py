"""El ciclo de vida del intento de pago: reabrir el checkout.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §1.3, §2.1 I-4, I-5; RN-C03, RN-C04)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

| Test | Garantía congelada |
|---|---|
| `test_reabrir_el_checkout_crea_un_intento_nuevo` | I-4 — la orden no se duplica |
| `test_el_intento_anterior_se_conserva_como_historial` | RN-C04 — trazabilidad de todo intento |
| `test_reabrir_el_checkout_no_crea_otra_orden` | I-4 — ni otra compra ni otra orden |
| `test_una_orden_pagada_no_admite_un_intento_nuevo` | I-1 — una orden confirmada se queda |
"""

import pytest
from asgiref.sync import async_to_sync

from modules.pagos.domain.constants import EstadoOrdenPago, EstadoTransaccionPago
from modules.pagos.domain.exceptions import (
    OrdenPagoNoEncontradaError,
    OrdenPagoNoPagableError,
)
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.flujos.pago_intento_flujo import PagoIntentoFlujo

pytestmark = pytest.mark.django_db


@pytest.fixture
def flujo(injector):
    """El flujo real de intentos."""
    return injector.get(PagoIntentoFlujo)


def test_reabrir_el_checkout_crea_un_intento_nuevo(flujo, orden_pago, intento):
    """GIVEN una orden con un intento vivo
    WHEN  se reabre el checkout
    THEN  se crea un intento NUEVO con su propia identidad y su propio ordinal.
    """
    resultado = async_to_sync(flujo.abrir_intento)(str(orden_pago.id))

    assert resultado.intento == 2
    assert resultado.estado == EstadoTransaccionPago.PENDIENTE
    assert resultado.referencia_proveedor != intento.referencia_proveedor


def test_el_intento_anterior_se_conserva_como_historial(flujo, orden_pago, intento):
    """GIVEN una orden con un intento vivo
    WHEN  se reabre el checkout
    THEN  el intento anterior queda RETIRADO, nunca borrado (RN-C04).
    """
    async_to_sync(flujo.abrir_intento)(str(orden_pago.id))

    intento.refresh_from_db()
    assert intento.estado == EstadoTransaccionPago.CANCELADO
    assert TransaccionPago.objects.filter(orden_pago=orden_pago).count() == 2


def test_reabrir_el_checkout_no_crea_otra_orden(flujo, orden_pago, compra, intento):
    """GIVEN una compra pendiente con su orden
    WHEN  se reabre el checkout
    THEN  sigue habiendo UNA compra y UNA orden: no se duplica nada.
    """
    async_to_sync(flujo.abrir_intento)(str(orden_pago.id))

    assert OrdenPago.objects.count() == 1
    assert compra.orden_pago_id == orden_pago.id


def test_solo_hay_un_intento_vivo_por_orden(flujo, orden_pago, intento):
    """GIVEN una orden con un intento vivo
    WHEN  se reabre el checkout dos veces
    THEN  queda UN solo intento vivo: los anteriores están cerrados.
    """
    async_to_sync(flujo.abrir_intento)(str(orden_pago.id))
    async_to_sync(flujo.abrir_intento)(str(orden_pago.id))

    vivos = TransaccionPago.objects.filter(
        orden_pago=orden_pago,
        estado=EstadoTransaccionPago.PENDIENTE,
    )
    assert vivos.count() == 1
    assert TransaccionPago.objects.filter(orden_pago=orden_pago).count() == 3


def test_una_orden_pagada_no_admite_un_intento_nuevo(flujo, orden_pago, intento):
    """GIVEN una orden ya CONFIRMADA
    WHEN  se reabre el checkout
    THEN  se rechaza con ORDEN_PAGO_NO_PAGABLE: no se cobra dos veces.
    """
    orden_pago.estado = EstadoOrdenPago.CONFIRMADA
    orden_pago.save(update_fields=["estado"])

    with pytest.raises(OrdenPagoNoPagableError):
        async_to_sync(flujo.abrir_intento)(str(orden_pago.id))

    assert TransaccionPago.objects.filter(orden_pago=orden_pago).count() == 1


def test_una_orden_inexistente_no_admite_un_intento(flujo, db):
    """GIVEN una orden que no existe
    WHEN  se reabre el checkout
    THEN  se rechaza con ORDEN_PAGO_NO_ENCONTRADA.
    """
    with pytest.raises(OrdenPagoNoEncontradaError):
        async_to_sync(flujo.abrir_intento)(
            "00000000-0000-0000-0000-000000000000"
        )
