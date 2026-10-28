"""
Integration tests — checkout and settlement of a party-pass purchase (Apply 3).

What this file proves:

1. the CHECKOUT of a pass purchase is owner-scoped: the buyer (the generic
   `Compra.responsable`) starts the payment and nobody else can;
2. the SETTLEMENT reuses the existing payment machinery: the browser relay
   and the administrative manual approval settle the pass order through the
   SAME ports a sports purchase uses — no forked provider semantics;
3. the TRUTH PREDICATE still governs: without correlated evidence the
   purchase is never paid;
4. the settlement is IDEMPOTENT: re-driving it changes nothing;
5. a pass settlement allocates ZERO sports rights — no cupo, no participant,
   no team, no accreditation;
6. `origen_pago` is DERIVED from the payment evidence, never typed.

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
import json
import uuid
from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrdenPagoStatus,
    OrigenPago,
)
from modules.pagos.domain.exceptions import PagoNoVerificadoError
from modules.pagos.domain.models import (
    AprobacionPagoManual,
    TransaccionPago,
)
from modules.salesianos_fest.domain.exceptions import CompraSinCompradorError
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    CompraPase,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Participacion,
)
from modules.salesianos_fest.domain.services.core.acreditacion_service import (
    AcreditacionCoreService,
)
from modules.salesianos_fest.domain.services.core.asignacion_service import (
    AsignacionCoreService,
)
from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import (
    ConfirmarPagoFlujo,
)
from modules.salesianos_fest.domain.services.flujos.iniciar_pago_flujo import (
    IniciarPagoFlujo,
)
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.pagos.domain.services.core.izipay_core_service import (
    IzipayCoreService,
)
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import (
    RegistrarPagoIzipayFlujo,
)
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import (
    PagosOrchestrator,
)
from modules.pagos.infrastructure import VerificadorFirmaIzipay
from modules.pagos.tests.fixtures.ownership_fakes import (
    PropietarioOrdenPagoFake,
)
from modules.pagos.tests.fixtures.settlement_fakes import (
    ConfirmadorOrdenPagoFake,
)

RUTA_INICIAR_PAGO = "/api/compras/{compra_id}/iniciar-pago"
RUTA_RELAY = "/api/pagos/izipay/confirmar"
RUTA_APROBAR_MANUAL = "/api/administracion/pagos/{orden_pago_id}/aprobar-manual"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _auth_post(client, path, user, data=None):
    """POST with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=json.dumps(data) if data is not None else None,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _auth_get(client, path, user):
    """GET with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


def _crear_transaccion(orden_pago, *, transaction_id, amount, status=IzipayStatus.PENDIENTE):
    """Persist the provider attempt of an order."""
    return TransaccionPago.objects.create(
        orden_pago_id=orden_pago.id,
        transaction_id=transaction_id,
        order_number=f"TN-{transaction_id[-6:]}",
        amount=amount,
        currency="PEN",
        status=status,
    )


def _payload_relay(transaction_id, amount, order_number):
    """Provider payload of a successful payment (browser relay)."""
    return {
        "kr_answer": {
            "code": "00",
            "message": "Operación completada",
            "transactionId": transaction_id,
            "response": {
                "code": "00",
                "transactionId": transaction_id,
                "orderNumber": order_number,
                "amount": str(amount),
                "payMethod": "CARD",
            },
        }
    }


def _payload_aprobacion_manual(monto):
    """Payload of the administrative approval of a manual payment."""
    return {
        "canal": "TRANSFERENCIA_BANCARIA",
        "referencia": "OP-PASE-123",
        "monto": str(monto),
        "moneda": "PEN",
        "motivo": "Abono verificado en la cuenta de la institución",
    }


def _objetos_deportivos():
    """Snapshot of every sports object a pass settlement must NOT touch."""
    return {
        "inscripcion": Inscripcion.objects.count(),
        "compra_inscripcion": CompraInscripcion.objects.count(),
        "asignacion_cupo": AsignacionCupo.objects.count(),
        "participacion": Participacion.objects.count(),
        "equipo": Equipo.objects.count(),
        "inscripcion_persona": InscripcionPersona.objects.count(),
    }


# ── Doubles ───────────────────────────────────────────────────────────────────


class IzipayClientFake:
    """
    Provider double — records every session it opens.

    It is the SAME pattern as the pagos test suite
    (`modules/pagos/tests/integration/test_ciclo_vida_intentos.py`): the
    provider is the ONLY external boundary, so it is the only collaborator
    that is replaced, and it is INJECTED through the constructor — never
    patched at runtime (`contract/TEST_ARCHITECTURE_CONTRACT.md` §6).
    """

    shop_id = "TEST_SHOP_ID"

    def __init__(self):
        self.sesiones = []

    async def generar_token_sesion(self, **kwargs):
        """Answer a provider session without leaving the process."""
        self.sesiones.append(kwargs)
        return {"token": f"TOKEN-{len(self.sesiones)}"}


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def flujo_confirmacion():
    """The internal settlement flow, wired with the truth predicate."""
    return ConfirmarPagoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
        evidencia_pago=EvidenciaPagoService(),
    )


@pytest.fixture
def cliente_falso():
    """Provider double that never leaves the process."""
    return IzipayClientFake()


@pytest.fixture
def pagos_orchestrator(cliente_falso):
    """
    The REAL orchestrator of the payments with the provider double injected.

    Everything else is the production wiring: the transaction is persisted by
    the real flow, only the provider HTTP call is replaced.
    """
    return PagosOrchestrator(
        registrar_flujo=RegistrarPagoIzipayFlujo(
            izipay_core=IzipayCoreService(),
            izipay_client=cliente_falso,
            confirmador_orden_pago=ConfirmadorOrdenPagoFake(),
            propietario_orden_pago=PropietarioOrdenPagoFake(),
            verificador_firma=VerificadorFirmaIzipay(key_hash=""),
            verificacion_pago=VerificacionPagoService(),
        )
    )


@pytest.fixture
def flujo_iniciar_pago(pagos_orchestrator):
    """The checkout flow, wired with the provider double."""
    return IniciarPagoFlujo(pagos_orchestrator=pagos_orchestrator)


# ── Tests: checkout (ownership + buyer resolution) ───────────────────────────


@pytest.mark.django_db
def test_el_comprador_del_pase_inicia_el_pago(
    compra_pase_pendiente, usuario_comprador, flujo_iniciar_pago, cliente_falso, settings
):
    """
    GIVEN: a PENDIENTE pass purchase owned by the buyer
    WHEN:  the checkout flow opens the payment session for that purchase
    THEN:  the session is prepared for the BUYER of the purchase, the attempt
           is persisted and the result carries the contract of the endpoint

    The provider is the only external boundary and it is injected as a double
    (`IzipayClientFake`); the flow, the transaction and the buyer resolution
    are the production ones.
    """
    settings.PASES_FIESTA_ENABLED = True
    compra_id = str(compra_pase_pendiente.id)

    result = async_to_sync(flujo_iniciar_pago._iniciar_pago)(compra_id)

    # The result contract of the endpoint.
    assert result.compra_id == compra_id
    assert result.orden_pago_id == str(compra_pase_pendiente.orden_pago_id)
    assert result.amount == compra_pase_pendiente.total
    assert result.currency == "PEN"
    assert result.token
    assert result.transaction_id
    assert result.order_number

    # The buyer is resolved from `Compra.responsable`, NOT from the caller.
    assert len(cliente_falso.sesiones) == 1
    sesion = cliente_falso.sesiones[0]
    assert sesion["buyer_name"] == usuario_comprador.persona_fk.nombres
    assert sesion["buyer_surname"] == usuario_comprador.persona_fk.apellidos
    assert sesion["buyer_document"] == usuario_comprador.persona_fk.numero_documento

    # The attempt is persisted (a PENDIENTE attempt is not a charge).
    intento = TransaccionPago.objects.get(
        orden_pago_id=compra_pase_pendiente.orden_pago_id
    )
    assert intento.status == IzipayStatus.PENDIENTE
    assert intento.amount == compra_pase_pendiente.total

    # The purchase is still pending: opening the session never charges it.
    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_otro_comprador_no_puede_iniciar_el_pago_de_un_pase(
    api_client, usuario_comprador, usuario_ajeno, compra_pase_pendiente, settings
):
    """
    GIVEN: a PENDIENTE pass purchase owned by somebody else
    WHEN:  POST /api/compras/{compra_id}/iniciar-pago as another buyer
    THEN:  403 — the ownership of a pass purchase is NOT relaxed
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        RUTA_INICIAR_PAGO.format(compra_id=str(compra_pase_pendiente.id)),
        usuario_ajeno,
    )

    assert response.status_code == 403, response.content


