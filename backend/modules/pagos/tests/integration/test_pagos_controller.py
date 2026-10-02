"""
Integration tests for PagosController — Izipay Perú payment endpoints.

Uses django.test.AsyncClient + @pytest.mark.asyncio.
Token generation is wrapped in sync_to_async to avoid SQLite locking.
All DB object creation lives in sync fixtures (not inside async test body).
Provider HTTP calls are mocked via unittest.mock.patch context manager.
"""
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch

from django.test import AsyncClient
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from config.api import api
from modules.inscripciones.domain.constants import EstadoInscripcionChoices
from modules.pagos.domain.constants import IzipayStatus
from modules.pagos.domain.schemas.result import IzipayPrepareResult, IzipayConfirmResult


# ── Fixtures (sync — safe for ORM) ────────────────────────────────────────────

@pytest.fixture
def async_auth_client(db):
    """AsyncClient for testing async Ninja endpoints."""
    return AsyncClient()


@pytest.fixture
def otro_usuario(db):
    """A second user (different persona) for ownership tests."""
    from modules.usuarios.domain.models import Persona
    from modules.usuarios.domain.constants import GeneroChoices
    User = get_user_model()
    persona = Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="99887766",
        nombres="Otro",
        apellidos="Usuario",
        genero=GeneroChoices.MASCULINO,
    )
    return User.objects.create_user(
        username="otro_user",
        email="otro@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def inscripcion_owner(base_inscripcion_setup, usuario_con_persona):
    """Inscripcion owned by usuario_con_persona."""
    from modules.inscripciones.domain.models import Inscripcion
    return Inscripcion.objects.create(
        evento=base_inscripcion_setup["evento"],
        responsable=usuario_con_persona.persona_fk,
        paquete=base_inscripcion_setup["paquete"],
        promocion=base_inscripcion_setup["promocion"],
        estado=EstadoInscripcionChoices.PAGO_PENDIENTE,
    )


@pytest.fixture
def transaccion_pendiente(inscripcion_owner):
    """Pending IzipayTransaccion for inscripcion_owner."""
    from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
    core = IzipayCoreService()
    tx_id = core.generar_transaction_id()
    return core.crear_transaccion(
        inscripcion_id=str(inscripcion_owner.id),
        transaction_id=tx_id,
        order_number="ORD001",
        amount=Decimal("120.00"),
        currency="PEN",
    )


@pytest.fixture
def transaccion_exito(inscripcion_owner):
    """Confirmed IzipayTransaccion for inscripcion_owner."""
    from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
    core = IzipayCoreService()
    tx_id = core.generar_transaction_id()
    tx = core.crear_transaccion(
        inscripcion_id=str(inscripcion_owner.id),
        transaction_id=tx_id,
        order_number="ORD002",
        amount=Decimal("120.00"),
        currency="PEN",
    )
    # Mark as confirmed using save (actualizar_estado has metadata=None issue)
    tx.status = IzipayStatus.EXITO
    tx.response_code = "00"
    tx.response_message = "Operación exitosa"
    tx.save()
    return tx


# ── Token helper (sync_to_async for SQLite safety) ──────────────────────────────

async def _make_token(user) -> str:
    """Generate JWT token for user (sync AccessToken.for_user wrapped for async context)."""
    from ninja_jwt.tokens import AccessToken
    return str(await sync_to_async(AccessToken.for_user)(user))


# ── Auth tests ─────────────────────────────────────────────────────────────────

def test_get_authenticated_persona_id_sin_persona_raises():
    """
    Unit test: _get_authenticated_persona_id raises BusinessError when
    the authenticated user has no Persona linked (persona_fk_id=None).

    Since Usuario.persona_fk is non-null at DB level, we test the helper
    boundary directly with a mock request object.
    """
    from unittest.mock import MagicMock
    from modules.pagos.presentation.controllers.pagos_controller import _get_authenticated_persona_id
    from core.exceptions import BusinessError

    # Simulate a user with persona_fk_id = None
    mock_user = MagicMock()
    mock_user.persona_fk_id = None

    mock_request = MagicMock()
    mock_request.user = mock_user

    with pytest.raises(BusinessError) as exc_info:
        _get_authenticated_persona_id(mock_request)

    assert "sin persona vinculada" in str(exc_info.value).lower()


def test_get_authenticated_persona_id_con_persona_returns_id():
    """
    Unit test: _get_authenticated_persona_id returns str(persona_fk_id) when
    the authenticated user has a Persona linked.
    """
    from unittest.mock import MagicMock
    from modules.pagos.presentation.controllers.pagos_controller import _get_authenticated_persona_id

    mock_user = MagicMock()
    mock_user.persona_fk_id = "550e8400-e29b-41d4-a716-446655440000"

    mock_request = MagicMock()
    mock_request.user = mock_user

    result = _get_authenticated_persona_id(mock_request)
    assert result == "550e8400-e29b-41d4-a716-446655440000"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_preparar_endpoint_requires_auth(async_auth_client, inscripcion_owner):
    """
    GIVEN: No JWT token provided
    WHEN:  GET /api/pagos/izipay/preparar/{inscripcion_id}
    THEN:  401 or 403 returned.
    """
    response = await async_auth_client.get(
        f"/api/pagos/izipay/preparar/{inscripcion_owner.id}",
    )
    assert response.status_code in (401, 403), (
        f"Expected 401/403, got {response.status_code}: {response.json()}"
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_endpoint_requires_auth(async_auth_client, transaccion_pendiente):
    """
    GIVEN: No JWT token provided
    WHEN:  POST /pagos/izipay/confirmar
    THEN:  401 or 403 returned.
    """
    payload = {
        "kr_answer": {
            "code": "00",
            "transactionId": transaccion_pendiente.transaction_id,
        }
    }
    response = await async_auth_client.post(
        "/api/pagos/izipay/confirmar",
        data=payload,
        content_type="application/json",
    )
    assert response.status_code in (401, 403), (
        f"Expected 401/403, got {response.status_code}: {response.json()}"
    )


# ── Prepare endpoint tests ──────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_preparar_success_for_owner(
    async_auth_client, inscripcion_owner, usuario_con_persona
):
    """
    GIVEN: Auth user owns the inscription; inscription is PAGO_PENDIENTE
    WHEN:  GET /api/pagos/izipay/preparar/{inscripcion_id}
    THEN:  200 returned with token and merchant_code.
    """
    token = await _make_token(usuario_con_persona)

    mock_result = IzipayPrepareResult(
        transaction_id="TX1234567890",
        order_number="ORD001",
        amount=Decimal("120.00"),
        currency="PEN",
        inscripcion_id=str(inscripcion_owner.id),
        token="test-token-xyz",
        merchant_code="SHOP123",
        buyer_email="test@example.com",
        buyer_name="Juan",
        buyer_surname="Perez",
    )

    with patch(
        "modules.pagos.domain.services.orchestrators.pagos_orchestrator.PagosOrchestrator.preparar_pago_izipay",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await async_auth_client.get(
            f"/api/pagos/izipay/preparar/{inscripcion_owner.id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.json()}"
    )
    data = response.json()
    assert data["data"]["token"] == "test-token-xyz"
    assert data["data"]["merchant_code"] == "SHOP123"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_preparar_non_owner_denied(
    async_auth_client, inscripcion_owner, otro_usuario
):
    """
    GIVEN: Auth user does NOT own the inscription
    WHEN:  GET /api/pagos/izipay/preparar/{inscripcion_id}
    THEN:  400 returned (BusinessError: no permission).
    """
    token = await _make_token(otro_usuario)

    response = await async_auth_client.get(
        f"/api/pagos/izipay/preparar/{inscripcion_owner.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400, (
        f"Expected 400 for non-owner, got {response.status_code}: {response.json()}"
    )
    assert "permiso" in str(response.json()).lower()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_preparar_inscripcion_not_found(async_auth_client, usuario_con_persona):
    """
    GIVEN: Auth user with persona
    WHEN:  GET /api/pagos/izipay/preparar/{non-existent-inscripcion_id}
    THEN:  404 returned.
    """
    import uuid
    token = await _make_token(usuario_con_persona)

    response = await async_auth_client.get(
        f"/api/pagos/izipay/preparar/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}: {response.json()}"
    )


# ── Confirm endpoint tests ─────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_success_for_owner(
    async_auth_client, transaccion_pendiente, inscripcion_owner, usuario_con_persona
):
    """
    GIVEN: Auth user owns the inscription; transaction is PENDIENTE
    WHEN:  POST /pagos/izipay/confirmar with code=00
    THEN:  200 returned with success=True.
    """
    token = await _make_token(usuario_con_persona)
    payload = {
        "kr_answer": {
            "code": "00",
            "message": "Operación exitosa",
            "transactionId": transaccion_pendiente.transaction_id,
            "response": {
                "payMethod": "CARD",
                "order": [
                    {"orderNumber": transaccion_pendiente.order_number, "amount": "120.00"}
                ],
            },
        }
    }

    mock_result = IzipayConfirmResult(
        transaction_id=transaccion_pendiente.transaction_id,
        success=True,
        status=IzipayStatus.EXITO,
        response_code="00",
        response_message="Operación exitosa",
        metodo_pago="CARD",
        already_confirmed=False,
    )

    with patch(
        "modules.pagos.domain.services.orchestrators.pagos_orchestrator.PagosOrchestrator.confirmar_pago_izipay",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await async_auth_client.post(
            "/api/pagos/izipay/confirmar",
            data=payload,
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.json()}"
    )
    data = response.json()
    assert data["data"]["success"] is True
    assert data["data"]["status"] == IzipayStatus.EXITO


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_non_owner_denied(
    async_auth_client, transaccion_pendiente, otro_usuario
):
    """
    GIVEN: Auth user does NOT own the inscription for the transaction
    WHEN:  POST /pagos/izipay/confirmar
    THEN:  400 returned (BusinessError: no permission).
    """
    token = await _make_token(otro_usuario)
    payload = {
        "kr_answer": {
            "code": "00",
            "message": "Operación exitosa",
            "transactionId": transaccion_pendiente.transaction_id,
        }
    }

    response = await async_auth_client.post(
        "/api/pagos/izipay/confirmar",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400, (
        f"Expected 400 for non-owner, got {response.status_code}: {response.json()}"
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_idempotente_already_confirmed(
    async_auth_client, transaccion_exito, inscripcion_owner, usuario_con_persona
):
    """
    GIVEN: Transaction already confirmed (EXITO)
    WHEN:  POST /pagos/izipay/confirmar again
    THEN:  200 returned with already_confirmed=True (idempotent).
    """
    token = await _make_token(usuario_con_persona)
    payload = {
        "kr_answer": {
            "code": "00",
            "message": "Operación exitosa",
            "transactionId": transaccion_exito.transaction_id,
        }
    }

    mock_result = IzipayConfirmResult(
        transaction_id=transaccion_exito.transaction_id,
        success=True,
        status=IzipayStatus.EXITO,
        response_code="00",
        response_message="Operación exitosa",
        metodo_pago="CARD",
        already_confirmed=True,
    )

    with patch(
        "modules.pagos.domain.services.orchestrators.pagos_orchestrator.PagosOrchestrator.confirmar_pago_izipay",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await async_auth_client.post(
            "/api/pagos/izipay/confirmar",
            data=payload,
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.json()}"
    )
    data = response.json()
    assert data["data"]["already_confirmed"] is True


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_not_found_transaction(async_auth_client, usuario_con_persona):
    """
    GIVEN: Auth user with persona
    WHEN:  POST /pagos/izipay/confirmar with non-existent transactionId
    THEN:  400 returned (IzipayError: transaction not found).
    """
    token = await _make_token(usuario_con_persona)
    payload = {
        "kr_answer": {
            "code": "00",
            "message": "Operación exitosa",
            "transactionId": "99999999999999",
        }
    }

    response = await async_auth_client.post(
        "/api/pagos/izipay/confirmar",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Orchestrator raises IzipayError for not-found transaction → maps to 400
    assert response.status_code == 400, (
        f"Expected 400 for not-found transaction, got {response.status_code}: {response.json()}"
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_confirmar_failed_callback(
    async_auth_client, transaccion_pendiente, inscripcion_owner, usuario_con_persona
):
    """
    GIVEN: Auth user owns the inscription; transaction is PENDIENTE
    WHEN:  POST /pagos/izipay/confirmar with code=05 (card declined)
    THEN:  200 returned with success=False.
    """
    token = await _make_token(usuario_con_persona)
    payload = {
        "kr_answer": {
            "code": "05",
            "message": "Card declined",
            "transactionId": transaccion_pendiente.transaction_id,
        }
    }

    mock_result = IzipayConfirmResult(
        transaction_id=transaccion_pendiente.transaction_id,
        success=False,
        status=IzipayStatus.FALLIDO,
        response_code="05",
        response_message="Card declined",
        metodo_pago="CARD",
        already_confirmed=False,
    )

    with patch(
        "modules.pagos.domain.services.orchestrators.pagos_orchestrator.PagosOrchestrator.confirmar_pago_izipay",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        response = await async_auth_client.post(
            "/api/pagos/izipay/confirmar",
            data=payload,
            content_type="application/json",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.json()}"
    )
    data = response.json()
    assert data["data"]["success"] is False
    assert data["data"]["status"] == IzipayStatus.FALLIDO
