"""
Focused integration tests for Phase 2: Backend Rules.

Covers:
- Task 2.1: Preregistro allowed (no equipo_id), capacity validation blocks excess
- Task 2.2: Participacion creation/move rejected without active cup (CUPO_NO_ASIGNADO)
- Task 2.3: Validation order enforced (deadline, cup, R11, roster)
- Task 2.4: Focused tests for preregistration, cup-less team-drop rejection,
            roster full, R11 and deadline
"""
import uuid
import json

import pytest
from decimal import Decimal
from datetime import date, timedelta

import pytest
from django.test import Client
from django.utils import timezone
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
def evento_cerrado(db):
    """Evento with fecha_limite_modificacion already passed."""
    yesterday = date.today() - timedelta(days=1)
    return Evento.objects.create(
        nombre="Salesianos FEST Cerrado",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        fecha_limite_modificacion=yesterday,
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
def inscripcion_base(db, evento, persona, paquete_fiesta, promocion_junior):
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_fiesta,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def inscripcion_cerrada(db, evento_cerrado, persona, paquete_fiesta, promocion_junior):
    return Inscripcion.objects.create(
        evento=evento_cerrado,
        responsable=persona,
        paquete=paquete_fiesta,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def categoria(db, inscripcion_base):
    return Categoria.objects.create(
        evento=inscripcion_base.evento,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2005,
        esta_activa=True,
    )


@pytest.fixture
def equipo_futbol(db, inscripcion_base, disciplina_futbol, categoria):
    return Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        nombre="Los Tigres FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria,
    )


@pytest.fixture
def disciplina_voley(db):
    """Create a second test disciplina (different from football)."""
    return Disciplina.objects.create(
        nombre="Voley Mixto",
        sigla="VBX",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=12,
        esta_activa=True,
    )


@pytest.fixture
def equipo_futbol_2(db, inscripcion_base, disciplina_futbol, disciplina_voley, categoria):
    """Second equipo with a different disciplina to avoid unique (inscripcion, disciplina) constraint."""
    return Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_voley,
        nombre="Los Lobos FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria,
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


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth_post(client, path, user, data=None):
    token = AccessToken.for_user(user)
    return client.post(
        path,
        data=json.dumps(data) if data else None,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


# ── Task 2.1: Preregistro capacity validation ─────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_preregistro_sin_equipo_id_permitido_cuando_hay_capacidad(
    db, inscripcion_base, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Compra PAGADA with cantidad=3 (3 paid cups), no InscripcionPersona yet
    WHEN:  agregar_persona_flujo is called WITHOUT equipo_id (preregistro)
    THEN:  InscripcionPersona is created (preregistro allowed within capacity).
    """
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionPersonaCreateData

    flujo = AgregarPersonaFlujo()
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(persona_2.id),
        equipo_id=None,  # preregistro — no team
    )

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ip, participacion = loop.run_until_complete(flujo.ejecutar(data))
    loop.close()

    assert ip is not None
    assert ip.persona_id == str(persona_2.id)
    assert ip.inscripcion_id == str(inscripcion_base.id)
    assert ip.estado == "A"
    assert participacion is None  # no equipo_id → no Participacion


@pytest.mark.django_db(transaction=True)
def test_preregistro_bloqueado_cuando_capacidad_excedida(
    db, inscripcion_base, compra_pagada_cantidad_3, persona_2, persona_3, persona_4
):
    """
    GIVEN: Compra PAGADA with cantidad=3 (3 paid cups), 3 InscripcionPersona already active
    WHEN:  A 4th agregar_persona_flujo is called (preregistro)
    THEN:  CupoContratadoExcedidoError is raised.
    """
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionPersonaCreateData
    from modules.salesianos_fest.domain.exceptions import CupoContratadoExcedidoError

    flujo = AgregarPersonaFlujo()

    # Create 3 active InscripcionPersona (reaching the paid capacity of 3)
    for p in [persona_2, persona_3, persona_4]:
        InscripcionPersona.objects.create(
            inscripcion=inscripcion_base,
            persona=p,
            estado="A",
        )

    # 4th preregistro attempt should be blocked
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(persona_2.id),  # reusing persona_2 — get_or_create should trigger the check
    )

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Note: reusing persona_2 creates get_or_create (ip exists, estado='A'), so the
    # activos_count would be 3 (persona_2 + persona_3 + persona_4). With cantidad=3,
    # the check fails. But if persona doesn't exist yet, it would try to create it
    # and activos_count = 3, cantidad = 3 → >= → blocked.
    # Let's use a NEW persona to test the count check
    new_persona = Persona.objects.create(
        nombres="Nuevo",
        apellidos="Test",
        tipo_documento="DNI",
        numero_documento="99999999",
        genero="M",
    )
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(new_persona.id),
        equipo_id=None,
    )

    with pytest.raises(CupoContratadoExcedidoError) as exc_info:
        loop.run_until_complete(flujo.ejecutar(data))

    assert exc_info.value.code == "CUPO_CONTRATADO_EXCEDIDO"
    loop.close()


# ── Task 2.2: Cup-less Participacion creation rejected ─────────────────────────

@pytest.mark.django_db
def test_crear_participacion_sin_cupo_rechazado_cupo_no_asignado(
    db, inscripcion_base, equipo_futbol, persona_2
):
    """
    GIVEN: InscripcionPersona active, NO AsignacionCupo ACTIVA
    WHEN:  ParticipacionCoreService.crear() is called
    THEN:  CupoNoAsignadoError is raised (409 / CUPO_NO_ASIGNADO).
    """
    from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import ParticipacionCreateData
    from modules.salesianos_fest.domain.exceptions import CupoNoAsignadoError

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    # Note: NO AsignacionCupo created — person is in pool without paid cup

    service = ParticipacionCoreService()
    data = ParticipacionCreateData(
        inscripcion_persona_id=str(ip.id),
        equipo_id=str(equipo_futbol.id),
        rol="J",
    )

    with pytest.raises(CupoNoAsignadoError) as exc_info:
        service.crear(data)

    assert exc_info.value.code == "CUPO_NO_ASIGNADO"


@pytest.mark.django_db
def test_crear_participacion_con_cupo_activo_permitido(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: InscripcionPersona active WITH AsignacionCupo ACTIVA
    WHEN:  ParticipacionCoreService.crear() is called
    THEN:  Participacion is created successfully.
    """
    from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import ParticipacionCreateData

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    # Create active AsignacionCupo
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    service = ParticipacionCoreService()
    data = ParticipacionCreateData(
        inscripcion_persona_id=str(ip.id),
        equipo_id=str(equipo_futbol.id),
        rol="J",
    )

    p = service.crear(data)
    assert p is not None
    assert p.estado == EstadoParticipacionChoices.ACTIVA
    assert p.equipo_id == str(equipo_futbol.id)


# ── Task 2.2: Cup-less Participacion move rejected ─────────────────────────────

@pytest.mark.django_db
def test_mover_participacion_sin_cupo_rechazado(
    db, inscripcion_base, equipo_futbol, equipo_futbol_2,
    compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Participacion ACTIVA with AsignacionCupo ACTIVA, cup is then revoked
    WHEN:  ParticipacionCoreService.mover() is called without active cup
    THEN:  CupoNoAsignadoError is raised.
    """
    from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    asignacion = AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    # Create Participacion with cup
    participacion = Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo_futbol,
        disciplina=equipo_futbol.disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # Revoke the cup
    asignacion.estado = EstadoAsignacionCupoChoices.REVOCADA
    asignacion.save()

    service = ParticipacionCoreService()
    from modules.salesianos_fest.domain.exceptions import CupoNoAsignadoError
    with pytest.raises(CupoNoAsignadoError):
        service.mover(participacion, str(equipo_futbol_2.id))


@pytest.mark.django_db
def test_mover_participacion_con_cupo_activo_permitido(
    db, inscripcion_base, equipo_futbol, equipo_futbol_2,
    compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Participacion ACTIVA with active AsignacionCupo
    WHEN:  ParticipacionCoreService.mover() is called
    THEN:  Move succeeds to new equipo.
    """
    from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService

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

    service = ParticipacionCoreService()
    p = service.mover(participacion, str(equipo_futbol_2.id))
    assert str(p.equipo_id) == str(equipo_futbol_2.id)


# ── Task 2.3: Validation order — deadline blocks first ─────────────────────────

@pytest.mark.django_db(transaction=True)
def test_agregar_persona_fecha_limite_excedida_bloquea_antes_de_cupo(
    db, inscripcion_cerrada, equipo_futbol, persona_2
):
    """
    GIVEN: Evento with fecha_limite_modificacion passed (no more modifications allowed)
    WHEN:  agregar_persona_flujo is called with equipo_id
    THEN:  FechaLimiteExcedidaError is raised (deadline checked before cup).

    This verifies the validation order: deadline is checked before the cup check.
    The cup check would also fail (no cup), but deadline fires first.
    """
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionPersonaCreateData
    from modules.salesianos_fest.domain.exceptions import FechaLimiteExcedidaError

    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_cerrada,
        persona=persona_2,
        estado="A",
    )
    # No cup, but deadline should fire first

    flujo = AgregarPersonaFlujo()
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_cerrada.id),
        persona_id=str(persona_2.id),
        equipo_id=str(equipo_futbol.id),
    )

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with pytest.raises(FechaLimiteExcedidaError):
        loop.run_until_complete(flujo.ejecutar(data))
    loop.close()


