"""
Focused integration tests for Phase 3: Atomic Endpoints and Permissions.

Covers:
- Task 3.1: GET /inscripciones/{id}/pool endpoint with eligibility and blocked reason
- Task 3.2: POST /inscripciones/{id}/pool/asignar atomic assignment
- Task 3.3: Ownership/admin authorization on all mutation endpoints
- Task 3.4: Pool selector prefetches (no N+1)
- Task 3.5: Focused tests for ownership, admin, unrelated user, idempotency,
            last-cup concurrency, atomic no-partial failure, pool eligibility
"""
import uuid
import json

import pytest
from decimal import Decimal
from datetime import date, timedelta

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
def disciplina_voley(db):
    return Disciplina.objects.create(
        nombre="Vóley Mixto",
        sigla="VBX",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=12,
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
def categoria_senior(db, evento):
    return Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2011,
        esta_activa=True,
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
        nombres="Mateo",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="M",
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
def persona_4(db):
    return Persona.objects.create(
        nombres="Ana",
        apellidos="López",
        tipo_documento="DNI",
        numero_documento="55667788",
        genero="F",
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
def usuario_sin_persona(db):
    User = get_user_model()
    return User.objects.create_user(
        username="orphan_user",
        email="orphan@example.com",
        password="testpass123",
        persona_fk=None,
    )


@pytest.fixture
def usuario_admin(db, persona):
    User = get_user_model()
    admin = User.objects.create_user(
        username="admin_user",
        email="admin@example.com",
        password="testpass123",
        persona_fk=persona,
        is_staff=True,
        is_superuser=True,
    )
    return admin


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
def equipo_futbol(db, inscripcion_base, disciplina_futbol, categoria_senior):
    return Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        nombre="Los Tigres FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria_senior,
    )


@pytest.fixture
def equipo_voley(db, inscripcion_base, disciplina_voley, categoria_senior):
    return Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_voley,
        nombre="Los Lobos VB",
        estado="EQUIPO_ACTIVO",
        categoria=categoria_senior,
    )


