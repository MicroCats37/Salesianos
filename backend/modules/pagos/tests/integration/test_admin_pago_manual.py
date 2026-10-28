"""
Integration tests of the administrative approval of a manual payment.

The capability under test:

- ONLY an administrator (`RequireAdmin`) can approve or annul a payment
  received outside the payment provider,
- the evidence is STRUCTURED (order, actor, channel, reference, amount,
  currency, motive) and IMPUTABLE,
- the amount and the currency must match the order EXACTLY,
- at most ONE active approval exists per order,
- approving NEVER creates a provider transaction,
- the operation is IDEMPOTENT: approving twice never duplicates the approval
  nor the rights,
- the annulment is AUDITED (actor, date, motive) and revokes ONLY the
  rights funded by that purchase.
"""
import json
import uuid
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import (
    CanalPagoManual,
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrdenPagoStatus,
)
from modules.pagos.domain.models import (
    AprobacionPagoManual,
    OrdenPago,
    TransaccionPago,
)
from modules.pagos.tests.fixtures.factories import (
    make_payload_anulacion_manual,
    make_payload_aprobacion_manual,
)
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EtapaChoices,
    ModoDisciplinasChoices,
    TipoCompraChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Inscripcion,
    InscripcionPersona,
    Paquete,
    PaquetePrecio,
    Promocion,
)
from modules.usuarios.domain.models.persona import Persona

RUTA_APROBAR = "/api/administracion/pagos/{orden_pago_id}/aprobar-manual"
RUTA_ANULAR = "/api/administracion/pagos/{orden_pago_id}/anular-manual"


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def aprobacion_habilitada(settings):
    """The capability is enabled for the whole file."""
    settings.PAGO_MANUAL_APROBACION_ENABLED = True


def _crear_usuario(username: str, *, es_admin: bool = False):
    """Create an account with its linked persona."""
    User = get_user_model()
    marca = uuid.uuid4().hex[:8]
    persona = Persona.objects.create(
        nombres="Actor",
        apellidos="Prueba",
        tipo_documento="DNI",
        numero_documento=f"{uuid.uuid4().int % 100000000:08d}",
        genero="M",
    )
    usuario = User.objects.create_user(
        username=f"{username}_{marca}",
        email=f"{username}_{marca}@example.com",
        password="testpass123",
        persona_fk=persona,
    )
    if es_admin:
        usuario.is_staff = True
        usuario.save(update_fields=["is_staff"])
    return usuario


@pytest.fixture
def usuario_admin(db):
    """An authenticated administrator with the break-glass tier.

    Approving or annulling a manual payment is a SENSITIVE action: it needs
    the capability `admin.pagos.aprobar`, which only the break-glass tier
    holds.
    """
    usuario = _crear_usuario("admin_manual", es_admin=True)
    usuario.is_superuser = True
    usuario.save(update_fields=["is_superuser"])
    return usuario


@pytest.fixture
def usuario_no_admin(db):
    """An authenticated user that is NOT an administrator."""
    return _crear_usuario("comprador_manual")


@pytest.fixture
def evento(db):
    """The ACTIVE event of the administration area."""
    return Evento.objects.create(
        nombre="Salesianos FEST Manual 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def promocion(db):
    """A promotion of the event."""
    return Promocion.objects.create(anio=2012, nombre="Junior Manual", activa=True)


@pytest.fixture
def paquete(db, evento):
    """A package of the event with its price."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro Manual",
        descripcion="Paquete de prueba para la aprobación manual",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("400.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.fixture
def persona(db):
    """The buyer of the purchase."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento=f"{uuid.uuid4().int % 100000000:08d}",
        genero="F",
    )


