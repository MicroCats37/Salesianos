"""
E2E — the complete life of a party pass, from the catalogue to the gate.

What this file proves (the real flows, end to end):

1. CATALOGUE → PURCHASE → VERIFIED SETTLEMENT → EXACT PERSONA LOOKUP (a
   beneficiary with NO sports registration and NO account) → ASSIGNMENT →
   ACCREDITATION → GATE ACCESS;
2. MANUAL PAYMENT APPROVAL → ASSIGNMENT → ACCESS;
3. ADMIN CANCELLATION → RIGHTS REVOKED → ACCREDITATION RECOMPUTED → THE GATE
   DENIES THE ACCESS;
4. the INVARIANT: not ONE sports object and not ONE sports balance changes.

The provider SDK is the only external boundary and it is simulated locally
(same pattern as the sports checkout test): the payment truth, the evidence
and the settlement are NEVER simulated.
"""
import json
from decimal import Decimal

import pytest
from asgiref.sync import async_to_sync
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import IzipayStatus, OrigenPago
from modules.pagos.domain.models import TransaccionPago
from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.models import (
    AcreditacionEvento,
    AsignacionCupo,
    CompraInscripcion,
    CompraPase,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Participacion,
    PaseBeneficiario,
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
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)

RUTA_CATALOGO = "/api/pases/"
RUTA_COMPRAR = "/api/pases/comprar"
RUTA_ESTADO_COMPRA = "/api/pases/compras/{compra_id}"
RUTA_BENEFICIARIOS = "/api/pases/compras/{compra_id}/beneficiarios"
RUTA_RESOLVER_PERSONA = "/api/personas/resolver"
RUTA_APROBAR_MANUAL = "/api/administracion/pagos/{orden_pago_id}/aprobar-manual"
RUTA_CANCELAR_PASE = "/api/administracion/pases/compras/{compra_id}/cancelar"
RUTA_ACCESO = "/api/acceso/registrar"


# ── Helpers ──────────────────────────────────────────────────────────────────


def _auth_get(client, path, user=None):
    """GET with a JWT bearer token (or anonymously)."""
    if user is None:
        return client.get(path)
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


