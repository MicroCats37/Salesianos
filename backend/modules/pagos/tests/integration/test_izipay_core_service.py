"""
Integration tests for IzipayCoreService.

Tests:
- test_crear_orden_pago_crea_orden_pendiente
- test_crear_transaccion_guarda_orden_pago FK
- test_crear_transaccion_guarda_amount_snapshot
- test_actualizar_estado_exito_cambia_status
- test_actualizar_estado_fallido_cambia_status
- test_actualizar_estado_cancelado_cambia_status
- test_es_duplicada_retorna_true_cuando_existe
- test_es_duplicada_retorna_false_cuando_no_existe
"""
import pytest
from decimal import Decimal
from asgiref.sync import sync_to_async

from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.domain.exceptions import TransaccionDuplicadaError
from modules.pagos.infrastructure import VerificadorFirmaIzipay

# The authenticated caller of the browser relay.
PERSONA_PROPIETARIA = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def izipay_core_service():
    """IzipayCoreService instance."""
    return IzipayCoreService()


def _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """Build the flow with the test doubles for the trust dependencies."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import (
        RegistrarPagoIzipayFlujo,
    )

    return RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        izipay_client=AsyncMock(),
        confirmador_orden_pago=confirmador_orden_pago,
        propietario_orden_pago=propietario_orden_pago,
        verificador_firma=VerificadorFirmaIzipay(key_hash=""),
        verificacion_pago=VerificacionPagoService(),
    )


def _crear_orden_pago(izipay_core_service):
    """Helper to create an OrdenPago (sync)."""
    numero = izipay_core_service.generar_numero_orden()
    return izipay_core_service.crear_orden_pago(
        numero=numero,
        monto_total=Decimal("100.00"),
        moneda="PEN",
    )


# ── OrdenPago tests ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_crear_orden_pago_crea_orden_pendiente(izipay_core_service):
    """
    GIVEN: A generated order number
    WHEN: crear_orden_pago is called
    THEN: An OrdenPago is created with estado=PENDIENTE.
    """
    numero = izipay_core_service.generar_numero_orden()
    orden = izipay_core_service.crear_orden_pago(
        numero=numero,
        monto_total=Decimal("100.00"),
        moneda="PEN",
    )
    assert orden.estado == OrdenPagoStatus.PENDIENTE
    assert orden.monto_total == Decimal("100.00")
    assert orden.moneda == "PEN"
    assert orden.numero == numero


# ── Core service tests (sync) ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_crear_transaccion_genera_transaction_id_14_digitos(
    izipay_core_service,
):
    """
    GIVEN: A valid OrdenPago
    WHEN: generar_transaction_id is called
    THEN: A 14-digit string is returned.
    """
    _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    assert len(tx_id) == 14
    assert tx_id.isdigit()


@pytest.mark.django_db
def test_crear_transaccion_guarda_orden_pago_fk(
    izipay_core_service,
):
    """
    GIVEN: A valid OrdenPago
    WHEN: crear_transaccion is called
    THEN: The TransaccionPago is linked to the OrdenPago.
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    tx = izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER003",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    assert str(tx.orden_pago_id) == str(orden.id)


@pytest.mark.django_db
def test_crear_transaccion_guarda_amount_snapshot(
    izipay_core_service,
):
    """
    GIVEN: A valid OrdenPago
    WHEN: crear_transaccion is called
    THEN: The amount is stored as a snapshot on TransaccionPago.
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    tx = izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER003",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    assert tx.amount == Decimal("100.00")
    assert tx.currency == "PEN"


@pytest.mark.django_db
def test_crear_transaccion_duplicada_raises(
    izipay_core_service,
):
    """
    GIVEN: An existing transaction with transaction_id
    WHEN: crear_transaccion is called again with the same transaction_id
    THEN: TransaccionDuplicadaError is raised.
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER004",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    with pytest.raises(TransaccionDuplicadaError):
        izipay_core_service.crear_transaccion(
            orden_pago_id=str(orden.id),
            transaction_id=tx_id,
            order_number="ORDER005",
            amount=Decimal("100.00"),
            currency="PEN",
        )


@pytest.mark.django_db
def test_actualizar_estado_exito_cambia_status(
    izipay_core_service,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with status=EXITO
    THEN: The transaction status is updated to EXITO.
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER006",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    updated = izipay_core_service.actualizar_estado(
        transaction_id=tx_id,
        status=IzipayStatus.EXITO,
        response_code="00",
        response_message="Success",
        metodo_pago="CARD",
        metadata={"payMethod": "CARD"},
    )
    assert updated is not None
    assert updated.status == IzipayStatus.EXITO
    assert updated.response_code == "00"
    assert updated.metodo_pago == "CARD"


@pytest.mark.django_db
def test_actualizar_estado_fallido_cambia_status(
    izipay_core_service,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with status=FALLIDO
    THEN: The transaction status is updated to FALLIDO.
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER007",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    updated = izipay_core_service.actualizar_estado(
        transaction_id=tx_id,
        status=IzipayStatus.FALLIDO,
        response_code="05",
        response_message="Card declined",
        metodo_pago="CARD",
        metadata={},
    )
    assert updated is not None
    assert updated.status == IzipayStatus.FALLIDO
    assert updated.response_code == "05"


