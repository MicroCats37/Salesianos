"""
Focused integration tests for the paid-cup / pool status synchronization.

Covers the change `pool-cupo-pagado-status-sync`:

- Task 1: the preregistration claims a paid cup automatically when the
          inscription has free paid capacity (atomic, FIFO, idempotent).
- Task 2: the release / removal lifecycle returns the capacity to the
          available pool and offers it to the earliest waiting participant.
- Task 3: the pool endpoint exposes a typed eligibility discriminator
          (`estado_pool`) and honest copy — a paid capacity that already
          exists is NEVER reported as "esperando pago".
- Task 4: the repair command materializes the paid cups that were never
          assigned (idempotent, dry-run safe).
- Task 5: the manual assignment endpoint requires ownership.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.salesianos_fest.domain.constants import (
    AlcanceBeneficioChoices,
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EstadoPoolChoices,
    EtapaChoices,
    MOTIVO_CUPO_POR_ASIGNAR,
    MOTIVO_ESPERANDO_PAGO,
    MOTIVO_SIN_CAPACIDAD,
    ModalidadChoices,
    ModoCalculoBeneficioChoices,
    ModoDisciplinasChoices,
    TipoBeneficioChoices,
    TipoCompraChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Disciplina,
    Inscripcion,
    InscripcionPersona,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
    Promocion,
)
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    InscripcionPersonaCreateData,
)
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)
from modules.salesianos_fest.domain.services.core.acreditacion_service import (
    AcreditacionCoreService,
)
from modules.salesianos_fest.domain.services.core.asignacion_service import (
    AsignacionCoreService,
)
from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import (
    AgregarPersonaFlujo,
)
from modules.salesianos_fest.domain.services.flujos.reparar_cupos_flujo import (
    RepararCuposFlujo,
)
from modules.salesianos_fest.domain.services.flujos.retirar_persona_flujo import (
    RetirarPersonaFlujo,
)
from modules.usuarios.domain.models.persona import Persona


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def evento(db):
    return Evento.objects.create(
        nombre="Salesianos FEST Cupo 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina(db):
    return Disciplina.objects.create(
        nombre="Voley Mixto",
        sigla="VM",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=12,
        esta_activa=True,
    )


@pytest.fixture
def promocion(db):
    return Promocion.objects.create(anio=2012, nombre="Junior", activa=True)


@pytest.fixture
def paquete(db, evento, disciplina):
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta (cupo)",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=1,
        minimo_compra_inicial=1,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=date.today() - timedelta(days=1),
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
        nombres="Ana",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="11111111",
        genero="F",
    )


@pytest.fixture
def persona_2(db):
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Ramos",
        tipo_documento="DNI",
        numero_documento="22222222",
        genero="M",
    )


@pytest.fixture
def persona_3(db):
    return Persona.objects.create(
        nombres="Sara",
        apellidos="Diaz",
        tipo_documento="DNI",
        numero_documento="33333333",
        genero="F",
    )


@pytest.fixture
def usuario_responsable(db, persona):
    User = get_user_model()
    return User.objects.create_user(
        username="ana_responsable",
        email="ana@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def inscripcion(db, evento, persona, paquete, promocion):
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete,
        promocion=promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def compra_pagada(db, inscripcion):
    """Factory of PAGADA compras linked to the inscripcion."""

    def _crear(cantidad=2, tipo=TipoCompraChoices.INICIAL):
        total = Decimal("50.00") * cantidad
        compra = Compra.objects.create(
            responsable=inscripcion.responsable,
            descripcion=f"Compra cupos #{cantidad}",
            referencia_externa=f"CUPO-REF-{cantidad}",
            total=total,
            estado=EstadoCompraChoices.PAGADA,
        )
        orden_pago = OrdenPago.objects.create(
            numero=f"OP-CUPO-{cantidad}",
            monto_total=total,
            estado=OrdenPagoStatus.PAGADA,
        )
        TransaccionPago.objects.create(
            orden_pago=orden_pago,
            transaction_id=f"CUPO-TX-{cantidad}",
            order_number=f"CUPO-TN-{cantidad}",
            amount=total,
            currency="PEN",
            status=IzipayStatus.EXITO,
        )
        compra.orden_pago = orden_pago
        compra.save(update_fields=["orden_pago", "updated_at"])
        CompraInscripcion.objects.create(
            compra=compra,
            inscripcion=inscripcion,
            tipo=tipo,
            cantidad=cantidad,
            precio_unitario=Decimal("50.00"),
            total=total,
        )
        return compra

    return _crear


# ── Helpers ───────────────────────────────────────────────────────────────────


def _preregistrar(inscripcion, persona, equipo_id=None):
    """Run the preregistration flow and return the (InscripcionPersona, Participacion)."""
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion.id),
        persona_id=str(persona.id),
        equipo_id=equipo_id,
    )
    return async_to_sync(AgregarPersonaFlujo().ejecutar)(data)


def _cupo_activo(inscripcion, persona):
    return AsignacionCupo.objects.filter(
        inscripcion=inscripcion,
        inscripcion_persona__persona=persona,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    ).first()


def _liquidar(compra):
    """Run the commercial settlement of a paid compra (allocates the cupos)."""
    from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import (
        ConfirmarPagoFlujo,
    )

    flujo = ConfirmarPagoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
        evidencia_pago=EvidenciaPagoService(),
    )
    return async_to_sync(flujo._confirmar_compra)(str(compra.orden_pago_id))


def _pool(inscripcion, persona):
    entries = InscripcionSelector.get_pool(str(inscripcion.id))
    return next(e for e in entries if e.persona_id == str(persona.id))


def _saldo(inscripcion):
    return AsignacionCoreService().calcular_saldo_inscripcion(str(inscripcion.id))


# ── Task 1: the preregistration claims a paid cup automatically ──────────────


@pytest.mark.django_db
def test_preregistro_asigna_cupo_pagado_automaticamente(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: an inscription with a PAGADA compra of 2 cupos and an EMPTY pool
    WHEN:  a person is preregistered in the pool
    THEN:  the backend creates the ACTIVA AsignacionCupo in the same
           transaction and the pool reports the person as eligible.
    """
    compra_pagada(cantidad=2)

    ip, participacion = _preregistrar(inscripcion, persona)

    assert participacion is None  # preregistration: no team
    assert ip.estado == EstadoInscripcionPersonaChoices.ACTIVO

    cupo = _cupo_activo(inscripcion, persona)
    assert cupo is not None
    assert cupo.compra_id is not None

    # The aggregate agrees with the specific participant
    saldo = _saldo(inscripcion)
    assert saldo["asignados_pagados"] == 1
    assert saldo["disponibles_pagados"] == 1

    entrada = _pool(inscripcion, persona)
    assert entrada.tiene_cupo_activo is True
    assert entrada.estado_pool == EstadoPoolChoices.LISTO
    assert entrada.motivo_bloqueo is None