@pytest.mark.django_db
def test_iniciar_el_pago_de_un_pase_sin_autenticacion_es_rechazado(
    api_client, compra_pase_pendiente, settings
):
    """
    GIVEN: an anonymous caller
    WHEN:  POST /api/compras/{compra_id}/iniciar-pago
    THEN:  401 — the checkout of a pass purchase requires a buyer
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.post(
        RUTA_INICIAR_PAGO.format(compra_id=str(compra_pase_pendiente.id))
    )

    assert response.status_code == 401, response.content


@pytest.mark.django_db
def test_iniciar_el_pago_de_una_compra_inexistente_es_rechazado(
    api_client, usuario_comprador, settings
):
    """
    GIVEN: a purchase that does not exist
    WHEN:  POST /api/compras/{compra_id}/iniciar-pago
    THEN:  404
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        RUTA_INICIAR_PAGO.format(compra_id=str(uuid.uuid4())),
        usuario_comprador,
    )

    assert response.status_code == 404, response.content


@pytest.mark.django_db
def test_el_comprador_de_un_pase_se_resuelve_desde_compra_responsable(
    flujo_iniciar_pago, usuario_comprador, compra_pase_pendiente
):
    """
    GIVEN: a pass purchase without any sports inscription
    WHEN:  the checkout flow loads the payment context
    THEN:  the buyer is the generic `Compra.responsable`
    """
    compra, orden_pago, buyer = flujo_iniciar_pago._cargar_contexto_pago(
        str(compra_pase_pendiente.id)
    )

    assert str(compra.responsable_id) == str(usuario_comprador.persona_fk_id)
    assert buyer["document"] == usuario_comprador.persona_fk.numero_documento
    assert buyer["name"] == usuario_comprador.persona_fk.nombres
    assert buyer["surname"] == usuario_comprador.persona_fk.apellidos
    assert orden_pago.id == compra_pase_pendiente.orden_pago_id