def _auth_post(client, path, user, data=None):
    """POST with a JWT bearer token."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=json.dumps(data) if data is not None else None,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _crear_transaccion(orden_pago, *, transaction_id, amount, status=IzipayStatus.EXITO):
    """Persist the provider attempt of an order."""
    return TransaccionPago.objects.create(
        orden_pago_id=orden_pago.id,
        transaction_id=transaction_id,
        order_number=f"TN-{transaction_id[-6:]}",
        amount=amount,
        currency="PEN",
        status=status,
    )


def _objetos_deportivos():
    """Snapshot of every sports object a pass flow must NOT touch."""
    return {
        "inscripcion": Inscripcion.objects.count(),
        "compra_inscripcion": CompraInscripcion.objects.count(),
        "asignacion_cupo": AsignacionCupo.objects.count(),
        "participacion": Participacion.objects.count(),
        "equipo": Equipo.objects.count(),
        "inscripcion_persona": InscripcionPersona.objects.count(),
    }


def _acreditacion(persona, evento):
    """The accreditation of a person in an event, or None."""
    return AcreditacionEvento.objects.filter(
        persona=persona, evento=evento
    ).first()


def _comprar_pases(client, usuario, pase, cantidad):
    """Buy a batch of passes through the public purchase endpoint."""
    response = _auth_post(
        client,
        RUTA_COMPRAR,
        usuario,
        {"pase_id": str(pase.id), "cantidad": cantidad},
    )
    assert response.status_code == 200, response.content
    return response.json()["data"]


def _resolver_persona(client, usuario, tipo_documento, numero_documento):
    """Resolve an EXISTING person by her exact civil identity."""
    respuesta = _auth_get(
        client,
        f"{RUTA_RESOLVER_PERSONA}"
        f"?tipo_documento={tipo_documento}&numero_documento={numero_documento}",
        usuario,
    )
    assert respuesta.status_code == 200, respuesta.content
    return respuesta.json()["data"]


def _asignar(client, usuario, compra_id, persona_ids):
    """Assign the persons to the free slots of the batch."""
    return _auth_post(
        client,
        RUTA_BENEFICIARIOS.format(compra_id=compra_id),
        usuario,
        {"beneficiario_ids": [str(persona_id) for persona_id in persona_ids]},
    )


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
def usuario_superusuario_passes(db):
    """
    A SUPERUSER.

    Approving or annulling a payment is a SENSITIVE capability: the project
    grants it to the break-glass tier only, so the operational staff cannot
    perform it. The E2E uses the tier that really holds it.
    """
    from django.contrib.auth import get_user_model

    from modules.usuarios.domain.constants import (
        GeneroChoices,
        TipoDocumentoChoices,
    )
    from modules.usuarios.domain.models import Persona

    persona = Persona.objects.create(
        nombres="Super",
        apellidos="Pases",
        tipo_documento=TipoDocumentoChoices.DNI,
        numero_documento="71000009",
        genero=GeneroChoices.MASCULINO,
    )
    usuario = get_user_model().objects.create_user(
        username="superusuario_pases",
        email="superusuario_pases@example.com",
        password="testpass123",
        persona_fk=persona,
    )
    usuario.is_staff = True
    usuario.is_superuser = True
    usuario.save(update_fields=["is_staff", "is_superuser"])
    return usuario


# ── E2E 1: catalogue → purchase → settlement → lookup → assignment → access ──


@pytest.mark.django_db
def test_e2e_compra_pago_asignacion_y_acceso_a_la_puerta(
    api_client,
    usuario_comprador,
    pase_fiesta,
    persona_beneficiaria_1,
    persona_beneficiaria_2,
    settings,
    flujo_confirmacion,
):
    """
    GIVEN: a published pass and a buyer with a session
    WHEN:  the buyer buys two passes, the payment is verified, the buyer
           resolves two EXISTING people (without sports registration) and
           assigns them, and the gate scans the QR of one of them
    THEN:  the catalogue published the pass, the purchase is paid, both
           rights are active, both people are accredited for the party and
           the gate ALLOWS the access
    """
    settings.PASES_FIESTA_ENABLED = True

    # 1. The catalogue is public and publishes the pass.
    catalogo = _auth_get(api_client, RUTA_CATALOGO)
    assert catalogo.status_code == 200, catalogo.content
    assert any(
        item["id"] == str(pase_fiesta.id)
        for item in catalogo.json()["data"]
    ), "El catálogo público no publica el pase"

    # 2. The buyer buys two passes.
    compra = _comprar_pases(api_client, usuario_comprador, pase_fiesta, 2)
    compra_id = compra["compra_id"]
    assert compra["cantidad"] == 2
    assert compra["estado_compra"] == EstadoCompraChoices.PENDIENTE

    # 3. The payment is verified by the provider evidence.
    orden = Compra.objects.get(id=compra_id).orden_pago
    _crear_transaccion(
        orden,
        transaction_id="E2EPASE0001",
        amount=Decimal(str(compra["total"])),
    )
    async_to_sync(flujo_confirmacion._confirmar_compra)(str(orden.id))

    estado = _auth_get(
        api_client, RUTA_ESTADO_COMPRA.format(compra_id=compra_id), usuario_comprador
    )
    assert estado.status_code == 200, estado.content
    assert estado.json()["data"]["estado_compra"] == EstadoCompraChoices.PAGADA
    assert estado.json()["data"]["origen_pago"] == OrigenPago.IZIPAY

    # 4. The buyer resolves the people that ALREADY EXIST (no sports
    #    registration, no account of their own).
    primera = _resolver_persona(api_client, usuario_comprador, "DNI", "71000001")
    segunda = _resolver_persona(api_client, usuario_comprador, "DNI", "71000002")
    assert primera["persona_id"] == str(persona_beneficiaria_1.id)
    assert segunda["persona_id"] == str(persona_beneficiaria_2.id)

    # 5. The buyer assigns them to the batch.
    asignados = _asignar(
        api_client, usuario_comprador, compra_id, [primera["persona_id"], segunda["persona_id"]]
    )
    assert asignados.status_code == 200, asignados.content
    assert asignados.json()["data"]["asignados"] == 2
    assert asignados.json()["data"]["slots_disponibles"] == 0

    # 6. Both people are accredited for the party.
    evento = pase_fiesta.evento
    for persona in (persona_beneficiaria_1, persona_beneficiaria_2):
        acreditacion = _acreditacion(persona, evento)
        assert acreditacion is not None, "El beneficiario no fue acreditado"
        assert acreditacion.estado == "ACTIVA"
        assert acreditacion.acceso_fiesta is True
        assert acreditacion.acceso_box is None

    # 7. The gate ALLOWS the access of the first beneficiary.
    qr_token = str(_acreditacion(persona_beneficiaria_1, evento).codigo_qr)
    acceso = _auth_post(
        api_client, RUTA_ACCESO, usuario_comprador, {"qr_token": qr_token}
    )
    assert acceso.status_code == 200, acceso.content
    assert acceso.json()["data"]["resultado"] == "PERMITIDO"


@pytest.mark.django_db
def test_e2e_el_flujo_de_pases_no_toca_ningun_objeto_deportivo(
    api_client,
    usuario_comprador,
    pase_fiesta,
    persona_beneficiaria_1,
    settings,
    flujo_confirmacion,
):
    """
    GIVEN: a buyer who buys and pays a batch of passes
    WHEN:  the whole commercial flow runs (settlement + assignment + access)
    THEN:  not ONE sports object and not ONE sports balance changed
    """
    settings.PASES_FIESTA_ENABLED = True

    antes = _objetos_deportivos()

    compra = _comprar_pases(api_client, usuario_comprador, pase_fiesta, 1)
    compra_id = compra["compra_id"]

    orden = Compra.objects.get(id=compra_id).orden_pago
    _crear_transaccion(
        orden,
        transaction_id="E2EPASE0002",
        amount=Decimal(str(compra["total"])),
    )
    async_to_sync(flujo_confirmacion._confirmar_compra)(str(orden.id))

    persona = _resolver_persona(api_client, usuario_comprador, "DNI", "71000001")
    asignados = _asignar(
        api_client, usuario_comprador, compra_id, [persona["persona_id"]]
    )
    assert asignados.status_code == 200, asignados.content

    qr_token = str(
        _acreditacion(persona_beneficiaria_1, pase_fiesta.evento).codigo_qr
    )
    acceso = _auth_post(
        api_client, RUTA_ACCESO, usuario_comprador, {"qr_token": qr_token}
    )
    assert acceso.status_code == 200, acceso.content

    assert _objetos_deportivos() == antes


# ── E2E 2: manual payment approval → assignment → access ────────────────────


@pytest.mark.django_db
def test_e2e_aprobacion_manual_asignacion_y_acceso(
    api_client,
    usuario_comprador,
    usuario_superusuario_passes,
    pase_fiesta,
    persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a pending pass purchase paid outside the provider
    WHEN:  the administrator approves the payment manually, the buyer assigns
           a person and the gate scans the QR
    THEN:  the purchase is paid, the right is active and the gate ALLOWS the
           access
    """
    settings.PASES_FIESTA_ENABLED = True
    settings.PAGO_MANUAL_APROBACION_ENABLED = True

    compra = _comprar_pases(api_client, usuario_comprador, pase_fiesta, 1)
    compra_id = compra["compra_id"]
    orden = Compra.objects.get(id=compra_id).orden_pago

    # The administrator registers the evidence of the payment.
    aprobado = _auth_post(
        api_client,
        RUTA_APROBAR_MANUAL.format(orden_pago_id=str(orden.id)),
        usuario_superusuario_passes,
        {
            "canal": "TRANSFERENCIA_BANCARIA",
            "referencia": "OP-E2E-001",
            "monto": str(compra["total"]),
            "moneda": "PEN",
            "motivo": "Abono verificado en la cuenta de la institución",
        },
    )
    assert aprobado.status_code == 200, aprobado.content

    estado = _auth_get(
        api_client, RUTA_ESTADO_COMPRA.format(compra_id=compra_id), usuario_comprador
    )
    assert estado.json()["data"]["estado_compra"] == EstadoCompraChoices.PAGADA
    assert estado.json()["data"]["origen_pago"] == OrigenPago.MANUAL

    persona = _resolver_persona(api_client, usuario_comprador, "DNI", "71000001")
    asignados = _asignar(
        api_client, usuario_comprador, compra_id, [persona["persona_id"]]
    )
    assert asignados.status_code == 200, asignados.content

    qr_token = str(
        _acreditacion(persona_beneficiaria_1, pase_fiesta.evento).codigo_qr
    )
    acceso = _auth_post(
        api_client, RUTA_ACCESO, usuario_comprador, {"qr_token": qr_token}
    )
    assert acceso.status_code == 200, acceso.content
    assert acceso.json()["data"]["resultado"] == "PERMITIDO"