@pytest.mark.django_db
def test_preregistro_es_idempotente_no_duplica_el_cupo(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: a person already preregistered with an active paid cup
    WHEN:  the same person is preregistered again
    THEN:  no second assignment is created.
    """
    compra_pagada(cantidad=2)
    _preregistrar(inscripcion, persona)

    _preregistrar(inscripcion, persona)

    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona__persona=persona,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_preregistro_sin_capacidad_pagada_no_crea_derecho_ficticio(
    db, inscripcion, persona
):
    """
    GIVEN: an inscription WITHOUT any paid capacity
    WHEN:  a person is preregistered
    THEN:  no AsignacionCupo is created and the pool says the person is
           waiting for the payment.
    """
    _preregistrar(inscripcion, persona)

    assert _cupo_activo(inscripcion, persona) is None

    entrada = _pool(inscripcion, persona)
    assert entrada.tiene_cupo_activo is False
    assert entrada.estado_pool == EstadoPoolChoices.ESPERANDO_PAGO
    assert entrada.motivo_bloqueo == MOTIVO_ESPERANDO_PAGO


@pytest.mark.django_db
def test_preregistro_no_roba_el_cupo_de_un_preregistro_anterior(
    db, inscripcion, compra_pagada, persona, persona_2, persona_3
):
    """
    GIVEN: an inscription with 2 paid cupos
    WHEN:  two people are preregistered and a third one tries to get in
    THEN:  each preregistration holds exactly one cup (nobody steals the cup
           of an earlier preregistration) and the third one is rejected by the
           contracted-capacity gate.
    """
    from modules.salesianos_fest.domain.exceptions import (
        CupoContratadoExcedidoError,
    )

    compra_pagada(cantidad=2)

    _preregistrar(inscripcion, persona)
    _preregistrar(inscripcion, persona_2)

    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona__persona=persona,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona__persona=persona_2,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )

    with pytest.raises(CupoContratadoExcedidoError):
        _preregistrar(inscripcion, persona_3)

    assert _cupo_activo(inscripcion, persona_3) is None


# ── Task 2: the release / removal lifecycle returns the capacity ──────────────


@pytest.mark.django_db
def test_retiro_devuelve_la_capacidad_y_la_reasigna_fifo(
    db, inscripcion, compra_pagada, persona, persona_2
):
    """
    GIVEN: 2 preregistrations waiting and a paid cupo that the settlement
           gave to the earliest one (FIFO); the second one still waits
    WHEN:  the participant that holds the cup is retired
    THEN:  the cup is released, the capacity returns to the available pool and
           it is offered to the participant still waiting.
    """
    # The pool fills up before the payment: the capacity gate is skipped.
    _preregistrar(inscripcion, persona)
    _preregistrar(inscripcion, persona_2)
    assert _cupo_activo(inscripcion, persona) is None

    # A payment of 1 cupo arrives → the settlement serves the earliest one.
    compra = compra_pagada(cantidad=1)
    _liquidar(compra)
    assert _cupo_activo(inscripcion, persona) is not None
    assert _cupo_activo(inscripcion, persona_2) is None

    flujo = RetirarPersonaFlujo(acreditacion_core=AcreditacionCoreService())
    async_to_sync(flujo.ejecutar)(str(inscripcion.id), str(persona.id))

    # The retired participant keeps no active right
    assert _cupo_activo(inscripcion, persona) is None
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona__persona=persona,
            estado=EstadoAsignacionCupoChoices.LIBERADA,
        ).exists()
    )

    # The freed slot went to the participant that was still waiting
    assert _cupo_activo(inscripcion, persona_2) is not None

    saldo = _saldo(inscripcion)
    assert saldo["asignados_pagados"] == 1
    assert saldo["disponibles_pagados"] == 0


@pytest.mark.django_db
def test_retiro_sin_espera_devuelve_la_capacidad_disponible(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: 1 paid cupo held by the only preregistered participant
    WHEN:  the participant is retired
    THEN:  the capacity returns to the available pool (0 assigned, 1 free).
    """
    compra_pagada(cantidad=1)
    _preregistrar(inscripcion, persona)
    assert _cupo_activo(inscripcion, persona) is not None

    flujo = RetirarPersonaFlujo(acreditacion_core=AcreditacionCoreService())
    async_to_sync(flujo.ejecutar)(str(inscripcion.id), str(persona.id))

    saldo = _saldo(inscripcion)
    assert saldo["asignados_pagados"] == 0
    assert saldo["disponibles_pagados"] == 1


# ── Task 3: the pool exposes a typed status and honest copy ──────────────────


@pytest.mark.django_db
def test_pool_estado_cupo_por_asignar_cuando_hay_capacidad_y_no_cupo(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: an inscription with paid capacity and a participant preregistered
           OUTSIDE the preregistration flow (legacy/seed data)
    WHEN:  the pool is read
    THEN:  the participant is NOT reported as "esperando pago": the payment
           already exists, so the state is "cupo por asignar".
    """
    compra_pagada(cantidad=2)
    InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    entrada = _pool(inscripcion, persona)

    assert entrada.tiene_cupo_activo is False
    assert entrada.estado_pool == EstadoPoolChoices.CUPO_POR_ASIGNAR
    assert entrada.motivo_bloqueo == MOTIVO_CUPO_POR_ASIGNAR
    assert entrada.motivo_bloqueo != MOTIVO_ESPERANDO_PAGO


@pytest.mark.django_db
def test_pool_estado_sin_capacidad_cuando_la_capacidad_pagada_esta_agotada(
    db, inscripcion, compra_pagada, persona, persona_2
):
    """
    GIVEN: 2 preregistrations and a paid cupo that the settlement gave to the
           earliest one — the paid capacity is exhausted
    WHEN:  the pool is read
    THEN:  the participant without a cup is reported as "sin capacidad"
           (the paid capacity is exhausted), never as "esperando pago".
    """
    # The pool fills up before the payment: the capacity gate is skipped.
    _preregistrar(inscripcion, persona)
    _preregistrar(inscripcion, persona_2)

    compra = compra_pagada(cantidad=1)
    _liquidar(compra)

    entrada = _pool(inscripcion, persona_2)

    assert entrada.tiene_cupo_activo is False
    assert entrada.estado_pool == EstadoPoolChoices.SIN_CAPACIDAD
    assert entrada.motivo_bloqueo == MOTIVO_SIN_CAPACIDAD
    assert entrada.motivo_bloqueo != MOTIVO_ESPERANDO_PAGO


@pytest.mark.django_db
def test_pool_endpoint_expone_el_discriminador_estado_pool(
    db, api_client, inscripcion, compra_pagada, persona, usuario_responsable
):
    """
    GIVEN: a participant preregistered without paid capacity
    WHEN:  GET /api/inscripciones/{id}/pool is called by the responsable
    THEN:  the response carries the typed `estado_pool` discriminator.
    """
    _preregistrar(inscripcion, persona)

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.get(
        f"/api/inscripciones/{inscripcion.id}/pool",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert len(data["pool"]) == 1
    entrada = data["pool"][0]
    assert entrada["estado_pool"] == EstadoPoolChoices.ESPERANDO_PAGO
    assert entrada["tiene_cupo_activo"] is False
    assert entrada["motivo_bloqueo"] == MOTIVO_ESPERANDO_PAGO


# ── Task 4: the repair command ───────────────────────────────────────────────


@pytest.mark.django_db
def test_reparar_cupos_materializa_los_cupos_pendientes(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: a PAGADA compra and a participant preregistered outside the flow
    WHEN:  the repair flow runs
    THEN:  the pending paid cup is materialized and the access is synced.
    """
    compra_pagada(cantidad=2)
    InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    flujo = RepararCuposFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
    )
    resultado = async_to_sync(flujo._reparar)(dry_run=False)

    assert resultado.revisadas == 1
    assert resultado.reparadas == 1
    assert resultado.asignaciones_creadas == 1

    assert _cupo_activo(inscripcion, persona) is not None

    # The accreditation of the person was synced with the new right
    from modules.salesianos_fest.domain.models import AcreditacionEvento

    acreditacion = AcreditacionEvento.objects.get(
        evento=inscripcion.evento,
        persona=persona,
    )
    assert acreditacion.acceso_fiesta is True


@pytest.mark.django_db
def test_reparar_cupos_respeta_el_orden_fifo(
    db, inscripcion, compra_pagada, persona, persona_2
):
    """
    GIVEN: two participants preregistered before the payment and a paid cupo
    WHEN:  the repair materializes the pending cup
    THEN:  the cup goes to the EARLIEST preregistration (FIFO), never to a
           later one.
    """
    from django.utils import timezone
    from datetime import timedelta

    base = timezone.now() - timedelta(hours=1)
    for offset, persona_ in ((0, persona), (1, persona_2)):
        ip = InscripcionPersona.objects.create(
            inscripcion=inscripcion,
            persona=persona_,
            estado=EstadoInscripcionPersonaChoices.ACTIVO,
        )
        InscripcionPersona.objects.filter(id=ip.id).update(
            created_at=base + timedelta(seconds=offset)
        )

    compra_pagada(cantidad=1)

    flujo = RepararCuposFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
    )
    async_to_sync(flujo._reparar)(dry_run=False)

    assert _cupo_activo(inscripcion, persona) is not None
    assert _cupo_activo(inscripcion, persona_2) is None