@pytest.mark.django_db
def test_actualizar_estado_cancelado_cambia_status(
    izipay_core_service,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with status=CANCELADO
    THEN: The transaction status is updated to CANCELADO.
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER007B",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    updated = izipay_core_service.actualizar_estado(
        transaction_id=tx_id,
        status=IzipayStatus.CANCELADO,
        response_code="111",
        response_message="Cancelled by user",
        metodo_pago="",
        metadata={},
    )
    assert updated is not None
    assert updated.status == IzipayStatus.CANCELADO
    assert updated.response_code == "111"


@pytest.mark.django_db
def test_actualizar_estado_metadata_none_no_falla(
    izipay_core_service,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with metadata=None
    THEN: The update succeeds — None is safely converted to {}.

    This is a regression test for the defect where actualizar_estado
    passed metadata=None directly to Django's ORM .update(), which would fail when
    the JSONField has null=False (enforced by Django's model definition).
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER014",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    # Explicitly pass metadata=None — this must NOT raise
    updated = izipay_core_service.actualizar_estado(
        transaction_id=tx_id,
        status=IzipayStatus.EXITO,
        response_code="00",
        response_message="OK",
        metodo_pago="CARD",
        metadata=None,  # explicit None — the regression case
    )
    assert updated is not None
    assert updated.status == IzipayStatus.EXITO
    assert updated.metadata == {}


@pytest.mark.django_db
def test_es_duplicada_retorna_true_cuando_existe(
    izipay_core_service,
):
    """
    GIVEN: An existing transaction with transaction_id=X
    WHEN: es_duplicada is called with X
    THEN: True is returned.
    """
    orden = _crear_orden_pago(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER008",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    assert izipay_core_service.es_duplicada(tx_id) is True


@pytest.mark.django_db
def test_es_duplicada_retorna_false_cuando_no_existe(
    izipay_core_service,
):
    """
    GIVEN: No transaction with transaction_id=X exists
    WHEN: es_duplicada is called with X
    THEN: False is returned.
    """
    assert izipay_core_service.es_duplicada("NONEXISTENT12345") is False


# ── Marcar orden pagada ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_marcar_orden_pagada_cambia_estado(izipay_core_service):
    """
    GIVEN: A PENDIENTE OrdenPago
    WHEN: marcar_orden_pagada is called
    THEN: The orden estado is updated to PAGADA and pagada_en is set.
    """
    orden = _crear_orden_pago(izipay_core_service)
    assert orden.estado == OrdenPagoStatus.PENDIENTE

    updated = izipay_core_service.marcar_orden_pagada(orden)
    assert updated.estado == OrdenPagoStatus.PAGADA
    assert updated.pagada_en is not None


@pytest.mark.django_db
def test_cancelar_orden_pago_cambia_estado(izipay_core_service):
    """
    GIVEN: A PENDIENTE OrdenPago
    WHEN: cancelar_orden_pago is called
    THEN: The orden estado is updated to CANCELADA.
    """
    orden = _crear_orden_pago(izipay_core_service)
    updated = izipay_core_service.cancelar_orden_pago(orden)
    assert updated.estado == OrdenPagoStatus.CANCELADA


# ── Izipay flujo integration tests (async) ─────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_prepare_guarda_transaccion_pendiente(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """GIVEN: OrdenPago. WHEN: _preparar_pago called. THEN: PENDIENTE tx persisted."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo

    orden = await sync_to_async(_crear_orden_pago)(izipay_core_service)

    mock_client = AsyncMock()
    mock_client.shop_id = "SHOP123"
    mock_client.generar_token_sesion = AsyncMock(return_value={
        "token": "test-jwt-token-abc123",
        "response": {"token": "test-jwt-token-abc123"}
    })

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        izipay_client=mock_client,
        confirmador_orden_pago=confirmador_orden_pago,
        propietario_orden_pago=propietario_orden_pago,
        verificador_firma=VerificadorFirmaIzipay(key_hash=""),
        verificacion_pago=VerificacionPagoService(),
    )

    result = await flujo._preparar_pago(
        orden_pago_id=str(orden.id),
        buyer_email="test@example.com",
        buyer_name="Juan",
        buyer_surname="Perez",
    )

    tx = await sync_to_async(TransaccionPago.objects.get)(transaction_id=result.transaction_id)
    assert tx.status == IzipayStatus.PENDIENTE
    assert tx.orden_pago_id == orden.id
    assert result.token == "test-jwt-token-abc123"
    assert result.merchant_code == "SHOP123"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_codigo_00_transiciona_a_exito_y_orden_pagada(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """GIVEN: PENDIENTE tx. WHEN: kr_answer code=00. THEN: tx EXITO, orden PAGADA."""

    orden = await sync_to_async(_crear_orden_pago)(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        orden_pago_id=str(orden.id),
        transaction_id=tx_id,
        order_number="ORDER009",
        amount=Decimal("100.00"),
        currency="PEN",
    )

    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    kr_answer = {
        "code": "00", "message": "Operación exitosa", "transactionId": tx_id,
        "response": {"payMethod": "CARD", "order": [{"orderNumber": "ORDER009", "amount": "100.00"}]}
    }

    result = await flujo._confirmar_pago(persona_id=PERSONA_PROPIETARIA, kr_answer=kr_answer)

    assert result.success is True
    assert result.status == IzipayStatus.EXITO
    assert result.response_code == "00"

    # Verify orden is now PAGADA
    orden_updated = await sync_to_async(OrdenPago.objects.get)(id=orden.id)
    assert orden_updated.estado == OrdenPagoStatus.PAGADA


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_idempotente_no_duplica(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """GIVEN: EXITO tx. WHEN: _confirmar_pago called again. THEN: already_confirmed=True."""

    orden = await sync_to_async(_crear_orden_pago)(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        orden_pago_id=str(orden.id), transaction_id=tx_id,
        order_number="ORDER010", amount=Decimal("100.00"), currency="PEN",
    )
    await sync_to_async(izipay_core_service.actualizar_estado)(
        transaction_id=tx_id, status=IzipayStatus.EXITO,
        response_code="00", response_message="OK", metodo_pago="CARD", metadata={},
    )

    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    result = await flujo._confirmar_pago(persona_id=PERSONA_PROPIETARIA, kr_answer={"code": "00", "message": "OK", "transactionId": tx_id})

    assert result.already_confirmed is True
    assert result.success is True


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_codigo_no_00_es_fallido(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """GIVEN: PENDIENTE tx. WHEN: kr_answer code=05. THEN: tx FALLIDO, orden unchanged."""

    orden = await sync_to_async(_crear_orden_pago)(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        orden_pago_id=str(orden.id), transaction_id=tx_id,
        order_number="ORDER011", amount=Decimal("100.00"), currency="PEN",
    )

    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    result = await flujo._confirmar_pago(persona_id=PERSONA_PROPIETARIA, kr_answer={"code": "05", "message": "Card declined", "transactionId": tx_id})

    assert result.success is False
    assert result.status == IzipayStatus.FALLIDO

    # Verify orden is still PENDIENTE
    orden_updated = await sync_to_async(OrdenPago.objects.get)(id=orden.id)
    assert orden_updated.estado == OrdenPagoStatus.PENDIENTE


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_transactionid_no_existente_raises(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """GIVEN: no tx. WHEN: kr_answer with unknown transactionId. THEN: 404 error."""
    from modules.pagos.domain.exceptions import TransaccionPagoNoEncontradaError

    await sync_to_async(_crear_orden_pago)(izipay_core_service)

    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    with pytest.raises(TransaccionPagoNoEncontradaError):
        await flujo._confirmar_pago(persona_id=PERSONA_PROPIETARIA, kr_answer={"code": "00", "transactionId": "99999999999999"})


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_sanitiza_metadata(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """GIVEN: PENDIENTE tx. WHEN: kr_answer has sensitive fields. THEN: metadata stripped."""

    orden = await sync_to_async(_crear_orden_pago)(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        orden_pago_id=str(orden.id), transaction_id=tx_id,
        order_number="ORDER012", amount=Decimal("100.00"), currency="PEN",
    )

    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    kr_answer = {
        "code": "00", "message": "OK", "transactionId": tx_id,
        "pan": "4111111111111111", "cvv": "123",
        "cardToken": "tok_secret_123", "privateKey": "secret_key_xyz",
        "payMethod": "CARD", "response": {"cardScheme": "VISA"},
    }

    await flujo._confirmar_pago(persona_id=PERSONA_PROPIETARIA, kr_answer=kr_answer)

    tx = await sync_to_async(TransaccionPago.objects.get)(transaction_id=tx_id)
    metadata = tx.metadata

    assert "pan" not in metadata
    assert "cvv" not in metadata
    assert "cardToken" not in metadata
    assert "privateKey" not in metadata
    assert "payMethod" in metadata or "response" in metadata


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_metadata_no_contiene_izipayshopid_ni_secret(izipay_core_service, confirmador_orden_pago, propietario_orden_pago):
    """GIVEN: kr_answer with credential fields. WHEN: processed. THEN: stripped from metadata."""

    orden = await sync_to_async(_crear_orden_pago)(izipay_core_service)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        orden_pago_id=str(orden.id), transaction_id=tx_id,
        order_number="ORDER013", amount=Decimal("100.00"), currency="PEN",
    )

    flujo = _flujo(izipay_core_service, confirmador_orden_pago, propietario_orden_pago)

    kr_answer = {
        "code": "00", "message": "OK", "transactionId": tx_id,
        "izipayKey": "pk_test_123", "shopId": "SHOP123",
        "secretKey": "sk_test_456", "apiKey": "api_test_789",
    }

    await flujo._confirmar_pago(persona_id=PERSONA_PROPIETARIA, kr_answer=kr_answer)

    tx = await sync_to_async(TransaccionPago.objects.get)(transaction_id=tx_id)
    assert "izipayKey" not in tx.metadata
    assert "shopId" not in tx.metadata
    assert "secretKey" not in tx.metadata
    assert "apiKey" not in tx.metadata
