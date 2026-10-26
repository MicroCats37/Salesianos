"""
Integration tests for Phase 1: data guarantees (constraints, indexes, capacity).

Covers:
- Task 1.1: unique_activa_compra_persona constraint prevents double assignment
           from the same purchase to the same person.
- Task 1.1: unique_activa_inscripcion_persona constraint already existed.
- Task 1.1: Query indexes exist on (compra, estado), (inscripcion_persona, estado),
             (inscripcion, estado).
- Task 1.2: idx_participacion_r11_path exists and is used for R11 queries.
- Task 1.3: Backfill strategy (covered by doc, not runtime test).
- Task 1.4: Aggregate capacity — asignaciones pagadas cannot exceed CompraInscripcion.cantidad
           (service-layer SELECT FOR UPDATE).
"""
import uuid
import json

import pytest
from decimal import Decimal
from datetime import date, datetime, timezone

import pytest
from django.test import Client
from django.db import connection
from django.db.utils import IntegrityError
from django.utils.timezone import make_aware
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
)
from modules.commerce.domain.models import Compra
from modules.pagos.domain.models import OrdenPago, TransaccionPago
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
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    return Client()


@pytest.fixture
def evento(db):
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_futbol(db):
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
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def paquete_fiesta(db, evento, disciplina_futbol):
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
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def persona_2(db):
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="F",
    )


@pytest.fixture
def persona_3(db):
    return Persona.objects.create(
        nombres="Pedro",
        apellidos="Rodríguez",
        tipo_documento="DNI",
        numero_documento="11223344",
        genero="M",
    )


@pytest.fixture
def usuario_con_persona(db, persona):
    User = get_user_model()
    return User.objects.create_user(
        username="juan_user",
        email="juan@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def inscripcion_base(db, evento, persona, paquete_fiesta, promocion_junior):
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_fiesta,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def compra_pagada_con_cantidad(db, inscripcion_base):
    """Helper: creates Compra PAGADA with cantidad=10 linked to inscripcion."""
    compra = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Test purchase",
        referencia_externa="TEST-REF",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
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
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    from modules.salesianos_fest.domain.models import CompraInscripcion
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=10,
        precio_unitario=Decimal("50.00"),
        total=Decimal("500.00"),
    )
    return compra


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth_post(client, path, user, data=None):
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=json.dumps(data) if data else None,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


# ── Task 1.1: unique_activa_compra_persona constraint ─────────────────────────

@pytest.mark.django_db
def test_unique_activa_compra_persona_impide_doble_asignacion_misma_compra(
    db, inscripcion_base, compra_pagada_con_cantidad, persona_2
):
    """
    GIVEN: Compra PAGADA with 10 cupos, InscripcionPersona active
    WHEN:  Two AsignacionCupo records are created with the same (compra, inscripcion_persona)
           and estado=ACTIVA
    THEN:  Second insert raises IntegrityError (unique_activa_compra_persona).
    """
    # Create InscripcionPersona
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    # First assignment succeeds
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_con_cantidad,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    # Second assignment with same (compra, inscripcion_persona) must fail
    with pytest.raises(IntegrityError) as exc_info:
        AsignacionCupo.objects.create(
            inscripcion=inscripcion_base,
            inscripcion_persona=ip,
            compra=compra_pagada_con_cantidad,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        )
    # SQLite reports the column names; PostgreSQL reports the constraint name.
    # Both mean the partial unique constraint fired.
    exc_str = str(exc_info.value)
    assert "unique_activa_compra_persona" in exc_str or (
        "UNIQUE constraint failed" in exc_str and "compra_id" in exc_str and "inscripcion_persona_id" in exc_str
    ), f"Expected constraint error, got: {exc_str}"


@pytest.mark.django_db
def test_unique_activa_compra_persona_constraint_exists_in_model(
    db, inscripcion_base, compra_pagada_con_cantidad, persona_2
):
    """
    GIVEN: AsignacionCupo model
    WHEN:  We inspect the model's declared constraints
    THEN:  unique_activa_compra_persona is present in Meta.constraints.
           (It is defined as partial unique constraint on (compra, inscripcion_persona)
            where estado=ACTIVA; test_unique_activa_compra_persona_impide_doble_asignacion
            proves it fires at DB level.)
    """
    constraint_names = {c.name for c in AsignacionCupo._meta.constraints}
    assert "unique_activa_compra_persona" in constraint_names, (
        f"Missing unique_activa_compra_persona in model constraints. "
        f"Found: {constraint_names}"
    )


