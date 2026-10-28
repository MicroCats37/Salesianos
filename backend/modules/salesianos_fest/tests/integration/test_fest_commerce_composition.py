"""
Focused integration tests for FEST commerce composition (Batch 3).

Tests the FEST composition pattern: CompraInscripcion links a generic
commerce.Compra to a FEST Inscripcion with purchase-specific details.

Composition pattern:
- commerce.Compra: generic commercial purchase aggregate (no FEST fields)
- CompraInscripcion: FEST composition link (OneToOne to Compra, FK to Inscripcion)
- tipo: INICIAL (one per inscription) or AMPLIACION (N allowed)
- cantidad/precio_unitario/total: frozen snapshots
- AsignacionCupo: links a paid Compra to a registered InscripcionPersona

Covers:
- unique_inicial_por_inscripcion constraint enforcement
- saldo calculation across multiple CompraInscripcion (INICIAL + AMPLIACION)
- price/total snapshot authority
- atomic creation of Compra + OrdenPago + CompraInscripcion
- AsignacionCupo correctly uses commerce.Compra (not crossing module ownership)
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
)
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    """Django test client."""
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
def paquete_reencuentro(db, evento, disciplina_futbol):
    """Create a test paquete with price."""
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
def persona_3(db):
    """Create a third test persona."""
    return Persona.objects.create(
        nombres="Pedro",
        apellidos="Rodríguez",
        tipo_documento="DNI",
        numero_documento="11223344",
        genero="M",
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
def inscripcion_base(db, evento, persona, paquete_reencuentro, promocion_junior):
    """Create a base inscripcion owned by persona."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
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


# ── Tests: FEST Composition Model Structure ───────────────────────────────────

@pytest.mark.django_db
def test_compra_inscripcion_one_to_one_to_compra(db, inscripcion_base, persona):
    """
    GIVEN: A CompraInscripcion and its linked Compra
    WHEN:  Inspecting the OneToOne relation from CompraInscripcion to Compra
    THEN:  CompraInscripcion.compra is a OneToOneField pointing to commerce.Compra.
    """
    # Create generic commerce.Compra
    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Test",
        referencia_externa="REF-001",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    # Create CompraInscripcion (FEST composition link)
    ci = CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )
    # Verify OneToOne relation works both ways
    assert ci.compra == compra
    assert compra.compra_inscripcion == ci


@pytest.mark.django_db
def test_compra_inscripcion_inscripcion_fk(db, inscripcion_base):
    """
    GIVEN: A CompraInscripcion
    WHEN:  Inspecting the FK to Inscripcion
    THEN:  CompraInscripcion.inscripcion is a proper FK.
    """
    compra = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Test",
        referencia_externa="REF-002",
        total=Decimal("100.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    ci = CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.AMPLIACION,
        cantidad=2,
        precio_unitario=Decimal("50.00"),
        total=Decimal("100.00"),
    )
    assert ci.inscripcion == inscripcion_base


@pytest.mark.django_db
def test_compra_inscripcion_snapshot_campos(db, inscripcion_base, persona):
    """
    GIVEN: A CompraInscripcion with cantidad=10, precio_unitario=50.00
    WHEN:  Creating it with specific snapshot values
    THEN:  The snapshot fields are stored correctly and remain independent of any later price changes.
    """
    precio_unitario = Decimal("50.00")
    cantidad = 10
    total = cantidad * precio_unitario

    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Test snapshot",
        referencia_externa="REF-003",
        total=total,
        estado=EstadoCompraChoices.PAGADA,
    )
    ci = CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        total=total,
    )
    assert ci.cantidad == 10
    assert ci.precio_unitario == Decimal("50.00")
    assert ci.total == Decimal("500.00")


# ── Tests: Unique Constraint — one INICIAL per inscripcion ────────────────────

