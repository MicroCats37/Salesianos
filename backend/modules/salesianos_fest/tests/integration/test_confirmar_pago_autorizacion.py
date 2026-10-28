"""
Integration tests for the CLOSURE of the public self-settlement.

`POST /api/compras/confirmar-pago` used to let the OWNER of a purchase
confirm it. That was a self-settlement surface: the buyer decided that their
own money had arrived.

It no longer exists. The commercial settlement belongs to the backend (right
after the payment is verified) or to an administrator (through the audited
manual approval of the administration area).

This file proves TWO things:

1. the route is gone — nobody, authenticated or not, can reach it, and the
   purchase stays PENDIENTE;
2. the settlement obeys the TRUTH PREDICATE: an order without a correlated
   successful provider transaction does NOT settle its purchase and grants
   NO right.
"""
import pytest
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.exceptions import PagoNoVerificadoError
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    TipoCompraChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Inscripcion,
    InscripcionPersona,
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
from modules.usuarios.domain.models.persona import Persona


# ── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def responsable(db):
    """Persona that owns the inscription (and therefore the purchase)."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def usuario_responsable(db, responsable):
    """Authenticated owner of the inscription."""
    User = get_user_model()
    return User.objects.create_user(
        username="responsable_user",
        email="responsable@example.com",
        password="testpass123",
        persona_fk=responsable,
    )


@pytest.fixture
def inscripcion_base(db, evento, paquete_reencuentro, promocion_junior, responsable):
    """Inscription owned by the responsable."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=responsable,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def compra_pendiente(db, inscripcion_base, responsable):
    """A PENDIENTE purchase funded by a PENDIENTE payment order."""
    total = Decimal("50.00")

    orden_pago = OrdenPago.objects.create(
        numero="OP-AUTH-001",
        monto_total=total,
        estado=OrdenPagoStatus.PENDIENTE,
    )
    compra = Compra.objects.create(
        responsable=responsable,
        descripcion="Compra FEST #1",
        referencia_externa="AUTH-REF-1",
        total=total,
        estado=EstadoCompraChoices.PENDIENTE,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=total,
        total=total,
    )
    return compra


@pytest.fixture
def participante_preregistrado(db, inscripcion_base, responsable):
    """The owner is preregistered in the pool.

    A successful settlement WOULD allocate a cupo to this participant, so a
    refused settlement that leaves no cupo proves it never ran.
    """
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=responsable,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


@pytest.fixture
def flujo_confirmacion(db):
    """The internal settlement flow, wired with the truth predicate."""
    return ConfirmarPagoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
        evidencia_pago=EvidenciaPagoService(),
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _auth_post(client, path, user):
    """POST with the caller's JWT."""
    token = AccessToken.for_user(user)
    return client.post(path, HTTP_AUTHORIZATION=f"Bearer {token}")


def _cupos_activos(inscripcion_id):
    return AsignacionCupo.objects.filter(
        inscripcion_id=inscripcion_id,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).count()


# ── Tests: the public self-settlement route no longer exists ──────────────────

@pytest.mark.django_db
def test_la_ruta_de_confirmar_pago_no_existe(
    api_client, usuario_responsable, inscripcion_base, compra_pendiente
):
    """
    GIVEN: the authenticated owner of a pending purchase
    WHEN:  POST /api/compras/confirmar-pago with the order of the purchase
    THEN:  405 — the route no longer accepts a settlement and the purchase
            stays PENDIENTE.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}",
        usuario_responsable,
    )

    assert response.status_code == 405, response.content

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_la_ruta_de_confirmar_pago_no_existe_sin_autenticacion(
    api_client, inscripcion_base, compra_pendiente
):
    """
    GIVEN: an anonymous caller
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  405 — the route does not accept the settlement, not even as 401.
    """
    response = api_client.post(
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}"
    )

    assert response.status_code == 405, response.content

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_la_autoliquidacion_no_concede_derechos(
    api_client, usuario_responsable, inscripcion_base, compra_pendiente,
    participante_preregistrado,
):
    """
    GIVEN: the owner of a pending purchase with a preregistered participant
    WHEN:  the owner tries to self-settle the purchase
    THEN:  no cupo is allocated and the order stays PENDIENTE.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}",
        usuario_responsable,
    )

    assert response.status_code == 405, response.content
    assert _cupos_activos(inscripcion_base.id) == 0

    orden = OrdenPago.objects.get(id=compra_pendiente.orden_pago_id)
    assert orden.estado == OrdenPagoStatus.PENDIENTE


# ── Tests: the truth predicate ────────────────────────────────────────────────

@pytest.mark.django_db
def test_una_orden_sin_transaccion_exitosa_no_liquida(
    flujo_confirmacion, compra_pendiente, inscripcion_base,
    participante_preregistrado,
):
    """
    GIVEN: a pending purchase whose order has NO successful transaction
    WHEN:  the internal settlement flow is driven for that order
    THEN:  it is refused with PAGO_NO_VERIFICADO and no right is granted.
    """
    with pytest.raises(PagoNoVerificadoError):
        async_to_sync(flujo_confirmacion._confirmar_compra)(
            str(compra_pendiente.orden_pago_id)
        )

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE
    assert _cupos_activos(inscripcion_base.id) == 0


@pytest.mark.django_db
def test_una_orden_con_transaccion_exitosa_correlacionada_liquida(
    flujo_confirmacion, compra_pendiente, inscripcion_base,
    participante_preregistrado,
):
    """
    GIVEN: a pending purchase whose order has a CORRELATED successful attempt
    WHEN:  the internal settlement flow is driven for that order
    THEN:  the purchase is paid and the right is allocated.
    """
    TransaccionPago.objects.create(
        orden_pago_id=compra_pendiente.orden_pago_id,
        transaction_id="AUTHTX001",
        order_number="AUTHTN001",
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )

    async_to_sync(flujo_confirmacion._confirmar_compra)(
        str(compra_pendiente.orden_pago_id)
    )

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA
    assert _cupos_activos(inscripcion_base.id) == 1


@pytest.mark.django_db
def test_una_transaccion_exitosa_no_correlacionada_no_liquida(
    flujo_confirmacion, compra_pendiente, inscripcion_base,
    participante_preregistrado,
):
    """
    GIVEN: a pending purchase whose order has a successful attempt of ANOTHER
           amount
    WHEN:  the internal settlement flow is driven for that order
    THEN:  it is refused — a purchase is never paid for an amount the order
           does not carry.
    """
    TransaccionPago.objects.create(
        orden_pago_id=compra_pendiente.orden_pago_id,
        transaction_id="AUTHTX002",
        order_number="AUTHTN002",
        amount=Decimal("500.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )

    with pytest.raises(PagoNoVerificadoError):
        async_to_sync(flujo_confirmacion._confirmar_compra)(
            str(compra_pendiente.orden_pago_id)
        )

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE
    assert _cupos_activos(inscripcion_base.id) == 0
