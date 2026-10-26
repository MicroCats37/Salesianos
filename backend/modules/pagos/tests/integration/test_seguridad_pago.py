"""
Security tests for the Izipay payment confirmation.

Phase 1 of izipay-automatic-commercial-confirmation — the backend owns the
commercial settlement, so ONLY a trusted confirmation may mutate payment,
purchase or cup rights.

Covers:

- The browser relay requires an authenticated caller that owns the order.
- A payload that contradicts the persisted order is refused.
- The provider signature is enforced as soon as the merchant key is
  configured (browser relay and server-to-server notification).
- The server-to-server notification is refused when it cannot be verified.
- Reading a transaction or an order requires ownership or administration.
- Every refusal leaves the payment, the order and the purchase untouched.
"""
import json
from decimal import Decimal

import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.exceptions import (
    PagoDatosInconsistentesError,
    PagoNoAutorizadoError,
)
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import (
    RegistrarPagoIzipayFlujo,
)
from modules.pagos.infrastructure import VerificadorFirmaIzipay
from modules.usuarios.domain.models.persona import Persona

CLAVE_COMERCIO = "clave-hash-de-prueba-izipay"
TRANSACTION_ID = "SEC00000000001"
ORDER_NUMBER = "SECORDER001"
MONTO = Decimal("360.00")


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def izipay_core_service():
    """IzipayCoreService instance."""
    return IzipayCoreService()