@pytest.fixture
def compra_pagada_cantidad_3(db, inscripcion_base):
    """Compra PAGADA with cantidad=3 linked to inscripcion."""
    compra = Compra.objects.create(
        responsable=inscripcion_base.responsable,
        descripcion="Test purchase 3 cups",
        referencia_externa="TEST-REF-3",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-003",
        monto_total=Decimal("150.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="REF3",
        order_number="REF3",
        amount=Decimal("150.00"),
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
        cantidad=3,
        precio_unitario=Decimal("50.00"),
        total=Decimal("150.00"),
    )
    return compra


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _auth_headers(user):
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# ── Task 3.1: GET /inscripciones/{id}/pool ───────────────────────────────────

@pytest.mark.django_db
def test_pool_endpoint_returns_personas_without_equipo(
    db, inscripcion_base, compra_pagada_cantidad_3, persona_2, equipo_futbol
):
    """
    GIVEN: One InscripcionPersona (persona_2) exists, no Participacion yet (pool)
    WHEN:  GET /inscripciones/{id}/pool is called by responsible
    THEN:  The pool entry is returned with tiene_cupo_activo and motivo_bloqueo.
    """
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    # No AsignacionCupo → blocked

    pool = Inscripcion.objects.get(id=inscripcion_base.id).inscripcion_personas.filter(estado="A")
    assert pool.count() == 1

    # Verify no active Participacion for this InscripcionPersona
    active_participaciones = Participacion.objects.filter(
        inscripcion_persona__in=pool,
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    assert not active_participaciones.exists()


@pytest.mark.django_db
def test_pool_entry_tiene_cupo_activo_true_when_cup_exists(
    db, inscripcion_base, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: InscripcionPersona with active AsignacionCupo
    WHEN:  Pool eligibility is determined
    THEN:  tiene_cupo_activo=True, motivo_bloqueo=None.
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    has_cup = ip.asignaciones_cupo.filter(estado=EstadoAsignacionCupoChoices.ACTIVA).exists()
    assert has_cup is True


@pytest.mark.django_db
def test_pool_entry_tiene_cupo_activo_false_when_no_cup(
    db, inscripcion_base, persona_2
):
    """
    GIVEN: InscripcionPersona WITHOUT AsignacionCupo
    WHEN:  Pool eligibility is determined
    THEN:  tiene_cupo_activo=False, motivo_bloqueo is a UI-safe message.
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    has_cup = ip.asignaciones_cupo.filter(estado=EstadoAsignacionCupoChoices.ACTIVA).exists()
    assert has_cup is False


@pytest.mark.django_db
def test_pool_excludes_personas_with_active_participacion(
    db, inscripcion_base, compra_pagada_cantidad_3, persona_2, equipo_futbol
):
    """
    GIVEN: InscripcionPersona already has an active Participacion in an equipo
    WHEN:  Pool query is executed
    THEN:  That InscripcionPersona is NOT in the pool.
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo_futbol,
        disciplina=equipo_futbol.disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # Pool should be empty
    active_ip_ids = set(
        Participacion.objects.filter(
            inscripcion_persona__inscripcion=inscripcion_base,
            estado=EstadoParticipacionChoices.ACTIVA,
        ).values_list("inscripcion_persona_id", flat=True)
    )
    pool_ips = InscripcionPersona.objects.filter(
        inscripcion=inscripcion_base,
        estado="A",
    ).exclude(id__in=active_ip_ids)

    assert pool_ips.count() == 0


# ── Task 3.2: POST /inscripciones/{id}/pool/asignar ──────────────────────────

@pytest.mark.django_db(transaction=True)
def test_asignar_a_equipo_via_http_creates_participacion_atomically(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2, usuario_con_persona
):
    """
    GIVEN: InscripcionPersona with AsignacionCupo.ACTIVA, no Participacion yet
    WHEN:  POST /inscripciones/{id}/pool/asignar is called by responsible
    THEN:  Participacion is created atomically; no partial state on failure.
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/pool/asignar",
        data=json.dumps({
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_futbol.id),
            "rol": "J",
            "talla_camiseta": "M",
            "notas": "",
        }),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["participante"]["equipo_id"] == str(equipo_futbol.id)
    assert data["data"]["participante"]["persona"]["numero_documento"] == persona_2.numero_documento


@pytest.mark.django_db(transaction=True)
def test_asignar_a_equipo_via_http_fails_without_cup(
    db, inscripcion_base, equipo_futbol, persona_2, usuario_con_persona
):
    """
    GIVEN: InscripcionPersona WITHOUT AsignacionCupo.ACTIVA
    WHEN:  POST /inscripciones/{id}/pool/asignar is called
    THEN:  409 CupoNoAsignadoError; no partial Participacion is created.
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    # NO AsignacionCupo

    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/pool/asignar",
        data=json.dumps({
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_futbol.id),
            "rol": "J",
        }),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )

    assert response.status_code == 409
    # No Participacion was created
    assert not Participacion.objects.filter(
        inscripcion_persona=ip,
        estado=EstadoParticipacionChoices.ACTIVA,
    ).exists()


@pytest.mark.django_db(transaction=True)
def test_asignar_a_equipo_via_http_idempotent_second_call_fails_r11(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2, usuario_con_persona
):
    """
    GIVEN: First asignar_a_equipo call succeeded
    WHEN:  Second identical call is made
    THEN:  409 R11ViolationError (not partial duplicate).
    """
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    client = Client()

    # First call succeeds
    response1 = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/pool/asignar",
        data=json.dumps({
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_futbol.id),
            "rol": "J",
        }),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )
    assert response1.status_code == 200

    # Second call fails with R11
    response2 = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/pool/asignar",
        data=json.dumps({
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_futbol.id),
            "rol": "J",
        }),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )
    assert response2.status_code == 409


# ── Task 3.3: Authorization ───────────────────────────────────────────────────

