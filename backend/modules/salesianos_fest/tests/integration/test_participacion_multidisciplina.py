"""
Focused integration tests for multi-discipline participation.

Covers the change `participacion-multidisciplina-por-inscripcion`:

- Task 1: the team-scoped eligible-participant read endpoint
  (`GET /inscripciones/{id}/equipos/{equipo_id}/elegibles`) reports the paid-cup
  eligibility, the disciplines already used and the verdict for the target team.
  The `/pool` contract is untouched.
- Task 2: the existing assignment write endpoint registers a SECOND discipline
  for a person that already plays (one paid cup, several disciplines) and still
  rejects a second participation in the SAME discipline (R11).
- Task 3: `mover()` syncs the redundant `disciplina`/`evento` fields, re-checks
  R11 for the destination and refuses a team of another inscripcion.
- Task 4: releasing a cupo does NOT liberate it while another active discipline
  participation exists.
- Task 5: the detail summary distinguishes distinct people from roster rows.
"""
import pytest
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.salesianos_fest.domain.constants import (
    AlcanceBeneficioChoices,
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EstadoParticipacionChoices,
    EtapaChoices,
    MOTIVO_CUPO_POR_ASIGNAR,
    MOTIVO_YA_EN_DISIPLINA,
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
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Paquete,
    PaqueteBeneficio,
    PaqueteDisciplina,
    PaquetePrecio,
    Participacion,
    Promocion,
)
from modules.salesianos_fest.domain.services.core.participacion_service import (
    ParticipacionCoreService,
)
from modules.salesianos_fest.domain.services.core.asignacion_service import (
    AsignacionCoreService,
)
from modules.salesianos_fest.domain.services.core.acreditacion_service import (
    AcreditacionCoreService,
)
from modules.salesianos_fest.domain.services.flujos.liberar_cupo_flujo import (
    LiberarCupoFlujo,
)
from modules.usuarios.domain.models.persona import Persona


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def evento(db):
    return Evento.objects.create(
        nombre="Salesianos FEST Multi 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina_futbol(db):
    return Disciplina.objects.create(
        nombre="Futbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_voley(db):
    return Disciplina.objects.create(
        nombre="Voley Mixto",
        sigla="VOL",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=12,
        esta_activa=True,
    )


@pytest.fixture
def promocion(db):
    return Promocion.objects.create(anio=2012, nombre="Junior", activa=True)


@pytest.fixture
def paquete(db, evento, disciplina_futbol, disciplina_voley):
    """Pack with TWO disciplines — the Trío scenario of the product."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Trio + Fiesta Box",
        descripcion="Pack con dos disciplinas",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=2,
        minimo_compra_inicial=1,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol)
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_voley)
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
def usuario_responsable(db, persona):
    User = get_user_model()
    return User.objects.create_user(
        username="ana_responsable_multi",
        email="ana_multi@example.com",
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
def equipo_futbol(db, inscripcion, disciplina_futbol):
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_futbol,
        nombre="Los Tigres",
        estado="EQUIPO_ACTIVO",
    )


@pytest.fixture
def equipo_voley(db, inscripcion, disciplina_voley):
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_voley,
        nombre="Los Lobos",
        estado="EQUIPO_ACTIVO",
    )


@pytest.fixture
def otra_inscripcion(db, inscripcion, persona_2):
    """A second inscripcion of the same evento — a DIFFERENT responsable.

    The unique constraint is (evento, responsable, paquete), so the responsable
    must differ to get a second inscripcion of the same evento + paquete.
    """
    return Inscripcion.objects.create(
        evento=inscripcion.evento,
        responsable=persona_2,
        paquete=inscripcion.paquete,
        promocion=inscripcion.promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def compra_pagada(db, inscripcion):
    """Factory of PAGADA compras linked to the inscripcion."""

    def _crear(cantidad=2):
        total = Decimal("50.00") * cantidad
        compra = Compra.objects.create(
            responsable=inscripcion.responsable,
            descripcion=f"Compra cupos #{cantidad}",
            referencia_externa=f"MULTI-REF-{cantidad}",
            total=total,
            estado=EstadoCompraChoices.PAGADA,
        )
        orden_pago = OrdenPago.objects.create(
            numero=f"OP-MULTI-{cantidad}",
            monto_total=total,
            estado=OrdenPagoStatus.PAGADA,
        )
        TransaccionPago.objects.create(
            orden_pago=orden_pago,
            transaction_id=f"MULTI-TX-{cantidad}",
            order_number=f"MULTI-TN-{cantidad}",
            amount=total,
            currency="PEN",
            status=IzipayStatus.EXITO,
        )
        compra.orden_pago = orden_pago
        compra.save(update_fields=["orden_pago", "updated_at"])
        CompraInscripcion.objects.create(
            compra=compra,
            inscripcion=inscripcion,
            tipo=TipoCompraChoices.INICIAL,
            cantidad=cantidad,
            precio_unitario=Decimal("50.00"),
            total=total,
        )
        return compra

    return _crear


# ── Helpers ───────────────────────────────────────────────────────────────────


def _inscripcion_persona(inscripcion, persona):
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


def _cupo_activo(inscripcion, ip, compra):
    return AsignacionCupo.objects.create(
        inscripcion=inscripcion,
        inscripcion_persona=ip,
        compra=compra,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )


def _participacion(inscripcion, ip, persona, equipo):
    return Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo,
        evento=inscripcion.evento,
        disciplina=equipo.disciplina,
        persona=persona,
        rol="J",
        estado=EstadoParticipacionChoices.ACTIVA,
    )


def _elegibles(inscripcion_id, equipo_id):
    from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
        InscripcionSelector,
    )

    return InscripcionSelector.get_elegibles_equipo(
        str(inscripcion_id), str(equipo_id)
    )


def _elegible(result, persona):
    return next(e for e in result.elegibles if e.persona_id == str(persona.id))


# ── Task 1: the team-scoped eligible-participant read endpoint ───────────────


@pytest.mark.django_db
def test_elegibles_equipo_expone_elegibilidad_y_disciplinas_usadas(
    db, inscripcion, compra_pagada, persona, persona_2,
    equipo_futbol, equipo_voley,
):
    """
    GIVEN: a person with ONE paid cup who already plays in Futbol
    WHEN:  the eligible list of the Voley team is read
    THEN:  the person is assignable (one cup, several disciplines) and the
           disciplines already used are reported.
    """
    compra = compra_pagada(cantidad=2)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)

    # A second participant without a cup — the commercial block.
    _inscripcion_persona(inscripcion, persona_2)

    result = _elegibles(inscripcion.id, equipo_voley.id)

    assert result.equipo_id == str(equipo_voley.id)
    assert result.disciplina_id == str(equipo_voley.disciplina_id)

    candidata = _elegible(result, persona)
    assert candidata.tiene_cupo_activo is True
    assert candidata.estado_pool == "LISTO"
    assert candidata.ya_en_disciplina is False
    assert candidata.asignable is True
    assert candidata.motivo_no_asignable is None
    assert len(candidata.disciplinas_asignadas) == 1
    assert candidata.disciplinas_asignadas[0].disciplina_id == str(
        equipo_futbol.disciplina_id
    )
    assert candidata.disciplinas_asignadas[0].equipo_nombre == equipo_futbol.nombre

    # The person without a cup is reported as blocked, never as assignable.
    # The payment already exists (2 paid cupos, 1 consumed) so the honest
    # state is "cupo por asignar" — NEVER "esperando pago".
    bloqueada = _elegible(result, persona_2)
    assert bloqueada.tiene_cupo_activo is False
    assert bloqueada.estado_pool == "CUPO_POR_ASIGNAR"
    assert bloqueada.asignable is False
    assert bloqueada.motivo_no_asignable == MOTIVO_CUPO_POR_ASIGNAR
    assert bloqueada.disciplinas_asignadas == []


@pytest.mark.django_db
def test_elegibles_equipo_marca_ya_en_la_disciplina_como_no_asignable(
    db, inscripcion, compra_pagada, persona, equipo_voley,
):
    """
    GIVEN: a person who already plays in the Voley team
    WHEN:  the eligible list of the Voley team is read
    THEN:  the person is NOT assignable and the reason is the R11 one
           ("Ya participa en esta disciplina") — never a commercial reason.
    """
    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_voley)

    result = _elegibles(inscripcion.id, equipo_voley.id)

    candidata = _elegible(result, persona)
    assert candidata.tiene_cupo_activo is True
    assert candidata.estado_pool == "LISTO"
    assert candidata.ya_en_disciplina is True
    assert candidata.asignable is False
    assert candidata.motivo_no_asignable == MOTIVO_YA_EN_DISIPLINA


@pytest.mark.django_db
def test_elegibles_equipo_http_expone_las_disciplinas_ya_usadas(
    db, api_client, inscripcion, compra_pagada, persona,
    equipo_futbol, equipo_voley, usuario_responsable,
):
    """
    GIVEN: a person with one paid cup who already plays in Futbol
    WHEN:  the eligible list of the Voley team is read over HTTP
    THEN:  the payload carries `disciplinas_asignadas` — the team where the
            person already plays — so the UI can say WHERE they play.

    The domain selector always reported it; the presenter wrote the field
    with an English key (`disciplines_asignadas`), Pydantic ignored it and
    the HTTP payload silently shipped an empty list.
    """
    compra = compra_pagada(cantidad=2)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)

    url = f"/api/inscripciones/{inscripcion.id}/equipos/{equipo_voley.id}/elegibles"
    token = AccessToken.for_user(usuario_responsable)
    response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    candidata = next(
        c for c in data["elegibles"] if c["persona"]["id"] == str(persona.id)
    )

    assert candidata["asignable"] is True
    assert candidata["ya_en_disciplina"] is False
    assert len(candidata["disciplinas_asignadas"]) == 1
    assert candidata["disciplinas_asignadas"][0]["equipo_id"] == str(
        equipo_futbol.id
    )
    assert candidata["disciplinas_asignadas"][0]["equipo_nombre"] == equipo_futbol.nombre
    assert (
        candidata["disciplinas_asignadas"][0]["disciplina"]["sigla"]
        == equipo_futbol.disciplina.sigla
    )


@pytest.mark.django_db
def test_elegibles_equipo_requiere_ownership(
    db, api_client, inscripcion, compra_pagada, persona,
    equipo_voley, usuario_responsable,
):
    """
    GIVEN: an authenticated user that is NOT the responsable of the inscripcion
    WHEN:  GET /api/inscripciones/{id}/equipos/{equipo_id}/elegibles is called
    THEN:  403 Forbidden — the roster of somebody else's inscripcion is private.
    """
    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)

    otro = Persona.objects.create(
        nombres="Otro",
        apellidos="Usuario",
        tipo_documento="DNI",
        numero_documento="99999999",
        genero="M",
    )
    User = get_user_model()
    usuario_ajeno = User.objects.create_user(
        username="unrelated_multi",
        email="unrelated_multi@example.com",
        password="testpass123",
        persona_fk=otro,
    )

    url = f"/api/inscripciones/{inscripcion.id}/equipos/{equipo_voley.id}/elegibles"

    token_ajeno = AccessToken.for_user(usuario_ajeno)
    response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {token_ajeno}")
    assert response.status_code == 403, response.content

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["equipo_id"] == str(equipo_voley.id)
    assert len(data["elegibles"]) == 1
    assert data["elegibles"][0]["asignable"] is True
    assert data["elegibles"][0]["ya_en_disciplina"] is False
    assert data["elegibles"][0]["disciplinas_asignadas"] == []


@pytest.mark.django_db
def test_elegibles_equipo_de_otra_inscripcion_responde_404(
    db, api_client, inscripcion, compra_pagada, persona, persona_2,
    equipo_voley, usuario_responsable,
):
    """
    GIVEN: a team that belongs to another inscripcion
    WHEN:  the eligible list of that team is requested for this inscripcion
    THEN:  404 — the team is not reachable through this inscripcion.
    """
    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)

    otra_inscripcion = Inscripcion.objects.create(
        evento=inscripcion.evento,
        responsable=persona_2,
        paquete=inscripcion.paquete,
        promocion=inscripcion.promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    equipo_ajeno = Equipo.objects.create(
        inscripcion=otra_inscripcion,
        disciplina=equipo_voley.disciplina,
        nombre="Equipo Ajeno",
        estado="EQUIPO_ACTIVO",
    )

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.get(
        f"/api/inscripciones/{inscripcion.id}/equipos/{equipo_ajeno.id}/elegibles",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 404, response.content


@pytest.mark.django_db
def test_pool_no_expone_a_quien_ya_juega_en_otra_disciplina(
    db, inscripcion, compra_pagada, persona, equipo_futbol,
):
    """
    GIVEN: a person who already plays in Futbol
    WHEN:  the pre-registration pool is read
    THEN:  the `/pool` contract is UNCHANGED — the person is still excluded
           (the pool means "waiting in the pool").
    """
    from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
        InscripcionSelector,
    )

    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)

    pool = InscripcionSelector.get_pool(str(inscripcion.id))

    assert all(entry.persona_id != str(persona.id) for entry in pool)


# ── Task 2: one cup, several disciplines ─────────────────────────────────────


@pytest.mark.django_db
def test_asignar_registra_una_segunda_disciplina_con_un_solo_cupo(
    db, api_client, inscripcion, compra_pagada, persona,
    equipo_futbol, equipo_voley, usuario_responsable,
):
    """
    GIVEN: a person with ONE paid cup who already plays in Futbol
    WHEN:  the person is assigned to the Voley team
    THEN:  the second participation is created and the cup is NOT consumed
           twice — the person holds one cup and two participaciones.
    """
    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.post(
        f"/api/inscripciones/{inscripcion.id}/pool/asignar",
        data={
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_voley.id),
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    assert (
        Participacion.objects.filter(
            inscripcion_persona=ip,
            estado=EstadoParticipacionChoices.ACTIVA,
        ).count()
        == 2
    )
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona=ip,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_asignar_a_la_misma_disciplina_es_rechazado_por_r11(
    db, api_client, inscripcion, compra_pagada, persona,
    equipo_futbol, usuario_responsable,
):
    """
    GIVEN: a person who already plays in the Futbol team
    WHEN:  the person is assigned to the SAME discipline again
    THEN:  409 — R11 forbids playing twice in the same discipline.
    """
    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.post(
        f"/api/inscripciones/{inscripcion.id}/pool/asignar",
        data={
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_futbol.id),
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 409, response.content
    assert (
        Participacion.objects.filter(
            inscripcion_persona=ip,
            estado=EstadoParticipacionChoices.ACTIVA,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_asignar_a_un_participante_retirado_es_rechazado(
    db, api_client, inscripcion, compra_pagada, persona,
    equipo_voley, usuario_responsable,
):
    """
    GIVEN: a participant whose inscription link is RETIRED
    WHEN:  the person is assigned to a team
    THEN:  409 — a retired participant must re-enter before playing.
    """
    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    ip.estado = EstadoInscripcionPersonaChoices.RETIRADO
    ip.save(update_fields=["estado", "updated_at"])

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.post(
        f"/api/inscripciones/{inscripcion.id}/pool/asignar",
        data={
            "inscripcion_persona_id": str(ip.id),
            "equipo_id": str(equipo_voley.id),
        },
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 409, response.content
    assert Participacion.objects.filter(inscripcion_persona=ip).count() == 0


# ── Task 3: `mover()` syncs the discipline and re-checks R11 ─────────────────


@pytest.mark.django_db
def test_mover_sincroniza_la_disciplina_y_el_evento(
    db, inscripcion, compra_pagada, persona, equipo_futbol, equipo_voley,
):
    """
    GIVEN: an ACTIVE participation in the Futbol team
    WHEN:  it is moved to the Voley team
    THEN:  the redundant `disciplina` and `evento` fields are re-synced from
           the destination team (they are the fields R11 reads).
    """
    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    participacion = _participacion(inscripcion, ip, persona, equipo_futbol)

    assert participacion.disciplina_id == equipo_futbol.disciplina_id

    service = ParticipacionCoreService()
    movida = service.mover(participacion, str(equipo_voley.id))

    assert str(movida.equipo_id) == str(equipo_voley.id)
    assert str(movida.disciplina_id) == str(equipo_voley.disciplina_id)
    assert str(movida.evento_id) == str(inscripcion.evento_id)


@pytest.mark.django_db
def test_mover_revalida_r11_en_la_disciplina_destino(
    db, inscripcion, compra_pagada, persona, equipo_futbol, equipo_voley,
):
    """
    GIVEN: a person who ALREADY plays in the Voley team
    WHEN:  their Futbol participation is moved to the Voley team
    THEN:  R11ViolationError — the move would duplicate the participation of
           the same (evento, disciplina, persona).
    """
    from modules.salesianos_fest.domain.exceptions import R11ViolationError

    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    participacion = _participacion(inscripcion, ip, persona, equipo_futbol)
    _participacion(inscripcion, ip, persona, equipo_voley)

    service = ParticipacionCoreService()
    with pytest.raises(R11ViolationError):
        service.mover(participacion, str(equipo_voley.id))


@pytest.mark.django_db
def test_mover_rechaza_un_equipo_de_otra_inscripcion(
    db, inscripcion, compra_pagada, persona, persona_2, equipo_futbol,
):
    """
    GIVEN: a team that belongs to another inscripcion
    WHEN:  a participation of this inscripcion is moved to that team
    THEN:  EquipoDeOtraInscripcionError — the roster of an inscripcion is paid
           by the cupos of that SAME inscripcion.
    """
    from modules.salesianos_fest.domain.exceptions import EquipoDeOtraInscripcionError

    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    participacion = _participacion(inscripcion, ip, persona, equipo_futbol)

    otra_inscripcion = Inscripcion.objects.create(
        evento=inscripcion.evento,
        responsable=persona_2,
        paquete=inscripcion.paquete,
        promocion=inscripcion.promocion,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    equipo_ajeno = Equipo.objects.create(
        inscripcion=otra_inscripcion,
        disciplina=equipo_futbol.disciplina,
        nombre="Equipo Ajeno",
        estado="EQUIPO_ACTIVO",
    )

    service = ParticipacionCoreService()
    with pytest.raises(EquipoDeOtraInscripcionError):
        service.mover(participacion, str(equipo_ajeno.id))


# ── Task 4: the cup survives while another discipline is still active ─────────


@pytest.mark.django_db
def test_liberar_cupo_conserva_el_cupo_con_otra_disciplina_activa(
    db, inscripcion, compra_pagada, persona, equipo_futbol, equipo_voley,
):
    """
    GIVEN: a person with ONE paid cup who plays in Futbol AND Voley
    WHEN:  the release is scoped to the Futbol discipline
    THEN:  the Futbol participation is retired but the cup SURVIVES — the
           person still plays with it in Voley.
    """
    from asgiref.sync import async_to_sync

    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)
    _participacion(inscripcion, ip, persona, equipo_voley)

    flujo = LiberarCupoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
    )
    resultado = async_to_sync(flujo._liberar_cupo)(
        str(inscripcion.id),
        str(persona.id),
        "Salida de una disciplina",
        str(equipo_futbol.disciplina_id),
    )

    assert resultado["cupo_liberado"] is False
    assert resultado["asignacion_id"] is None
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona=ip,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )
    # The Voley participation survives; only the Futbol one was retired.
    assert (
        Participacion.objects.filter(
            inscripcion_persona=ip,
            disciplina=equipo_voley.disciplina,
            estado=EstadoParticipacionChoices.ACTIVA,
        ).count()
        == 1
    )
    assert (
        Participacion.objects.filter(
            inscripcion_persona=ip,
            disciplina=equipo_futbol.disciplina,
            estado=EstadoParticipacionChoices.RETIRADA,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_liberar_cupo_sin_otra_disciplina_libera_el_cupo(
    db, inscripcion, compra_pagada, persona, equipo_futbol,
):
    """
    GIVEN: a person with ONE paid cup who plays only in Futbol
    WHEN:  the release is scoped to the Futbol discipline
    THEN:  the cup IS liberated — no active participation is left.
    """
    from asgiref.sync import async_to_sync

    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)

    flujo = LiberarCupoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
    )
    resultado = async_to_sync(flujo._liberar_cupo)(
        str(inscripcion.id),
        str(persona.id),
        "Salida de la disciplina",
        str(equipo_futbol.disciplina_id),
    )

    assert resultado["cupo_liberado"] is True
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona=ip,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 0
    )


@pytest.mark.django_db
def test_liberar_cupo_sin_disciplina_conserva_el_comportamiento_anterior(
    db, inscripcion, compra_pagada, persona, equipo_futbol, equipo_voley,
):
    """
    GIVEN: a person who plays in two disciplines
    WHEN:  the release is NOT scoped to a discipline (inscripcion-scoped)
    THEN:  every participation is retired and the cup is liberated — the
           previous behaviour of the endpoint is preserved.
    """
    from asgiref.sync import async_to_sync

    compra = compra_pagada(cantidad=1)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)
    _participacion(inscripcion, ip, persona, equipo_voley)

    flujo = LiberarCupoFlujo(
        asignacion_core=AsignacionCoreService(),
        acreditacion_core=AcreditacionCoreService(),
    )
    resultado = async_to_sync(flujo._liberar_cupo)(
        str(inscripcion.id),
        str(persona.id),
        "Salida de la inscripcion",
    )

    assert resultado["cupo_liberado"] is True
    assert (
        Participacion.objects.filter(
            inscripcion_persona=ip,
            estado=EstadoParticipacionChoices.RETIRADA,
        ).count()
        == 2
    )


# ── Task 5: the detail distinguishes people from participaciones ─────────────


@pytest.mark.django_db
def test_detalle_distingue_personas_de_participaciones(
    db, api_client, inscripcion, compra_pagada, persona, persona_2,
    equipo_futbol, equipo_voley, usuario_responsable,
):
    """
    GIVEN: two people, one of them playing in TWO disciplines
    WHEN:  the inscription detail is read
    THEN:  `resumen_participantes` reports 3 participaciones and 2 distinct
           people — the roster rows are never confused with the paid persons.
    """
    compra = compra_pagada(cantidad=2)
    ip = _inscripcion_persona(inscripcion, persona)
    _cupo_activo(inscripcion, ip, compra)
    _participacion(inscripcion, ip, persona, equipo_futbol)
    _participacion(inscripcion, ip, persona, equipo_voley)

    ip_2 = _inscripcion_persona(inscripcion, persona_2)
    _cupo_activo(inscripcion, ip_2, compra)
    _participacion(inscripcion, ip_2, persona_2, equipo_futbol)

    token = AccessToken.for_user(usuario_responsable)
    response = api_client.get(
        f"/api/inscripciones/{inscripcion.id}/detalle",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 200, response.content
    resumen = response.json()["data"]["resumen_participantes"]
    assert resumen["participaciones"] == 3
    assert resumen["personas"] == 2
