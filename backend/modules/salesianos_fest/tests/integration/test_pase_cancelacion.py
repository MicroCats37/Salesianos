"""
Integration tests — cancellation of a party-pass purchase (Apply 5).

What this file proves:

1. the ordinary buyer endpoint CANNOT cancel a pass purchase: the
   cancellation of a pass purchase is an administrative, audited decision;
2. the administrative cancellation cancels the purchase AND its order,
   revokes the nominative rights with their audit and recomputes the
   effective access;
3. it is IDEMPOTENT: cancelling twice revokes nothing twice;
4. the motive is MANDATORY and the endpoint is ADMIN-ONLY;
5. the annulment of a manual payment approval revokes the pass rights with
   the SAME canonical revocation;
6. it is NOT a monetary refund: no money movement is recorded.

NOT EXECUTED IN THIS PHASE: the tests are written here and run only once, in
Apply 9 (the consolidated validation of the whole change).
"""
import json
import uuid

import pytest
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.pagos.domain.constants import (
    CanalPagoManual,
    EstadoAprobacionPagoManual,
    OrdenPagoStatus,
)
from modules.pagos.domain.models import AprobacionPagoManual, TransaccionPago
from modules.salesianos_fest.domain.models import (
    AcreditacionEvento,
    PaseBeneficiario,
)

RUTA_BENEFICIARIOS = "/api/pases/compras/{compra_id}/beneficiarios"
RUTA_CANCELAR_ADMIN = "/api/administracion/pases/compras/{compra_id}/cancelar"
RUTA_CANCELAR_COMPRADOR = "/api/compras/{compra_id}/cancelar"
RUTA_ANULAR_MANUAL = "/api/administracion/pagos/{orden_pago_id}/anular-manual"


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


def _asignar(client, usuario, compra, personas):
    """Assign the given personas to the free slots of a purchase."""
    return _auth_post(
        client,
        RUTA_BENEFICIARIOS.format(compra_id=str(compra.id)),
        usuario,
        {"beneficiario_ids": [str(persona.id) for persona in personas]},
    )


def _cancelar_admin(client, admin, compra, motivo="Cancelación administrativa"):
    """Cancel a pass purchase as an administrator."""
    return _auth_post(
        client,
        RUTA_CANCELAR_ADMIN.format(compra_id=str(compra.id)),
        admin,
        {"motivo": motivo},
    )


def _aprobacion_manual(orden_pago, admin, monto):
    """Register an ACTIVE manual approval over an order."""
    return AprobacionPagoManual.objects.create(
        orden_pago=orden_pago,
        actor=admin,
        canal=CanalPagoManual.TRANSFERENCIA_BANCARIA,
        referencia="OP-PASE-MANUAL",
        monto=monto,
        moneda="PEN",
        motivo="Abono verificado",
        estado=EstadoAprobacionPagoManual.APROBADA,
    )


# ── Tests: the buyer cannot cancel a pass purchase ──────────────────────────