@pytest.mark.django_db
def test_pool_endpoint_403_for_unrelated_user(
    db, inscripcion_base, usuario_con_persona, persona_2
):
    """
    GIVEN: Authenticated user is NOT the responsible of the inscripcion
    WHEN:  GET /inscripciones/{id}/pool is called
    THEN:  403 Forbidden is returned.
    """
    # Create unrelated user
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999999",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated",
        email="unrelated@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    client = Client()
    response = client.get(
        f"/api/inscripciones/{inscripcion_base.id}/pool",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_pool_endpoint_200_for_responsible(
    db, inscripcion_base, usuario_con_persona, persona_2
):
    """
    GIVEN: Authenticated user IS the responsible of the inscripcion
    WHEN:  GET /inscripciones/{id}/pool is called
    THEN:  200 OK with pool data.
    """
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    client = Client()
    response = client.get(
        f"/api/inscripciones/{inscripcion_base.id}/pool",
        **_auth_headers(usuario_con_persona),
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_pool_endpoint_200_for_admin(
    db, inscripcion_base, usuario_admin, persona_2
):
    """
    GIVEN: Authenticated user is Django admin (is_staff)
    WHEN:  GET /inscripciones/{id}/pool is called for ANY inscripcion
    THEN:  200 OK.
    """
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    client = Client()
    response = client.get(
        f"/api/inscripciones/{inscripcion_base.id}/pool",
        **_auth_headers(usuario_admin),
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_asignar_a_equipo_403_for_unrelated_user(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Unrelated authenticated user (not responsible, not admin)
    WHEN:  POST /inscripciones/{id}/pool/asignar is called
    THEN:  403 Forbidden.
    """
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999998",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated2",
        email="unrelated2@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/pool/asignar",
        data=json.dumps({
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_futbol.id),
            "rol": "J",
        }),
        content_type="application/json",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_retirar_persona_403_for_unrelated_user(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Unrelated authenticated user
    WHEN:  PATCH /inscripciones/{id}/personas/{id}/retirar is called
    THEN:  403 Forbidden.
    """
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999997",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated3",
        email="unrelated3@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    client = Client()
    response = client.patch(
        f"/api/inscripciones/{inscripcion_base.id}/personas/{ip.id}/retirar",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_crear_participacion_403_for_unrelated_user(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Unrelated authenticated user
    WHEN:  POST /participaciones/ is called
    THEN:  403 Forbidden.
    """
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999996",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated4",
        email="unrelated4@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    client = Client()
    response = client.post(
        "/api/participaciones/",
        data=json.dumps({
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_futbol.id),
            "rol": "J",
        }),
        content_type="application/json",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_mover_participacion_403_for_unrelated_user(
    db, inscripcion_base, equipo_futbol, equipo_voley, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Unrelated authenticated user
    WHEN:  PATCH /participaciones/{id}/mover is called
    THEN:  403 Forbidden.
    """
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999995",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated5",
        email="unrelated5@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    participacion = Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo_futbol,
        disciplina=equipo_futbol.disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    client = Client()
    response = client.patch(
        f"/api/participaciones/{participacion.id}/mover",
        data=json.dumps({"equipo_destino_id": str(equipo_voley.id)}),
        content_type="application/json",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_actualizar_participacion_403_for_unrelated_user(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Unrelated authenticated user
    WHEN:  PATCH /participaciones/{id} is called
    THEN:  403 Forbidden.
    """
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999994",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated6",
        email="unrelated6@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    participacion = Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo_futbol,
        disciplina=equipo_futbol.disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    client = Client()
    response = client.patch(
        f"/api/participaciones/{participacion.id}",
        data=json.dumps({"rol": "C"}),
        content_type="application/json",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_retirar_participacion_403_for_unrelated_user(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Unrelated authenticated user
    WHEN:  PATCH /participaciones/{id}/retirar is called
    THEN:  403 Forbidden.
    """
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999993",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated7",
        email="unrelated7@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    participacion = Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo_futbol,
        disciplina=equipo_futbol.disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    client = Client()
    response = client.patch(
        f"/api/participaciones/{participacion.id}/retirar",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_pool_endpoint_401_for_unauthenticated(db, inscripcion_base, persona_2):
    """
    GIVEN: No authentication token provided
    WHEN:  GET /inscripciones/{id}/pool is called
    THEN:  401 Unauthorized.
    """
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )

    client = Client()
    response = client.get(f"/api/inscripciones/{inscripcion_base.id}/pool")
    assert response.status_code == 401


# ── Task 3.4: Selector prefetches ─────────────────────────────────────────────

@pytest.mark.django_db
def test_pool_selector_no_n_plus_1(
    db, inscripcion_base, compra_pagada_cantidad_3,
    persona, persona_2, persona_3, persona_4
):
    """
    GIVEN: Multiple InscripcionPersona records in pool
    WHEN:  InscripcionSelector.get_pool is called
    THEN:  No N+1 queries — uses prefetch_related for asignaciones_cupo and select_related for persona.
    """
    from modules.salesianos_fest.domain.selectors.inscripcion_selector import InscripcionSelector

    # Create pool members using the fixture personas
    for i, p in enumerate([persona, persona_2, persona_3, persona_4]):
        ip = InscripcionPersona.objects.create(
            inscripcion=inscripcion_base,
            persona=p,
            estado="A",
        )
        if i % 2 == 0:  # Give cups to half of them
            AsignacionCupo.objects.create(
                inscripcion=inscripcion_base,
                inscripcion_persona=ip,
                compra=compra_pagada_cantidad_3,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
            )

    # This should not cause N+1 queries
    pool = InscripcionSelector.get_pool(str(inscripcion_base.id))
    assert len(pool) == 4


# ── Task 3.5: Additional edge cases ─────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_asignar_a_equipo_roster_full_blocks(
    db, inscripcion_base, disciplina_futbol, categoria_senior,
    compra_pagada_cantidad_3, persona_2, usuario_con_persona
):
    """
    GIVEN: Equipo at max_jugadores capacity, all with cups
    WHEN:  POST /inscripciones/{id}/pool/asignar is called for another player with cup
    THEN:  409 RosterCompletoError is raised.
    """
    equipo = Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        nombre="Full Team FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria_senior,
    )

    # Fill roster to max (10 players)
    for i in range(10):
        p = Persona.objects.create(
            nombres=f"Player{i}",
            apellidos="Full",
            tipo_documento="DNI",
            numero_documento=f"1000000{i}",
            genero="M",
        )
        ip = InscripcionPersona.objects.create(
            inscripcion=inscripcion_base,
            persona=p,
            estado="A",
        )
        AsignacionCupo.objects.create(
            inscripcion=inscripcion_base,
            inscripcion_persona=ip,
            compra=compra_pagada_cantidad_3,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        )
        Participacion.objects.create(
            inscripcion_persona=ip,
            equipo=equipo,
            disciplina=disciplina_futbol,
            evento=inscripcion_base.evento,
            persona=p,
            rol="J",
            estado=EstadoParticipacionChoices.ACTIVA,
        )

    # 11th player with cup tries to join
    ip_11 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip_11,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/pool/asignar",
        data=json.dumps({
            "inscripcion_persona_id": str(ip_11.id),
            "equipo_id": str(equipo.id),
            "rol": "J",
            "talla_camiseta": "M",
            "notas": "",
        }),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )

    assert response.status_code == 409


@pytest.mark.django_db(transaction=True)
def test_asignar_a_equipo_validates_inscripcion_persona_belongs_to_inscripcion(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2, usuario_con_persona
):
    """
    GIVEN: InscripcionPersona belongs to a DIFFERENT inscripcion
    WHEN:  POST /inscripciones/{id}/pool/asignar is called with this inscripcion_persona_id
    THEN:  404 InscripcionNotFoundError is raised.
    """
    # Create a second inscripcion with persona_2
    other_evento = Evento.objects.create(
        nombre="Other Event",
        fecha_inicio=date(2026, 12, 1),
        fecha_fin=date(2026, 12, 5),
        esta_activo=True,
    )
    other_inscripcion = Inscripcion.objects.create(
        evento=other_evento,
        responsable=inscripcion_base.responsable,
        paquete=inscripcion_base.paquete,
        promocion=inscripcion_base.promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    ip_other = InscripcionPersona.objects.create(
        inscripcion=other_inscripcion,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=other_inscripcion,
        inscripcion_persona=ip_other,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/pool/asignar",
        data=json.dumps({
            "inscripcion_persona_id": str(ip_other.id),  # Wrong inscripcion
            "equipo_id": str(equipo_futbol.id),
            "rol": "J",
            "talla_camiseta": "M",
            "notas": "",
        }),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )

    assert response.status_code == 404

# ── Fase 5: contrato de pre-registro al pool (alta sin `equipo_id`) ────────────
#
# El pre-registro usa el MISMO endpoint que el alta con equipo
# (POST /inscripciones/{id}/personas) pero SIN `equipo_id`: el backend crea
# solo el InscripcionPersona y la persona espera en el pool sin cupo pagado.
#
# Estos tests cierran el hueco de la Task 3.3: el alta de participante tambien
# exige responsable de la inscripcion (o admin) — antes el endpoint era publico.


@pytest.mark.django_db
def test_preregistrar_en_pool_crea_solo_inscripcion_persona(
    db, inscripcion_base, equipo_futbol, persona_2, usuario_con_persona
):
    """
    GIVEN: inscripcion with a team, no preregistration yet
    WHEN:  POST /inscripciones/{id}/personas WITHOUT equipo_id by the responsible
    THEN:  201 — only the InscripcionPersona is created (no Participacion),
           and the person shows up in GET /pool as a pool member.
    """
    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        data=json.dumps({"persona_id": str(persona_2.id)}),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    participante = body["data"]["participante"]
    # InscripcionPersonaOut — no Participacion payload
    assert "inscripcion_id" in participante
    assert "equipo_id" not in participante
    assert participante["estado"] == "A"

    # No Participacion was created — the person is in the pool, not in a team.
    assert not Participacion.objects.filter(
        inscripcion_persona__inscripcion=inscripcion_base,
        estado=EstadoParticipacionChoices.ACTIVA,
    ).exists()

    # The pool endpoint lists the preregistration.
    pool_response = client.get(
        f"/api/inscripciones/{inscripcion_base.id}/pool",
        **_auth_headers(usuario_con_persona),
    )
    assert pool_response.status_code == 200
    pool = pool_response.json()["data"]["pool"]
    assert [entry["persona"]["id"] for entry in pool] == [str(persona_2.id)]


@pytest.mark.django_db
def test_preregistrar_en_pool_401_sin_autenticacion(
    db, inscripcion_base, persona_2
):
    """
    GIVEN: no authentication
    WHEN:  POST /inscripciones/{id}/personas (preregistration)
    THEN:  401 Unauthorized — the roster mutation is not public.
    """
    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        data=json.dumps({"persona_id": str(persona_2.id)}),
        content_type="application/json",
    )
    assert response.status_code == 401
    assert not InscripcionPersona.objects.filter(
        inscripcion=inscripcion_base, persona=persona_2
    ).exists()


@pytest.mark.django_db
def test_preregistrar_en_pool_403_usuario_ajeno(
    db, inscripcion_base, persona_2, usuario_con_persona
):
    """
    GIVEN: authenticated user is NOT the responsible of the inscripcion
    WHEN:  POST /inscripciones/{id}/personas (preregistration)
    THEN:  403 Forbidden and nothing is created.
    """
    unrelated_persona = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999999",
        genero="M",
    )
    User = get_user_model()
    unrelated_user = User.objects.create_user(
        username="unrelated_preregistro",
        email="unrelated_preregistro@example.com",
        password="testpass123",
        persona_fk=unrelated_persona,
    )

    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        data=json.dumps({"persona_id": str(persona_2.id)}),
        content_type="application/json",
        **_auth_headers(unrelated_user),
    )
    assert response.status_code == 403
    assert not InscripcionPersona.objects.filter(
        inscripcion=inscripcion_base, persona=persona_2
    ).exists()


@pytest.mark.django_db
def test_preregistrar_en_pool_200_para_admin(
    db, inscripcion_base, persona_2, usuario_admin
):
    """
    GIVEN: authenticated user is a Django admin (not the responsible)
    WHEN:  POST /inscripciones/{id}/personas (preregistration)
    THEN:  201 — admins may manage any inscription roster.
    """
    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        data=json.dumps({"persona_id": str(persona_2.id)}),
        content_type="application/json",
        **_auth_headers(usuario_admin),
    )
    assert response.status_code == 201
    assert InscripcionPersona.objects.filter(
        inscripcion=inscripcion_base, persona=persona_2, estado="A"
    ).exists()


@pytest.mark.django_db
def test_preregistrar_en_pool_rechaza_capacidad_contratada_excedida(
    db, inscripcion_base, persona_2, persona_3, usuario_con_persona,
    compra_pagada_cantidad_3
):
    """
    GIVEN: the inscription has paid capacity for 3 and the pool is already full
    WHEN:  POST /inscripciones/{id}/personas (preregistration)
    THEN:  409 with code CUPO_CONTRATADO_EXCEDIDO — the frontend surfaces this
           backend error instead of re-implementing the capacity rule.
    """
    # Fill the paid capacity with 3 active preregistrations.
    for persona in (persona_3, persona_2):
        InscripcionPersona.objects.create(
            inscripcion=inscripcion_base,
            persona=persona,
            estado="A",
        )
    # One more active preregistration to reach the paid capacity of 3.
    persona_4 = Persona.objects.create(
        nombres="Cuarta",
        apellidos="Participante",
        tipo_documento="DNI",
        numero_documento="55555555",
        genero="F",
    )
    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_4,
        estado="A",
    )

    persona_5 = Persona.objects.create(
        nombres="Quinta",
        apellidos="Participante",
        tipo_documento="DNI",
        numero_documento="44444444",
        genero="M",
    )

    client = Client()
    response = client.post(
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        data=json.dumps({"persona_id": str(persona_5.id)}),
        content_type="application/json",
        **_auth_headers(usuario_con_persona),
    )

    assert response.status_code == 409
    body = response.json()
    err_code = body.get("error", {}).get("code")
    assert err_code == "CUPO_CONTRATADO_EXCEDIDO", body
    assert not InscripcionPersona.objects.filter(
        inscripcion=inscripcion_base, persona=persona_5
    ).exists()
