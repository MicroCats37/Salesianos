"""
Integration tests for AcreditacionEvento and ControlAcceso (Phase 5).

Covers:
- Acreditacion sync from paid compras with FIESTA benefit
- Admin override for fiesta
- QR scan single-use per event day
"""
import uuid
import json

import pytest
from decimal import Decimal
from datetime import date

from django.test import Client
from ninja_jwt.tokens import AccessToken
from django.contrib.auth import get_user_model

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    PaqueteBeneficio,
    Inscripcion,
    InscripcionPersona,
    CompraInscripcion,
    AsignacionCupo,
    AcreditacionEvento,
    ControlAcceso,
)
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    EstadoInscripcionChoices,
    TipoCompraChoices,
    EstadoCompraChoices,
    EstadoAsignacionCupoChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
    AutorizacionFiestaChoices,
    ResultadoAccesoChoices,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    """Django test client for async controllers."""
    return Client()


@pytest.fixture
def evento(db):
    """Create a test evento."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_futbol(db):
    """Create a test disciplina."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def promocion_junior(db):
    """Create a test promocion."""
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def categoria_senior(db, evento, promocion_junior):
    """Create a test categoria."""
    return Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2011,
        esta_activa=True,
    )


@pytest.fixture
def paquete_fiesta(db, evento, disciplina_futbol):
    """Create a test paquete with FIESTA benefit."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    PaqueteBeneficio.objects.create(
        paquete=paquete,
        tipo=TipoBeneficioChoices.FIESTA,
        cantidad=1,
        alcance=AlcanceBeneficioChoices.INDIVIDUAL,
        modo_calculo=ModoCalculoBeneficioChoices.FIJO_INICIAL,
    )
    return paquete


@pytest.fixture
def paquete_sin_fiesta(db, evento, disciplina_futbol):
    """Create a test paquete WITHOUT FIESTA benefit (DISCIPLINA only)."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Fútbol Solo",
        descripcion="Torneo sin fiesta",
        tipo=TipoPaqueteChoices.DISCIPLINA,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=7,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("40.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    return paquete


@pytest.fixture
def persona(db):
    """Create a test persona (owner)."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def persona_2(db):
    """Create a second test persona."""
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="F",
    )


@pytest.fixture
def usuario_con_persona(db, persona):
    """Create a user linked to a persona (owner)."""
    User = get_user_model()
    return User.objects.create_user(
        username="juan_user",
        email="juan@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def usuario_2(db, persona_2):
    """Create another user."""
    User = get_user_model()
    return User.objects.create_user(
        username="maria_user",
        email="maria@example.com",
        password="testpass123",
        persona_fk=persona_2,
    )


@pytest.fixture
def admin_user(db, persona):
    """Create an admin user."""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        persona_fk=persona,
    )


@pytest.fixture
def inscripcion_fiesta(db, evento, persona, paquete_fiesta, promocion_junior):
    """Create an inscripcion with FIESTA package."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_fiesta,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth_post(client, path, user, data=None, content_type="application/json"):
    """Helper to make an authenticated POST request."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=data,
        content_type=content_type,
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


def _auth_get(client, path, user):
    """Helper to make an authenticated GET request."""
    token = AccessToken.for_user(user)
    return client.get(path, HTTP_AUTHORIZATION=f"Bearer {token}")


def _admin_post(client, path, user, data=None, content_type="application/json"):
    """Helper to make an authenticated admin POST request."""
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=data,
        content_type=content_type,
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


# ── Tests: Acreditacion sync from pago ───────────────────────────────────────

@pytest.mark.django_db
def test_acreditacion_sync_con_fiesta(
    api_client, usuario_con_persona, inscripcion_fiesta, persona_2
):
    """
    GIVEN: Compra PAGADA with FIESTA benefit, InscripcionPersona active
    WHEN:  sync_acreditacion_desde_compras is called
    THEN:  acceso_fiesta = True and estado = ACTIVA.
    """
    # Create InscripcionPersona
    inscripcion_persona = InscripcionPersona.objects.create(
        inscripcion=inscripcion_fiesta,
        persona=persona_2,
        estado="A",
    )

    # Create the generic commerce.Compra (PAGADA)
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus

    compra = Compra.objects.create(
        responsable=inscripcion_fiesta.responsable,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-ACRED",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-010",
        monto_total=Decimal("500.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="00000000000010",
        order_number="0000000010",
        amount=Decimal("500.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    # Link OrdenPago to the generic Compra
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    # Create CompraInscripcion (FEST composition)
    from modules.salesianos_fest.domain.models import CompraInscripcion
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_fiesta,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # Create AsignacionCupo
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_fiesta,
        compra=compra,
        inscripcion_persona=inscripcion_persona,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    # Sync acreditacion
    from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
    acreditacion_core = AcreditacionCoreService()
    acreditacion = acreditacion_core.sync_acreditacion_desde_compras(
        str(inscripcion_fiesta.evento_id), str(persona_2.id)
    )

    assert acreditacion.acceso_fiesta is True
    assert acreditacion.estado == "ACTIVA"


# ── Tests: Admin override fiesta ─────────────────────────────────────────────

@pytest.mark.django_db
def test_override_fiesta_bloquear(
    api_client, admin_user, evento, persona_2
):
    """
    GIVEN: Admin wants to block fiesta access
    WHEN:  PATCH /api/acreditaciones/{evento_id}/{persona_id}/override-fiesta
    THEN:  200 with autorizacion_fiesta = BLOQUEADA and acceso_fiesta = False.
    """
    # Create acreditacion first
    AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_2,
        estado="ACTIVA",
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
    )

    payload = {
        "autorizacion": "BLOQUEADA",
        "motivo": "Usuario suspendido por comite",
    }
    token = AccessToken.for_user(admin_user)
    response = api_client.patch(
        f"/api/acreditaciones/{evento.id}/{persona_2.id}/override-fiesta",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["autorizacion_fiesta"] == "BLOQUEADA"
    assert data["data"]["acceso_fiesta"] is False


# ── Tests: QR scan single-use ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_qr_scan_primer_intento_permitido(
    api_client, usuario_con_persona, evento, persona_2
):
    """
    GIVEN: Valid QR for acreditacion with acceso_fiesta=True
    WHEN:  POST /api/acceso/registrar
    THEN:  200 with resultado = PERMITIDO.
    """
    # Create acreditacion with acceso_fiesta=True
    acreditacion = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_2,
        estado="ACTIVA",
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
    )

    payload = {
        "qr_token": str(acreditacion.codigo_qr),
    }
    response = _auth_post(
        api_client,
        "/api/acceso/registrar",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["resultado"] == "PERMITIDO"


@pytest.mark.django_db
def test_qr_scan_segundo_intento_denegado(
    api_client, usuario_con_persona, evento, persona_2
):
    """
    GIVEN: QR already scanned PERMITIDO today
    WHEN:  POST /api/acceso/registrar again
    THEN:  200 with resultado = DENEGADO (single-use per day).
    """
    # Create acreditacion with acceso_fiesta=True
    acreditacion = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_2,
        estado="ACTIVA",
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
    )

    # First scan - PERMITIDO
    ControlAcceso.objects.create(
        acreditacion=acreditacion,
        resultado=ResultadoAccesoChoices.PERMITIDO,
        punto_acceso="ENTRADA_PRINCIPAL",
    )

    payload = {
        "qr_token": str(acreditacion.codigo_qr),
    }
    response = _auth_post(
        api_client,
        "/api/acceso/registrar",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["resultado"] == "DENEGADO"