# ── Task 2.3: Validation order — cup checked before R11/roster ─────────────────

@pytest.mark.django_db(transaction=True)
def test_crear_participacion_cupo_verificado_antes_de_r11_diferente_disciplina(
    db, inscripcion_base, equipo_futbol, disciplina_voley, equipo_futbol_2,
    compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Persona has cup + Participacion ACTIVA in disciplina_futbol.
           Same persona has a second InscripcionPersona (different inscripcion, same evento)
           in disciplina_voley, but NO cup.
    WHEN:  ParticipacionCoreService.crear() is called for the cup-less InscripcionPersona
           in disciplina_voley
    THEN:  CupoNoAsignadoError fires before R11 is even evaluated.
           R11 is (evento, disciplina, persona) — discipline_voley is different from
           disciplina_futbol so R11 would not fire for that disciplina. Cup fires first.
    """
    from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import ParticipacionCreateData
    from modules.salesianos_fest.domain.exceptions import CupoNoAsignadoError

    # Second inscripcion with same evento (different paquete to avoid unique constraint)
    from modules.salesianos_fest.domain.models import PaqueteDisciplina, PaquetePrecio, PaqueteBeneficio
    paquete_2 = Paquete.objects.create(
        evento=inscripcion_base.evento,
        nombre="Paquete Voley",
        descripcion="Disciplina individual",
        tipo=TipoPaqueteChoices.DISCIPLINA,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete_2, disciplina=disciplina_voley)
    PaquetePrecio.objects.create(
        paquete=paquete_2,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )

    inscripcion_2 = Inscripcion.objects.create(
        evento=inscripcion_base.evento,
        responsable=inscripcion_base.responsable,
        paquete=paquete_2,
        promocion=inscripcion_base.promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )

    # InscripcionPersona 1: has cup + Participacion in disciplina_futbol
    ip_1 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip_1,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    Participacion.objects.create(
        inscripcion_persona=ip_1,
        equipo=equipo_futbol,
        disciplina=equipo_futbol.disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # InscripcionPersona 2: same persona, different inscripcion, disciplina_voley — NO cup
    ip_2 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_2,
        persona=persona_2,
        estado="A",
    )
    # NO cup for ip_2

    service = ParticipacionCoreService()
    data = ParticipacionCreateData(
        inscripcion_persona_id=str(ip_2.id),
        equipo_id=str(equipo_futbol_2.id),  # disciplina_voley
    )

    # Cup fires first (ip_2 has no cup), R11 not evaluated
    with pytest.raises(CupoNoAsignadoError):
        service.crear(data)


# ── Task 2.4: R11 still enforced with cup ─────────────────────────────────────

@pytest.mark.django_db
def test_r11_impide_dos_participaciones_activas_misma_disciplina(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: Person already has Participacion ACTIVA in (evento, disciplina)
    WHEN:  A second Participacion is created for same (evento, disciplina) with cup
    THEN:  R11ViolationError is raised.
    """
    from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import ParticipacionCreateData
    from modules.salesianos_fest.domain.exceptions import R11ViolationError

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

    # First Participacion — succeeds
    service = ParticipacionCoreService()
    p1 = service.crear(ParticipacionCreateData(
        inscripcion_persona_id=str(ip.id),
        equipo_id=str(equipo_futbol.id),
        rol="J",
    ))
    assert p1 is not None

    # Second Participacion in same equipo/disciplina — R11 fires
    with pytest.raises(R11ViolationError) as exc_info:
        service.crear(ParticipacionCreateData(
            inscripcion_persona_id=str(ip.id),
            equipo_id=str(equipo_futbol.id),
            rol="J",
        ))
    assert exc_info.value.code == "R11_DUPLICATE_PARTICIPATION"


# ── Task 2.4: Roster full still enforced with cup ──────────────────────────────

@pytest.mark.django_db
def test_roster_lleno_impide_agregar_mas_jugadores(
    db, inscripcion_base, disciplina_futbol, categoria, compra_pagada_cantidad_3
):
    """
    GIVEN: Equipo already has max_jugadores (10) ACTIVA Participaciones, all with cups
    WHEN:  Another Participacion is created for that equipo
    THEN:  RosterCompletoError is raised.
    """
    from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import ParticipacionCreateData
    from modules.salesianos_fest.domain.exceptions import RosterCompletoError

    equipo = Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        nombre="Equiplo Lleno FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria,
    )

    # Create 10 active Participaciones (max_jugadores=10) with cups
    service = ParticipacionCoreService()
    for i in range(10):
        p = Persona.objects.create(
            nombres=f"Jugador{i}",
            apellidos=f"Apellido{i}",
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
    persona_11 = Persona.objects.create(
        nombres="Jugador11",
        apellidos="Apellido11",
        tipo_documento="DNI",
        numero_documento="10000010",
        genero="M",
    )
    ip_11 = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_11,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip_11,
        compra=compra_pagada_cantidad_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    with pytest.raises(RosterCompletoError) as exc_info:
        service.crear(ParticipacionCreateData(
            inscripcion_persona_id=str(ip_11.id),
            equipo_id=str(equipo.id),
            rol="J",
        ))
    assert exc_info.value.code == "ROSTER_COMPLETO"


# ── Task 2.4: Deadline blocks agregar_persona ───────────────────────────────────

@pytest.mark.django_db(transaction=True)
def test_fecha_limite_excedida_impide_agregar_persona(
    db, inscripcion_cerrada, persona_2
):
    """
    GIVEN: Inscripcion whose evento has fecha_limite_modificacion passed
    WHEN:  agregar_persona_flujo is called (preregistro without equipo)
    THEN:  FechaLimiteExcedidaError is raised.
    """
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionPersonaCreateData
    from modules.salesianos_fest.domain.exceptions import FechaLimiteExcedidaError

    flujo = AgregarPersonaFlujo()
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_cerrada.id),
        persona_id=str(persona_2.id),
        equipo_id=None,
    )

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with pytest.raises(FechaLimiteExcedidaError):
        loop.run_until_complete(flujo.ejecutar(data))
    loop.close()


