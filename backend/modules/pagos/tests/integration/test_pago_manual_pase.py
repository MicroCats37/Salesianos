"""
Cross-module contract test — the payment module settles a PASS purchase.

The pass purchase is a commercial batch that lives in `salesianos_fest`, but
it is funded and settled by the SAME payment machinery as a sports purchase:
the Izipay evidence, the administrative manual approval and the settlement
port are reused verbatim.

This file proves the contract FROM THE PAYMENT SIDE, without changing a
single line of production code in `pagos`:

1. an administrator can approve the manual payment of a PASS order,
2. the approval settles the pass purchase through the existing port,
3. approving never fabricates a provider transaction,
4. the settlement of a pass order allocates ZERO sports rights.

The sports behaviour is untouched: the payment module does not know that a
pass exists, it only sees a `Compra` and an `OrdenPago`.
"""
import json
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrdenPagoStatus,
)
from modules.pagos.domain.models import (
    AprobacionPagoManual,
    OrdenPago,
    TransaccionPago,
)
from modules.pagos.tests.fixtures.factories import make_payload_aprobacion_manual
from modules.salesianos_fest.domain.constants import EtapaChoices
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    CompraPase,
    Inscripcion,
    InscripcionPersona,
    Pase,
    PasePrecio,
    Participacion,
)
from modules.usuarios.domain.models.persona import Persona

RUTA_APROBAR = "/api/administracion/pagos/{orden_pago_id}/aprobar-manual"


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def aprobacion_habilitada(settings):
    """The capability is enabled for the whole file."""
    settings.PAGO_MANUAL_APROBACION_ENABLED = True


@pytest.fixture
def api_client(db):
    """Django test client - it handles the async controllers correctly."""
    from django.test import Client

    return Client()


@pytest.fixture
def usuario_admin(db):
    """An authenticated administrator with the break-glass tier.

    Approving or annulling a manual payment is a SENSITIVE action: it needs
    the capability `admin.pagos.aprobar`, which only the break-glass tier
    holds.
    """
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
        username=f"admin_pase_{marca}",
        email=f"admin_pase_{marca}@example.com",
        password="testpass123",
        persona_fk=persona,
    )
    usuario.is_staff = True
    usuario.is_superuser = True
    usuario.save(update_fields=["is_staff", "is_superuser"])
    return usuario