@pytest.mark.django_db
def test_el_comprador_no_puede_cancelar_una_compra_de_pases(
    api_client, usuario_comprador, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a PAID pass purchase of the buyer
    WHEN:  the buyer calls the ordinary cancellation endpoint
    THEN:  403 — the cancellation of a pass purchase is administrative
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    response = _auth_post(
        api_client,
        RUTA_CANCELAR_COMPRADOR.format(compra_id=str(compra_pase_pagada.id)),
        usuario_comprador,
    )

    assert response.status_code == 403, response.content
    assert (
        response.json()["error"]["code"]
        == "PASE_CANCELACION_REQUIERE_ADMINISTRACION"
    )

    compra_pase_pagada.refresh_from_db()
    assert compra_pase_pagada.estado == EstadoCompraChoices.PAGADA
    assert PaseBeneficiario.objects.filter(
        estado="ACTIVA"
    ).count() == 1


# ── Tests: the administrative cancellation ────────────────────────────────────


@pytest.mark.django_db
def test_la_cancelacion_administrativa_cancela_la_compra_y_la_orden(
    api_client, usuario_admin_pases, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a PAID pass purchase with a beneficiary
    WHEN:  an administrator cancels it
    THEN:  the purchase AND its order are CANCELADA
    """
    settings.PASES_FIESTA_ENABLED = True
    orden_pago = compra_pase_pagada.orden_pago

    response = _cancelar_admin(api_client, usuario_admin_pases, compra_pase_pagada)

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["estado_compra"] == EstadoCompraChoices.CANCELADA
    assert data["estado_orden"] == OrdenPagoStatus.CANCELADA
    assert data["ya_cancelada"] is False

    compra_pase_pagada.refresh_from_db()
    orden_pago.refresh_from_db()
    assert compra_pase_pagada.estado == EstadoCompraChoices.CANCELADA
    assert orden_pago.estado == OrdenPagoStatus.CANCELADA


@pytest.mark.django_db
def test_la_cancelacion_administrativa_revoca_los_beneficiarios_con_auditoria(
    api_client, usuario_admin_pases, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, settings,
):
    """
    GIVEN: a PAID pass purchase with an ACTIVE beneficiary
    WHEN:  an administrator cancels it
    THEN:  the right is REVOCADA with the actor, the date and the motive
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    response = _cancelar_admin(
        api_client,
        usuario_admin_pases,
        compra_pase_pagada,
        motivo="Solicitud del comprador",
    )
    assert response.status_code == 200, response.content
    assert response.json()["data"]["beneficiarios_revocados"] == 1

    fila = PaseBeneficiario.objects.get(persona=persona_beneficiaria_1)
    assert fila.estado == "REVOCADA"
    assert fila.revocado_por_id == usuario_admin_pases.id
    assert fila.revocado_en is not None
    assert fila.motivo_revocacion == "Solicitud del comprador"


@pytest.mark.django_db
def test_la_cancelacion_administrativa_recalcula_el_acceso(
    api_client, usuario_admin_pases, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, settings,
):
    """
    GIVEN: a beneficiary with fiesta access thanks to the pass
    WHEN:  an administrator cancels the purchase
    THEN:  the effective access is recomputed and the access is gone
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    acreditacion = AcreditacionEvento.objects.get(
        persona=persona_beneficiaria_1, evento=compra_pase_pagada.evento
    )
    assert acreditacion.acceso_fiesta is True

    response = _cancelar_admin(api_client, usuario_admin_pases, compra_pase_pagada)
    assert response.status_code == 200, response.content
    assert response.json()["data"]["personas_afectadas"] == 1

    acreditacion.refresh_from_db()
    assert acreditacion.acceso_fiesta is False


@pytest.mark.django_db
def test_la_cancelacion_administrativa_es_idempotente(
    api_client, usuario_admin_pases, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, settings,
):
    """
    GIVEN: a pass purchase already cancelled by the administration
    WHEN:  the cancellation is repeated
    THEN:  200 with ya_cancelada=True and NOTHING is revoked twice
    """
    settings.PASES_FIESTA_ENABLED = True
    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content
    assert _cancelar_admin(
        api_client, usuario_admin_pases, compra_pase_pagada
    ).status_code == 200

    segunda = _cancelar_admin(
        api_client, usuario_admin_pases, compra_pase_pagada
    )

    assert segunda.status_code == 200, segunda.content
    data = segunda.json()["data"]
    assert data["ya_cancelada"] is True
    assert data["beneficiarios_revocados"] == 0
    assert PaseBeneficiario.objects.count() == 1


@pytest.mark.django_db
def test_la_cancelacion_administrativa_exige_motivo(
    api_client, usuario_admin_pases, compra_pase_pagada, settings
):
    """
    GIVEN: an administrator without a motive
    WHEN:  the cancellation is requested
    THEN:  422 — the motive is mandatory and audited
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        RUTA_CANCELAR_ADMIN.format(compra_id=str(compra_pase_pagada.id)),
        usuario_admin_pases,
        {"motivo": ""},
    )

    assert response.status_code == 422, response.content
    compra_pase_pagada.refresh_from_db()
    assert compra_pase_pagada.estado == EstadoCompraChoices.PAGADA


@pytest.mark.django_db
def test_la_cancelacion_administrativa_exige_administrador(
    api_client, usuario_comprador, compra_pase_pagada, settings
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  the cancellation is requested
    THEN:  403 — the endpoint is admin-only
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        RUTA_CANCELAR_ADMIN.format(compra_id=str(compra_pase_pagada.id)),
        usuario_comprador,
        {"motivo": "No soy administrador"},
    )

    assert response.status_code == 403, response.content
    compra_pase_pagada.refresh_from_db()
    assert compra_pase_pagada.estado == EstadoCompraChoices.PAGADA


@pytest.mark.django_db
def test_la_cancelacion_administrativa_sin_autenticacion_es_rechazada(
    api_client, compra_pase_pagada, settings
):
    """
    GIVEN: an anonymous caller
    WHEN:  the cancellation is requested
    THEN:  401
    """
    settings.PASES_FIESTA_ENABLED = True

    response = api_client.post(
        RUTA_CANCELAR_ADMIN.format(compra_id=str(compra_pase_pagada.id)),
        data=json.dumps({"motivo": "Sin sesión"}),
        content_type="application/json",
    )

    assert response.status_code == 401, response.content


@pytest.mark.django_db
def test_la_cancelacion_administrativa_de_una_compra_inexistente_es_404(
    api_client, usuario_admin_pases, settings
):
    """
    GIVEN: a purchase that does not exist
    WHEN:  the cancellation is requested
    THEN:  404
    """
    settings.PASES_FIESTA_ENABLED = True

    response = _auth_post(
        api_client,
        RUTA_CANCELAR_ADMIN.format(compra_id=str(uuid.uuid4())),
        usuario_admin_pases,
        {"motivo": "No existe"},
    )

    assert response.status_code == 404, response.content


@pytest.mark.django_db
def test_la_cancelacion_administrativa_no_reembolsa(
    api_client, usuario_admin_pases, compra_pase_pagada, persona_beneficiaria_1,
    settings,
):
    """
    GIVEN: a pass purchase paid with a manual approval
    WHEN:  an administrator cancels it
    THEN:  NO money movement is recorded: no provider transaction is created
           and the ACTIVE manual approval (the evidence of the payment) is
           annulled in the SAME operation — a cancelled purchase never keeps
           a live payment evidence.
    """
    settings.PASES_FIESTA_ENABLED = True
    orden_pago = compra_pase_pagada.orden_pago
    _aprobacion_manual(orden_pago, usuario_admin_pases, orden_pago.monto_total)
    transacciones = TransaccionPago.objects.count()

    response = _cancelar_admin(api_client, usuario_admin_pases, compra_pase_pagada)

    assert response.status_code == 200, response.content
    assert TransaccionPago.objects.count() == transacciones
    assert AprobacionPagoManual.objects.filter(
        orden_pago_id=orden_pago.id,
        estado=EstadoAprobacionPagoManual.ANULADA,
    ).count() == 1
    assert AprobacionPagoManual.objects.filter(
        orden_pago_id=orden_pago.id,
        estado=EstadoAprobacionPagoManual.APROBADA,
    ).count() == 0


# ── Tests: the annulment of a manual approval ───────────────────────────────


@pytest.mark.django_db
def test_la_anulacion_de_un_pago_manual_revoca_los_pases(
    api_client, usuario_admin_pases, usuario_comprador, compra_pase_pagada,
    persona_beneficiaria_1, settings,
):
    """
    GIVEN: a pass purchase paid with a manual approval and a beneficiary
    WHEN:  an administrator annuls that approval
    THEN:  the approval, the order and the purchase are cancelled and the
            pass rights are revoked with the SAME canonical revocation
    """
    settings.PASES_FIESTA_ENABLED = True
    settings.PAGO_MANUAL_APROBACION_ENABLED = True
    orden_pago = compra_pase_pagada.orden_pago
    _aprobacion_manual(orden_pago, usuario_admin_pases, orden_pago.monto_total)

    asignada = _asignar(
        api_client, usuario_comprador, compra_pase_pagada, [persona_beneficiaria_1]
    )
    assert asignada.status_code == 200, asignada.content

    response = _auth_post(
        api_client,
        RUTA_ANULAR_MANUAL.format(orden_pago_id=str(orden_pago.id)),
        usuario_admin_pases,
        {"motivo": "El abono no se verificó"},
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["resultado"] == "ANULADA"

    compra_pase_pagada.refresh_from_db()
    orden_pago.refresh_from_db()
    fila = PaseBeneficiario.objects.get(persona=persona_beneficiaria_1)

    assert compra_pase_pagada.estado == EstadoCompraChoices.CANCELADA
    assert orden_pago.estado == OrdenPagoStatus.CANCELADA
    assert fila.estado == "REVOCADA"

    acreditacion = AcreditacionEvento.objects.get(
        persona=persona_beneficiaria_1, evento=compra_pase_pagada.evento
    )
    assert acreditacion.acceso_fiesta is False
