"""
Integration tests for the authorization of the manual commercial recovery.

`POST /api/compras/confirmar-pago` is NOT part of the normal checkout: the
backend settles the purchase right after the payment is verified. The
endpoint only exists to recover a purchase whose commercial settlement did
not complete, so it is restricted to the owner of the purchase — the
responsible of the linked inscription — or a Django administrator.

A caller without that authority gets 403 and changes nothing: not the
Compra, not the payment order, not the cup rights.
"""
import pytest
from decimal import Decimal

from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago
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
def tercero(db):
    """Persona that does NOT own the inscription."""
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="F",
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
def usuario_tercero(db, tercero):
    """Authenticated caller that does not own the inscription."""
    User = get_user_model()
    return User.objects.create_user(
        username="tercero_user",
        email="tercero@example.com",
        password="testpass123",
        persona_fk=tercero,
    )


@pytest.fixture
def usuario_admin(db, tercero):
    """Django admin (is_staff) that does not own the inscription."""
    User = get_user_model()
    return User.objects.create_user(
        username="admin_user",
        email="admin@example.com",
        password="testpass123",
        persona_fk=tercero,
        is_staff=True,
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
    denied request that leaves no cupo proves the settlement never ran.
    """
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=responsable,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
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


# ── Tests: the owner of the purchase may recover it ───────────────────────────

@pytest.mark.django_db
def test_confirmar_pago_por_responsable_es_permitido(
    api_client, usuario_responsable, inscripcion_base, compra_pendiente
):
    """
    GIVEN: the authenticated caller is the responsible of the inscription
    WHEN:  POST /api/compras/confirmar-pago with the order of the purchase
    THEN:  200 returned, the Compra is PAGADA and the cupo is allocated.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}",
        usuario_responsable,
    )

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["success"] is True
    assert body["data"]["success"] is True
    assert body["data"]["already_confirmed"] is False

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA


@pytest.mark.django_db
def test_confirmar_pago_por_responsable_asigna_los_cupos(
    api_client, usuario_responsable, inscripcion_base, compra_pendiente,
    participante_preregistrado,
):
    """
    GIVEN: the owner of the purchase with a preregistered participant
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  the paid capacity becomes an active cupo.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}",
        usuario_responsable,
    )

    assert response.status_code == 200, response.content
    assert _cupos_activos(inscripcion_base.id) == 1


# ── Tests: a foreign caller is refused and changes nothing ─────────────────────

@pytest.mark.django_db
def test_confirmar_pago_por_usuario_ajeno_es_rechazado(
    api_client, usuario_tercero, inscripcion_base, compra_pendiente
):
    """
    GIVEN: an authenticated caller that does NOT own the purchase
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  403 returned and the public error exposes no internal identifier.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}",
        usuario_tercero,
    )

    assert response.status_code == 403, response.content
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "COMPRA_NO_AUTORIZADA"
    # The public message never interpolates internal identifiers.
    assert str(compra_pendiente.id) not in response.content.decode()
    assert str(compra_pendiente.orden_pago_id) not in response.content.decode()


@pytest.mark.django_db
def test_confirmar_pago_por_usuario_ajeno_no_modifica_compra_orden_ni_cupos(
    api_client, usuario_tercero, inscripcion_base, compra_pendiente,
    participante_preregistrado,
):
    """
    GIVEN: an authenticated caller that does NOT own the purchase
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  the Compra stays PENDIENTE, the order stays PENDIENTE and no cupo
           is allocated.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}",
        usuario_tercero,
    )

    assert response.status_code == 403, response.content

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE

    orden_pago = OrdenPago.objects.get(id=compra_pendiente.orden_pago_id)
    assert orden_pago.estado == OrdenPagoStatus.PENDIENTE

    assert _cupos_activos(inscripcion_base.id) == 0


# ── Tests: a Django admin may recover any purchase ────────────────────────────

@pytest.mark.django_db
def test_confirmar_pago_por_administrador_es_permitido(
    api_client, usuario_admin, inscripcion_base, compra_pendiente
):
    """
    GIVEN: a Django admin (is_staff) that does not own the purchase
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  200 returned and the Compra is PAGADA.
    """
    response = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}",
        usuario_admin,
    )

    assert response.status_code == 200, response.content
    assert response.json()["data"]["success"] is True

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PAGADA


# ── Tests: contractual validation of the query parameter ───────────────────────

@pytest.mark.django_db
def test_confirmar_pago_con_orden_pago_invalida_es_rechazado(
    api_client, usuario_responsable, inscripcion_base
):
    """
    GIVEN: a malformed orden_pago_id
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  422 returned — the input never reaches the domain.
    """
    response = _auth_post(
        api_client,
        "/api/compras/confirmar-pago?orden_pago_id=no-es-un-uuid",
        usuario_responsable,
    )

    assert response.status_code == 422, response.content


@pytest.mark.django_db
def test_confirmar_pago_sin_orden_pago_es_rechazado(
    api_client, usuario_responsable, inscripcion_base
):
    """
    GIVEN: a request without the mandatory orden_pago_id
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  422 returned — the parameter is required by the contract.
    """
    response = _auth_post(
        api_client,
        "/api/compras/confirmar-pago",
        usuario_responsable,
    )

    assert response.status_code == 422, response.content


@pytest.mark.django_db
def test_confirmar_pago_sin_autenticacion_es_rechazado(
    api_client, inscripcion_base, compra_pendiente
):
    """
    GIVEN: an anonymous caller
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  the request is refused and the purchase stays PENDIENTE.
    """
    response = api_client.post(
        f"/api/compras/confirmar-pago?orden_pago_id={compra_pendiente.orden_pago_id}"
    )

    assert response.status_code == 401, response.content

    compra_pendiente.refresh_from_db()
    assert compra_pendiente.estado == EstadoCompraChoices.PENDIENTE