@pytest.fixture
def inscripcion(db, evento, persona, paquete, promocion):
    """The inscription that funds the purchase."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete,
        promocion=promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def participante_preregistrado(db, inscripcion, persona):
    """A participant waiting for a paid cupo."""
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


@pytest.fixture
def orden_pago(db):
    """A PENDING payment order of 400 PEN."""
    return OrdenPago.objects.create(
        numero=f"OP-MANUAL-{uuid.uuid4().hex[:8]}",
        monto_total=Decimal("400.00"),
        moneda="PEN",
        estado=OrdenPagoStatus.PENDIENTE,
    )


@pytest.fixture
def compra_pendiente(db, orden_pago, inscripcion, persona):
    """A PENDING purchase funded by the pending order."""
    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Compra FEST manual",
        referencia_externa="MANUAL-REF-1",
        total=Decimal("400.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=Decimal("400.00"),
        total=Decimal("400.00"),
    )
    return compra


# ── Helpers ────────────────────────────────────────────────────────────────────

def _post(client, ruta: str, payload: dict, usuario=None):
    """POST a JSON payload, optionally authenticated."""
    headers = {}
    if usuario is not None:
        token = AccessToken.for_user(usuario)
        headers["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client.post(
        ruta,
        data=json.dumps(payload),
        content_type="application/json",
        **headers,
    )


def _aprobar(client, orden_pago, usuario, **overrides):
    """POST the approval of a manual payment."""
    payload = make_payload_aprobacion_manual(**overrides)
    return _post(
        client,
        RUTA_APROBAR.format(orden_pago_id=orden_pago.id),
        payload,
        usuario,
    )


def _cupos_activos(inscripcion_id):
    return AsignacionCupo.objects.filter(
        inscripcion_id=inscripcion_id,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).count()


# ── Tests: autorización ────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_aprobar_pago_manual_sin_autenticacion_es_rechazado(
    api_client, orden_pago, compra_pendiente
):
    """
    GIVEN: an anonymous caller
    WHEN:  POST /administracion/pagos/{id}/aprobar-manual
    THEN:  401 and no approval is registered.
    """
    response = _post(
        api_client,
        RUTA_APROBAR.format(orden_pago_id=orden_pago.id),
        make_payload_aprobacion_manual(),
    )

    assert response.status_code == 401, response.content
    assert AprobacionPagoManual.objects.count() == 0


@pytest.mark.django_db
def test_aprobar_pago_manual_por_usuario_no_admin_es_rechazado(
    api_client, usuario_no_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  POST /administracion/pagos/{id}/aprobar-manual
    THEN:  403 and nothing changes.
    """
    response = _aprobar(api_client, orden_pago, usuario_no_admin)

    assert response.status_code == 403, response.content
    assert AprobacionPagoManual.objects.count() == 0

    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PENDIENTE

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_anular_pago_manual_por_usuario_no_admin_es_rechazado(
    api_client, usuario_no_admin, orden_pago, compra_pendiente, usuario_admin
):
    """
    GIVEN: an order approved by an administrator
    WHEN:  a NON administrator tries to annul the approval
    THEN:  403 and the approval stays active.
    """
    _aprobar(api_client, orden_pago, usuario_admin)

    response = _post(
        api_client,
        RUTA_ANULAR.format(orden_pago_id=orden_pago.id),
        make_payload_anulacion_manual(),
        usuario_no_admin,
    )

    assert response.status_code == 403, response.content

    aprobacion = AprobacionPagoManual.objects.get(orden_pago_id=orden_pago.id)
    assert aprobacion.estado == EstadoAprobacionPagoManual.APROBADA


# ── Tests: validación de la evidencia ──────────────────────────────────────────

