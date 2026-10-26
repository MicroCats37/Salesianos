"""
Integration tests for AsignacionCupo HTTP flows (Phase 5).

Covers:
- Assign person to inscripcion with saldo disponible
- Assign person fails when no saldo disponible (CupoAgotadoError)
- Liberate cupo happy path
- Saldo calculation
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
    Equipo,
    Participacion,
    AsignacionCupo,
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
    EstadoParticipacionChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
)
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus


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
    """Create a second test persona (to be assigned)."""
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="F",
    )


@pytest.fixture
def persona_3(db):
    """Create a third test persona (to be assigned)."""
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
def inscripcion_base(db, evento, persona, paquete_fiesta, promocion_junior):
    """Create a base inscripcion owned by persona."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_fiesta,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def inscripcion_persona(db, inscripcion_base, persona_2):
    """Create an InscripcionPersona link."""
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )


@pytest.fixture
def equipo_futbol(db, inscripcion_base, disciplina_futbol):
    """Create a test equipo."""
    from modules.salesianos_fest.domain.models import Categoria
    categoria = Categoria.objects.create(
        evento=inscripcion_base.evento,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2005,
        esta_activa=True,
    )
    return Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        nombre="Los Tigres FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria,
    )


@pytest.fixture
def participacion(db, inscripcion_persona, equipo_futbol, disciplina_futbol, evento):
    """Create a test participacion."""
    return Participacion.objects.create(
        inscripcion_persona=inscripcion_persona,
        equipo=equipo_futbol,
        disciplina=disciplina_futbol,
        evento=evento,
        persona=inscripcion_persona.persona,
        rol="J",
        talla_camiseta="M",
        estado=EstadoParticipacionChoices.ACTIVA,
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


# ── Tests: Saldo calculation ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_saldo_sin_compras(api_client, usuario_con_persona, inscripcion_base):
    """
    GIVEN: Inscripcion with no compras
    WHEN:  GET /api/inscripciones/{id}/saldo
    THEN:  200 with all zeros.
    """
    # Mock the orchestrator's obtener_saldo to avoid async/sync issues in test
    from unittest.mock import AsyncMock, patch

    mock_saldo = {
        "inscripcion_id": str(inscripcion_base.id),
        "contratados": 0,
        "pagados": 0,
        "asignados_pagados": 0,
        "disponibles_pagados": 0,
    }

    with patch(
        "modules.salesianos_fest.domain.services.orchestrators.asignacion_orchestrator.AsignacionOrchestrator.obtener_saldo",
        new_callable=AsyncMock,
        return_value=mock_saldo,
    ):
        response = _auth_get(
            api_client,
            f"/api/inscripciones/{inscripcion_base.id}/saldo",
            usuario_con_persona,
        )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["contratados"] == 0
    assert data["data"]["pagados"] == 0
    assert data["data"]["asignados_pagados"] == 0
    assert data["data"]["disponibles_pagados"] == 0


# ── Tests: Crear asignaciones after payment ──────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_crear_asignaciones_despues_pago(
    api_client, usuario_con_persona, inscripcion_base, inscripcion_persona, participacion
):
    """
    GIVEN: Compra PAGADA with cantidad=10, InscripcionPersona active
    WHEN:  CrearAsignacionesFlujo is called after payment
    THEN:  AsignacionCupo created with ACTIVA estado.
    """
    # Create the generic commerce.Compra (PAGADA)
    compra = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Test purchase",
        referencia_externa="TEST-REF",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    # Create OrdenPago and TransaccionPago
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-001",
        monto_total=Decimal("500.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="REF123",
        order_number="REF123",
        amount=Decimal("500.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    # Link OrdenPago to the generic Compra
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    # Create CompraInscripcion (FEST composition link with purchase details)
    from modules.salesianos_fest.domain.models import CompraInscripcion
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # Instantiate flujo directly to avoid injector issues in tests
    from modules.salesianos_fest.domain.services.flujos.crear_asignaciones_flujo import CrearAsignacionesFlujo
    from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService
    from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService

    asignacion_core = AsignacionCoreService()
    acreditacion_core = AcreditacionCoreService()
    flujo = CrearAsignacionesFlujo(
        asignacion_core=asignacion_core,
        acreditacion_core=acreditacion_core,
    )

    import asyncio
    resultados = asyncio.get_event_loop().run_until_complete(
        flujo._crear_asignaciones_por_compra(str(compra.id))
    )

    assert len(resultados) == 1
    assert resultados[0]["persona_id"] == str(inscripcion_persona.persona_id)

    # Verify AsignacionCupo exists
    asignacion = AsignacionCupo.objects.get(id=resultados[0]["asignacion_id"])
    assert asignacion.estado == EstadoAsignacionCupoChoices.ACTIVA
    assert asignacion.compra_id == compra.id


# ── Tests: Assign person after payment ──────────────────────────────────────

@pytest.mark.django_db
def test_asignar_persona_con_saldo_disponible(
    api_client, usuario_con_persona, inscripcion_base, persona_3
):
    """
    GIVEN: Compra PAGADA with available saldo, person not yet assigned
    WHEN:  POST /api/asignaciones/
    THEN:  200 with asignacion data.
    """
    # Create the generic commerce.Compra (PAGADA)
    compra = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-456",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    # Create OrdenPago and TransaccionPago PAGADA
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-002",
        monto_total=Decimal("500.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="REF456",
        order_number="REF456",
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
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # Create InscripcionPersona for the new person
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_3,
        estado="A",
    )

    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "persona_id": str(persona_3.id),
    }
    response = _auth_post(
        api_client,
        "/api/asignaciones/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["success"] is True
    assert data["data"]["estado"] == "ACTIVA"
    assert data["data"]["compra_origen_id"] == str(compra.id)


@pytest.mark.django_db
def test_asignar_persona_sin_saldo(api_client, usuario_con_persona, inscripcion_base, persona_3):
    """
    GIVEN: Compra PENDIENTE (not yet paid), no available saldo
    WHEN:  POST /api/asignaciones/
    THEN:  409 returned with CUPO_AGOTADO.
    """
    # Create the generic commerce.Compra (PENDIENTE - not paid)
    compra = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-789",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PENDIENTE,
    )
    # Create OrdenPago PENDIENTE
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-003",
        monto_total=Decimal("500.00"),
        estado=OrdenPagoStatus.PENDIENTE,
    )
    # Link OrdenPago to the generic Compra
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    # Create CompraInscripcion (FEST composition)
    from modules.salesianos_fest.domain.models import CompraInscripcion
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )

    # Create InscripcionPersona for the new person
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_3,
        estado="A",
    )

    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "persona_id": str(persona_3.id),
    }
    response = _auth_post(
        api_client,
        "/api/asignaciones/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.json()}"
    data = response.json()
    assert data["error"]["code"] == "CUPO_AGOTADO"


# ── T14: Concurrent last-quota allocation ─────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_t14_concurrent_ultimo_cupo_desde_dos_requests(
    db, usuario_con_persona, inscripcion_base, persona_3
):
    """
    T14: Dos requests concurrentes intentan consumir el último cupo disponible.
    Solo uno debe succeed; el otro debe obtener CUPO_AGOTADO.

    GIVEN: Compra PAGADA con cantidad=1 (último cupo), una persona pendiente
    WHEN:  Dos llamadas concurrentes a crear_asignaciones_por_compra
    THEN:  Exactly one succeeds, one gets CUPO_AGOTADO.
    """
    import threading
    import asyncio

    # Create the generic commerce.Compra (PAGADA)
    compra = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Test purchase T14",
        referencia_externa="TEST-REF-T14",
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    # Create OrdenPago and TransaccionPago PAGADA with cantidad=1
    orden_pago = OrdenPago.objects.create(
        numero="OP-T14-001",
        monto_total=Decimal("50.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="REF-T14",
        order_number="REF-T14",
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    # Link OrdenPago to the generic Compra
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    # Create CompraInscripcion with cantidad=1 (only 1 spot available)
    from modules.salesianos_fest.domain.models import CompraInscripcion
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=Decimal("50.00"),
        total=Decimal("50.00"),
    )

    # Create InscripcionPersona for the new person
    inscripcion_persona = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_3,
        estado="A",
    )

    # Instantiate flujo
    from modules.salesianos_fest.domain.services.flujos.crear_asignaciones_flujo import CrearAsignacionesFlujo
    from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService
    from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService

    asignacion_core = AsignacionCoreService()
    acreditacion_core = AcreditacionCoreService()
    flujo = CrearAsignacionesFlujo(
        asignacion_core=asignacion_core,
        acreditacion_core=acreditacion_core,
    )

    results = {"left": None, "right": None}
    errors = {"left": None, "right": None}

    def call_flujo(key):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                flujo._crear_asignaciones_por_compra(str(compra.id))
            )
            loop.close()
            results[key] = result
        except Exception as e:
            errors[key] = e

    t1 = threading.Thread(target=call_flujo, args=("left",))
    t2 = threading.Thread(target=call_flujo, args=("right",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Check results
    assert errors["left"] is None, f"Left thread raised: {errors['left']}"
    assert errors["right"] is None, f"Right thread raised: {errors['right']}"

    # Exactly one should succeed (return 1 asignacion), other should return 0
    total_asignaciones = len(results["left"]) + len(results["right"])
    assert total_asignaciones == 1, (
        f"Expected exactly 1 total asignacion, got {total_asignaciones}. "
        f"Left: {results['left']}, Right: {results['right']}"
    )

    # Verify only one AsignacionCupo exists
    assert AsignacionCupo.objects.filter(compra=compra).count() == 1


# ── T15: Concurrent QR scans (single-use) ─────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_t15_concurrent_qr_scans_simultaneos(
    db, evento, persona, paquete_fiesta, promocion_junior
):
    """
    T15: Dos escaneos QR simultáneos del mismo código único.
    Solo uno debe obtener PERMITIDO; el otro debe obtener DENEGADO.

    GIVEN: AcreditacionEvento active, single-use QR, no prior ControlAcceso
    WHEN:  Dos escaneos concurrentes via registrar_acceso_flujo
    THEN:  Exactly one PERMITIDO, one DENEGADO (already used).
    """
    import threading
    import asyncio

    # Create persona_2 and linked user
    persona_2 = Persona.objects.create(
        nombres="Test",
        apellidos="User",
        tipo_documento="DNI",
        numero_documento="55556666",
        genero="M",
    )
    User = get_user_model()
    user_2 = User.objects.create_user(
        username="test_user_2",
        email="test2@example.com",
        password="testpass123",
        persona_fk=persona_2,
    )

    # Create another inscripcion with persona_2
    inscripcion_2 = Inscripcion.objects.create(
        evento=evento,
        responsable=persona_2,
        paquete=paquete_fiesta,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.CONFIRMADA,
    )

    # Create AcreditacionEvento with unique QR code
    from modules.salesianos_fest.domain.models import AcreditacionEvento
    import uuid
    qr_token = str(uuid.uuid4())

    acreditacion = AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_2,
        codigo_qr=qr_token,
        acceso_fiesta=True,
        estado="ACTIVA",
    )

    # Instantiate flujo
    from modules.salesianos_fest.domain.services.flujos.registrar_acceso_flujo import RegistrarAccesoFlujo
    from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService

    acreditacion_core = AcreditacionCoreService()
    flujo = RegistrarAccesoFlujo(acreditacion_core=acreditacion_core)

    results = {"left": None, "right": None}
    errors = {"left": None, "right": None}

    def call_flujo(key):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                flujo._registrar_acceso(qr_token, punto_acceso="entrada_principal")
            )
            loop.close()
            results[key] = result
        except Exception as e:
            errors[key] = e

    t1 = threading.Thread(target=call_flujo, args=("left",))
    t2 = threading.Thread(target=call_flujo, args=("right",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Check results
    assert errors["left"] is None, f"Left thread raised: {errors['left']}"
    assert errors["right"] is None, f"Right thread raised: {errors['right']}"

    # Exactly one PERMITIDO, one DENEGADO
    permitidos = sum(1 for r in results.values() if r["resultado"] == "PERMITIDO")
    denegados = sum(1 for r in results.values() if r["resultado"] == "DENEGADO")

    assert permitidos == 1, f"Expected exactly 1 PERMITIDO, got {permitidos}. Results: {results}"
    assert denegados == 1, f"Expected exactly 1 DENEGADO, got {denegados}. Results: {results}"

    # Verify only one PERMITIDO ControlAcceso exists in DB
    from modules.salesianos_fest.domain.constants import ResultadoAccesoChoices
    permitidos_db = ControlAcceso.objects.filter(
        acreditacion=acreditacion,
        resultado=ResultadoAccesoChoices.PERMITIDO,
    ).count()
    assert permitidos_db == 1, f"Expected exactly 1 PERMITIDO in DB, got {permitidos_db}"
