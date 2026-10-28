"""
Focused integration tests for Phase 4: Pago y Derechos.

Covers:
- Task 4.1: Payment confirmation creates AsignacionCupo for preregistered
             participants up to the paid capacity (deterministic + idempotent)
- Task 4.2: Participants over the paid capacity stay preregistered and blocked
             (no fictitious rights, no empty assignments)
- Task 4.3: Retirement releases the assignment and recalculates accreditation;
             re-entry restores the right only when capacity/right is valid
- Task 4.4: Initial payment, amplification, repeated payment, overflow,
             retirement/re-entry and cancelled purchase
"""
import pytest
from decimal import Decimal
from datetime import date

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
    CompraInscripcion,
    AcreditacionEvento,
)
from modules.commerce.domain.models import Compra
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
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
    EstadoInscripcionPersonaChoices,
    EstadoAcreditacionChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
)
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus


# ── Fixtures ─────────────────────────────────────────────────────────────────

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
def paquete_fiesta_b(db, evento, disciplina_futbol):
    """Second paquete with fiesta benefit — allows a second inscripcion of the same person."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta B",
        descripcion="Pack con fiesta (segunda inscripcion)",
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
def equipo_futbol(db, inscripcion_base, disciplina_futbol, categoria_senior):
    return Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        nombre="Los Tigres FC",
        estado="EQUIPO_ACTIVO",
        categoria=categoria_senior,
    )


@pytest.fixture
def crear_compra(db, inscripcion_base):
    """Factory of compras linked to the inscripcion (PENDIENTE by default).

    The payment order ALWAYS carries the evidence of a verified payment (a
    correlated successful transaction): the settlement only turns a purchase
    into `PAGADA` when the order proves it was paid. The purchase stays
    PENDIENTE — the commercial settlement is what the tests drive.
    """
    contador = {"n": 0}

    def _crear(
        cantidad=2,
        tipo=TipoCompraChoices.INICIAL,
        estado=EstadoCompraChoices.PENDIENTE,
    ):
        contador["n"] += 1
        n = contador["n"]
        total = Decimal("50.00") * cantidad
        compra = Compra.objects.create(
            responsable=inscripcion_base.responsable,
            descripcion=f"Compra FEST #{n}",
            referencia_externa=f"PHASE4-REF-{n}",
            total=total,
            estado=estado,
        )
        orden_pago = OrdenPago.objects.create(
            numero=f"OP-PHASE4-{n:03d}",
            monto_total=total,
            estado=OrdenPagoStatus.PAGADA,
        )
        TransaccionPago.objects.create(
            orden_pago=orden_pago,
            transaction_id=f"PHASE4TX{n}",
            order_number=f"PHASE4TN{n}",
            amount=total,
            currency="PEN",
            status=IzipayStatus.EXITO,
        )
        compra.orden_pago = orden_pago
        compra.save(update_fields=["orden_pago", "updated_at"])
        CompraInscripcion.objects.create(
            compra=compra,
            inscripcion=inscripcion_base,
            tipo=tipo,
            cantidad=cantidad,
            precio_unitario=Decimal("50.00"),
            total=total,
        )
        return compra

    return _crear


@pytest.fixture
def preregistrar(db, inscripcion_base):
    """Factory that preregisters participants in the pool (no team).

    The registration order is pinned (created_at) so the allocation order of
    the paid rights is explicit and reproducible in the assertions.
    """
    from datetime import timedelta

    from django.utils import timezone

    base = timezone.now() - timedelta(hours=1)
    contador = {"offset": 0}

    def _preregistrar(*personas):
        resultado = []
        for persona in personas:
            created_at = base + timedelta(seconds=contador["offset"])
            contador["offset"] += 1
            ip = InscripcionPersona.objects.create(
                inscripcion=inscripcion_base,
                persona=persona,
                estado=EstadoInscripcionPersonaChoices.ACTIVO,
            )
            InscripcionPersona.objects.filter(id=ip.id).update(created_at=created_at)
            resultado.append(ip)
        return resultado

    return _preregistrar


# ── Helpers ──────────────────────────────────────────────────────────────────

def _confirmar_pago(orden_pago_id: str):
    """Run ConfirmarPagoFlujo for an orden_pago and return the result."""
    from asgiref.sync import async_to_sync

    from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import (
        ConfirmarPagoFlujo,
    )
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )
    from modules.salesianos_fest.domain.services.core.asignacion_service import (
        AsignacionCoreService,
    )

    flujo = ConfirmarPagoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
        evidencia_pago=EvidenciaPagoService(),
    )
    return async_to_sync(flujo._confirmar_compra)(orden_pago_id)


def _asignaciones_activas(inscripcion_id):
    return list(
        AsignacionCupo.objects.filter(
            inscripcion_id=inscripcion_id,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).select_related("inscripcion_persona")
    )


# ── Task 4.1: pago inicial asigna derechos hasta la capacidad pagada ──────────

@pytest.mark.django_db
def test_pago_inicial_asigna_cupos_hasta_capacidad_pagada(
    db, inscripcion_base, crear_compra, preregistrar, persona, persona_2, persona_3
):
    """
    GIVEN: 3 participants preregistered, Compra INICIAL PENDIENTE with cantidad=2
    WHEN:  the payment is confirmed
    THEN:  2 AsignacionCupo ACTIVA are created (deterministic order) and the
           third participant keeps no right.
    """
    preregistrar(persona, persona_2, persona_3)
    compra = crear_compra(cantidad=2)

    _confirmar_pago(str(compra.orden_pago_id))

    asignaciones = _asignaciones_activas(inscripcion_base.id)
    assert len(asignaciones) == 2

    # Deterministic order: the oldest preregistration is served first
    asignadas_ids = sorted(str(a.inscripcion_persona.persona_id) for a in asignaciones)
    assert asignadas_ids == sorted([str(persona.id), str(persona_2.id)])

    # The participant over the paid capacity has no right
    assert not AsignacionCupo.objects.filter(
        inscripcion=inscripcion_base,
        inscripcion_persona__persona=persona_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).exists()

    # The capacity of the compra is respected
    assert AsignacionCupo.objects.filter(
        compra=compra,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).count() == 2


@pytest.mark.django_db
def test_pago_repetido_es_idempotente(
    db, inscripcion_base, crear_compra, preregistrar, persona, persona_2
):
    """
    GIVEN: A paid compra with 2 cupos and 2 preregistered participants
    WHEN:  the payment confirmation is executed twice
    THEN:  no duplicate assignment is created and the second call reports
           already_confirmed.
    """
    preregistrar(persona, persona_2)
    compra = crear_compra(cantidad=2)

    first = _confirmar_pago(str(compra.orden_pago_id))
    assert first.already_confirmed is False
    assert len(_asignaciones_activas(inscripcion_base.id)) == 2

    second = _confirmar_pago(str(compra.orden_pago_id))
    assert second.already_confirmed is True

    assert len(_asignaciones_activas(inscripcion_base.id)) == 2
    assert AsignacionCupo.objects.filter(
        compra=compra,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).count() == 2


@pytest.mark.django_db
def test_ampliacion_pagada_asigna_cupos_a_los_que_sobran(
    db, inscripcion_base, crear_compra, preregistrar, persona, persona_2, persona_3
):
    """
    GIVEN: 3 participants preregistered, initial compra (2 cupos) already paid
    WHEN:  an AMPLIACION compra (1 cupo) is paid
    THEN:  the third participant receives the right of the amplification.
    """
    preregistrar(persona, persona_2, persona_3)

    inicial = crear_compra(cantidad=2, tipo=TipoCompraChoices.INICIAL)
    _confirmar_pago(str(inicial.orden_pago_id))
    assert len(_asignaciones_activas(inscripcion_base.id)) == 2

    ampliacion = crear_compra(
        cantidad=1,
        tipo=TipoCompraChoices.AMPLIACION,
    )
    _confirmar_pago(str(ampliacion.orden_pago_id))

    asignaciones = _asignaciones_activas(inscripcion_base.id)
    assert len(asignaciones) == 3

    # The new right comes from the amplification
    nueva = AsignacionCupo.objects.get(
        compra=ampliacion,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    assert str(nueva.inscripcion_persona.persona_id) == str(persona_3.id)


@pytest.mark.django_db
def test_el_responsable_no_puede_liquidar_por_http(
    db, api_client, inscripcion_base, crear_compra, preregistrar,
    persona, persona_2, usuario_con_persona
):
    """
    GIVEN: 2 preregistered participants and a pending compra
    WHEN:  POST /api/compras/confirmar-pago is called by the responsible
    THEN:  the route does not exist (405) and NO right is created.

    The commercial settlement belongs to the backend (after the payment is
    verified) or to an administrator (through the audited manual approval).
    """
    preregistrar(persona, persona_2)
    compra = crear_compra(cantidad=2)

    token = AccessToken.for_user(usuario_con_persona)
    response = api_client.post(
        f"/api/compras/confirmar-pago?orden_pago_id={compra.orden_pago_id}",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 405, response.content
    compra.refresh_from_db()
    assert compra.estado == EstadoCompraChoices.PENDIENTE
    assert len(_asignaciones_activas(inscripcion_base.id)) == 0


# ── Task 4.2: exceso de participantes queda bloqueado ────────────────────────

@pytest.mark.django_db
def test_participantes_sobre_capacidad_quedan_bloqueados_sin_derecho_ficticio(
    db, inscripcion_base, crear_compra, preregistrar, persona, persona_2, persona_3
):
    """
    GIVEN: 3 participants preregistered but only 2 paid cupos
    WHEN:  the payment is confirmed
    THEN:  the participant over the capacity stays preregistered, blocked in the
           pool, and NO AsignacionCupo row is created for him.
    """
    preregistrar(persona, persona_2, persona_3)
    compra = crear_compra(cantidad=2)

    _confirmar_pago(str(compra.orden_pago_id))

    # No empty assignment is created for the participant over the capacity
    assert AsignacionCupo.objects.filter(
        inscripcion=inscripcion_base,
        inscripcion_persona__persona=persona_3,
    ).count() == 0

    # He stays preregistered (not retired) and blocked in the pool
    ip_3 = InscripcionPersona.objects.get(
        inscripcion=inscripcion_base,
        persona=persona_3,
    )
    assert ip_3.estado == EstadoInscripcionPersonaChoices.ACTIVO

    from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
        InscripcionSelector,
    )

    pool = InscripcionSelector.get_pool(str(inscripcion_base.id))
    entrada_3 = next(e for e in pool if e.persona_id == str(persona_3.id))
    assert entrada_3.tiene_cupo_activo is False
    assert entrada_3.motivo_bloqueo is not None

    # The participants inside the capacity are eligible
    entrada_1 = next(e for e in pool if e.persona_id == str(persona.id))
    assert entrada_1.tiene_cupo_activo is True
    assert entrada_1.motivo_bloqueo is None


# ── Task 4.3: retiro libera el cupo y recalcula la acreditación ─────────────

@pytest.mark.django_db
def test_retiro_libera_asignacion_y_recalcula_acreditacion(
    db, inscripcion_base, equipo_futbol, crear_compra, preregistrar, persona_2
):
    """
    GIVEN: A participant with an active paid right and an active Participacion
    WHEN:  the participant is retired from the inscripcion
    THEN:  the Participacion is RETIRADA, the AsignacionCupo is LIBERADA and the
           acreditacion is recalculated (no more fiesta access).
    """
    from asgiref.sync import async_to_sync

    from modules.salesianos_fest.domain.services.flujos.retirar_persona_flujo import (
        RetirarPersonaFlujo,
    )
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )

    ip = preregistrar(persona_2)[0]
    compra = crear_compra(cantidad=1)
    _confirmar_pago(str(compra.orden_pago_id))

    Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo_futbol,
        disciplina=equipo_futbol.disciplina,
        evento=inscripcion_base.evento,
        persona=persona_2,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    assert AsignacionCupo.objects.filter(
        inscripcion_persona=ip,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).exists()

    flujo = RetirarPersonaFlujo(acreditacion_core=AcreditacionCoreService())
    async_to_sync(flujo.ejecutar)(str(inscripcion_base.id), str(persona_2.id))

    participacion = Participacion.objects.get(inscripcion_persona=ip)
    assert participacion.estado == EstadoParticipacionChoices.RETIRADA

    asignacion = AsignacionCupo.objects.get(inscripcion_persona=ip)
    assert asignacion.estado == EstadoAsignacionCupoChoices.LIBERADA
    assert asignacion.liberada_en is not None

    # The accreditation is recalculated: the only paid origin is gone
    acreditacion = AcreditacionEvento.objects.get(
        evento=inscripcion_base.evento,
        persona=persona_2,
    )
    assert acreditacion.acceso_fiesta is False
    assert acreditacion.estado == EstadoAcreditacionChoices.PENDIENTE


@pytest.mark.django_db
def test_reingreso_reactiva_el_cupo_liberado(
    db, inscripcion_base, equipo_futbol, crear_compra, preregistrar, persona_2
):
    """
    GIVEN: A retired participant whose paid right was released
    WHEN:  the participant re-enters the inscripcion with an equipo
    THEN:  the released right is restored (ACTIVA) and the Participacion is created.
    """
    from asgiref.sync import async_to_sync

    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import (
        AgregarPersonaFlujo,
    )
    from modules.salesianos_fest.domain.services.flujos.retirar_persona_flujo import (
        RetirarPersonaFlujo,
    )
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
        InscripcionPersonaCreateData,
    )

    ip = preregistrar(persona_2)[0]
    compra = crear_compra(cantidad=1)
    _confirmar_pago(str(compra.orden_pago_id))

    # Retire → the right is released
    flujo_retiro = RetirarPersonaFlujo(acreditacion_core=AcreditacionCoreService())
    async_to_sync(flujo_retiro.ejecutar)(str(inscripcion_base.id), str(persona_2.id))
    assert AsignacionCupo.objects.get(inscripcion_persona=ip).estado == (
        EstadoAsignacionCupoChoices.LIBERADA
    )

    # Re-entry with a team → the released right is restored
    flujo = AgregarPersonaFlujo()
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(persona_2.id),
        equipo_id=str(equipo_futbol.id),
    )
    result_ip, result_p = async_to_sync(flujo.ejecutar)(data)

    assert result_ip.estado == EstadoInscripcionPersonaChoices.ACTIVO
    assert result_p is not None
    assert result_p.estado == EstadoParticipacionChoices.ACTIVA

    asignacion = AsignacionCupo.objects.get(inscripcion_persona=result_ip)
    assert asignacion.estado == EstadoAsignacionCupoChoices.ACTIVA


@pytest.mark.django_db
def test_reingreso_sin_capacidad_queda_bloqueado(
    db, inscripcion_base, equipo_futbol, crear_compra, preregistrar,
    persona_2, persona_3
):
    """
    GIVEN: The paid capacity is released by the retirement and is re-assigned
           (FIFO) to the participant still waiting in the pool
    WHEN:  The retired participant re-enters with an equipo
    THEN:  the re-entry is blocked (CUPO_AGOTADO) and no right is restored.
    """

    from asgiref.sync import async_to_sync

    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import (
        AgregarPersonaFlujo,
    )
    from modules.salesianos_fest.domain.services.flujos.retirar_persona_flujo import (
        RetirarPersonaFlujo,
    )
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
        InscripcionPersonaCreateData,
    )
    from modules.salesianos_fest.domain.exceptions import CupoAgotadoError

    ip_2 = preregistrar(persona_2)[0]
    preregistrar(persona_3)
    compra = crear_compra(cantidad=1)
    _confirmar_pago(str(compra.orden_pago_id))

    # The only paid right belongs to the first preregistered participant
    assert AsignacionCupo.objects.filter(
        inscripcion_persona=ip_2,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).exists()

    # persona_2 holds the only paid right; retire → released
    flujo_retiro = RetirarPersonaFlujo(acreditacion_core=AcreditacionCoreService())
    async_to_sync(flujo_retiro.ejecutar)(str(inscripcion_base.id), str(persona_2.id))

    # The freed slot returns to the available paid capacity and is offered to
    # the earliest participant still waiting in the pool (persona_3, FIFO).
    # The retired participant is excluded — its InscripcionPersona is RETIRADA.
    ip_3 = InscripcionPersona.objects.get(
        inscripcion=inscripcion_base,
        persona=persona_3,
    )
    assert AsignacionCupo.objects.filter(
        inscripcion_persona=ip_3,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).exists()

    flujo = AgregarPersonaFlujo()
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion_base.id),
        persona_id=str(persona_2.id),
        equipo_id=str(equipo_futbol.id),
    )

    with pytest.raises(CupoAgotadoError) as exc_info:
        async_to_sync(flujo.ejecutar)(data)

    assert exc_info.value.code == "CUPO_AGOTADO"
    assert AsignacionCupo.objects.get(inscripcion_persona=ip_2).estado == (
        EstadoAsignacionCupoChoices.LIBERADA
    )


# ── Task 4.4: compra cancelada (reembolso) ───────────────────────────────────

@pytest.mark.django_db
def test_compra_cancelada_revoca_solo_las_asignaciones_afectadas(
    db, inscripcion_base, crear_compra, preregistrar, persona, persona_2
):
    """
    GIVEN: Two paid compras funding two different participants
    WHEN:  one of the compras is cancelled
    THEN:  only the assignments of that compra are revoked — the other keeps its
           right — and the access of the affected person is recalculated.
    """
    from asgiref.sync import async_to_sync

    from modules.salesianos_fest.domain.services.flujos.cancelar_compra_flujo import (
        CancelarCompraFlujo,
    )
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )
    from modules.salesianos_fest.domain.services.core.asignacion_service import (
        AsignacionCoreService,
    )
    from modules.salesianos_fest.domain.services.core.pase_beneficiario_service import (
        PaseBeneficiarioCoreService,
    )

    preregistrar(persona, persona_2)
    compra_inicial = crear_compra(cantidad=1, tipo=TipoCompraChoices.INICIAL)
    compra_ampliacion = crear_compra(
        cantidad=1,
        tipo=TipoCompraChoices.AMPLIACION,
    )

    _confirmar_pago(str(compra_inicial.orden_pago_id))
    _confirmar_pago(str(compra_ampliacion.orden_pago_id))
    assert len(_asignaciones_activas(inscripcion_base.id)) == 2

    flujo = CancelarCompraFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
        pase_beneficiario_core=PaseBeneficiarioCoreService(),
    )
    result = async_to_sync(flujo._cancelar_compra)(str(compra_inicial.id))

    assert result.ya_cancelada is False
    assert result.asignaciones_revocadas == 1

    compra_inicial.refresh_from_db()
    assert compra_inicial.estado == EstadoCompraChoices.CANCELADA

    # Only the assignments of the cancelled compra are revoked
    assert AsignacionCupo.objects.filter(
        compra=compra_inicial,
        estado=EstadoAsignacionCupoChoices.REVOCADA,
    ).count() == 1
    assert AsignacionCupo.objects.filter(
        compra=compra_ampliacion,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).count() == 1
    assert len(_asignaciones_activas(inscripcion_base.id)) == 1


@pytest.mark.django_db
def test_compra_cancelada_conserva_acreditacion_entre_inscripciones(
    db, evento, persona, paquete_fiesta, paquete_fiesta_b, promocion_junior
):
    """
    GIVEN: A person with two paid inscriptions (A and B) of the same evento
    WHEN:  the compra of inscription A is cancelled
    THEN:  the person keeps the fiesta access granted by inscription B (R10).
    """
    from asgiref.sync import async_to_sync

    from modules.salesianos_fest.domain.services.flujos.cancelar_compra_flujo import (
        CancelarCompraFlujo,
    )
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )
    from modules.salesianos_fest.domain.services.core.asignacion_service import (
        AsignacionCoreService,
    )
    from modules.salesianos_fest.domain.services.core.pase_beneficiario_service import (
        PaseBeneficiarioCoreService,
    )

    inscripcion_a = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_fiesta,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    inscripcion_b = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_fiesta_b,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )

    ip_a = InscripcionPersona.objects.create(
        inscripcion=inscripcion_a,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    ip_b = InscripcionPersona.objects.create(
        inscripcion=inscripcion_b,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    compra_a = Compra.objects.create(
        responsable=persona,
        descripcion="Compra A",
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_a = OrdenPago.objects.create(
        numero="OP-A",
        monto_total=Decimal("50.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_a,
        transaction_id="OPATXA",
        order_number="OPATNA",
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra_a.orden_pago = orden_a
    compra_a.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra_a,
        inscripcion=inscripcion_a,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=Decimal("50.00"),
        total=Decimal("50.00"),
    )

    compra_b = Compra.objects.create(
        responsable=persona,
        descripcion="Compra B",
        total=Decimal("50.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_b = OrdenPago.objects.create(
        numero="OP-B",
        monto_total=Decimal("50.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_b,
        transaction_id="OPATXB",
        order_number="OPATNB",
        amount=Decimal("50.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra_b.orden_pago = orden_b
    compra_b.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra_b,
        inscripcion=inscripcion_b,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=1,
        precio_unitario=Decimal("50.00"),
        total=Decimal("50.00"),
    )

    _confirmar_pago(str(orden_a.id))
    _confirmar_pago(str(orden_b.id))

    acreditacion = AcreditacionEvento.objects.get(evento=evento, persona=persona)
    assert acreditacion.acceso_fiesta is True

    # Cancel the compra of inscription A
    flujo = CancelarCompraFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
        pase_beneficiario_core=PaseBeneficiarioCoreService(),
    )
    async_to_sync(flujo._cancelar_compra)(str(compra_a.id))

    assert AsignacionCupo.objects.get(inscripcion_persona=ip_a).estado == (
        EstadoAsignacionCupoChoices.REVOCADA
    )
    assert AsignacionCupo.objects.get(inscripcion_persona=ip_b).estado == (
        EstadoAsignacionCupoChoices.ACTIVA
    )

    # The access survives through the other inscription
    acreditacion.refresh_from_db()
    assert acreditacion.acceso_fiesta is True
    assert acreditacion.estado == EstadoAcreditacionChoices.ACTIVA


@pytest.mark.django_db
def test_cancelar_compra_por_http_requiere_ownership(
    db, api_client, inscripcion_base, crear_compra, preregistrar,
    persona, persona_2, usuario_con_persona
):
    """
    GIVEN: An authenticated user that is not the responsable of the inscripcion
    WHEN:  POST /api/compras/{id}/cancelar is called
    THEN:  403 Forbidden — the auth gate is not relaxed.
    """
    otro = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999999",
        genero="M",
    )
    User = get_user_model()
    usuario_ajeno = User.objects.create_user(
        username="unrelated",
        email="unrelated@example.com",
        password="testpass123",
        persona_fk=otro,
    )

    preregistrar(persona, persona_2)
    compra = crear_compra(cantidad=2)

    token = AccessToken.for_user(usuario_ajeno)
    response = api_client.post(
        f"/api/compras/{compra.id}/cancelar",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 403
    compra.refresh_from_db()
    assert compra.estado == EstadoCompraChoices.PENDIENTE


@pytest.mark.django_db
def test_cancelar_compra_por_http_por_responsable(
    db, api_client, inscripcion_base, crear_compra, preregistrar,
    persona, persona_2, usuario_con_persona
):
    """
    GIVEN: The responsable of the inscripcion and a paid compra
    WHEN:  POST /api/compras/{id}/cancelar is called
    THEN:  200 — the compra is cancelled and its rights are revoked.
    """
    preregistrar(persona, persona_2)
    compra = crear_compra(cantidad=2, estado=EstadoCompraChoices.PAGADA)
    _confirmar_pago(str(compra.orden_pago_id))
    assert len(_asignaciones_activas(inscripcion_base.id)) == 2

    token = AccessToken.for_user(usuario_con_persona)
    response = api_client.post(
        f"/api/compras/{compra.id}/cancelar",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["estado"] == EstadoCompraChoices.CANCELADA
    assert data["asignaciones_revocadas"] == 2

    assert len(_asignaciones_activas(inscripcion_base.id)) == 0