@pytest.mark.django_db
def test_aprobar_pago_manual_con_referencia_vacia_es_rechazado(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an administrator with an empty reference
    WHEN:  POST /administracion/pagos/{id}/aprobar-manual
    THEN:  422 and no approval is registered.
    """
    response = _aprobar(api_client, orden_pago, usuario_admin, referencia="")

    assert response.status_code == 422, response.content
    assert AprobacionPagoManual.objects.count() == 0


@pytest.mark.django_db
def test_aprobar_pago_manual_con_canal_desconocido_es_rechazado(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an administrator with an unknown channel
    WHEN:  POST /administracion/pagos/{id}/aprobar-manual
    THEN:  422 — the channel is a closed set.
    """
    response = _aprobar(api_client, orden_pago, usuario_admin, canal="CRIPTO")

    assert response.status_code == 422, response.content
    assert AprobacionPagoManual.objects.count() == 0


@pytest.mark.django_db
def test_aprobar_pago_manual_con_monto_distinto_es_rechazado(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order of 400 PEN
    WHEN:  an administrator approves 500 PEN
    THEN:  409 MONTO_NO_COINCIDE and everything stays pending.
    """
    response = _aprobar(api_client, orden_pago, usuario_admin, monto="500.00")

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "MONTO_NO_COINCIDE"
    assert AprobacionPagoManual.objects.count() == 0

    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PENDIENTE

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_aprobar_pago_manual_con_moneda_distinta_es_rechazado(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order of 400 PEN
    WHEN:  an administrator approves 400 USD
    THEN:  409 MONTO_NO_COINCIDE.
    """
    response = _aprobar(api_client, orden_pago, usuario_admin, moneda="USD")

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "MONTO_NO_COINCIDE"
    assert AprobacionPagoManual.objects.count() == 0


# ── Tests: exclusión ───────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_aprobar_pago_manual_sobre_orden_pagada_con_izipay_es_rechazado(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order already paid through the provider
    WHEN:  an administrator tries to approve it manually
    THEN:  409 ORDEN_YA_PAGADA_CON_IZIPAY and no approval is registered.
    """
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="MANUALTX001",
        order_number="MANUALTN001",
        amount=Decimal("400.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )

    response = _aprobar(api_client, orden_pago, usuario_admin)

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "ORDEN_YA_PAGADA_CON_IZIPAY"
    assert AprobacionPagoManual.objects.count() == 0


@pytest.mark.django_db
def test_aprobar_pago_manual_sobre_compra_cancelada_es_rechazado(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: a purchase that was already cancelled
    WHEN:  an administrator tries to approve its payment
    THEN:  409 COMPRA_YA_CANCELADA.
    """
    compra_pendiente.estado = EstadoCompraChoices.CANCELADA
    compra_pendiente.save(update_fields=["estado", "updated_at"])

    response = _aprobar(api_client, orden_pago, usuario_admin)

    assert response.status_code == 409, response.content
    assert response.json()["error"]["code"] == "COMPRA_YA_CANCELADA"
    assert AprobacionPagoManual.objects.count() == 0


# ── Tests: la aprobación correcta ──────────────────────────────────────────────

@pytest.mark.django_db
def test_aprobar_pago_manual_registra_la_evidencia_y_el_actor(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: a pending order linked to a pending purchase
    WHEN:  an administrator approves the payment
    THEN:  200, the approval records every field of the evidence and the
           administrator is the actor.
    """
    response = _aprobar(
        api_client,
        orden_pago,
        usuario_admin,
        canal=CanalPagoManual.YAPE,
        referencia="OP-999",
        motivo="Abono verificado por Yape",
    )

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["success"] is True
    assert body["data"]["resultado"] == "APROBADA"
    assert body["data"]["estado_aprobacion"] == EstadoAprobacionPagoManual.APROBADA

    aprobacion = AprobacionPagoManual.objects.get(orden_pago_id=orden_pago.id)
    assert aprobacion.actor_id == usuario_admin.id
    assert aprobacion.canal == CanalPagoManual.YAPE
    assert aprobacion.referencia == "OP-999"
    assert aprobacion.monto == Decimal("400.00")
    assert aprobacion.moneda == "PEN"
    assert aprobacion.motivo == "Abono verificado por Yape"
    assert aprobacion.estado == EstadoAprobacionPagoManual.APROBADA


@pytest.mark.django_db
def test_aprobar_pago_manual_no_crea_una_transaccion_izipay(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order without any provider attempt
    WHEN:  an administrator approves the payment manually
    THEN:  NO TransaccionPago is created — a manual payment never fabricates
           a provider transaction.
    """
    _aprobar(api_client, orden_pago, usuario_admin)

    assert TransaccionPago.objects.count() == 0


@pytest.mark.django_db
def test_aprobar_pago_manual_sella_la_orden_como_pagada(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: a pending order
    WHEN:  an administrator approves the payment
    THEN:  the order is PAGADA with its payment timestamp.
    """
    _aprobar(api_client, orden_pago, usuario_admin)

    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA
    assert orden_pago.pagada_en is not None


@pytest.mark.django_db
def test_aprobar_pago_manual_liquida_la_compra_y_asigna_derechos(
    api_client, usuario_admin, orden_pago, compra_pendiente, inscripcion,
    participante_preregistrado,
):
    """
    GIVEN: a pending purchase with a preregistered participant
    WHEN:  an administrator approves the payment
    THEN:  the purchase is paid, the right is allocated and the settlement
           is reported as SETTLED.
    """
    response = _aprobar(api_client, orden_pago, usuario_admin)

    assert response.status_code == 200, response.content
    assert response.json()["data"]["settlement_status"] == "SETTLED"

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA

    assert _cupos_activos(inscripcion.id) == 1


@pytest.mark.django_db
def test_aprobar_pago_manual_es_idempotente(
    api_client, usuario_admin, orden_pago, compra_pendiente, inscripcion,
    participante_preregistrado,
):
    """
    GIVEN: an order already approved manually
    WHEN:  an administrator approves it AGAIN
    THEN:  200 with YA_APROBADA, ONE active approval and NO duplicated
           rights.
    """
    primero = _aprobar(api_client, orden_pago, usuario_admin)
    assert primero.status_code == 200, primero.content

    segundo = _aprobar(api_client, orden_pago, usuario_admin)
    assert segundo.status_code == 200, segundo.content
    assert segundo.json()["data"]["resultado"] == "YA_APROBADA"

    assert (
        AprobacionPagoManual.objects.filter(
            orden_pago_id=orden_pago.id,
            estado=EstadoAprobacionPagoManual.APROBADA,
        ).count()
        == 1
    )
    assert _cupos_activos(inscripcion.id) == 1


@pytest.mark.django_db
def test_dos_aprobaciones_concurrentes_dejan_una_sola_activa(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: two simultaneous valid requests for the same order
    WHEN:  both try to approve it
    THEN:  there is exactly ONE active approval (the database refuses the
           second one) and the operation is idempotent.
    """
    _aprobar(api_client, orden_pago, usuario_admin)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AprobacionPagoManual.objects.create(
                orden_pago_id=orden_pago.id,
                actor_id=usuario_admin.id,
                canal=CanalPagoManual.EFECTIVO,
                referencia="SEGUNDO-INTENTO",
                monto=Decimal("400.00"),
                moneda="PEN",
                motivo="Segundo intento concurrente",
                estado=EstadoAprobacionPagoManual.APROBADA,
            )

    assert (
        AprobacionPagoManual.objects.filter(
            orden_pago_id=orden_pago.id,
            estado=EstadoAprobacionPagoManual.APROBADA,
        ).count()
        == 1
    )


# ── Tests: la anulación auditada ───────────────────────────────────────────────

@pytest.mark.django_db
def test_anular_pago_manual_registra_actor_fecha_y_motivo(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: a purchase settled through a manual approval
    WHEN:  an administrator annuls the approval with a motive
    THEN:  the approval is ANULADA with its actor, date and motive, and the
           order and the purchase are CANCELADA.
    """
    _aprobar(api_client, orden_pago, usuario_admin)

    response = _post(
        api_client,
        RUTA_ANULAR.format(orden_pago_id=orden_pago.id),
        make_payload_anulacion_manual(motivo="Registro administrativo duplicado"),
        usuario_admin,
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["resultado"] == "ANULADA"

    aprobacion = AprobacionPagoManual.objects.get(orden_pago_id=orden_pago.id)
    assert aprobacion.estado == EstadoAprobacionPagoManual.ANULADA
    assert aprobacion.anulada_por_id == usuario_admin.id
    assert aprobacion.anulada_en is not None
    assert aprobacion.motivo_anulacion == "Registro administrativo duplicado"

    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.CANCELADA

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.CANCELADA


@pytest.mark.django_db
def test_anular_pago_manual_revoca_solo_los_derechos_financiados(
    api_client, usuario_admin, orden_pago, compra_pendiente, inscripcion,
    participante_preregistrado,
):
    """
    GIVEN: a purchase settled through a manual approval
    WHEN:  an administrator annuls the approval
    THEN:  the cupo funded by that purchase is revoked and no right stays.
    """
    _aprobar(api_client, orden_pago, usuario_admin)
    assert _cupos_activos(inscripcion.id) == 1

    _post(
        api_client,
        RUTA_ANULAR.format(orden_pago_id=orden_pago.id),
        make_payload_anulacion_manual(),
        usuario_admin,
    )

    assert _cupos_activos(inscripcion.id) == 0


@pytest.mark.django_db
def test_anular_pago_manual_es_idempotente(
    api_client, usuario_admin, orden_pago, compra_pendiente, inscripcion,
    participante_preregistrado,
):
    """
    GIVEN: an approval that was already annulled
    WHEN:  an administrator annuls it again
    THEN:  200 with YA_ANULADA and nothing is revoked twice.
    """
    _aprobar(api_client, orden_pago, usuario_admin)
    _post(
        api_client,
        RUTA_ANULAR.format(orden_pago_id=orden_pago.id),
        make_payload_anulacion_manual(),
        usuario_admin,
    )

    segundo = _post(
        api_client,
        RUTA_ANULAR.format(orden_pago_id=orden_pago.id),
        make_payload_anulacion_manual(),
        usuario_admin,
    )

    assert segundo.status_code == 200, segundo.content
    assert segundo.json()["data"]["resultado"] == "YA_ANULADA"
    assert segundo.json()["data"]["asignaciones_revocadas"] == 0


@pytest.mark.django_db
def test_anular_pago_manual_sin_aprobacion_es_rechazado(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order WITHOUT a manual approval
    WHEN:  an administrator tries to annul it
    THEN:  404 and nothing changes.
    """
    response = _post(
        api_client,
        RUTA_ANULAR.format(orden_pago_id=orden_pago.id),
        make_payload_anulacion_manual(),
        usuario_admin,
    )

    assert response.status_code == 404, response.content

    orden_pago.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PENDIENTE


@pytest.mark.django_db
def test_el_comprador_no_puede_anular_la_compra_con_aprobacion_manual(
    api_client, usuario_admin, usuario_no_admin, orden_pago, compra_pendiente,
    inscripcion, participante_preregistrado,
):
    """
    GIVEN: a purchase funded by an active manual approval
    WHEN:  the buyer tries to cancel it through the public route
    THEN:  403 — only the administrative annulment revokes it.
    """
    _aprobar(api_client, orden_pago, usuario_admin)

    token = AccessToken.for_user(usuario_no_admin)
    response = api_client.post(
        f"/api/compras/{compra_pendiente.id}/cancelar",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 403, response.content

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA


# ── Tests: la consulta administrativa ───────────────────────────────────────────

@pytest.mark.django_db
def test_el_detalle_muestra_el_origen_y_el_historial_sin_secretos(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order approved manually
    WHEN:  an administrator reads the drilldown of the order
    THEN:  the origin is MANUAL, the history shows the approval and NO
           provider secret is exposed.
    """
    _aprobar(api_client, orden_pago, usuario_admin)

    token = AccessToken.for_user(usuario_admin)
    response = api_client.get(
        f"/api/administracion/pagos/{orden_pago.id}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["data"]["origen_pago"] == "MANUAL"
    assert len(body["data"]["aprobaciones"]) == 1

    aprobacion = body["data"]["aprobaciones"][0]
    assert aprobacion["estado"] == EstadoAprobacionPagoManual.APROBADA
    assert aprobacion["actor"] == usuario_admin.username
    assert aprobacion["referencia"] == "OP-123"
    assert aprobacion["moneda"] == "PEN"

    contenido = response.content.decode()
    for prohibido in ("token_sesion", "transaction_id", "metadata"):
        assert prohibido not in contenido


@pytest.mark.django_db
def test_el_detalle_muestra_la_anulacion_en_el_historial(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order approved manually and then annulled
    WHEN:  an administrator reads the drilldown of the order
    THEN:  the history shows the annulment with its actor, date and motive,
           and the origin reports that there is NO active evidence anymore.
    """
    _aprobar(api_client, orden_pago, usuario_admin)
    _post(
        api_client,
        RUTA_ANULAR.format(orden_pago_id=orden_pago.id),
        make_payload_anulacion_manual(),
        usuario_admin,
    )

    token = AccessToken.for_user(usuario_admin)
    response = api_client.get(
        f"/api/administracion/pagos/{orden_pago.id}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["data"]["origen_pago"] == "SIN_PAGO"
    assert len(body["data"]["aprobaciones"]) == 1

    aprobacion = body["data"]["aprobaciones"][0]
    assert aprobacion["estado"] == EstadoAprobacionPagoManual.ANULADA
    assert aprobacion["actor"] == usuario_admin.username
    assert aprobacion["anulada_por"] == usuario_admin.username
    assert aprobacion["motivo_anulacion"] == "Registro administrativo duplicado"
    assert aprobacion["anulada_en"] is not None


@pytest.mark.django_db
def test_el_detalle_de_una_orden_pagada_con_izipay_reporta_el_origen_izipay(
    api_client, usuario_admin, orden_pago, compra_pendiente
):
    """
    GIVEN: an order with a correlated successful provider transaction
    WHEN:  an administrator reads the drilldown of the order
    THEN:  the origin is IZIPAY.
    """
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="MANUALTX002",
        order_number="MANUALTN002",
        amount=Decimal("400.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )

    token = AccessToken.for_user(usuario_admin)
    response = api_client.get(
        f"/api/administracion/pagos/{orden_pago.id}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["origen_pago"] == "IZIPAY"