@pytest.mark.django_db
def test_una_compra_sin_comprador_es_rechazada(
    flujo_iniciar_pago, compra_pase_pendiente
):
    """
    GIVEN: a purchase with NO owner (no inscription and no responsable)
    WHEN:  the checkout flow loads the payment context
    THEN:  it is refused — a purchase without a buyer cannot be charged
    """
    compra_pase_pendiente.responsable = None
    compra_pase_pendiente.save(update_fields=["responsable", "updated_at"])

    with pytest.raises(CompraSinCompradorError):
        flujo_iniciar_pago._cargar_contexto_pago(str(compra_pase_pendiente.id))

    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PENDIENTE
    assert Compra.objects.count() == 1


# ── Tests: settlement through the browser relay ──────────────────────────────


@pytest.mark.django_db
def test_el_relay_del_navegador_liquida_una_compra_de_pases(
    api_client, usuario_comprador, compra_pase_pendiente, settings
):
    """
    GIVEN: a PENDIENTE pass purchase whose order has a provider attempt
    WHEN:  the browser relays the successful provider payload as the buyer
    THEN:  the order and the purchase are PAGADA and NO sports right exists
    """
    settings.PASES_FIESTA_ENABLED = True
    # La verificación de firma del proveedor no está disponible: el canal del
    # navegador confía en la propiedad de la orden, no en la firma.
    settings.IZIPAY_KEY_HASH = ""
    orden_pago = compra_pase_pendiente.orden_pago
    transaccion = _crear_transaccion(
        orden_pago,
        transaction_id="PASETX001",
        amount=orden_pago.monto_total,
    )
    antes = _objetos_deportivos()

    response = _auth_post(
        api_client,
        RUTA_RELAY,
        usuario_comprador,
        _payload_relay(
            transaccion.transaction_id,
            orden_pago.monto_total,
            transaccion.order_number,
        ),
    )

    assert response.status_code == 200, response.content

    compra_pase_pendiente.refresh_from_db()
    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PAGADA
    assert _objetos_deportivos() == antes
    assert AsignacionCupo.objects.count() == 0