@pytest.mark.django_db
def test_reparar_cupos_es_idempotente(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: a repair already materialized the pending cup
    WHEN:  the repair runs again
    THEN:  nothing changes and no right is duplicated.
    """
    compra_pagada(cantidad=2)
    InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    flujo = RepararCuposFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
    )
    async_to_sync(flujo._reparar)(dry_run=False)
    segundo = async_to_sync(flujo._reparar)(dry_run=False)

    assert segundo.asignaciones_creadas == 0
    assert segundo.reparadas == 0
    assert segundo.sin_pendientes == 1
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_reparar_cupos_dry_run_no_cambia_nada(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: a PAGADA compra and a participant waiting for a cup
    WHEN:  the repair runs in dry-run mode
    THEN:  it reports what it would do and creates nothing.
    """
    compra_pagada(cantidad=2)
    InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    flujo = RepararCuposFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
    )
    resultado = async_to_sync(flujo._reparar)(dry_run=True)

    assert resultado.dry_run is True
    assert resultado.asignaciones_creadas == 1
    assert _cupo_activo(inscripcion, persona) is None


@pytest.mark.django_db
def test_comando_reparar_cupos_reporta_el_resumen(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: an inscription with a pending paid cup
    WHEN:  the `reparar_cupos` management command runs
    THEN:  it materializes the cup and reports the summary.
    """
    from django.core.management import call_command

    compra_pagada(cantidad=2)
    InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    call_command("reparar_cupos", "--dry-run", stdout=None, stderr=None)
    assert _cupo_activo(inscripcion, persona) is None

    call_command("reparar_cupos", stdout=None, stderr=None)
    assert _cupo_activo(inscripcion, persona) is not None


# ── Task 5: the manual assignment endpoint requires ownership ────────────────


@pytest.mark.django_db
def test_asignacion_manual_requiere_ownership(
    db, api_client, inscripcion, compra_pagada, persona_2
):
    """
    GIVEN: an authenticated user that is NOT the responsable of the inscripcion
    WHEN:  POST /api/asignaciones/ is called
    THEN:  403 Forbidden — the paid capacity of somebody else's inscripcion
           cannot be consumed.
    """
    compra_pagada(cantidad=2)

    otro = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999999",
        genero="M",
    )
    User = get_user_model()
    usuario_ajeno = User.objects.create_user(
        username="unrelated_cupo",
        email="unrelated_cupo@example.com",
        password="testpass123",
        persona_fk=otro,
    )

    token = AccessToken.for_user(usuario_ajeno)
    response = api_client.post(
        "/api/asignaciones/",
        data={"inscripcion_id": str(inscripcion.id), "persona_id": str(persona_2.id)},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 403, response.content
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 0
    )


@pytest.mark.django_db
def test_asignacion_manual_permitida_para_el_responsable(
    db, api_client, inscripcion, compra_pagada, persona_2, usuario_responsable
):
    """
    GIVEN: the responsable of the inscripcion with free paid capacity
    WHEN:  POST /api/asignaciones/ is called
    THEN:  200 — the responsible can consume the paid capacity of their own
           inscripcion.
    """
    compra_pagada(cantidad=2)

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.post(
        "/api/asignaciones/",
        data={"inscripcion_id": str(inscripcion.id), "persona_id": str(persona_2.id)},
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona__persona=persona_2,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )
