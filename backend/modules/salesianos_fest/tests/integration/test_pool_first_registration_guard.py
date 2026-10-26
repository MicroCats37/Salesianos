"""
Focused integration tests for the pool-first participant registration guard.

Covers the change `pool-first-participant-registration-ux`:

- The input guard rejects `persona_data` + `equipo_id` (a NEW person created
  inside a team) with a stable 422 code and a safe public message.
- The guard is side-effect free: nothing is written when it fires.
- The preregistration (no `equipo_id`) keeps working and still claims the paid
  cup automatically.
- The compatibility path (`persona_id` + `equipo_id`) keeps working: it places
  an ALREADY registered participant, it does not create a new person.
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
from modules.salesianos_fest.domain.constants import (
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionChoices,
    EstadoInscripcionPersonaChoices,
    EtapaChoices,
    ModalidadChoices,
    ModoDisciplinasChoices,
    TipoCompraChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.exceptions import (
    ParticipanteDebePreregistrarseError,
)
from modules.salesianos_fest.domain.models import (
    AsignacionCupo,
    CompraInscripcion,
    Disciplina,
    Equipo,
    Inscripcion,
    InscripcionPersona,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    Participacion,
    Promocion,
)
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    InscripcionPersonaCreateData,
    PersonaInlineData,
)
from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import (
    AgregarPersonaFlujo,
)
from modules.usuarios.domain.models.persona import Persona


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def evento(db):
    return Evento.objects.create(
        nombre="Salesianos FEST Pool Primero 2026",
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
        nombre="Reencuentro + Fiesta (pool primero)",
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
        username="ana_pool_primero",
        email="ana_pool_primero@example.com",
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
def equipo(db, inscripcion, disciplina):
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        nombre="Los Tigres",
        estado="EQUIPO_ACTIVO",
    )


@pytest.fixture
def compra_pagada(db, inscripcion):
    """Factory of PAGADA compras linked to the inscripcion."""

    def _crear(cantidad=2):
        total = Decimal("50.00") * cantidad
        compra = Compra.objects.create(
            responsable=inscripcion.responsable,
            descripcion=f"Compra cupos #{cantidad}",
            referencia_externa=f"POOLFIRST-REF-{cantidad}",
            total=total,
            estado=EstadoCompraChoices.PAGADA,
        )
        orden_pago = OrdenPago.objects.create(
            numero=f"OP-POOLFIRST-{cantidad}",
            monto_total=total,
            estado=OrdenPagoStatus.PAGADA,
        )
        TransaccionPago.objects.create(
            orden_pago=orden_pago,
            transaction_id=f"POOLFIRST-TX-{cantidad}",
            order_number=f"POOLFIRST-TN-{cantidad}",
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


PERSONA_DATA_NUEVA = {
    "tipo_documento": "DNI",
    "numero_documento": "77777777",
    "nombres": "Nueva",
    "apellidos": "Participante",
    "genero": "F",
}


def _post_personas(api_client, usuario, inscripcion_id, body):
    token = AccessToken.for_user(usuario)
    return api_client.post(
        f"/api/inscripciones/{inscripcion_id}/personas",
        data=body,
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )


# ── The guard: `persona_data` + `equipo_id` is rejected ──────────────────────


@pytest.mark.django_db
def test_persona_data_con_equipo_id_es_rechazado_con_422(
    db, api_client, inscripcion, equipo, usuario_responsable
):
    """
    GIVEN: the responsable of an inscripcion with a team
    WHEN:  POST /api/inscripciones/{id}/personas carries BOTH `persona_data`
           (a brand-new person) and `equipo_id`
    THEN:  422 with the stable code PARTICIPANTE_DEBE_PREREGISTRARSE — the
           pool is the only entry point of the participant lifecycle.
    """
    response = _post_personas(
        api_client,
        usuario_responsable,
        str(inscripcion.id),
        {"persona_data": PERSONA_DATA_NUEVA, "equipo_id": str(equipo.id)},
    )

    assert response.status_code == 422, response.content
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "PARTICIPANTE_DEBE_PREREGISTRARSE"


@pytest.mark.django_db
def test_el_mensaje_publico_del_guard_no_expone_identificadores(
    db, api_client, inscripcion, equipo, usuario_responsable
):
    """
    GIVEN: a rejected `persona_data` + `equipo_id` request
    WHEN:  the public error message is read
    THEN:  it states the pool-first rule and leaks NO uuid, id or technical
           detail (contract/api-wrapper-presenter-contract.md §8).
    """
    response = _post_personas(
        api_client,
        usuario_responsable,
        str(inscripcion.id),
        {"persona_data": PERSONA_DATA_NUEVA, "equipo_id": str(equipo.id)},
    )

    assert response.status_code == 422, response.content
    mensaje = response.json()["error"]["message"]

    assert "pool" in mensaje.lower()
    assert str(inscripcion.id) not in mensaje
    assert str(equipo.id) not in mensaje
    assert "Traceback" not in mensaje


@pytest.mark.django_db
def test_el_guard_no_escribe_nada(
    db, api_client, inscripcion, equipo, usuario_responsable
):
    """
    GIVEN: a rejected `persona_data` + `equipo_id` request
    WHEN:  the request is rejected
    THEN:  no Persona, no InscripcionPersona and no Participacion were
           created — the guard fires before any write.
    """
    _post_personas(
        api_client,
        usuario_responsable,
        str(inscripcion.id),
        {"persona_data": PERSONA_DATA_NUEVA, "equipo_id": str(equipo.id)},
    )

    assert not Persona.objects.filter(numero_documento="77777777").exists()
    assert InscripcionPersona.objects.count() == 0
    assert Participacion.objects.count() == 0


@pytest.mark.django_db
def test_el_guard_rechaza_en_el_dominio_antes_de_la_transaccion():
    """
    GIVEN: a domain DTO built with `persona_data` AND `equipo_id`
    WHEN:  the DTO is constructed
    THEN:  it raises ParticipanteDebePreregistrarseError (422) — the guard is
           a domain rule, not an HTTP-only check.
    """
    with pytest.raises(ParticipanteDebePreregistrarseError) as exc_info:
        InscripcionPersonaCreateData(
            inscripcion_id="inscripcion-cualquiera",
            persona_data=PersonaInlineData(**PERSONA_DATA_NUEVA),
            equipo_id="equipo-cualquiera",
        )

    assert exc_info.value.status_code == 422
    assert exc_info.value.code == "PARTICIPANTE_DEBE_PREREGISTRARSE"


# ── The pool path keeps working ──────────────────────────────────────────────


@pytest.mark.django_db
def test_preregistro_sin_equipo_id_sigue_funcionando(
    db, api_client, inscripcion, usuario_responsable
):
    """
    GIVEN: the responsable of an inscripcion
    WHEN:  POST /api/inscripciones/{id}/personas is called WITHOUT `equipo_id`
    THEN:  201 — the person is preregistered in the pool (no team).
    """
    response = _post_personas(
        api_client,
        usuario_responsable,
        str(inscripcion.id),
        {"persona_data": PERSONA_DATA_NUEVA},
    )

    assert response.status_code == 201, response.content
    assert InscripcionPersona.objects.count() == 1
    assert Participacion.objects.count() == 0


@pytest.mark.django_db
def test_el_autoregistro_del_responsable_va_al_pool(
    db, api_client, inscripcion, usuario_responsable, persona_2
):
    """
    GIVEN: the responsable of the inscripcion (an existing Persona)
    WHEN:  POST /api/inscripciones/{id}/personas is called with `persona_id`
           and WITHOUT `equipo_id`
    THEN:  201 — the self registration is a POOL preregistration: no team, no
           Participacion. The team placement is a later step (the selector).
    """
    response = _post_personas(
        api_client,
        usuario_responsable,
        str(inscripcion.id),
        {"persona_id": str(persona_2.id)},
    )

    assert response.status_code == 201, response.content
    assert InscripcionPersona.objects.filter(
        inscripcion=inscripcion, persona=persona_2
    ).count() == 1
    assert Participacion.objects.count() == 0


@pytest.mark.django_db
def test_el_preregistro_reclama_el_cupo_pagado(
    db, inscripcion, compra_pagada, persona
):
    """
    GIVEN: an inscription with free paid capacity
    WHEN:  a person is preregistered in the pool
    THEN:  the paid cup is claimed automatically (same transaction) — the
           pool-first lifecycle keeps its commercial semantics.
    """
    compra_pagada(cantidad=2)

    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion.id),
        persona_id=str(persona.id),
    )
    ip, participacion = async_to_sync(AgregarPersonaFlujo().ejecutar)(data)

    assert participacion is None
    assert (
        AsignacionCupo.objects.filter(
            inscripcion=inscripcion,
            inscripcion_persona=ip,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_persona_existente_con_equipo_id_sigue_funcionando(
    db, api_client, inscripcion, equipo, usuario_responsable, persona_2, compra_pagada
):
    """
    GIVEN: an ALREADY registered participant that holds a paid cup
    WHEN:  POST /api/inscripciones/{id}/personas is called with `persona_id`
           AND `equipo_id`
    THEN:  201 — the compatibility path places an existing person in a team
           and never creates a new Persona.
    """
    compra_pagada(cantidad=2)

    # The participant is preregistered in the pool first (pool-first lifecycle).
    preregistro = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion.id),
        persona_id=str(persona_2.id),
    )
    async_to_sync(AgregarPersonaFlujo().ejecutar)(preregistro)

    response = _post_personas(
        api_client,
        usuario_responsable,
        str(inscripcion.id),
        {"persona_id": str(persona_2.id), "equipo_id": str(equipo.id)},
    )

    assert response.status_code == 201, response.content
    assert Participacion.objects.count() == 1
    assert Persona.objects.filter(numero_documento="22222222").count() == 1


# ── Ownership stays in force on the rejected path ────────────────────────────


@pytest.mark.django_db
def test_el_guard_no_omite_la_ownership(
    db, api_client, inscripcion, equipo, persona_2
):
    """
    GIVEN: an authenticated user that is NOT the responsable of the inscripcion
    WHEN:  POST /api/inscripciones/{id}/personas carries `persona_data` +
           `equipo_id`
    THEN:  403 Forbidden — ownership is evaluated BEFORE the payload guard, so
           a foreign user cannot probe the inscription.
    """
    User = get_user_model()
    usuario_ajeno = User.objects.create_user(
        username="ajeno_pool_primero",
        email="ajeno_pool_primero@example.com",
        password="testpass123",
        persona_fk=persona_2,
    )

    response = _post_personas(
        api_client,
        usuario_ajeno,
        str(inscripcion.id),
        {"persona_data": PERSONA_DATA_NUEVA, "equipo_id": str(equipo.id)},
    )

    assert response.status_code == 403, response.content
    assert InscripcionPersona.objects.count() == 0


@pytest.mark.django_db
def test_el_preregistro_marca_el_estado_activo(
    db, inscripcion, persona
):
    """
    GIVEN: a person preregistered in the pool
    WHEN:  the flow runs
    THEN:  the InscripcionPersona is ACTIVE (the pool only lists active ones).
    """
    data = InscripcionPersonaCreateData(
        inscripcion_id=str(inscripcion.id),
        persona_id=str(persona.id),
    )
    ip, _ = async_to_sync(AgregarPersonaFlujo().ejecutar)(data)

    assert ip.estado == EstadoInscripcionPersonaChoices.ACTIVO