@pytest.fixture
def persona_compradora(db):
    """The buyer of the pass batch."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Compradora",
        tipo_documento="DNI",
        numero_documento=f"{uuid.uuid4().int % 100000000:08d}",
        genero="F",
    )


@pytest.fixture
def evento(db):
    """The ACTIVE event of the pass catalogue."""
    return Evento.objects.create(
        nombre="Salesianos FEST Pases 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def pase(db, evento):
    """An active pass with a vigente price."""
    pase = Pase.objects.create(
        evento=evento,
        nombre="Pase de Fiesta",
        descripcion="Acceso nominativo a la fiesta de cierre.",
        cantidad_maxima=0,
        activo=True,
    )
    PasePrecio.objects.create(
        pase=pase,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("25.00"),
        vigente_desde=date.today() - timedelta(days=1),
        vigente_hasta=date.today() + timedelta(days=30),
        activo=True,
    )
    return pase


@pytest.fixture
def compra_pase_pendiente(db, persona_compradora, pase):
    """A PENDIENTE pass purchase funded by a PENDIENTE payment order."""
    total = Decimal("25.00") * 2

    orden_pago = OrdenPago.objects.create(
        numero=f"OP-PASE-{uuid.uuid4().hex[:8].upper()}",
        monto_total=total,
        moneda="PEN",
        estado=OrdenPagoStatus.PENDIENTE,
    )
    compra = Compra.objects.create(
        responsable=persona_compradora,
        descripcion=f"Compra de pases - {pase.nombre}",
        referencia_externa=f"PASE-{str(pase.id)[:8]}",
        total=total,
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraPase.objects.create(
        compra=compra,
        pase=pase,
        evento=pase.evento,
        cantidad=2,
        precio_unitario=Decimal("25.00"),
        total=total,
    )
    return compra


# ── Helpers ──────────────────────────────────────────────────────────────────


def _aprobar(client, orden_pago, usuario, **overrides):
    """POST the approval of a manual payment."""
    from ninja_jwt.tokens import AccessToken

    payload = make_payload_aprobacion_manual(**overrides)
    token = AccessToken.for_user(usuario)
    return client.post(
        RUTA_APROBAR.format(orden_pago_id=orden_pago.id),
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _objetos_deportivos():
    """Snapshot of every sports object a pass settlement must NOT touch."""
    return {
        "inscripcion": Inscripcion.objects.count(),
        "compra_inscripcion": CompraInscripcion.objects.count(),
        "asignacion_cupo": AsignacionCupo.objects.count(),
        "participacion": Participacion.objects.count(),
        "inscripcion_persona": InscripcionPersona.objects.count(),
    }


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_la_aprobacion_manual_liquida_una_compra_de_pases(
    api_client, usuario_admin, compra_pase_pendiente
):
    """
    GIVEN: a pending PASS purchase with its pending payment order
    WHEN:  an administrator approves the manual payment
    THEN:  the order is PAGADA, the purchase is PAGADA and NO sports right
           exists.
    """
    orden_pago = compra_pase_pendiente.orden_pago
    antes = _objetos_deportivos()

    response = _aprobar(
        api_client,
        orden_pago,
        usuario_admin,
        monto=str(orden_pago.monto_total),
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["settlement_status"] == "SETTLED"

    orden_pago.refresh_from_db()
    compra_pase_pendiente.refresh_from_db()
    assert orden_pago.estado == OrdenPagoStatus.PAGADA
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PAGADA
    assert _objetos_deportivos() == antes
    assert AsignacionCupo.objects.count() == 0


@pytest.mark.django_db
def test_la_aprobacion_manual_de_un_pase_no_crea_una_transaccion_izipay(
    api_client, usuario_admin, compra_pase_pendiente
):
    """
    GIVEN: a pending PASS purchase
    WHEN:  an administrator approves the manual payment
    THEN:  NO provider transaction is fabricated — the manual payment did not
           go through the provider.
    """
    orden_pago = compra_pase_pendiente.orden_pago

    _aprobar(
        api_client,
        orden_pago,
        usuario_admin,
        monto=str(orden_pago.monto_total),
    )

    assert TransaccionPago.objects.filter(orden_pago_id=orden_pago.id).count() == 0
    assert (
        AprobacionPagoManual.objects.filter(
            orden_pago_id=orden_pago.id,
            estado=EstadoAprobacionPagoManual.APROBADA,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_la_aprobacion_manual_de_un_pase_es_idempotente(
    api_client, usuario_admin, compra_pase_pendiente
):
    """
    GIVEN: a PASS order already approved manually
    WHEN:  an administrator approves it AGAIN
    THEN:  200 with YA_APROBADA, ONE active approval and NO duplicated rights.
    """
    orden_pago = compra_pase_pendiente.orden_pago
    monto = str(orden_pago.monto_total)

    primero = _aprobar(api_client, orden_pago, usuario_admin, monto=monto)
    assert primero.status_code == 200, primero.content

    segundo = _aprobar(api_client, orden_pago, usuario_admin, monto=monto)
    assert segundo.status_code == 200, segundo.content
    assert segundo.json()["data"]["resultado"] == "YA_APROBADA"

    assert (
        AprobacionPagoManual.objects.filter(
            orden_pago_id=orden_pago.id,
            estado=EstadoAprobacionPagoManual.APROBADA,
        ).count()
        == 1
    )
    assert AsignacionCupo.objects.count() == 0


@pytest.mark.django_db
def test_la_aprobacion_manual_de_un_pase_con_monto_distinto_es_rechazada(
    api_client, usuario_admin, compra_pase_pendiente
):
    """
    GIVEN: a pending PASS purchase
    WHEN:  an administrator approves a DIFFERENT amount
    THEN:  it is refused — the approval must match the order exactly.
    """
    orden_pago = compra_pase_pendiente.orden_pago

    response = _aprobar(
        api_client,
        orden_pago,
        usuario_admin,
        monto="999.00",
    )

    assert response.status_code == 409, response.content
    compra_pase_pendiente.refresh_from_db()
    assert compra_pase_pendiente.estado == EstadoCompraChoices.PENDIENTE
    assert (
        AprobacionPagoManual.objects.filter(orden_pago_id=orden_pago.id).count()
        == 0
    )