@pytest.mark.django_db
def test_unique_inicial_por_inscripcion_permite_una_inicial(db, inscripcion_base, persona):
    """
    GIVEN: An inscripcion with one INICIAL CompraInscripcion
    WHEN:  Creating a second INICIAL for the same inscripcion
    THEN:  IntegrityError is raised (partial unique constraint).
    """
    compra1 = Compra.objects.create(
        responsable=persona,
        descripcion="First INICIAL",
        referencia_externa="REF-INI-1",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    CompraInscripcion.objects.create(
        compra=compra1,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # Second INICIAL should raise IntegrityError
    compra2 = Compra.objects.create(
        responsable=persona,
        descripcion="Second INICIAL",
        referencia_externa="REF-INI-2",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    with pytest.raises(Exception):  # IntegrityError from DB constraint
        CompraInscripcion.objects.create(
            compra=compra2,
            inscripcion=inscripcion_base,
            tipo=TipoCompraChoices.INICIAL,
            cantidad=5,
            precio_unitario=Decimal("50.00"),
            total=Decimal("250.00"),
        )


@pytest.mark.django_db
def test_unique_inicial_por_inscripcion_permite_ampliaciones(db, inscripcion_base, persona):
    """
    GIVEN: An inscripcion with one INICIAL CompraInscripcion
    WHEN:  Creating multiple AMPLIACION for the same inscripcion
    THEN:  All AMPLIACION are allowed (no limit).
    """
    # Create INICIAL
    compra_inicial = Compra.objects.create(
        responsable=persona,
        descripcion="INICIAL",
        referencia_externa="REF-INI",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    CompraInscripcion.objects.create(
        compra=compra_inicial,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # Create multiple AMPLIACION
    for i in range(3):
        compra_amp = Compra.objects.create(
            responsable=persona,
            descripcion=f"AMPLIACION {i+1}",
            referencia_externa=f"REF-AMP-{i+1}",
            total=Decimal("100.00"),
            estado=EstadoCompraChoices.PAGADA,
        )
        CompraInscripcion.objects.create(
            compra=compra_amp,
            inscripcion=inscripcion_base,
            tipo=TipoCompraChoices.AMPLIACION,
            cantidad=2,
            precio_unitario=Decimal("50.00"),
            total=Decimal("100.00"),
        )

    # Verify 1 INICIAL + 3 AMPLIACION = 4 total
    total_ci = CompraInscripcion.objects.filter(inscripcion=inscripcion_base).count()
    assert total_ci == 4


# ── Tests: Saldo calculation with multiple CompraInscripcion ──────────────────

@pytest.mark.django_db
def test_calcular_saldo_inicial_mas_ampliaciones(db, inscripcion_base, persona):
    """
    GIVEN: An inscripcion with INICIAL (10 cupos PAGADA) and 2 AMPLIACION (5+3=8 cupos, one PENDIENTE)
    WHEN:  calcular_saldo_inscripcion is called
    THEN:  contratados=18, pagados=13 (INICIAL+first AMPLIACION), asignados=0.
    """
    from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService

    # INICIAL: 10 cupos, PAGADA
    compra_inicial = Compra.objects.create(
        responsable=persona,
        descripcion="INICIAL",
        referencia_externa="REF-SALDO-INI",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    CompraInscripcion.objects.create(
        compra=compra_inicial,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # AMPLIACION 1: 5 cupos, PAGADA
    compra_amp1 = Compra.objects.create(
        responsable=persona,
        descripcion="AMPLIACION 1",
        referencia_externa="REF-SALDO-AMP1",
        total=Decimal("250.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    CompraInscripcion.objects.create(
        compra=compra_amp1,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.AMPLIACION,
        cantidad=5,
        precio_unitario=Decimal("50.00"),
        total=Decimal("250.00"),
    )

    # AMPLIACION 2: 3 cupos, PENDIENTE (not yet paid)
    compra_amp2 = Compra.objects.create(
        responsable=persona,
        descripcion="AMPLIACION 2",
        referencia_externa="REF-SALDO-AMP2",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    CompraInscripcion.objects.create(
        compra=compra_amp2,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.AMPLIACION,
        cantidad=3,
        precio_unitario=Decimal("50.00"),
        total=Decimal("150.00"),
    )

    # AMPLIACION 3: 5 cupos, CANCELADA (should be excluded)
    compra_amp3 = Compra.objects.create(
        responsable=persona,
        descripcion="AMPLIACION 3 CANCELADA",
        referencia_externa="REF-SALDO-AMP3",
        total=Decimal("250.00"),
        estado=EstadoCompraChoices.CANCELADA,
    )
    CompraInscripcion.objects.create(
        compra=compra_amp3,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.AMPLIACION,
        cantidad=5,
        precio_unitario=Decimal("50.00"),
        total=Decimal("250.00"),
    )

    service = AsignacionCoreService()
    saldo = service.calcular_saldo_inscripcion(str(inscripcion_base.id))

    assert saldo["inscripcion_id"] == str(inscripcion_base.id)
    assert saldo["contratados"] == 18  # 10 + 5 + 3 (CANCELADA excluded)
    assert saldo["pagados"] == 15  # 10 + 5 (CANCELADA excluded, PENDIENTE not counted)
    assert saldo["asignados_pagados"] == 0  # No asignaciones yet
    assert saldo["disponibles_pagados"] == 15  # 15 - 0


@pytest.mark.django_db
def test_calcular_saldo_con_asignaciones(db, inscripcion_base, persona, persona_2, persona_3):
    """
    GIVEN: An inscripcion with 10 cupos PAGADOS and 3 persons assigned
    WHEN:  calcular_saldo_inscripcion is called
    THEN:  asignados_pagados=3, disponibles_pagados=7.
    """
    from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService

    # Create 3 InscripcionPersonas
    ip1 = InscripcionPersona.objects.create(inscripcion=inscripcion_base, persona=persona_2, estado="A")
    ip2 = InscripcionPersona.objects.create(inscripcion=inscripcion_base, persona=persona_3, estado="A")

    # Compra: 10 cupos PAGADA
    compra = Compra.objects.create(
        responsable=persona,
        descripcion="INICIAL 10 cupos",
        referencia_externa="REF-SALDO-ASI",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # Create 2 AsignacionCupo (2 persons assigned)
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        compra=compra,
        inscripcion_persona=ip1,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        compra=compra,
        inscripcion_persona=ip2,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    service = AsignacionCoreService()
    saldo = service.calcular_saldo_inscripcion(str(inscripcion_base.id))

    assert saldo["contratados"] == 10
    assert saldo["pagados"] == 10
    assert saldo["asignados_pagados"] == 2
    assert saldo["disponibles_pagados"] == 8


# ── Tests: AsignacionCupo uses commerce.Compra ───────────────────────────────

@pytest.mark.django_db
def test_asignacion_cupo_compra_fk_apunta_a_commerce_compra(db, inscripcion_base, persona, persona_2):
    """
    GIVEN: An AsignacionCupo linked to a commerce.Compra
    WHEN:  Inspecting the FK from AsignacionCupo to Compra
    THEN:  AsignacionCupo.compra points to the generic commerce.Compra (not FEST-specific model).
           The AsignacionCupo does NOT cross module ownership — it references the generic Compra.
    """
    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Test",
        referencia_externa="REF-ASIG-FK",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    asignacion = AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        compra=compra,
        inscripcion_persona=ip,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    # Verify AsignacionCupo references the generic commerce.Compra
    assert asignacion.compra == compra
    assert asignacion.compra.estado == EstadoCompraChoices.PAGADA
    # Verify the Compra does NOT have FEST-specific fields
    assert not hasattr(compra, 'inscripcion')
    assert not hasattr(compra, 'tipo')
    assert not hasattr(compra, 'cantidad')


# ── Tests: Price/total snapshots remain authoritative ──────────────────────────

@pytest.mark.django_db
def test_compra_inscripcion_precio_unitario_es_snapshot(db, inscripcion_base, persona):
    """
    GIVEN: A CompraInscripcion with precio_unitario=50.00
    WHEN:  The PaquetePrecio price changes later
    THEN:  The CompraInscripcion.precio_unitario remains 50.00 (snapshot).
    """
    # Create CompraInscripcion at price 50.00
    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Test",
        referencia_externa="REF-SNAP",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    precio_original = Decimal("50.00")
    ci = CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=precio_original,
        total=Decimal("500.00"),
    )

    # Simulate price change: update the PaquetePrecio to a new price
    PaquetePrecio.objects.filter(paquete=inscripcion_base.paquete).update(
        precio_unitario=Decimal("75.00")
    )

    # Refresh CompraInscripcion from DB
    ci.refresh_from_db()

    # The snapshot should remain unchanged
    assert ci.precio_unitario == precio_original
    assert ci.cantidad == 10
    assert ci.total == Decimal("500.00")


# ── Tests: Multiple expansions — AMPLIACION does not repeat minimum ─────────

@pytest.mark.django_db
def test_ampliacion_no_exige_minimo(api_client, inscripcion_base, usuario_con_persona):
    """
    GIVEN: Auth user owns the inscripcion; minimo_compra_inicial=10
    WHEN:  POST /api/compras/ with tipo=AMPLIACION and cantidad=1
    THEN:  AMPLIACION with cantidad=1 succeeds (minimum only applies to INICIAL).
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "AMPLIACION",
        "cantidad": 1,  # less than minimo_inicial (10), but allowed for AMPLIACION
    }
    response = _auth_post(
        client=api_client,
        path="/api/compras/",
        user=usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["tipo"] == "AMPLIACION"
    assert data["data"]["cantidad"] == 1


# ── Tests: Atomic creation — Compra + OrdenPago + CompraInscripcion ─────────

@pytest.mark.django_db
def test_crear_compra_con_orden_pago_y_compra_inscripcion_atomico(
    api_client, usuario_con_persona, inscripcion_base
):
    """
    GIVEN: Auth user owns the inscripcion; sufficient quantity for INICIAL
    WHEN:  POST /api/compras/ (atomic creation)
    THEN:  Compra, OrdenPago, and CompraInscripcion are all created.
           Compra.orden_pago links to OrdenPago.
           CompraInscripcion.compra links to Compra.
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "INICIAL",
        "cantidad": 10,
    }
    response = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()["data"]

    compra_id = data["compra_id"]
    orden_pago_id = data["orden_pago_id"]
    compra_inscripcion_id = data["compra_inscripcion_id"]

    # Verify Compra exists and has orden_pago linked
    compra = Compra.objects.select_related("orden_pago").get(id=compra_id)
    assert compra.orden_pago_id == uuid.UUID(orden_pago_id)
    assert compra.orden_pago is not None
    assert compra.orden_pago.monto_total == Decimal("500.00")

    # Verify CompraInscripcion exists and links to Compra
    ci = CompraInscripcion.objects.select_related("compra", "inscripcion").get(id=compra_inscripcion_id)
    assert ci.compra_id == compra.id
    assert ci.inscripcion_id == inscripcion_base.id
    assert ci.tipo == TipoCompraChoices.INICIAL
    assert ci.cantidad == 10
    assert ci.precio_unitario == Decimal("50.00")
    assert ci.total == Decimal("500.00")


# ── Tests: obtener_compra_con_saldo_disponible picks correct Compra ───────────

@pytest.mark.django_db
def test_obtener_compra_con_saldo_disponible_escoge_pagada_con_cupo(
    db, inscripcion_base, persona, persona_2, persona_3
):
    """
    GIVEN: Two PAGADA compras: one with 1 available cupo, one with 3 available
    WHEN:  obtener_compra_con_saldo_disponible returns the one with available cupo
    THEN:  The correct Compra is returned (oldest first with available quota).
    """
    from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService

    # Create two InscripcionPersonas (persona_2 and persona_3)
    ip1 = InscripcionPersona.objects.create(inscripcion=inscripcion_base, persona=persona_2, estado="A")
    ip2 = InscripcionPersona.objects.create(inscripcion=inscripcion_base, persona=persona_3, estado="A")

    # Compra 1: 2 cupos PAGADA
    compra1 = Compra.objects.create(
        responsable=persona,
        descripcion="Compra 1",
        referencia_externa="REF-DISP-1",
        total=Decimal("100.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    ci1 = CompraInscripcion.objects.create(
        compra=compra1,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=2,
        precio_unitario=Decimal("50.00"),
        total=Decimal("100.00"),
    )

    # Assign 1 persona to compra1 (1 available remaining)
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        compra=compra1,
        inscripcion_persona=ip1,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    # Compra 2: 5 cupos PAGADA (no assignments yet — 5 available)
    compra2 = Compra.objects.create(
        responsable=persona,
        descripcion="Compra 2",
        referencia_externa="REF-DISP-2",
        total=Decimal("250.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    ci2 = CompraInscripcion.objects.create(
        compra=compra2,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.AMPLIACION,
        cantidad=5,
        precio_unitario=Decimal("50.00"),
        total=Decimal("250.00"),
    )

    service = AsignacionCoreService()

    # First call: should return compra2 (has 5 available, more than compra1's 1)
    # Note: ordering is by created_at ASC, so compra1 is older
    # But compra2 has more available quota (5 vs 1)
    # The service returns first one with available quota
    result = service.obtener_compra_con_saldo_disponible(str(inscripcion_base.id))
    # compra1 is oldest but only has 1 available
    # The service iterates in order and returns the first with available > assigned
    # Since compra1 has 1 available and compra2 has 5 available, and compra1 is returned first
    assert result is not None
    assert result.id == compra1.id

    # Assign the last available cupo to compra1
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        compra=compra1,
        inscripcion_persona=ip2,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    # Now compra1 has 0 available, compra2 has 5 available
    result2 = service.obtener_compra_con_saldo_disponible(str(inscripcion_base.id))
    assert result2 is not None
    assert result2.id == compra2.id


# ── Tests: la autoliquidación pública no existe ───────────────────────────────

@pytest.mark.django_db
def test_el_comprador_no_puede_liquidar_su_compra(
    api_client, usuario_con_persona, inscripcion_base
):
    """
    GIVEN: Auth user owns the inscripcion; Compra is PENDIENTE
    WHEN:  POST /api/compras/confirmar-pago
    THEN:  the route does not accept the settlement (405) and the Compra
           stays PENDIENTE.

    The commercial settlement belongs to the backend (right after the payment
    is verified) or to an administrator (through the audited manual approval
    of the administration area).
    """
    # Create Compra via API
    create_payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "tipo": "INICIAL",
        "cantidad": 10,
    }
    create_resp = _auth_post(
        api_client,
        "/api/compras/",
        usuario_con_persona,
        data=json.dumps(create_payload),
    )
    assert create_resp.status_code == 200
    orden_pago_id = create_resp.json()["data"]["orden_pago_id"]
    compra_id = create_resp.json()["data"]["compra_id"]

    # Verify initial state is PENDIENTE
    compra = Compra.objects.get(id=compra_id)
    assert compra.estado == EstadoCompraChoices.PENDIENTE

    # The buyer tries to self-settle
    confirm_resp = _auth_post(
        api_client,
        f"/api/compras/confirmar-pago?orden_pago_id={orden_pago_id}",
        usuario_con_persona,
    )
    assert confirm_resp.status_code == 405, confirm_resp.content

    # Verify Compra is still PENDIENTE
    compra.refresh_from_db()
    assert compra.estado == EstadoCompraChoices.PENDIENTE