@pytest.fixture
def persona_propietaria(db):
    """The person that funds the purchase."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="11111111",
        genero="F",
    )


@pytest.fixture
def persona_ajena(db):
    """A person that does NOT own the purchase."""
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Ramos",
        tipo_documento="DNI",
        numero_documento="22222222",
        genero="M",
    )


@pytest.fixture
def usuario_propietario(db, persona_propietaria):
    """The authenticated browser that owns the order."""
    User = get_user_model()
    return User.objects.create_user(
        username="propietario_pago",
        email="propietario@example.com",
        password="testpass123",
        persona_fk=persona_propietaria,
    )


@pytest.fixture
def usuario_ajeno(db, persona_ajena):
    """An authenticated browser that does NOT own the order."""
    User = get_user_model()
    return User.objects.create_user(
        username="ajeno_pago",
        email="ajeno@example.com",
        password="testpass123",
        persona_fk=persona_ajena,
    )


@pytest.fixture
def orden_pago(db, izipay_core_service):
    """A PENDIENTE order with a PENDIENTE transaction."""
    orden = izipay_core_service.crear_orden_pago(
        numero=izipay_core_service.generar_numero_orden(),
        monto_total=MONTO,
        moneda="PEN",
    )
    izipay_core_service.crear_transaccion(
        orden_pago_id=str(orden.id),
        transaction_id=TRANSACTION_ID,
        order_number=ORDER_NUMBER,
        amount=MONTO,
        currency="PEN",
    )
    return orden


@pytest.fixture
def compra(db, orden_pago, persona_propietaria):
    """A PENDIENTE purchase funded by the owner of the order."""
    compra = Compra.objects.create(
        responsable=persona_propietaria,
        descripcion="Compra de prueba",
        referencia_externa="SEC-REF-1",
        total=MONTO,
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    return compra


# ── Helpers ──────────────────────────────────────────────────────────────────

def _kr_answer(
    code: str = "00",
    transaction_id: str = TRANSACTION_ID,
    amount: str | None = None,
    order_number: str | None = None,
    signature: str | None = None,
    payload_http: str | None = None,
) -> dict:
    """Build a provider payload like the one the SDK delivers."""
    payload = {
        "code": code,
        "message": "Operación exitosa" if code == "00" else "Operación rechazada",
        "transactionId": transaction_id,
        "response": {"payMethod": "CARD"},
    }
    if amount is not None:
        payload["amount"] = amount
    if order_number is not None:
        payload["orderNumber"] = order_number
    if signature is not None:
        payload["signature"] = signature
    if payload_http is not None:
        payload["payloadHttp"] = payload_http
    return payload


def _payload_http(transaction_id: str = TRANSACTION_ID, code: str = "00") -> str:
    """The raw signed payload the provider signs."""
    return json.dumps(
        {
            "code": code,
            "message": "Operación exitosa",
            "transactionId": transaction_id,
            "response": {"payMethod": "CARD"},
        },
        separators=(",", ":"),
    )


def _firma(payload_http: str, key_hash: str = CLAVE_COMERCIO) -> str:
    """Sign a raw payload with the merchant key."""
    return VerificadorFirmaIzipay(key_hash=key_hash).calcular_firma(payload_http)


def _post_relay(api_client, kr_answer: dict, token: str | None = None):
    """POST the browser relay."""
    headers = {}
    if token:
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return api_client.post(
        "/api/pagos/izipay/confirmar",
        data=json.dumps({"kr_answer": kr_answer}),
        content_type="application/json",
        **headers,
    )


def _post_notificacion(api_client, payload_http: str, signature: str):
    """POST the server-to-server notification."""
    return api_client.post(
        "/api/pagos/izipay/notificacion",
        data=json.dumps(
            {
                "payloadHttp": payload_http,
                "signature": signature,
                "transactionId": TRANSACTION_ID,
            }
        ),
        content_type="application/json",
    )


def _estado(orden_pago) -> tuple[str, str, str]:
    """Return (order status, transaction status, purchase status)."""
    orden_pago.refresh_from_db()
    transaccion = TransaccionPago.objects.get(transaction_id=TRANSACTION_ID)
    compra = Compra.objects.filter(orden_pago_id=orden_pago.id).first()
    return (
        orden_pago.estado,
        transaccion.status,
        compra.estado if compra else "",
    )


# ── Browser relay: authentication and ownership ──────────────────────────────

@pytest.mark.django_db
def test_relay_anonimo_es_rechazado(api_client, orden_pago, compra):
    """
    GIVEN: An anonymous caller
    WHEN:  it relays a provider confirmation
    THEN:  the request is rejected
    AND    no payment, order or purchase state changes
    """
    response = _post_relay(api_client, _kr_answer())

    assert response.status_code == 401
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_relay_de_usuario_ajeno_es_rechazado(
    api_client, orden_pago, compra, usuario_ajeno
):
    """
    GIVEN: An authenticated user that does NOT own the order
    WHEN:  it relays the provider confirmation of that order
    THEN:  the request is forbidden
    AND    no payment, order or purchase state changes
    """
    token = AccessToken.for_user(usuario_ajeno)

    response = _post_relay(api_client, _kr_answer(), token=token)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PAGO_NO_AUTORIZADO"
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_relay_del_propietario_confirma_el_pago(
    api_client, orden_pago, compra, usuario_propietario
):
    """
    GIVEN: The owner of the order
    WHEN:  it relays the provider confirmation
    THEN:  the payment is confirmed and the order is paid
    """
    token = AccessToken.for_user(usuario_propietario)

    response = _post_relay(api_client, _kr_answer(), token=token)

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["success"] is True
    assert body["data"]["success"] is True

    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA


@pytest.mark.django_db
def test_relay_de_orden_sin_compra_no_puede_confirmar(
    api_client, orden_pago, usuario_propietario
):
    """
    GIVEN: An order with no purchase funding it (nobody owns it)
    WHEN:  a browser relays its confirmation
    THEN:  the request is forbidden — the ownership check fails closed
    AND    the order stays pending
    """
    token = AccessToken.for_user(usuario_propietario)

    response = _post_relay(api_client, _kr_answer(), token=token)

    assert response.status_code == 403
    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PENDIENTE


# ── Browser relay: correlation with the persisted order ──────────────────────

@pytest.mark.django_db
def test_relay_con_amount_distinto_es_rechazado(
    api_client, orden_pago, compra, usuario_propietario
):
    """
    GIVEN: A confirmation whose amount contradicts the persisted order
    WHEN:  it is relayed
    THEN:  the request is refused
    AND    no state changes
    """
    token = AccessToken.for_user(usuario_propietario)

    response = _post_relay(
        api_client,
        _kr_answer(amount="1.00"),
        token=token,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAGO_DATOS_INCONSISTENTES"
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_relay_con_amount_numerico_no_rompe_el_relay(
    api_client, orden_pago, compra, usuario_propietario
):
    """
    GIVEN: A provider that sends the amount as a number
    WHEN:  the owner relays it
    THEN:  the relay is accepted — the payload contract tolerates it
    AND    the amount is correlated against the persisted order
    """
    token = AccessToken.for_user(usuario_propietario)

    response = _post_relay(
        api_client,
        _kr_answer(amount=float(MONTO)),
        token=token,
    )

    assert response.status_code == 200, response.content
    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA


@pytest.mark.django_db
def test_relay_con_order_number_distinto_es_rechazado(
    api_client, orden_pago, compra, usuario_propietario
):
    """
    GIVEN: A confirmation whose order number contradicts the persisted order
    WHEN:  it is relayed
    THEN:  the request is refused
    AND    no state changes
    """
    token = AccessToken.for_user(usuario_propietario)

    response = _post_relay(
        api_client,
        _kr_answer(order_number="OTRA-ORDEN"),
        token=token,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAGO_DATOS_INCONSISTENTES"
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_relay_con_amount_correcto_es_aceptado(
    api_client, orden_pago, compra, usuario_propietario
):
    """
    GIVEN: A confirmation whose amount and order number match the order
    WHEN:  it is relayed by the owner
    THEN:  the payment is confirmed
    """
    token = AccessToken.for_user(usuario_propietario)

    response = _post_relay(
        api_client,
        _kr_answer(amount=str(MONTO), order_number=ORDER_NUMBER),
        token=token,
    )

    assert response.status_code == 200, response.content
    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA


# ── Provider signature ───────────────────────────────────────────────────────

@pytest.mark.django_db
def test_relay_con_firma_invalida_es_rechazado(
    api_client, orden_pago, compra, usuario_propietario, settings
):
    """
    GIVEN: A merchant key configured and a forged provider signature
    WHEN:  the confirmation is relayed
    THEN:  the request is refused
    AND    no state changes
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO
    token = AccessToken.for_user(usuario_propietario)
    payload = _payload_http()

    response = _post_relay(
        api_client,
        _kr_answer(
            signature=_firma(payload, key_hash="otra-clave"),
            payload_http=payload,
        ),
        token=token,
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAGO_FIRMA_INVALIDA"
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_relay_exitoso_sin_firma_con_clave_configurada_es_rechazado(
    api_client, orden_pago, compra, usuario_propietario, settings
):
    """
    GIVEN: A merchant key configured and a successful payload without signature
    WHEN:  it is relayed
    THEN:  the request is refused — an unverifiable success is not a payment
    AND    no state changes
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO
    token = AccessToken.for_user(usuario_propietario)

    response = _post_relay(api_client, _kr_answer(), token=token)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAGO_FIRMA_INVALIDA"
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_relay_con_firma_valida_es_aceptado(
    api_client, orden_pago, compra, usuario_propietario, settings
):
    """
    GIVEN: A merchant key configured and a correctly signed payload
    WHEN:  the owner relays it
    THEN:  the payment is confirmed
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO
    token = AccessToken.for_user(usuario_propietario)
    payload = _payload_http()

    response = _post_relay(
        api_client,
        _kr_answer(signature=_firma(payload), payload_http=payload),
        token=token,
    )

    assert response.status_code == 200, response.content
    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA


# ── Server-to-server notification ────────────────────────────────────────────

@pytest.mark.django_db
def test_notificacion_sin_clave_configurada_es_rechazada(
    api_client, orden_pago, compra, settings
):
    """
    GIVEN: No merchant key configured
    WHEN:  a notification arrives
    THEN:  it is refused — the channel has no fallback
    AND    no state changes
    """
    settings.IZIPAY_KEY_HASH = ""
    payload = _payload_http()

    response = _post_notificacion(api_client, payload, _firma(payload))

    assert response.status_code == 409
    assert (
        response.json()["error"]["code"] == "PAGO_NOTIFICACION_NO_VERIFICABLE"
    )
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_notificacion_con_firma_invalida_es_rechazada(
    api_client, orden_pago, compra, settings
):
    """
    GIVEN: A merchant key configured and a forged notification signature
    WHEN:  the notification arrives
    THEN:  it is refused
    AND    no state changes
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO
    payload = _payload_http()

    response = _post_notificacion(
        api_client, payload, _firma(payload, key_hash="otra-clave")
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PAGO_FIRMA_INVALIDA"
    assert _estado(orden_pago) == (
        OrdenPagoStatus.PENDIENTE,
        IzipayStatus.PENDIENTE,
        EstadoCompraChoices.PENDIENTE,
    )


@pytest.mark.django_db
def test_notificacion_con_firma_valida_confirma_el_pago(
    api_client, orden_pago, compra, settings
):
    """
    GIVEN: A merchant key configured and a correctly signed notification
    WHEN:  the provider calls the server-to-server endpoint
    THEN:  the payment is confirmed — no browser involved
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO
    payload = _payload_http()

    response = _post_notificacion(api_client, payload, _firma(payload))

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["data"]["success"] is True

    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA


@pytest.mark.django_db
def test_notificacion_repetida_es_idempotente(
    api_client, orden_pago, compra, settings
):
    """
    GIVEN: A notification that was already processed
    WHEN:  the provider retries it
    THEN:  it converges without creating a second payment record
    """
    settings.IZIPAY_KEY_HASH = CLAVE_COMERCIO
    payload = _payload_http()
    firma = _firma(payload)

    primero = _post_notificacion(api_client, payload, firma)
    segundo = _post_notificacion(api_client, payload, firma)

    assert primero.status_code == 200
    assert segundo.status_code == 200
    assert segundo.json()["data"]["already_confirmed"] is True
    assert TransaccionPago.objects.filter(transaction_id=TRANSACTION_ID).count() == 1


# ── Protected reads ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_lectura_de_transaccion_ajena_es_rechazada(
    api_client, orden_pago, compra, usuario_ajeno
):
    """
    GIVEN: A transaction that belongs to somebody else
    WHEN:  it is read
    THEN:  the request is forbidden
    """
    token = AccessToken.for_user(usuario_ajeno)

    response = api_client.get(
        f"/api/pagos/transacciones/{TRANSACTION_ID}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PAGO_NO_AUTORIZADO"


@pytest.mark.django_db
def test_lectura_de_transaccion_propia_es_permitida(
    api_client, orden_pago, compra, usuario_propietario
):
    """
    GIVEN: The owner of the order
    WHEN:  it reads its transaction
    THEN:  the transaction is returned
    """
    token = AccessToken.for_user(usuario_propietario)

    response = api_client.get(
        f"/api/pagos/transacciones/{TRANSACTION_ID}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["transaction_id"] == TRANSACTION_ID


@pytest.mark.django_db
def test_lectura_de_orden_ajena_es_rechazada(
    api_client, orden_pago, compra, usuario_ajeno
):
    """
    GIVEN: A payment order that belongs to somebody else
    WHEN:  it is read
    THEN:  the request is forbidden
    """
    token = AccessToken.for_user(usuario_ajeno)

    response = api_client.get(
        f"/api/pagos/ordenes/{orden_pago.id}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PAGO_NO_AUTORIZADO"


@pytest.mark.django_db
def test_lectura_de_orden_propia_es_permitida(
    api_client, orden_pago, compra, usuario_propietario
):
    """
    GIVEN: The owner of the order
    WHEN:  it reads the order
    THEN:  the order is returned
    """
    token = AccessToken.for_user(usuario_propietario)

    response = api_client.get(
        f"/api/pagos/ordenes/{orden_pago.id}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["id"] == str(orden_pago.id)


@pytest.mark.django_db
def test_lectura_anonima_es_rechazada(api_client, orden_pago, compra):
    """
    GIVEN: An anonymous caller
    WHEN:  it reads a transaction
    THEN:  the request is rejected
    """
    response = api_client.get(f"/api/pagos/transacciones/{TRANSACTION_ID}")

    assert response.status_code == 401


# ── Flow level ───────────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_flujo_rechaza_relay_sin_actor(
    izipay_core_service, orden_pago, confirmador_orden_pago, propietario_orden_pago,
    verificador_firma, verificacion_pago,
):
    """
    GIVEN: A browser relay without an authenticated caller
    WHEN:  the flow processes it
    THEN:  it refuses the confirmation
    AND    the order stays pending
    """
    from unittest.mock import AsyncMock

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        izipay_client=AsyncMock(),
        confirmador_orden_pago=confirmador_orden_pago,
        propietario_orden_pago=propietario_orden_pago,
        verificador_firma=verificador_firma,
        verificacion_pago=verificacion_pago,
    )

    with pytest.raises(PagoNoAutorizadoError):
        await flujo._confirmar_pago(kr_answer=_kr_answer())

    orden_actualizada = await sync_to_async(OrdenPago.objects.get)(id=orden_pago.id)
    assert orden_actualizada.estado == OrdenPagoStatus.PENDIENTE


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_flujo_rechaza_relay_de_tercero(
    izipay_core_service, orden_pago, confirmador_orden_pago, propietario_orden_pago,
    verificador_firma, verificacion_pago,
):
    """
    GIVEN: A browser relay from somebody that does not own the order
    WHEN:  the flow processes it
    THEN:  it refuses the confirmation
    AND    the order stays pending and no settlement is driven
    """
    from unittest.mock import AsyncMock
    from modules.pagos.tests.fixtures.ownership_fakes import (
        PropietarioOrdenPagoFake,
    )

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        izipay_client=AsyncMock(),
        confirmador_orden_pago=confirmador_orden_pago,
        propietario_orden_pago=PropietarioOrdenPagoFake(propietarios={"otro"}),
        verificador_firma=verificador_firma,
        verificacion_pago=verificacion_pago,
    )

    with pytest.raises(PagoNoAutorizadoError):
        await flujo._confirmar_pago(
            persona_id="persona-ajena",
            kr_answer=_kr_answer(),
        )

    orden_actualizada = await sync_to_async(OrdenPago.objects.get)(id=orden_pago.id)
    assert orden_actualizada.estado == OrdenPagoStatus.PENDIENTE
    assert confirmador_orden_pago.llamadas == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_flujo_rechaza_amount_inconsistente(
    izipay_core_service, orden_pago, confirmador_orden_pago, propietario_orden_pago,
    verificador_firma, verificacion_pago,
):
    """
    GIVEN: A confirmation whose amount contradicts the persisted order
    WHEN:  the flow processes it
    THEN:  it refuses the confirmation before touching any state
    """
    from unittest.mock import AsyncMock

    flujo = RegistrarPagoIzipayFlujo(
        izipay_core=izipay_core_service,
        izipay_client=AsyncMock(),
        confirmador_orden_pago=confirmador_orden_pago,
        propietario_orden_pago=propietario_orden_pago,
        verificador_firma=verificador_firma,
        verificacion_pago=verificacion_pago,
    )

    with pytest.raises(PagoDatosInconsistentesError):
        await flujo._confirmar_pago(
            persona_id="persona-propietaria",
            kr_answer=_kr_answer(amount="999.00"),
        )

    orden_actualizada = await sync_to_async(OrdenPago.objects.get)(id=orden_pago.id)
    assert orden_actualizada.estado == OrdenPagoStatus.PENDIENTE
    assert confirmador_orden_pago.llamadas == []
