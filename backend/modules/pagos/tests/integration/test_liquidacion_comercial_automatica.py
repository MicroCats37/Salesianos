"""
Focused integration tests for the automatic commercial settlement.

Covers the backend-owned settlement of a paid order (Phase 2 of
izipay-automatic-commercial-confirmation):

- A verified payment drives the commercial settlement from the backend — no
  second browser request is involved.
- The settlement is re-driven on the idempotent path, so a retry after a
  partial failure converges.
- A settlement failure never rolls back the recorded payment.
- A failed payment never triggers a settlement.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock

from asgiref.sync import sync_to_async

from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus, SettlementStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import (
    RegistrarPagoIzipayFlujo,
)
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.infrastructure import VerificadorFirmaIzipay
from modules.pagos.tests.fixtures.settlement_fakes import ConfirmadorOrdenPagoFake

# The authenticated caller of the browser relay.
PERSONA_PROPIETARIA = "11111111-1111-4111-8111-111111111111"


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def izipay_core_service():
    """IzipayCoreService instance."""
    return IzipayCoreService()


@pytest.fixture
def orden_pago(izipay_core_service):
    """A PENDIENTE OrdenPago ready to be paid."""
    return izipay_core_service.crear_orden_pago(
        numero=izipay_core_service.generar_numero_orden(),
        monto_total=Decimal("100.00"),
        moneda="PEN",
    )


@pytest.fixture
def transaccion_pendiente(izipay_core_service, orden_pago):
    """A PENDIENTE TransaccionPago for the order."""
    transaction_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden_pago.id),
        transaction_id=transaction_id,
        order_number="ORDER-SETTLE",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    return transaction_id


def _kr_answer(transaction_id: str, code: str = "00") -> dict:
    """Build a minimal kr_answer for the given transaction."""
    return {
        "code": code,
        "message": "Operación exitosa" if code == "00" else "Operación rechazada",
        "transactionId": transaction_id,
        "response": {"payMethod": "CARD"},
    }


def _flujo(
    izipay_core_service,
    confirmador,
    propietario,
    verificador=None,
) -> RegistrarPagoIzipayFlujo:
    """Build the flow with the fake settlement port and the trust doubles."""
    return RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        izipay_client=AsyncMock(),
        confirmador_orden_pago=confirmador,
        propietario_orden_pago=propietario,
        verificador_firma=verificador or VerificadorFirmaIzipay(key_hash=""),
        verificacion_pago=VerificacionPagoService(),
    )


# ── Tests ────────────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_pago_dispara_liquidacion_comercial(
    izipay_core_service, orden_pago, transaccion_pendiente, confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A pending order with a pending transaction
    WHEN:  the payment is confirmed with code="00"
    THEN:  the backend drives the commercial settlement for that order
    AND    the payment is recorded as paid
    """
    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    result = await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente))

    assert result.success is True
    assert result.status == IzipayStatus.EXITO
    assert result.settlement_status == SettlementStatus.SETTLED

    # The backend — not the browser — triggered the settlement
    assert confirmador_orden_pago.llamadas == [str(orden_pago.id)]

    orden_actualizada = await sync_to_async(OrdenPago.objects.get)(id=orden_pago.id)
    assert orden_actualizada.estado == OrdenPagoStatus.PAGADA


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_pago_idempotente_vuelve_a_liquidar(
    izipay_core_service, orden_pago, transaccion_pendiente, confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: An order already confirmed and settled
    WHEN:  the same confirmation is replayed
    THEN:  the commercial settlement is re-driven (it is idempotent)
    AND    no duplicate payment record is created
    """
    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente))
    segundo = await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente))

    assert segundo.already_confirmed is True
    assert segundo.settlement_status == SettlementStatus.SETTLED
    assert confirmador_orden_pago.llamadas == [str(orden_pago.id), str(orden_pago.id)]

    total_transacciones = await sync_to_async(TransaccionPago.objects.count)()
    assert total_transacciones == 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_fallo_liquidacion_no_revierte_el_pago(
    izipay_core_service, orden_pago, transaccion_pendiente, propietario_orden_pago
):
    """
    GIVEN: A commercial settlement that fails
    WHEN:  the payment is confirmed with code="00"
    THEN:  the payment stays recorded (transaction EXITO, order PAGADA)
    AND    the activation is reported as pending, not as settled
    """
    confirmador = ConfirmadorOrdenPagoFake(error=RuntimeError("boom"))
    flujo = _flujo(izipay_core_service, confirmador, propietario_orden_pago)

    result = await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente))

    assert result.success is True
    assert result.settlement_status == SettlementStatus.PENDING

    transaccion = await sync_to_async(TransaccionPago.objects.get)(
        transaction_id=transaccion_pendiente
    )
    assert transaccion.status == IzipayStatus.EXITO

    orden_actualizada = await sync_to_async(OrdenPago.objects.get)(id=orden_pago.id)
    assert orden_actualizada.estado == OrdenPagoStatus.PAGADA


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_reintento_tras_fallo_liquida_la_compra(
    izipay_core_service, orden_pago, transaccion_pendiente, propietario_orden_pago
):
    """
    GIVEN: A confirmation whose settlement failed
    WHEN:  the confirmation is replayed and the settlement succeeds
    THEN:  the activation converges to SETTLED
    """
    confirmador = ConfirmadorOrdenPagoFake(error=RuntimeError("boom"))
    flujo = _flujo(izipay_core_service, confirmador, propietario_orden_pago)

    primero = await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente))
    assert primero.settlement_status == SettlementStatus.PENDING

    # The retry finds the settlement working — the payment was already EXITO
    confirmador.error = None
    segundo = await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente))

    assert segundo.already_confirmed is True
    assert segundo.settlement_status == SettlementStatus.SETTLED
    assert confirmador.llamadas == [str(orden_pago.id), str(orden_pago.id)]


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_pago_fallido_no_liquida_comercial(
    izipay_core_service, orden_pago, transaccion_pendiente, confirmador_orden_pago,
    propietario_orden_pago,
):
    """
    GIVEN: A payment that the provider did not approve
    WHEN:  the confirmation is processed with code="05"
    THEN:  no commercial settlement is triggered
    AND    the result reports NOT_APPLICABLE
    """
    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    result = await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente, code="05")
    )

    assert result.success is False
    assert result.status == IzipayStatus.FALLIDO
    assert result.settlement_status == SettlementStatus.NOT_APPLICABLE
    assert confirmador_orden_pago.llamadas == []

    orden_actualizada = await sync_to_async(OrdenPago.objects.get)(id=orden_pago.id)
    assert orden_actualizada.estado == OrdenPagoStatus.PENDIENTE


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_liquidacion_sin_compra_no_afirma_exito(
    izipay_core_service, orden_pago, transaccion_pendiente, propietario_orden_pago
):
    """
    GIVEN: A settlement with nothing to settle (no purchase linked)
    WHEN:  the payment is confirmed
    THEN:  the result does not claim a completed activation
    """
    confirmador = ConfirmadorOrdenPagoFake(settled=False)
    flujo = _flujo(izipay_core_service, confirmador, propietario_orden_pago)

    result = await flujo._confirmar_pago(
        persona_id=PERSONA_PROPIETARIA,
        kr_answer=_kr_answer(transaccion_pendiente))

    assert result.success is True
    assert result.settlement_status == SettlementStatus.PENDING