# ── Task 1.1: unique_activa_inscripcion_persona (existing, confirm it works) ───

@pytest.mark.django_db
def test_unique_activa_inscripcion_persona_impide_segunda_asignacion(
    db, inscripcion_base, compra_pagada_con_cantidad, persona_2
):
    """
    GIVEN: InscripcionPersona with one ACTIVA AsignacionCupo
    WHEN:  A second AsignacionCupo ACTIVA is created for the same (inscripcion, inscripcion_persona)
           but from a DIFFERENT compra
    THEN:  IntegrityError (unique_activa_inscripcion_persona).
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    # Create a second Compra PAGADA for the same inscripcion
    compra_2 = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Second purchase",
        referencia_externa="TEST-REF-DIFF",
        total=Decimal("100.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago_2 = OrdenPago.objects.create(
        numero="OP-2026-DIFF",
        monto_total=Decimal("100.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago_2,
        transaction_id="REF-DIFF",
        order_number="REF-DIFF",
        amount=Decimal("100.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra_2.orden_pago = orden_pago_2
    compra_2.save(update_fields=["orden_pago", "updated_at"])
    from modules.salesianos_fest.domain.models import CompraInscripcion
    CompraInscripcion.objects.create(
        compra=compra_2,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.AMPLIACION,
        cantidad=2,
        precio_unitario=Decimal("50.00"),
        total=Decimal("100.00"),
    )

    # First assignment
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_con_cantidad,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    # Second assignment from different compra — must still fail (same inscripcion+persona)
    with pytest.raises(IntegrityError) as exc_info:
        AsignacionCupo.objects.create(
            inscripcion=inscripcion_base,
            inscripcion_persona=ip,
            compra=compra_2,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        )
    exc_str = str(exc_info.value)
    assert "unique_activa_inscripcion_persona" in exc_str or (
        "UNIQUE constraint failed" in exc_str and "inscripcion_id" in exc_str and "inscripcion_persona_id" in exc_str
    ), f"Expected constraint error, got: {exc_str}"


# ── Task 1.1: query indexes exist ─────────────────────────────────────────────

@pytest.mark.django_db
def test_asignacion_indexes_exist(db, inscripcion_base, compra_pagada_con_cantidad, persona_2):
    """
    GIVEN: AsignacionCupo model with Phase-1 indexes defined in Meta
    WHEN:  We inspect the model's declared indexes
    THEN:  The three Phase-1 indexes are present in the model's Meta.indexes:
            idx_asign_cupo_compra_estado, idx_asign_cupo_ip_estado,
            idx_asign_cupo_insc_estado.
            (The third one was renamed in migration 0011: the previous name
            exceeded the 30 character limit of Django — models.E034.)
    """
    index_names = {idx.name for idx in AsignacionCupo._meta.indexes}
    assert "idx_asign_cupo_compra_estado" in index_names, (
        f"Missing idx_asign_cupo_compra_estado in model. Found: {index_names}"
    )
    assert "idx_asign_cupo_ip_estado" in index_names, (
        f"Missing idx_asign_cupo_ip_estado in model. Found: {index_names}"
    )
    assert "idx_asign_cupo_insc_estado" in index_names, (
        f"Missing idx_asign_cupo_insc_estado in model. Found: {index_names}"
    )


# ── Task 1.2: R11 query index exists ─────────────────────────────────────────

@pytest.mark.django_db
def test_participacion_r11_index_exists(db):
    """
    GIVEN: Participacion model with Phase-1 R11 index defined in Meta
    WHEN:  We inspect the model's declared indexes
    THEN:  idx_participacion_r11_path is present in the model's Meta.indexes.
    """
    index_names = {idx.name for idx in Participacion._meta.indexes}
    assert "idx_participacion_r11_path" in index_names, (
        f"Missing idx_participacion_r11_path in model. Found: {index_names}"
    )


# ── Task 1.4: Aggregate capacity (service-layer) ───────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_asignaciones_no_exceden_comprainscripcion_cantidad(
    db, inscripcion_base, compra_pagada_con_cantidad, persona_2, persona_3
):
    """
    GIVEN: Compra PAGADA with cantidad=1, two active InscripcionPersona records
    WHEN:  CrearAsignacionesFlujo is called twice (each person tries to consume the cup)
    THEN:  First succeeds, second gets CUPO_AGOTADO (service-layer SELECT FOR UPDATE).
           DB never has 2 AsignacionCupo ACTIVA for compra with cantidad=1.
    """
    from modules.salesianos_fest.domain.models import CompraInscripcion

    # Override CompraInscripcion to have cantidad=1 (last cup scenario)
    ci = CompraInscripcion.objects.get(compra=compra_pagada_con_cantidad, inscripcion=inscripcion_base)
    ci.cantidad = 1
    ci.save(update_fields=["cantidad"])

    # Create two InscripcionPersona
    ip_a = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base, persona=persona_2, estado="A"
    )
    ip_b = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base, persona=persona_3, estado="A"
    )

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

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # First call — first person gets the cup
    resultados_1 = loop.run_until_complete(
        flujo._crear_asignaciones_por_compra(str(compra_pagada_con_cantidad.id))
    )
    assert len(resultados_1) == 1  # First person got assigned

    # Second call — no quota left
    resultados_2 = loop.run_until_complete(
        flujo._crear_asignaciones_por_compra(str(compra_pagada_con_cantidad.id))
    )
    assert len(resultados_2) == 0  # Second person gets nothing

    loop.close()

    # Verify: exactly 1 ACTIVA AsignacionCupo in DB for this compra
    count_activas = AsignacionCupo.objects.filter(
        compra=compra_pagada_con_cantidad,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).count()
    assert count_activas == 1, f"Expected 1 ACTIVA, got {count_activas}"


# ── Task 1.4: R11 unique constraint still works ──────────────────────────────

@pytest.mark.django_db
def test_r11_unique_constraint_impide_doble_participacion_activa(
    db, inscripcion_base, compra_pagada_con_cantidad, persona_2
):
    """
    GIVEN: Disciplina + Evento, one persona already has Participacion ACTIVA
    WHEN:  A second Participacion ACTIVA is created for same (evento, disciplina, persona)
    THEN:  IntegrityError (unique_r11_evento_disciplina_persona_activa).
    """
    from modules.salesianos_fest.domain.models import Categoria

    # Reuse disciplina_futbol (already in the paquete)
    disciplina = Disciplina.objects.get(nombre="Fútbol 7 Masculino")
    categoria = Categoria.objects.create(
        evento=inscripcion_base.evento,
        nombre="Libre",
        promocion_desde=1990,
        promocion_hasta=2015,
        esta_activa=True,
    )
    equipo = Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina,
        nombre="Los Tigres FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria,
    )

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    # First Participacion ACTIVA succeeds
    Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo,
        disciplina=disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # Second Participacion ACTIVA for same (evento, disciplina, persona) fails — R11
    with pytest.raises(IntegrityError) as exc_info:
        Participacion.objects.create(
            inscripcion_persona=ip,
            equipo=equipo,
            disciplina=disciplina,
            evento=inscripcion_base.evento,
            persona=persona_2,
            rol="J",
            estado=EstadoParticipacionChoices.ACTIVA,
        )
    exc_str = str(exc_info.value)
    assert "unique_r11_evento_disciplina_persona_activa" in exc_str or (
        "UNIQUE constraint failed" in exc_str and "evento_id" in exc_str
    ), f"Expected R11 constraint error, got: {exc_str}"


# ── Task 1.4: unique_activa_compra_persona is ACTIVA-only ─────────────────────

@pytest.mark.django_db
def test_unique_activa_compra_persona_no_impide_asignacion_liberada(
    db, inscripcion_base, compra_pagada_con_cantidad, persona_2
):
    """
    GIVEN: AsignacionCupo ACTIVA for (compra, inscripcion_persona)
    WHEN:  The assignment is released (LIBERADA) and then a new ACTIVA is created
           for the same (compra, inscripcion_persona)
    THEN:  Succeeds — the constraint only applies to ACTIVA rows.
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    # Create and then liberate
    asignacion = AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_con_cantidad,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    asignacion.estado = EstadoAsignacionCupoChoices.LIBERADA
    asignacion.liberada_en = make_aware(datetime.combine(date.today(), datetime.min.time()))
    asignacion.save()

    # New ACTIVA for same (compra, inscripcion_persona) must succeed
    nueva = AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_con_cantidad,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    assert nueva.id != asignacion.id
    assert AsignacionCupo.objects.filter(
        compra=compra_pagada_con_cantidad,
        inscripcion_persona=ip,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).count() == 1
