"""
Integration tests for IzipayCoreService.

Tests:
- test_crear_transaccion_genera_transaction_id_unico
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

from modules.pagos.domain.models import IzipayTransaccion
from modules.pagos.domain.constants import IzipayStatus
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.exceptions import TransaccionDuplicadaError


@pytest.fixture
def izipay_core_service():
    """IzipayCoreService instance."""
    return IzipayCoreService()


def _crear_inscripcion(base_setup, usuario):
    """Helper to create an Inscripcion from base_setup (sync)."""
    from modules.inscripciones.domain.models import Inscripcion
    from modules.inscripciones.domain.constants import EstadoInscripcionChoices
    return Inscripcion.objects.create(
        evento=base_setup["evento"],
        responsable=usuario.persona_fk,
        paquete=base_setup["paquete"],
        promocion=base_setup["promocion"],
        estado=EstadoInscripcionChoices.PAGO_PENDIENTE,
    )


# ── Core service tests (sync) ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_crear_transaccion_genera_transaction_id_14_digitos(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: A valid inscription
    WHEN: generar_transaction_id is called
    THEN: A 14-digit string is returned.
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    assert len(tx_id) == 14
    assert tx_id.isdigit()


@pytest.mark.django_db
def test_crear_transaccion_guarda_amount_snapshot(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: A valid inscription with a paquete (precio_regular set)
    WHEN: crear_transaccion is called with precio_promocional (if set) or precio_regular
    THEN: The amount is stored as a snapshot on IzipayTransaccion.
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    paquete = base_inscripcion_setup["paquete"]
    precio_a_cobrar = (
        paquete.precio_promocional
        if paquete.precio_promocional is not None
        else paquete.precio_regular
    )
    tx_id = izipay_core_service.generar_transaction_id()
    tx = izipay_core_service.crear_transaccion(
        inscripcion_id=str(inscripcion.id),
        transaction_id=tx_id,
        order_number="ORDER003",
        amount=precio_a_cobrar,
        currency="PEN",
    )
    assert tx.amount == precio_a_cobrar
    assert tx.currency == "PEN"


@pytest.mark.django_db
def test_crear_transaccion_duplicada_raises(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: An existing transaction with transaction_id
    WHEN: crear_transaccion is called again with the same transaction_id
    THEN: TransaccionDuplicadaError is raised.
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        inscripcion_id=str(inscripcion.id),
        transaction_id=tx_id,
        order_number="ORDER004",
        amount=Decimal("100.00"),
        currency="PEN",
    )
    with pytest.raises(TransaccionDuplicadaError):
        izipay_core_service.crear_transaccion(
            inscripcion_id=str(inscripcion.id),
            transaction_id=tx_id,
            order_number="ORDER005",
            amount=Decimal("100.00"),
            currency="PEN",
        )


@pytest.mark.django_db
def test_actualizar_estado_exito_cambia_status(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with status=EXITO and response_code=00
    THEN: The transaction status is updated to EXITO.
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        inscripcion_id=str(inscripcion.id),
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
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with status=FALLIDO and a non-00 code
    THEN: The transaction status is updated to FALLIDO.
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        inscripcion_id=str(inscripcion.id),
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
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with status=CANCELADO (code 111)
    THEN: The transaction status is updated to CANCELADO.
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        inscripcion_id=str(inscripcion.id),
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
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: A PENDIENTE transaction
    WHEN: actualizar_estado is called with metadata=None (explicit None)
    THEN: The update succeeds — None is safely converted to {} (JSONField null=False guard).

    This is a regression test for the defect where IzipayCoreService.actualizar_estado
    passed metadata=None directly to Django's ORM .update(), which would fail when
    the JSONField has null=False (enforced by Django's model definition).
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        inscripcion_id=str(inscripcion.id),
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
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: An existing transaction with transaction_id=X
    WHEN: es_duplicada is called with X
    THEN: True is returned.
    """
    inscripcion = _crear_inscripcion(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    izipay_core_service.crear_transaccion(
        inscripcion_id=str(inscripcion.id),
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


# ── Izipay Perú flujo integration tests (async) ─────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_prepare_guarda_transaccion_pendiente(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """GIVEN: inscription. WHEN: _preparar_pago called. THEN: PENDIENTE tx persisted."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
    from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService

    inscripcion = await sync_to_async(_crear_inscripcion)(base_inscripcion_setup, usuario_con_persona)

    mock_client = AsyncMock()
    mock_client.shop_id = "SHOP123"
    mock_client.generar_token_sesion = AsyncMock(return_value={
        "token": "test-jwt-token-abc123",
        "response": {"token": "test-jwt-token-abc123"}
    })

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        inscripcion_svc=InscripcionService(),
        izipay_client=mock_client,
    )

    result = await flujo._preparar_pago(
        inscripcion_id=str(inscripcion.id),
        buyer_email="test@example.com",
        buyer_name="Juan",
        buyer_surname="Perez",
    )

    tx = await sync_to_async(IzipayTransaccion.objects.get)(transaction_id=result.transaction_id)
    assert tx.status == IzipayStatus.PENDIENTE
    assert tx.inscripcion_id == inscripcion.id
    assert result.token == "test-jwt-token-abc123"
    assert result.merchant_code == "SHOP123"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_codigo_00_transiciona_a_exito(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """GIVEN: PENDIENTE tx. WHEN: kr_answer code=00. THEN: tx EXITO, inscripcion PAGADA."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
    from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService
    from modules.inscripciones.domain.constants import EstadoInscripcionChoices
    from modules.inscripciones.domain.models import Inscripcion

    inscripcion = await sync_to_async(_crear_inscripcion)(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        inscripcion_id=str(inscripcion.id),
        transaction_id=tx_id,
        order_number="ORDER009",
        amount=Decimal("100.00"),
        currency="PEN",
    )

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        inscripcion_svc=InscripcionService(),
        izipay_client=AsyncMock(),
    )

    kr_answer = {
        "code": "00", "message": "Operación exitosa", "transactionId": tx_id,
        "response": {"payMethod": "CARD", "order": [{"orderNumber": "ORDER009", "amount": "100.00"}]}
    }

    result = await flujo._confirmar_pago(kr_answer=kr_answer)

    assert result.success is True
    assert result.status == IzipayStatus.EXITO
    assert result.response_code == "00"

    inscripcion_updated = await sync_to_async(Inscripcion.objects.get)(id=inscripcion.id)
    assert inscripcion_updated.estado == EstadoInscripcionChoices.PAGADA


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_idempotente_no_duplica(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """GIVEN: EXITO tx. WHEN: _confirmar_pago called again. THEN: already_confirmed=True."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
    from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService

    inscripcion = await sync_to_async(_crear_inscripcion)(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        inscripcion_id=str(inscripcion.id), transaction_id=tx_id,
        order_number="ORDER010", amount=Decimal("100.00"), currency="PEN",
    )
    await sync_to_async(izipay_core_service.actualizar_estado)(
        transaction_id=tx_id, status=IzipayStatus.EXITO,
        response_code="00", response_message="OK", metodo_pago="CARD", metadata={},
    )

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        inscripcion_svc=InscripcionService(),
        izipay_client=AsyncMock(),
    )

    result = await flujo._confirmar_pago(kr_answer={"code": "00", "message": "OK", "transactionId": tx_id})

    assert result.already_confirmed is True
    assert result.success is True


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_codigo_no_00_es_fallido(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """GIVEN: PENDIENTE tx. WHEN: kr_answer code=05. THEN: tx FALLIDO, inscripcion unchanged."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
    from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService
    from modules.inscripciones.domain.constants import EstadoInscripcionChoices
    from modules.inscripciones.domain.models import Inscripcion

    inscripcion = await sync_to_async(_crear_inscripcion)(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        inscripcion_id=str(inscripcion.id), transaction_id=tx_id,
        order_number="ORDER011", amount=Decimal("100.00"), currency="PEN",
    )

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        inscripcion_svc=InscripcionService(),
        izipay_client=AsyncMock(),
    )

    result = await flujo._confirmar_pago(kr_answer={"code": "05", "message": "Card declined", "transactionId": tx_id})

    assert result.success is False
    assert result.status == IzipayStatus.FALLIDO

    inscripcion_updated = await sync_to_async(Inscripcion.objects.get)(id=inscripcion.id)
    assert inscripcion_updated.estado == EstadoInscripcionChoices.PAGO_PENDIENTE


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_transactionid_no_existente_raises(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """GIVEN: no tx. WHEN: kr_answer with unknown transactionId. THEN: IzipayError."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
    from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService
    from modules.pagos.domain.exceptions import IzipayError

    await sync_to_async(_crear_inscripcion)(base_inscripcion_setup, usuario_con_persona)

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        inscripcion_svc=InscripcionService(),
        izipay_client=AsyncMock(),
    )

    with pytest.raises(IzipayError, match="not found"):
        await flujo._confirmar_pago(kr_answer={"code": "00", "transactionId": "99999999999999"})


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirm_sanitiza_metadata(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """GIVEN: PENDIENTE tx. WHEN: kr_answer has sensitive fields. THEN: metadata stripped."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
    from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService

    inscripcion = await sync_to_async(_crear_inscripcion)(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        inscripcion_id=str(inscripcion.id), transaction_id=tx_id,
        order_number="ORDER012", amount=Decimal("100.00"), currency="PEN",
    )

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        inscripcion_svc=InscripcionService(),
        izipay_client=AsyncMock(),
    )

    kr_answer = {
        "code": "00", "message": "OK", "transactionId": tx_id,
        "pan": "4111111111111111", "cvv": "123",
        "cardToken": "tok_secret_123", "privateKey": "secret_key_xyz",
        "payMethod": "CARD", "response": {"cardScheme": "VISA"},
    }

    await flujo._confirmar_pago(kr_answer=kr_answer)

    tx = await sync_to_async(IzipayTransaccion.objects.get)(transaction_id=tx_id)
    metadata = tx.metadata

    assert "pan" not in metadata
    assert "cvv" not in metadata
    assert "cardToken" not in metadata
    assert "privateKey" not in metadata
    assert "payMethod" in metadata or "response" in metadata


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_metadata_no_contiene_izipayshopid_ni_secret(
    izipay_core_service,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """GIVEN: kr_answer with credential fields. WHEN: processed. THEN: stripped from metadata."""
    from unittest.mock import AsyncMock
    from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
    from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService

    inscripcion = await sync_to_async(_crear_inscripcion)(base_inscripcion_setup, usuario_con_persona)
    tx_id = izipay_core_service.generar_transaction_id()
    await sync_to_async(izipay_core_service.crear_transaccion)(
        inscripcion_id=str(inscripcion.id), transaction_id=tx_id,
        order_number="ORDER013", amount=Decimal("100.00"), currency="PEN",
    )

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        inscripcion_svc=InscripcionService(),
        izipay_client=AsyncMock(),
    )

    kr_answer = {
        "code": "00", "message": "OK", "transactionId": tx_id,
        "izipayKey": "pk_test_123", "shopId": "SHOP123",
        "secretKey": "sk_test_456", "apiKey": "api_test_789",
    }

    await flujo._confirmar_pago(kr_answer=kr_answer)

    tx = await sync_to_async(IzipayTransaccion.objects.get)(transaction_id=tx_id)
    assert "izipayKey" not in tx.metadata
    assert "shopId" not in tx.metadata
    assert "secretKey" not in tx.metadata
    assert "apiKey" not in tx.metadata