# ── Task 2.4: Preregistro with capacity exactly at limit ──────────────────────

@pytest.mark.django_db(transaction=True)
def test_preregistro_permitido_cuando_activos_igual_a_cantidad_pero_get_or_create(
    db, inscripcion_base, compra_pagada_cantidad_3, persona_2, persona_3, persona_4
):
    """
    GIVEN: Compra PAGADA cantidad=3, exactly 3 InscripcionPersona ACTIVA exist
    WHEN:  agregar_persona_flujo is called for an EXISTING InscripcionPersona (get_or_create)
    THEN:  Succeeds — get_or_create of existing record does not increase count.
           (The existing record was counted in the capacity; reusing it is allowed.)
    """
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionPersonaCreateData

    # Create exactly 3 active InscripcionPersona (matching cantidad=3)
    for p in [persona_2, persona_3, persona_4]:
        InscripcionPersona.objects.create(
            inscripcion=inscripcion_base,
            persona=p,
            estado="A",
        )

    flujo = AgregarPersonaFlujo()
    # Try to add persona_2 again (get_or_create — existing, estado stays 'A')
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(persona_2.id),
        equipo_id=None,
    )

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    ip, participacion = loop.run_until_complete(flujo.ejecutar(data))
    loop.close()

    # Should succeed — persona_2 was already counted in the 3 active
    assert ip is not None
    assert str(ip.persona_id) == str(persona_2.id)
    assert participacion is None