@pytest.mark.django_db
def test_otro_comprador_no_puede_relayar_el_pago_de_un_pase(
    api_client, usuario_ajeno, compra_pase_pendiente, settings
):
    """
    GIVEN: a PENDIENTE pass purchase owned by somebody else
    WHEN:  another buyer relays the provider payload
    THEN:  403 and the purchase stays PENDIENTE
    """
    settings.PASES_FIESTA_ENABLED = True
    settings.IZIPAY_KEY_HASH = ""
    orden_pago = compra_pase_pendiente.orden_pago
    transaccion = _crear_transaccion(
        orden_pago,
        transaction_id="PASETX002",
        amount=orden_pago.monto_total,
    )

    response = _auth_post(
        api_client,
        RUTA_RELAY,
        usuario_ajeno,
        _payload_relay(
            transaccion.transaction_id,
            orden_pago.monto_total,
            transaccion.order_number,
        ),
    )

    assert response.status_code == 403, response.content
    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PENDIENTE


# ── Tests: the truth predicate ───────────────────────────────────────────────


@pytest.mark.django_db
def test_una_orden_de_pases_sin_evidencia_no_liquida(
    flujo_confirmacion, compra_pase_pendiente
):
    """
    GIVEN: a pass purchase whose order has NO successful transaction
    WHEN:  the internal settlement flow is driven for that order
    THEN:  it is refused with PAGO_NO_VERIFICADO and nothing is granted
    """
    with pytest.raises(PagoNoVerificadoError):
        async_to_sync(flujo_confirmacion._confirmar_compra)(
            str(compra_pase_pendiente.orden_pago_id)
        )

    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PENDIENTE
    assert AsignacionCupo.objects.count() == 0


@pytest.mark.django_db
def test_una_transaccion_exitosa_no_correlacionada_no_liquida(
    flujo_confirmacion, compra_pase_pendiente
):
    """
    GIVEN: a pass purchase whose order has a successful attempt of ANOTHER
           amount
    WHEN:  the internal settlement flow is driven for that order
    THEN:  it is refused — a purchase is never paid for an amount the order
           does not carry
    """
    _crear_transaccion(
        compra_pase_pendiente.orden_pago,
        transaction_id="PASETX003",
        amount=Decimal("999.00"),
        status=IzipayStatus.EXITO,
    )

    with pytest.raises(PagoNoVerificadoError):
        async_to_sync(flujo_confirmacion._confirmar_compra)(
            str(compra_pase_pendiente.orden_pago_id)
        )

    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_una_orden_de_pases_con_evidencia_liquida_la_compra(
    flujo_confirmacion, compra_pase_pendiente
):
    """
    GIVEN: a pass purchase whose order carries a CORRELATED successful attempt
    WHEN:  the internal settlement flow is driven for that order
    THEN:  the purchase is PAGADA and ZERO sports rights are allocated
    """
    antes = _objetos_deportivos()
    _crear_transaccion(
        compra_pase_pendiente.orden_pago,
        transaction_id="PASETX004",
        amount=compra_pase_pendiente.orden_pago.monto_total,
        status=IzipayStatus.EXITO,
    )

    async_to_sync(flujo_confirmacion._confirmar_compra)(
        str(compra_pase_pendiente.orden_pago_id)
    )

    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PAGADA
    assert _objetos_deportivos() == antes
    assert AsignacionCupo.objects.count() == 0
    assert CompraPase.objects.count() == 1


@pytest.mark.django_db
def test_la_liquidacion_de_pases_es_idempotente(
    flujo_confirmacion, compra_pase_pendiente
):
    """
    GIVEN: a pass purchase already settled
    WHEN:  the internal settlement flow is driven AGAIN for that order
    THEN:  it converges (already confirmed) and nothing is duplicated
    """
    _crear_transaccion(
        compra_pase_pendiente.orden_pago,
        transaction_id="PASETX005",
        amount=compra_pase_pendiente.orden_pago.monto_total,
        status=IzipayStatus.EXITO,
    )

    primero = async_to_sync(flujo_confirmacion._confirmar_compra)(
        str(compra_pase_pendiente.orden_pago_id)
    )
    segundo = async_to_sync(flujo_confirmacion._confirmar_compra)(
        str(compra_pase_pendiente.orden_pago_id)
    )

    assert primero.already_confirmed is False
    assert segundo.already_confirmed is True

    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PAGADA
    assert CompraPase.objects.count() == 1
    assert AsignacionCupo.objects.count() == 0


@pytest.mark.django_db
def test_la_liquidacion_de_pases_no_crea_objetos_deportivos(
    flujo_confirmacion, compra_pase_pendiente
):
    """
    GIVEN: a pass purchase with evidence
    WHEN:  it is settled
    THEN:  no inscripcion, cupo, participant, team nor pool row is created
    """
    antes = _objetos_deportivos()
    _crear_transaccion(
        compra_pase_pendiente.orden_pago,
        transaction_id="PASETX006",
        amount=compra_pase_pendiente.orden_pago.monto_total,
        status=IzipayStatus.EXITO,
    )

    async_to_sync(flujo_confirmacion._confirmar_compra)(
        str(compra_pase_pendiente.orden_pago_id)
    )

    despues = _objetos_deportivos()
    assert despues == antes
    assert Inscripcion.objects.count() == 0
    assert CompraInscripcion.objects.count() == 0
    assert AsignacionCupo.objects.count() == 0
    assert Participacion.objects.count() == 0
    assert Equipo.objects.count() == 0
    assert InscripcionPersona.objects.count() == 0


# ── Tests: administrative manual approval ────────────────────────────────────


@pytest.mark.django_db
def test_la_aprobacion_manual_liquida_una_compra_de_pases(
    api_client, usuario_admin_pases, compra_pase_pendiente, settings
):
    """
    GIVEN: a PENDIENTE pass purchase
    WHEN:  an administrator approves the payment manually
    THEN:  the purchase is PAGADA and ZERO sports rights are allocated
    """
    settings.PASES_FIESTA_ENABLED = True
    settings.PAGO_MANUAL_APROBACION_ENABLED = True
    antes = _objetos_deportivos()

    response = _auth_post(
        api_client,
        RUTA_APROBAR_MANUAL.format(
            orden_pago_id=str(compra_pase_pendiente.orden_pago_id)
        ),
        usuario_admin_pases,
        _payload_aprobacion_manual(compra_pase_pendiente.orden_pago.monto_total),
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["settlement_status"] == "SETTLED"

    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PAGADA
    assert _objetos_deportivos() == antes
    assert AsignacionCupo.objects.count() == 0


@pytest.mark.django_db
def test_la_aprobacion_manual_de_pases_es_idempotente(
    api_client, usuario_admin_pases, compra_pase_pendiente, settings
):
    """
    GIVEN: a pass purchase already approved manually
    WHEN:  an administrator approves it AGAIN
    THEN:  200 with YA_APROBADA, ONE active approval and NO duplicated rights
    """
    settings.PASES_FIESTA_ENABLED = True
    settings.PAGO_MANUAL_APROBACION_ENABLED = True
    payload = _payload_aprobacion_manual(
        compra_pase_pendiente.orden_pago.monto_total
    )

    primero = _auth_post(
        api_client,
        RUTA_APROBAR_MANUAL.format(
            orden_pago_id=str(compra_pase_pendiente.orden_pago_id)
        ),
        usuario_admin_pases,
        payload,
    )
    assert primero.status_code == 200, primero.content

    segundo = _auth_post(
        api_client,
        RUTA_APROBAR_MANUAL.format(
            orden_pago_id=str(compra_pase_pendiente.orden_pago_id)
        ),
        usuario_admin_pases,
        payload,
    )

    assert segundo.status_code == 200, segundo.content
    assert segundo.json()["data"]["resultado"] == "YA_APROBADA"
    assert (
        AprobacionPagoManual.objects.filter(
            orden_pago_id=compra_pase_pendiente.orden_pago_id,
            estado=EstadoAprobacionPagoManual.APROBADA,
        ).count()
        == 1
    )
    assert AsignacionCupo.objects.count() == 0


# ── Tests: derived payment origin ────────────────────────────────────────────


@pytest.mark.django_db
def test_el_origen_de_pago_de_un_pase_pendiente_es_sin_pago(
    api_client, usuario_comprador, compra_pase_pendiente, settings
):
    """
    GIVEN: a PENDIENTE pass purchase without payment evidence
    WHEN:  the owner reads the purchase
    THEN:  `origen_pago` is SIN_PAGO — the origin is derived, never typed
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_get(
        api_client,
        f"/api/pases/compras/{compra_pase_pendiente.id}",
        usuario_comprador,
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["origen_pago"] == OrigenPago.SIN_PAGO


@pytest.mark.django_db
def test_el_origen_de_pago_con_izipay_es_izipay(
    api_client, usuario_comprador, compra_pase_pendiente, settings
):
    """
    GIVEN: a pass purchase whose order carries a successful provider attempt
    WHEN:  the owner reads the purchase
    THEN:  `origen_pago` is IZIPAY
    """
    settings.PASES_FIESTA_ENABLED = True
    _crear_transaccion(
        compra_pase_pendiente.orden_pago,
        transaction_id="PASETX007",
        amount=compra_pase_pendiente.orden_pago.monto_total,
        status=IzipayStatus.EXITO,
    )

    response = _auth_get(
        api_client,
        f"/api/pases/compras/{compra_pase_pendiente.id}",
        usuario_comprador,
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["origen_pago"] == OrigenPago.IZIPAY


@pytest.mark.django_db
def test_el_origen_de_pago_manual_es_manual(
    api_client, usuario_comprador, usuario_admin_pases, compra_pase_pendiente,
    settings,
):
    """
    GIVEN: a pass purchase settled by an administrative manual approval
    WHEN:  the owner reads the purchase
    THEN:  `origen_pago` is MANUAL
    """
    settings.PASES_FIESTA_ENABLED = True
    settings.PAGO_MANUAL_APROBACION_ENABLED = True

    _auth_post(
        api_client,
        RUTA_APROBAR_MANUAL.format(
            orden_pago_id=str(compra_pase_pendiente.orden_pago_id)
        ),
        usuario_admin_pases,
        _payload_aprobacion_manual(compra_pase_pendiente.orden_pago.monto_total),
    )

    response = _auth_get(
        api_client,
        f"/api/pases/compras/{compra_pase_pendiente.id}",
        usuario_comprador,
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["origen_pago"] == OrigenPago.MANUAL
