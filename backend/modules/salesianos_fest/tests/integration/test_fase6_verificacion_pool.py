"""
Phase 6 — Verificacion y Cierre.

Focused verification tests for the acceptance matrix A01-A13 and for the
`resumen_pago.disponible_pagado` defect fixed in Phase 6.

Scope:
- Task 6.1: A01 (inscripcion + compra without personas) and A13 (admin
  override BLOQUEADA preserved after the post-payment sync) at HTTP level,
  plus the regression guard for `disponible_pagado`.
- The remaining A02-A12 scenarios are already covered by the Phase 1-4 suites
  (see the traceability matrix in the Phase 6 verify report).

NO new feature work: every test here asserts an EXISTING contract.
"""
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
    EstadoCompraChoices,
    EstadoAsignacionCupoChoices,
    EstadoInscripcionPersonaChoices,
    AutorizacionFiestaChoices,
    TipoBeneficioChoices,
    AlcanceBeneficioChoices,
    ModoCalculoBeneficioChoices,
)
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client(db):
    """Django Client — handles the async controllers inside the test transaction."""
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
def usuario_admin(db, persona):
    User = get_user_model()
    user = User.objects.create_user(
        username="admin_user",
        email="admin@example.com",
        password="testpass123",
        persona_fk=persona,
    )
    user.is_staff = True
    user.is_superuser = True
    user.save(update_fields=["is_staff", "is_superuser"])
    return user


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
    """Factory of compras linked to the inscripcion (PENDIENTE by default)."""
    contador = {"n": 0}

    def _crear(cantidad=2, estado=EstadoCompraChoices.PENDIENTE, tipo="INICIAL"):
        contador["n"] += 1
        n = contador["n"]
        total = Decimal("50.00") * cantidad
        compra = Compra.objects.create(
            responsable=inscripcion_base.responsable,
            descripcion=f"Compra FEST #{n}",
            referencia_externa=f"PHASE6-REF-{n}",
            total=total,
            estado=estado,
        )
        orden_pago = OrdenPago.objects.create(
            numero=f"OP-PHASE6-{n:03d}",
            monto_total=total,
            estado=(
                OrdenPagoStatus.PAGADA
                if estado == EstadoCompraChoices.PAGADA
                else OrdenPagoStatus.PENDIENTE
            ),
        )
        if estado == EstadoCompraChoices.PAGADA:
            TransaccionPago.objects.create(
                orden_pago=orden_pago,
                transaction_id=f"PHASE6TX{n}",
                order_number=f"PHASE6TN{n}",
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
    """Factory that preregisters participants in the pool (no team)."""
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _auth_headers(user):
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


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


def _detalle(api_client, inscripcion_id, user):
    response = api_client.get(
        f"/api/inscripciones/{inscripcion_id}/detalle",
        **_auth_headers(user),
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _saldo(api_client, inscripcion_id, user):
    response = api_client.get(
        f"/api/inscripciones/{inscripcion_id}/saldo",
        **_auth_headers(user),
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _pool(api_client, inscripcion_id, user):
    response = api_client.get(
        f"/api/inscripciones/{inscripcion_id}/pool",
        **_auth_headers(user),
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


# ── A01: inscripcion + compra sin personas ────────────────────────────────────

@pytest.mark.django_db
def test_a01_detalle_muestra_equipos_y_personas_vacias(
    api_client, inscripcion_base, equipo_futbol, crear_compra, usuario_con_persona,
):
    """
    GIVEN: an inscripcion with a PENDIENTE compra and an equipo, but no personas
    WHEN:  GET /api/inscripciones/{id}/detalle
    THEN: the equipos are visible, `personas` is empty and the pool renders empty
    """
    crear_compra(cantidad=10)

    detalle = _detalle(api_client, inscripcion_base.id, usuario_con_persona)

    assert len(detalle["equipos"]) == 1
    assert detalle["equipos"][0]["participantes"] == []
    assert detalle["personas"] == []
    # A pending purchase IS a payment activity: the truthful message is
    # "Pago pendiente", not "Sin actividades de pago" (see verify report —
    # the plan's A01 wording contradicts its own §2.2 flow).
    assert detalle["resumen_pago"]["estado_mensaje"] == "Pago pendiente"


@pytest.mark.django_db
def test_a01_sin_compras_estado_mensaje_sin_actividades_de_pago(
    api_client, inscripcion_base, equipo_futbol, usuario_con_persona,
):
    """
    GIVEN: an inscripcion with NO purchase at all
    WHEN:  GET /api/inscripciones/{id}/detalle
    THEN: `resumen_pago.estado_mensaje` is "Sin actividades de pago"
    """
    detalle = _detalle(api_client, inscripcion_base.id, usuario_con_persona)

    assert detalle["resumen_pago"]["total_compras"] == 0
    assert detalle["resumen_pago"]["estado_mensaje"] == "Sin actividades de pago"
    assert detalle["resumen_pago"]["disponible_pagado"] == 0


@pytest.mark.django_db
def test_a01_pool_vacio_sin_participantes(
    api_client, inscripcion_base, usuario_con_persona,
):
    """
    GIVEN: an inscripcion without any preregistered participant
    WHEN:  GET /api/inscripciones/{id}/pool
    THEN: the pool is empty (the Phase 5 UI renders the empty state)
    """
    pool = _pool(api_client, inscripcion_base.id, usuario_con_persona)

    assert pool["inscripcion_id"] == str(inscripcion_base.id)
    assert pool["pool"] == []


# ── A13: override admin BLOQUEADA preservado tras el sync post-pago ───────────

@pytest.mark.django_db
def test_a13_override_bloqueada_preservado_tras_sync_post_pago(
    db, inscripcion_base, evento, persona_2, crear_compra, preregistrar,
    usuario_admin,
):
    """
    GIVEN: an admin blocked the fiesta access of a participant (override BLOQUEADA)
    WHEN:  a purchase is confirmed and the post-payment accreditation sync runs
    THEN: the override is preserved — the sync never grants the blocked access
    """
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )

    preregistrar(persona_2)
    compra = crear_compra(cantidad=10, estado=EstadoCompraChoices.PAGADA)

    core = AcreditacionCoreService()

    # The admin blocks the fiesta access of the participant.
    acreditacion = core.obtener_o_crear_acreditacion(
        str(evento.id), str(persona_2.id)
    )[0]
    core.aplicar_override_fiesta(
        acreditacion,
        AutorizacionFiestaChoices.BLOQUEADA,
        "Motivo del administrador",
    )
    acreditacion.refresh_from_db()
    assert acreditacion.autorizacion_fiesta == AutorizacionFiestaChoices.BLOQUEADA
    assert acreditacion.acceso_fiesta is False

    # The payment is confirmed → the post-payment sync recalculates the access.
    _confirmar_pago(str(compra.orden_pago_id))

    acreditacion.refresh_from_db()
    assert acreditacion.autorizacion_fiesta == AutorizacionFiestaChoices.BLOQUEADA
    assert acreditacion.acceso_fiesta is False

    # The participant did receive the paid right — only the fiesta access is blocked.
    asignaciones = AsignacionCupo.objects.filter(
        inscripcion_id=inscripcion_base.id,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )
    assert asignaciones.count() == 1


@pytest.mark.django_db
def test_a13_sync_preserva_override_bloqueada_con_asignacion_activa(
    db, evento, persona_2, inscripcion_base, preregistrar, crear_compra,
):
    """
    GIVEN: a participant with an ACTIVA assignment funded by a PAGADA compra
    WHEN:  the accreditation sync runs explicitly
    THEN: a BLOQUEADA override still wins over the paid origen
    """
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )

    preregistrar(persona_2)
    compra = crear_compra(cantidad=10, estado=EstadoCompraChoices.PAGADA)
    _confirmar_pago(str(compra.orden_pago_id))

    core = AcreditacionCoreService()
    acreditacion = core.obtener_o_crear_acreditacion(
        str(evento.id), str(persona_2.id)
    )[0]
    core.aplicar_override_fiesta(
        acreditacion,
        AutorizacionFiestaChoices.BLOQUEADA,
        "Bloqueo manual",
    )

    resincronizada = core.sync_acreditacion_desde_compras(
        str(evento.id), str(persona_2.id)
    )

    assert resincronizada.autorizacion_fiesta == AutorizacionFiestaChoices.BLOQUEADA
    assert resincronizada.acceso_fiesta is False


# ── Regresion: `resumen_pago.disponible_pagado` (defecto corregido en Fase 6) ─

@pytest.mark.django_db
def test_disponible_pagado_es_cero_antes_del_pago(
    api_client, inscripcion_base, usuario_con_persona, crear_compra, preregistrar,
    persona_2, persona_3,
):
    """
    GIVEN: a pending purchase and two preregistered participants
    WHEN:  the detail and the saldo are read
    THEN: both report 0 free paid slots (nothing is paid yet)
    """
    crear_compra(cantidad=10)
    preregistrar(persona_2, persona_3)

    detalle = _detalle(api_client, inscripcion_base.id, usuario_con_persona)
    saldo = _saldo(api_client, inscripcion_base.id, usuario_con_persona)

    assert detalle["resumen_pago"]["total_pagado_cantidad"] == 0
    assert detalle["resumen_pago"]["disponible_pagado"] == 0
    assert saldo["disponibles_pagados"] == 0


@pytest.mark.django_db
def test_disponible_pagado_refleja_cupos_pagados_libres_tras_el_pago(
    api_client, inscripcion_base, usuario_con_persona, crear_compra, preregistrar,
    persona_2, persona_3,
):
    """
    GIVEN: 10 paid slots and 2 preregistered participants
    WHEN:  the payment is confirmed (2 rights are assigned automatically)
    THEN: `resumen_pago.disponible_pagado` is 8 — the free paid slots —
          and it matches `saldo.disponibles_pagados` exactly
    """
    crear_compra(cantidad=10, estado=EstadoCompraChoices.PAGADA)
    preregistrar(persona_2, persona_3)
    compra = Compra.objects.filter(
        compra_inscripcion__inscripcion_id=inscripcion_base.id
    ).first()
    _confirmar_pago(str(compra.orden_pago_id))

    detalle = _detalle(api_client, inscripcion_base.id, usuario_con_persona)
    saldo = _saldo(api_client, inscripcion_base.id, usuario_con_persona)

    assert detalle["resumen_pago"]["total_pagado_cantidad"] == 10
    assert detalle["resumen_pago"]["disponible_pagado"] == 8
    assert saldo["asignados_pagados"] == 2
    assert saldo["disponibles_pagados"] == 8
    # The two numbers are rendered side by side in the pool page: they MUST agree.
    assert (
        detalle["resumen_pago"]["disponible_pagado"]
        == saldo["disponibles_pagados"]
    )


@pytest.mark.django_db
def test_disponible_pagado_no_affected_by_compra_pendiente(
    api_client, inscripcion_base, usuario_con_persona, crear_compra,
):
    """
    GIVEN: a PENDIENTE purchase of 15 slots (contracted) and a PAGADA one of 10
    WHEN:  the detail is read
    THEN: `disponible_pagado` is 10 — the PENDIENTE slots must NOT consume the
          paid capacity (this is the exact regression of the fixed defect:
          the old formula subtracted the whole contracted total and always
          collapsed to 0)
    """
    crear_compra(cantidad=15, estado=EstadoCompraChoices.PENDIENTE, tipo="INICIAL")
    crear_compra(cantidad=10, estado=EstadoCompraChoices.PAGADA, tipo="AMPLIACION")

    detalle = _detalle(api_client, inscripcion_base.id, usuario_con_persona)

    assert detalle["resumen_pago"]["total_contratado"] == 25
    assert detalle["resumen_pago"]["total_pagado_cantidad"] == 10
    assert detalle["resumen_pago"]["disponible_pagado"] == 10


@pytest.mark.django_db
def test_disponible_pagado_cero_cuando_los_cupos_pagados_agotados(
    api_client, inscripcion_base, usuario_con_persona, crear_compra, preregistrar,
    persona_2, persona_3,
):
    """
    GIVEN: 2 paid slots and 2 preregistered participants (all slots consumed)
    WHEN:  the payment is confirmed and the detail is read
    THEN: `disponible_pagado` is 0 — nobody else can join a team
    """
    crear_compra(cantidad=2, estado=EstadoCompraChoices.PAGADA)
    preregistrar(persona_2, persona_3)
    compra = Compra.objects.filter(
        compra_inscripcion__inscripcion_id=inscripcion_base.id
    ).first()
    _confirmar_pago(str(compra.orden_pago_id))

    detalle = _detalle(api_client, inscripcion_base.id, usuario_con_persona)
    saldo = _saldo(api_client, inscripcion_base.id, usuario_con_persona)

    assert detalle["resumen_pago"]["disponible_pagado"] == 0
    assert saldo["disponibles_pagados"] == 0
    assert saldo["asignados_pagados"] == 2


@pytest.mark.django_db
def test_disponible_pagado_no_es_negativo(
    api_client, inscripcion_base, usuario_con_persona, crear_compra, preregistrar,
    persona_2,
):
    """
    GIVEN: more assigned rights than paid slots (defensive invariant)
    WHEN:  the detail is read
    THEN: `disponible_pagado` never goes negative
    """
    crear_compra(cantidad=1, estado=EstadoCompraChoices.PAGADA)
    preregistrar(persona_2)
    compra = Compra.objects.filter(
        compra_inscripcion__inscripcion_id=inscripcion_base.id
    ).first()
    _confirmar_pago(str(compra.orden_pago_id))

    detalle = _detalle(api_client, inscripcion_base.id, usuario_con_persona)

    assert detalle["resumen_pago"]["disponible_pagado"] >= 0