# ── Task 2.2: AgregarPersonaFlujo with equipo_id checks cup ─────────────────────

@pytest.mark.django_db(transaction=True)
def test_agregar_persona_con_equipo_id_sin_cupo_rechazado(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: InscripcionPersona active WITHOUT AsignacionCupo ACTIVA
    WHEN:  agregar_persona_flujo is called WITH equipo_id (tries to create Participacion)
    THEN:  CupoNoAsignadoError is raised.
    """
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionPersonaCreateData
    from modules.salesianos_fest.domain.exceptions import CupoNoAsignadoError

    InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    # NO AsignacionCupo

    flujo = AgregarPersonaFlujo()
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(persona_2.id),
        equipo_id=str(equipo_futbol.id),
    )

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    with pytest.raises(CupoNoAsignadoError):
        loop.run_until_complete(flujo.ejecutar(data))
    loop.close()


@pytest.mark.django_db(transaction=True)
def test_agregar_persona_con_equipo_id_y_cupo_permitido(
    db, inscripcion_base, equipo_futbol, compra_pagada_cantidad_3, persona_2
):
    """
    GIVEN: InscripcionPersona active WITH AsignacionCupo ACTIVA
    WHEN:  agregar_persona_flujo is called WITH equipo_id
    THEN:  Participacion is created successfully.
    """
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionPersonaCreateData

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

    flujo = AgregarPersonaFlujo()
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(persona_2.id),
        equipo_id=str(equipo_futbol.id),
    )

    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result_ip, result_p = loop.run_until_complete(flujo.ejecutar(data))
    loop.close()

    assert result_ip is not None
    assert result_p is not None
    assert result_p.equipo_id == str(equipo_futbol.id)