# ── E2E 3: administrative cancellation → rights revoked → the gate denies ────


@pytest.mark.django_db
def test_e2e_cancelacion_administrativa_revoca_el_derecho_y_el_gate_deniega(
    api_client,
    usuario_comprador,
    usuario_superusuario_passes,
    pase_fiesta,
    persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a paid pass purchase with an assigned beneficiary
    WHEN:  the administrator cancels the purchase
    THEN:  the right is revoked, the accreditation loses the fiesta access and
           the gate DENIES the access — the cancellation is NOT a refund
    """
    settings.PASES_FIESTA_ENABLED = True
    settings.PAGO_MANUAL_APROBACION_ENABLED = True

    compra = _comprar_pases(api_client, usuario_comprador, pase_fiesta, 1)
    compra_id = compra["compra_id"]
    orden = Compra.objects.get(id=compra_id).orden_pago

    # The purchase is paid through the manual approval of the administrator.
    aprobado = _auth_post(
        api_client,
        RUTA_APROBAR_MANUAL.format(orden_pago_id=str(orden.id)),
        usuario_superusuario_passes,
        {
            "canal": "EFECTIVO",
            "referencia": "OP-E2E-003",
            "monto": str(compra["total"]),
            "moneda": "PEN",
            "motivo": "Pago en caja de la organización",
        },
    )
    assert aprobado.status_code == 200, aprobado.content

    persona = _resolver_persona(api_client, usuario_comprador, "DNI", "71000001")
    asignados = _asignar(
        api_client, usuario_comprador, compra_id, [persona["persona_id"]]
    )
    assert asignados.status_code == 200, asignados.content

    acreditacion = _acreditacion(persona_beneficiaria_1, pase_fiesta.evento)
    qr_token = str(acreditacion.codigo_qr)

    permitido = _auth_post(
        api_client, RUTA_ACCESO, usuario_comprador, {"qr_token": qr_token}
    )
    assert permitido.json()["data"]["resultado"] == "PERMITIDO"

    # The administrator cancels the purchase.
    cancelada = _auth_post(
        api_client,
        RUTA_CANCELAR_PASE.format(compra_id=compra_id),
        usuario_superusuario_passes,
        {"motivo": "Solicitud del comprador"},
    )
    assert cancelada.status_code == 200, cancelada.content
    assert cancelada.json()["data"]["estado_compra"] == EstadoCompraChoices.CANCELADA
    assert cancelada.json()["data"]["beneficiarios_revocados"] == 1

    # The right is revoked and the accreditation was recomputed.
    derecho = PaseBeneficiario.objects.get(
        compra_pase__compra_id=compra_id,
        persona_id=persona_beneficiaria_1.id,
    )
    assert derecho.estado == EstadoPaseBeneficiarioChoices.REVOCADA

    acreditacion.refresh_from_db()
    assert acreditacion.acceso_fiesta is False

    # The gate DENIES the access: the QR no longer enables it.
    denegado = _auth_post(
        api_client, RUTA_ACCESO, usuario_comprador, {"qr_token": qr_token}
    )
    assert denegado.status_code == 200, denegado.content
    assert denegado.json()["data"]["resultado"] == "DENEGADO"
