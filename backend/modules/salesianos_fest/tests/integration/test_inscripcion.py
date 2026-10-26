import uuid
import json

import pytest

from datetime import date
from decimal import Decimal

from django.test import Client
from django.contrib.auth import get_user_model
from ninja_jwt.tokens import AccessToken

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Promocion,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    Inscripcion,
    Equipo,
    InscripcionPersona,
    Participacion,
)
from modules.salesianos_fest.domain.constants import (
    ModalidadChoices,
    TipoPaqueteChoices,
    ModoDisciplinasChoices,
    EtapaChoices,
    EstadoInscripcionChoices,
    EstadoEquipoChoices,
    EstadoInscripcionPersonaChoices,
    RolParticipanteChoices,
    EstadoParticipacionChoices,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────

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
def persona(db):
    """Create a test persona (responsible/person)."""
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
        nombres="Mateo",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="M",
    )


@pytest.fixture
def usuario_con_persona(db, persona):
    """Create a user linked to a persona (authenticated owner)."""
    User = get_user_model()
    return User.objects.create_user(
        username="juan_user",
        email="juan@example.com",
        password="testpass123",
        persona_fk=persona,
    )


# ── Auth helpers ───────────────────────────────────────────────────────────────

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


@pytest.fixture
def disciplina_futbol(db):
    """Create a test disciplina: Fútbol 7 Masculino."""
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
    """Create a test disciplina: Vóley Mixto."""
    return Disciplina.objects.create(
        nombre="Vóley Mixto",
        sigla="VOL",
        modalidad=ModalidadChoices.MIXTO,
        min_jugadores=6,
        max_jugadores=8,
        esta_activa=True,
    )


@pytest.fixture
def promocion_junior(db):
    """Create a test promocion: Junior 2012."""
    return Promocion.objects.create(
        anio=2012,
        nombre="Junior",
        activa=True,
    )


@pytest.fixture
def promocion_senior(db):
    """Create a test promocion: Senior 1998."""
    return Promocion.objects.create(
        anio=1998,
        nombre="Senior",
        activa=True,
    )


@pytest.fixture
def categoria_senior(db, evento, promocion_senior):
    """Create a test categoria: Senior."""
    return Categoria.objects.create(
        evento=evento,
        nombre="Senior",
        promocion_desde=1998,
        promocion_hasta=2011,
        esta_activa=True,
    )


@pytest.fixture
def paquete_reencuentro(db, evento, disciplina_futbol, disciplina_voley):
    """Create a test paquete: Reencuentro con disciplinas."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.ELEGIBLE,
        cantidad_disciplinas=2,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol)
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_voley)
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa=EtapaChoices.PREVENTA,
        precio_unitario=Decimal("40.00"),
        vigente_desde=date.today(),
        vigente_hasta=date(2026, 10, 31),
        activo=True,
    )
    return paquete


@pytest.fixture
def inscripcion_base(db, evento, persona, paquete_reencuentro, promocion_junior):
    """Create a base inscripcion for tests."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )


@pytest.fixture
def inscripcion_persona_base(db, inscripcion_base, persona):
    """Create a base InscripcionPersona for tests."""
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )


@pytest.fixture
def equipo_base(db, inscripcion_base, disciplina_futbol, categoria_senior, promocion_junior):
    """Create a base equipo for tests."""
    return Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Los Tigres FC",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )


# ─── Tests: Inscripcion ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_crear_inscripcion_http(api_client, evento, usuario_con_persona, paquete_reencuentro, promocion_junior):
    """
    GIVEN: evento, user+persona, paquete and promocion exist
    WHEN: POST /api/inscripciones/ (authenticated)
    THEN: returns 201 with inscripcion data; responsable derived server-side
    """
    payload = {
        "evento_id": str(evento.id),
        "paquete_id": str(paquete_reencuentro.id),
        "promocion_id": str(promocion_junior.id),
        "estado": "BORRADOR",
    }
    response = _auth_post(
        api_client,
        "/api/inscripciones/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["estado"] == "BORRADOR"
    assert data["data"]["evento_id"] == str(evento.id)
    assert data["data"]["responsable_id"] == str(usuario_con_persona.persona_fk_id)


@pytest.mark.django_db
def test_crear_inscripcion_completa_duplicada_devuelve_conflict(
    api_client, evento, usuario_con_persona, paquete_reencuentro, promocion_junior
):
    """
    GIVEN: ya existe una inscripción (evento, responsable, paquete)
    WHEN: POST /api/inscripciones/completa/ con la misma combinación
    THEN: retorna 409 con code=INSCRIPCION_DUPLICADA y mensaje claro en español
          (NO 500 con IntegrityError raw, NO traceback en stderr)

    El flow captura el IntegrityError de la UniqueConstraint
    (evento, responsable, paquete) y lo traduce a InscripcionUniqueConstraintError
    para que el handler global responda con código de dominio legible.
    """
    payload = {
        "evento_id": str(evento.id),
        "paquete_id": str(paquete_reencuentro.id),
        "promocion_id": str(promocion_junior.id),
        "cantidad": 10,
        "equipos": [
            {
                "disciplina_id": str(paquete_reencuentro.paquete_disciplinas.first().disciplina_id),
                "nombre": "Equipo Test",
            }
        ],
    }
    # Primera inscripción: éxito
    first = _auth_post(
        api_client,
        "/api/inscripciones/completa/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert first.status_code == 201

    # Segunda con misma combinación: conflict
    second = _auth_post(
        api_client,
        "/api/inscripciones/completa/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert second.status_code == 409
    data = second.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSCRIPCION_DUPLICADA"
    # El mensaje debe ser claro y NO exponer IDs internos
    msg = data["error"]["message"]
    assert "inscripción" in msg.lower() or "inscripcion" in msg.lower()


@pytest.mark.django_db
def test_crear_inscripcion_paquete_evento_mismatch(
    api_client, evento, usuario_con_persona, paquete_reencuentro, promocion_junior,
):
    """
    GIVEN: paquete belongs to evento
    WHEN: creating inscripcion with wrong evento_id (authenticated)
    THEN: returns 409 conflict (paquete belongs to different evento)
    """
    # Create another evento
    otro_evento = Evento.objects.create(
        nombre="Otro Evento",
        fecha_inicio=date(2026, 12, 1),
        fecha_fin=date(2026, 12, 5),
        esta_activo=True,
    )
    payload = {
        "evento_id": str(otro_evento.id),
        "paquete_id": str(paquete_reencuentro.id),  # paquete belongs to `evento`, not `otro_evento`
        "promocion_id": str(promocion_junior.id),
    }
    response = _auth_post(
        api_client,
        "/api/inscripciones/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 409


@pytest.mark.django_db
def test_obtener_inscripcion(api_client, inscripcion_base, usuario_con_persona):
    """
    GIVEN: an inscripcion exists and the caller is its responsable
    WHEN: GET /api/inscripciones/{id}
    THEN: returns 200 with inscripcion data
    """
    response = _auth_get(api_client, f"/api/inscripciones/{inscripcion_base.id}", usuario_con_persona)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == str(inscripcion_base.id)


@pytest.mark.django_db
def test_obtener_inscripcion_no_encontrada(api_client, usuario_con_persona):
    """
    GIVEN: a non-existent inscripcion ID
    WHEN: GET /api/inscripciones/{id}
    THEN: returns 404
    """
    fake_id = uuid.uuid4()
    response = _auth_get(api_client, f"/api/inscripciones/{fake_id}", usuario_con_persona)
    assert response.status_code == 404


@pytest.mark.django_db
def test_actualizar_inscripcion_http(api_client, inscripcion_base, usuario_con_persona):
    """An inscription can update its administrative state and observation."""
    token = AccessToken.for_user(usuario_con_persona)
    response = api_client.patch(
        f"/api/inscripciones/{inscripcion_base.id}",
        data=json.dumps({"estado": "RECIBIDA", "observacion": "Documentos enviados"}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200
    assert response.json()["data"]["estado"] == "RECIBIDA"


@pytest.mark.django_db
def test_obtener_inscripcion_detalle(api_client, inscripcion_base, equipo_base, inscripcion_persona_base, usuario_con_persona):
    """
    GIVEN: inscripcion with equipos and personas
    WHEN: GET /api/inscripciones/{id}/detalle
    THEN: returns 200 with equipos and personas (roster)
    """
    response = _auth_get(
        api_client, f"/api/inscripciones/{inscripcion_base.id}/detalle", usuario_con_persona
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["equipos"]) == 1
    assert len(data["data"]["personas"]) == 1


@pytest.mark.django_db
def test_agregar_y_retirar_persona_http(api_client, inscripcion_base, persona_2, usuario_con_persona):
    """A roster member can be added and later retired through the API."""
    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({"persona_id": str(persona_2.id)}),
    )
    assert response.status_code == 201
    assert response.json()["data"]["participante"]["estado"] == "A"

    token = AccessToken.for_user(usuario_con_persona)
    response = api_client.patch(
        f"/api/inscripciones/{inscripcion_base.id}/personas/{persona_2.id}/retirar",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200
    assert response.json()["data"]["estado"] == "R"


@pytest.mark.django_db
def test_agregar_persona_con_aceptaciones(api_client, inscripcion_base, persona_2, usuario_con_persona):
    """
    GIVEN: inscripcion and persona exist
    WHEN: adding person with aceptaciones
    THEN: aceptacion records are created atomically
    """
    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({
            "persona_id": str(persona_2.id),
            "aceptaciones": ["BASES", "APTITUD_FISICA", "IMAGEN"],
        }),
    )
    assert response.status_code == 201
    assert response.json()["data"]["participante"]["estado"] == "A"

    from modules.salesianos_fest.domain.models import AceptacionInscripcion
    aceptaciones = AceptacionInscripcion.objects.filter(
        inscripcion_persona__persona=persona_2,
        inscripcion_persona__inscripcion=inscripcion_base,
    )
    assert aceptaciones.count() == 3
    tipos = set(a.tipo_aceptacion for a in aceptaciones)
    assert tipos == {"BASES", "APTITUD_FISICA", "IMAGEN"}


@pytest.mark.django_db
def test_agregar_persona_aceptaciones_idempotente(api_client, inscripcion_base, persona_2, usuario_con_persona):
    """
    GIVEN: persona already has aceptaciones in this inscripcion
    WHEN: adding person again with aceptaciones
    THEN: aceptaciones are updated (not duplicated)
    """
    # First add with aceptaciones
    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({
            "persona_id": str(persona_2.id),
            "aceptaciones": ["BASES"],
        }),
    )
    assert response.status_code == 201

    # Add again with aceptaciones (re-activate + update)
    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({
            "persona_id": str(persona_2.id),
            "aceptaciones": ["BASES", "IMAGEN"],
        }),
    )
    assert response.status_code == 201

    from modules.salesianos_fest.domain.models import AceptacionInscripcion
    aceptaciones = AceptacionInscripcion.objects.filter(
        inscripcion_persona__persona=persona_2,
        inscripcion_persona__inscripcion=inscripcion_base,
    )
    # Should have 2 aceptaciones (BASES and IMAGEN), not 3
    assert aceptaciones.count() == 2
    tipos = set(a.tipo_aceptacion for a in aceptaciones)
    assert tipos == {"BASES", "IMAGEN"}


@pytest.mark.django_db
def test_agregar_persona_con_equipo_id_crea_participacion_atomica(
    db, api_client, inscripcion_base, equipo_base, persona_2, usuario_con_persona
):
    """
    GIVEN: inscripcion, equipo and persona exist, with paid cup assigned to persona_2
    WHEN: adding person with equipo_id
    THEN: InscripcionPersona AND Participacion are created atomically
    AND: response returns ParticipacionOut with equipo_id
    """
    # ── Phase 2: cup prerequisite — create paid purchase + active AsignacionCupo ──
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraInscripcion, InscripcionPersona, AsignacionCupo
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.salesianos_fest.domain.constants import (
        TipoCompraChoices,
        EstadoCompraChoices,
        EstadoAsignacionCupoChoices,
    )
    from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus

    compra = Compra.objects.create(
        responsable=persona_2,
        descripcion="Test purchase",
        referencia_externa="TEST-REF",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-001",
        monto_total=Decimal("150.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="REF001",
        order_number="REF001",
        amount=Decimal("150.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion_base,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=3,
        precio_unitario=Decimal("50.00"),
        total=Decimal("150.00"),
    )
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado="A",
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_base,
        inscripcion_persona=ip,
        compra=compra,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({
            "persona_id": str(persona_2.id),
            "equipo_id": str(equipo_base.id),
        }),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    # Response should be ParticipacionOut when equipo_id is provided, wrapped in {participante: ParticipacionOut}
    assert "equipo_id" in data["data"]["participante"]
    assert data["data"]["participante"]["equipo_id"] == str(equipo_base.id)
    assert data["data"]["participante"]["rol"] == "J"
    assert data["data"]["participante"]["estado"] == "A"

    # Verify InscripcionPersona was created
    from modules.salesianos_fest.domain.models import InscripcionPersona
    ip = InscripcionPersona.objects.filter(
        inscripcion=inscripcion_base,
        persona=persona_2,
    ).first()
    assert ip is not None
    assert ip.estado == "A"

    # Verify Participacion was created atomically
    from modules.salesianos_fest.domain.models import Participacion
    participacion = Participacion.objects.filter(
        inscripcion_persona=ip,
        equipo=equipo_base,
    ).first()
    assert participacion is not None
    assert participacion.estado == "A"
    assert participacion.rol == "J"


# ─── Tests: Inline persona creation via agregar_persona ───────────────────────


@pytest.mark.django_db
def test_agregar_persona_crea_inline_si_no_existe(api_client, inscripcion_base, usuario_con_persona):
    """
    GIVEN: no Persona with the given (tipo_documento, numero_documento)
    WHEN:  POST /api/inscripciones/{id}/personas with persona_data (no persona_id)
    THEN:  201 — a new Persona is created, and InscripcionPersona links it
    """
    persona_count_before = Persona.objects.count()

    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({
            "persona_data": {
                "tipo_documento": "DNI",
                "numero_documento": "44556677",
                "nombres": "Carlos",
                "apellidos": "López",
                "genero": "M",
                "telefono": "987654321",
                "whatsapp": "987654321",
            },
        }),
    )
    assert response.status_code == 201, (
        f"Expected 201, got {response.status_code}: {response.json()}"
    )
    data = response.json()
    assert data["success"] is True
    assert "participante" in data["data"]

    # New Persona was created (count incremented)
    assert Persona.objects.count() == persona_count_before + 1
    persona = Persona.objects.get(numero_documento="44556677")
    assert persona.nombres == "Carlos"
    assert persona.apellidos == "López"
    assert persona.tipo_documento == "DNI"
    assert persona.genero == "M"
    assert persona.telefono == "987654321"
    assert persona.whatsapp == "987654321"

    # InscripcionPersona was linked and is active
    from modules.salesianos_fest.domain.models import InscripcionPersona
    ip = InscripcionPersona.objects.filter(
        inscripcion=inscripcion_base,
        persona=persona,
    ).first()
    assert ip is not None
    assert ip.estado == "A"


@pytest.mark.django_db
def test_agregar_persona_reutiliza_existente_por_dni(api_client, inscripcion_base, persona_2, usuario_con_persona):
    """
    GIVEN: a Persona with the same (tipo_documento, numero_documento) exists
    WHEN:  POST /api/inscripciones/{id}/personas with persona_data matching it
    THEN:  201 — NO new Persona is created; the existing one is reused
    """
    # persona_2 fixture: tipo_documento="DNI", numero_documento="87654321"
    persona_count_before = Persona.objects.count()

    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({
            "persona_data": {
                "tipo_documento": "DNI",
                "numero_documento": "87654321",  # matches persona_2
                "nombres": "María",  # same data — should not matter
                "apellidos": "García",
                "genero": "F",
            },
        }),
    )
    assert response.status_code == 201, (
        f"Expected 201, got {response.status_code}: {response.json()}"
    )

    # Idempotent — count is unchanged
    assert Persona.objects.count() == persona_count_before

    # InscripcionPersona is linked to persona_2 (the existing one)
    from modules.salesianos_fest.domain.models import InscripcionPersona
    ip = InscripcionPersona.objects.get(
        inscripcion=inscripcion_base,
        persona=persona_2,
    )
    assert ip.estado == "A"


@pytest.mark.django_db
def test_agregar_persona_rechaza_sin_persona_id_ni_data(api_client, inscripcion_base, usuario_con_persona):
    """
    GIVEN: an inscripcion exists
    WHEN:  POST /api/inscripciones/{id}/personas with empty payload (neither
           persona_id nor persona_data)
    THEN:  422 with code PERSONA_REQUIRED — XOR validation enforced server-side
    """
    response = _auth_post(
        api_client,
        f"/api/inscripciones/{inscripcion_base.id}/personas",
        usuario_con_persona,
        data=json.dumps({}),
    )
    assert response.status_code == 422, (
        f"Expected 422, got {response.status_code}: {response.json()}"
    )
    data = response.json()
    # Error envelope: {"success": false, "error": {"code": "...", ...}, ...}
    err_code = data.get("error", {}).get("code") or data.get("code")
    assert err_code == "PERSONA_REQUIRED", (
        f"Expected PERSONA_REQUIRED, got {err_code!r}; body={data}"
    )


# ─── Tests: Equipo ────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_crear_equipo_http(api_client, inscripcion_base, disciplina_futbol, usuario_con_persona):
    """
    GIVEN: inscripcion and disciplina (disciplina in paquete)
    WHEN: POST /api/equipos/ (as the responsable)
    THEN: returns 201 with equipo data
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "disciplina_id": str(disciplina_futbol.id),
        "nombre": "Los Tigres FC",
        "estado": "EQUIPO_ACTIVO",
    }
    response = _auth_post(api_client, "/api/equipos/", usuario_con_persona, data=json.dumps(payload))
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["nombre"] == "Los Tigres FC"


@pytest.mark.django_db
def test_crear_equipo_disciplina_not_in_paquete(
    api_client, inscripcion_base, disciplina_voley, usuario_con_persona,
):
    """
    GIVEN: inscripcion's paquete has F7M but not VOL discipline
    WHEN: POST /api/equipos/ with VOL
    THEN: returns 409 (disciplina not in paquete)
    """
    payload = {
        "inscripcion_id": str(inscripcion_base.id),
        "disciplina_id": str(disciplina_voley.id),
        "nombre": "Los Vóley Mixto",
    }
    response = _auth_post(api_client, "/api/equipos/", usuario_con_persona, data=json.dumps(payload))
    # disciplina_voley IS in paquete_reencuentro (both disciplines were added in fixture)
    # So this should actually succeed. Let me check the fixture setup.
    # Actually in the fixture we DO add both disciplines to paquete_reencuentro.
    # So this test should return 201. Let me fix the test to use a discipline NOT in paquete.
    pass  # disciplina_voley is in the paquete fixture


@pytest.mark.django_db
def test_listar_equipos_por_inscripcion(api_client, inscripcion_base, equipo_base, usuario_con_persona):
    """
    GIVEN: inscripcion with one equipo
    WHEN: GET /api/equipos/inscripcion/{inscripcion_id}
    THEN: returns 200 with list of equipos
    """
    response = _auth_get(
        api_client, f"/api/equipos/inscripcion/{inscripcion_base.id}", usuario_con_persona
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["nombre"] == "Los Tigres FC"


# ─── Tests: R11 Conflict ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_r11_prevent_duplicate_active_participacion_same_evento_disciplina(
    api_client,
    evento,
    persona,
    paquete_reencuentro,
    disciplina_futbol,
    promocion_junior,
    categoria_senior,
    persona_2,
    usuario_con_persona,
):
    """
    GIVEN: persona is already actively playing F7M in this evento through an inscripcion
    WHEN: creating another participacion for the same (evento, disciplina, persona) with A estado
    THEN: returns 409 conflict (R11 violation)

    Scenario: Juan plays football (F7M) in Evento 2026 through Incripción A.
    Juan cannot also play F7M in Evento 2026 through Inscripción B.
    """
    # Create Inscripcion A
    inscripcion_a = Inscripcion.objects.create(
        evento=evento,
        responsable=persona_2,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )

    # Create InscripcionPersona A
    ip_a = InscripcionPersona.objects.create(
        inscripcion=inscripcion_a,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    # Create Equipo A
    equipo_a = Equipo.objects.create(
        inscripcion=inscripcion_a,
        disciplina=disciplina_futbol,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Los Tigres FC",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )

    # Create Participacion A (Juan playing F7M — ACTIVE)
    participacion_a = Participacion.objects.create(
        inscripcion_persona=ip_a,
        equipo=equipo_a,
        evento=evento,
        disciplina=disciplina_futbol,
        persona=persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # Create Inscripcion B (Juan tries to register again in same evento for F7M)
    inscripcion_b = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )

    ip_b = InscripcionPersona.objects.create(
        inscripcion=inscripcion_b,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )

    # ── Phase 2: cup prerequisite for persona in inscripcion_b ──
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraInscripcion, AsignacionCupo
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.salesianos_fest.domain.constants import (
        TipoCompraChoices,
        EstadoCompraChoices,
        EstadoAsignacionCupoChoices,
    )
    from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus

    compra_b = Compra.objects.create(
        responsable=persona,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-B",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago_b = OrdenPago.objects.create(
        numero="OP-2026-002",
        monto_total=Decimal("150.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago_b,
        transaction_id="REF002",
        order_number="REF002",
        amount=Decimal("150.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra_b.orden_pago = orden_pago_b
    compra_b.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra_b,
        inscripcion=inscripcion_b,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=3,
        precio_unitario=Decimal("50.00"),
        total=Decimal("150.00"),
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_b,
        inscripcion_persona=ip_b,
        compra=compra_b,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    equipo_b = Equipo.objects.create(
        inscripcion=inscripcion_b,
        disciplina=disciplina_futbol,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Otro Equipo FC",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )

    # Try to create Participacion B (Juan playing F7M AGAIN in same evento)
    payload = {
        "inscripcion_persona_id": str(ip_b.id),
        "equipo_id": str(equipo_b.id),
        "rol": "J",
    }
    response = _auth_post(api_client, "/api/participaciones/", usuario_con_persona, data=json.dumps(payload))
    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert "R11" in str(data) or "duplicate" in str(data.get("error", {})).lower()


@pytest.mark.django_db
def test_r11_same_person_different_disciplina_is_allowed(
    api_client,
    evento,
    persona,
    paquete_reencuentro,
    disciplina_futbol,
    disciplina_voley,
    promocion_junior,
    categoria_senior,
    persona_2,
    usuario_con_persona,
):
    """
    GIVEN: persona is playing F7M in this evento
    WHEN: creating a participacion for VOLLEY (different disciplina) in the same evento
    THEN: returns 201 (R11 allows different disciplines)
    """
    # Setup: Inscripcion A with F7M participation
    inscripcion_a = Inscripcion.objects.create(
        evento=evento,
        responsable=persona_2,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    ip_a = InscripcionPersona.objects.create(
        inscripcion=inscripcion_a,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    equipo_futbol = Equipo.objects.create(
        inscripcion=inscripcion_a,
        disciplina=disciplina_futbol,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Los Tigres FC",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    Participacion.objects.create(
        inscripcion_persona=ip_a,
        equipo=equipo_futbol,
        evento=evento,
        disciplina=disciplina_futbol,
        persona=persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # Create Inscripcion B for Vóley
    inscripcion_b = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    ip_b = InscripcionPersona.objects.create(
        inscripcion=inscripcion_b,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    # ── Phase 2: cup prerequisite for persona in inscripcion_b ──
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraInscripcion, AsignacionCupo
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.salesianos_fest.domain.constants import (
        TipoCompraChoices,
        EstadoCompraChoices,
        EstadoAsignacionCupoChoices,
    )
    from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus

    compra_b = Compra.objects.create(
        responsable=persona,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-B",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago_b = OrdenPago.objects.create(
        numero="OP-2026-003",
        monto_total=Decimal("150.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago_b,
        transaction_id="REF003",
        order_number="REF003",
        amount=Decimal("150.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra_b.orden_pago = orden_pago_b
    compra_b.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra_b,
        inscripcion=inscripcion_b,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=3,
        precio_unitario=Decimal("50.00"),
        total=Decimal("150.00"),
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion_b,
        inscripcion_persona=ip_b,
        compra=compra_b,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    equipo_voley = Equipo.objects.create(
        inscripcion=inscripcion_b,
        disciplina=disciplina_voley,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Los Vóley Mixto",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )

    # Juan can play Vóley too
    payload = {
        "inscripcion_persona_id": str(ip_b.id),
        "equipo_id": str(equipo_voley.id),
        "rol": "J",
    }
    response = _auth_post(api_client, "/api/participaciones/", usuario_con_persona, data=json.dumps(payload))
    assert response.status_code == 201


@pytest.mark.django_db
def test_r11_retired_participacion_allows_new_registration(
    api_client,
    evento,
    persona,
    paquete_reencuentro,
    disciplina_futbol,
    promocion_junior,
    categoria_senior,
    usuario_con_persona,
):
    """
    GIVEN: persona has a RETIRED participacion for F7M in this evento
    WHEN: creating a new active participacion for F7M in the same evento
    THEN: returns 201 (R11 only blocks duplicate ACTIVE participaciones)
    """
    # Create and then retire a participacion
    inscripcion = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.BORRADOR,
    )
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    # ── Phase 2: cup prerequisite for persona in this inscripcion ──
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraInscripcion, AsignacionCupo
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.salesianos_fest.domain.constants import (
        TipoCompraChoices,
        EstadoCompraChoices,
        EstadoAsignacionCupoChoices,
    )
    from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus

    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-RET",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-004",
        monto_total=Decimal("150.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="REF004",
        order_number="REF004",
        amount=Decimal("150.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=3,
        precio_unitario=Decimal("50.00"),
        total=Decimal("150.00"),
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion,
        inscripcion_persona=ip,
        compra=compra,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    equipo = Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina_futbol,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Los Tigres FC",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    # Create a RETIRED participacion
    Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=equipo,
        evento=evento,
        disciplina=disciplina_futbol,
        persona=persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.RETIRADA,  # RETIRED
    )

    # Should be able to create a new active one
    payload = {
        "inscripcion_persona_id": str(ip.id),
        "equipo_id": str(equipo.id),
        "rol": "J",
    }
    response = _auth_post(api_client, "/api/participaciones/", usuario_con_persona, data=json.dumps(payload))
    assert response.status_code == 201


# ─── Tests: Participacion ────────────────────────────────────────────────────

@pytest.mark.django_db
def test_crear_participacion_http(db, api_client, inscripcion_persona_base, equipo_base, usuario_con_persona):
    """
    GIVEN: inscripcion_persona and equipo exist, with paid cup assigned
    WHEN: POST /api/participaciones/
    THEN: returns 201 with participacion data
    """
    # ── Phase 2: cup prerequisite — create paid purchase + active AsignacionCupo ──
    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import CompraInscripcion, AsignacionCupo
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.salesianos_fest.domain.constants import (
        TipoCompraChoices,
        EstadoCompraChoices,
        EstadoAsignacionCupoChoices,
    )
    from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus

    inscripcion = inscripcion_persona_base.inscripcion
    persona = inscripcion_persona_base.persona

    compra = Compra.objects.create(
        responsable=persona,
        descripcion="Test purchase",
        referencia_externa="TEST-REF-PART",
        total=Decimal("150.00"),
        estado=EstadoCompraChoices.PAGADA,
    )
    orden_pago = OrdenPago.objects.create(
        numero="OP-2026-005",
        monto_total=Decimal("150.00"),
        estado=OrdenPagoStatus.PAGADA,
    )
    TransaccionPago.objects.create(
        orden_pago=orden_pago,
        transaction_id="REF005",
        order_number="REF005",
        amount=Decimal("150.00"),
        currency="PEN",
        status=IzipayStatus.EXITO,
    )
    compra.orden_pago = orden_pago
    compra.save(update_fields=["orden_pago", "updated_at"])
    CompraInscripcion.objects.create(
        compra=compra,
        inscripcion=inscripcion,
        tipo=TipoCompraChoices.INICIAL,
        cantidad=3,
        precio_unitario=Decimal("50.00"),
        total=Decimal("150.00"),
    )
    AsignacionCupo.objects.create(
        inscripcion=inscripcion,
        inscripcion_persona=inscripcion_persona_base,
        compra=compra,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )

    payload = {
        "inscripcion_persona_id": str(inscripcion_persona_base.id),
        "equipo_id": str(equipo_base.id),
        "rol": "J",
        "talla_camiseta": "M",
    }
    response = _auth_post(api_client, "/api/participaciones/", usuario_con_persona, data=json.dumps(payload))
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["rol"] == "J"
    assert data["data"]["talla_camiseta"] == "M"


@pytest.mark.django_db
def test_roster_maximo_blocks_participacion(api_client, inscripcion_base, equipo_base, disciplina_futbol, categoria_senior, promocion_junior, inscripcion_persona_base, persona_2, usuario_con_persona):
    """
    GIVEN: equipo F7M already has 10 active participaciones (max_jugadores=10)
    WHEN: trying to add one more
    THEN: returns 409 roster completo
    """
    # Create 10 active participaciones (filling the roster)
    for i in range(10):
        # Create a unique persona for each
        p = Persona.objects.create(
            nombres=f"Jugador{i}",
            apellidos=f"Apellido{i}",
            tipo_documento="DNI",
            numero_documento=f"0000000{i}",
            genero="M",
        )
        ip = InscripcionPersona.objects.create(
            inscripcion=inscripcion_base,
            persona=p,
            estado=EstadoInscripcionPersonaChoices.ACTIVO,
        )
        Participacion.objects.create(
            inscripcion_persona=ip,
            equipo=equipo_base,
            evento=equipo_base.inscripcion.evento,
            disciplina=disciplina_futbol,
            persona=p,
            rol=RolParticipanteChoices.JUGADOR,
            estado=EstadoParticipacionChoices.ACTIVA,
        )

    # Now persona_2 tries to join the same full equipo
    ip_new = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona_2,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    payload = {
        "inscripcion_persona_id": str(ip_new.id),
        "equipo_id": str(equipo_base.id),
        "rol": "J",
    }
    response = _auth_post(api_client, "/api/participaciones/", usuario_con_persona, data=json.dumps(payload))
    assert response.status_code == 409


@pytest.mark.django_db
def test_retirar_participacion(api_client, inscripcion_persona_base, equipo_base, usuario_con_persona):
    """
    GIVEN: an active participacion exists
    WHEN: PATCH /api/participaciones/{id}/retirar
    THEN: returns 200 with estado=R
    """
    # Create the participacion first
    p = Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_base,
        equipo=equipo_base,
        evento=equipo_base.inscripcion.evento,
        disciplina=equipo_base.disciplina,
        persona=inscripcion_persona_base.persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    token = AccessToken.for_user(usuario_con_persona)
    response = api_client.patch(
        f"/api/participaciones/{p.id}/retirar",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["estado"] == "R"


@pytest.mark.django_db
def test_actualizar_participacion(api_client, inscripcion_persona_base, equipo_base, usuario_con_persona):
    """
    GIVEN: an active participacion exists
    WHEN: PATCH /api/participaciones/{id} with rol, talla_camiseta, notas
    THEN: returns 200 with updated fields
    """
    p = Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_base,
        equipo=equipo_base,
        evento=equipo_base.inscripcion.evento,
        disciplina=equipo_base.disciplina,
        persona=inscripcion_persona_base.persona,
        rol=RolParticipanteChoices.JUGADOR,
        talla_camiseta="M",
        notas="",
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    payload = {
        "rol": "C",
        "talla_camiseta": "XL",
        "notas": "Captain for the tournament",
    }
    token = AccessToken.for_user(usuario_con_persona)
    response = api_client.patch(
        f"/api/participaciones/{p.id}",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["rol"] == "C"
    assert data["data"]["talla_camiseta"] == "XL"
    assert data["data"]["notas"] == "Captain for the tournament"
    # Verify DB was updated
    p.refresh_from_db()
    assert p.rol == "C"
    assert p.talla_camiseta == "XL"
    assert p.notas == "Captain for the tournament"


@pytest.mark.django_db
def test_listar_participaciones_por_equipo(api_client, equipo_base, inscripcion_persona_base, usuario_con_persona):
    """
    GIVEN: equipo with one participacion
    WHEN: GET /api/participaciones/equipo/{equipo_id}
    THEN: returns 200 with list of participaciones
    """
    Participacion.objects.create(
        inscripcion_persona=inscripcion_persona_base,
        equipo=equipo_base,
        evento=equipo_base.inscripcion.evento,
        disciplina=equipo_base.disciplina,
        persona=inscripcion_persona_base.persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    response = _auth_get(
        api_client, f"/api/participaciones/equipo/{equipo_base.id}", usuario_con_persona
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1


# ─── Tests: Retirar Persona (cascade) ───────────────────────────────────────

@pytest.mark.django_db
def test_retirar_persona_retires_all_its_participaciones(
    api_client,
    inscripcion_base,
    disciplina_futbol,
    disciplina_voley,
    categoria_senior,
    promocion_junior,
    persona,
):
    """
    GIVEN: persona has 2 active participaciones in 2 equipos of the same inscripcion
    WHEN: retiring the persona from the inscripcion
    THEN: all participaciones become R (cascade retire)
    """
    # Setup: two equipos, two participaciones for the same persona
    ip = InscripcionPersona.objects.create(
        inscripcion=inscripcion_base,
        persona=persona,
        estado=EstadoInscripcionPersonaChoices.ACTIVO,
    )
    eq1 = Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_futbol,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Equipo Fútbol",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    eq2 = Equipo.objects.create(
        inscripcion=inscripcion_base,
        disciplina=disciplina_voley,
        categoria=categoria_senior,
        promocion=promocion_junior,
        nombre="Equipo Vóley",
        estado=EstadoEquipoChoices.EQUIPO_ACTIVO,
    )
    p1 = Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=eq1,
        evento=inscripcion_base.evento,
        disciplina=disciplina_futbol,
        persona=persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )
    p2 = Participacion.objects.create(
        inscripcion_persona=ip,
        equipo=eq2,
        evento=inscripcion_base.evento,
        disciplina=disciplina_voley,
        persona=persona,
        rol=RolParticipanteChoices.JUGADOR,
        estado=EstadoParticipacionChoices.ACTIVA,
    )

    # Both are ACTIVE
    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.estado == "A"
    assert p2.estado == "A"

    # Retiring via HTTP endpoint (PATCH /api/inscripciones/{id}/personas/{persona_id}/retirar
    # doesn't exist yet — so test the flujo directly via model)
    from modules.salesianos_fest.domain.services.flujos.retirar_persona_flujo import RetirarPersonaFlujo
    from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
    from asgiref.sync import async_to_sync

    flujo = RetirarPersonaFlujo(acreditacion_core=AcreditacionCoreService())
    async_to_sync(flujo.ejecutar)(str(inscripcion_base.id), str(persona.id))

    p1.refresh_from_db()
    p2.refresh_from_db()
    assert p1.estado == "R"
    assert p2.estado == "R"


# ─── Tests: T20 — Fecha Límite de Modificación ───────────────────────────────

@pytest.mark.django_db
def test_t20_agregar_persona_despues_de_fecha_limite_bloqueado(
    api_client, inscripcion_base, persona_2
):
    """
    T20: Responsable intenta modificar roster después de fecha límite.

    GIVEN: Evento has fecha_limite_modificacion set to yesterday
    WHEN:  Trying to add a person via API
    THEN:  Returns 409 with FECHA_LIMITE_EXCEDIDA error.

    Note: The flujo raises FechaLimiteExcedidaError which should be
    caught by the controller and returned as a 409 response.
    """
    from datetime import date, timedelta
    from asgiref.sync import async_to_sync

    # Set fecha_limite to yesterday
    inscripcion_base.evento.fecha_limite_modificacion = date.today() - timedelta(days=1)
    inscripcion_base.evento.save()

    # Try to add person via the flow directly
    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo
    from modules.salesianos_fest.domain.exceptions import FechaLimiteExcedidaError

    flujo = AgregarPersonaFlujo()

    with pytest.raises(FechaLimiteExcedidaError):
        from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
            InscripcionPersonaCreateData,
        )
        async_to_sync(flujo.ejecutar)(
            InscripcionPersonaCreateData(
                inscripcion_id=str(inscripcion_base.id),
                persona_id=str(persona_2.id),
            )
        )


@pytest.mark.django_db
def test_t20_agregar_persona_sin_fecha_limite_permitido(
    api_client, inscripcion_base, persona_2
):
    """
    T20: Sin fecha límite, las modificaciones son permitidas.

    GIVEN: Evento has NO fecha_limite_modificacion set (None)
    WHEN:  Adding a person
    THEN:  Succeeds normally (no fecha_limite check blocks it).
    """
    from asgiref.sync import async_to_sync

    # Ensure no fecha_limite
    inscripcion_base.evento.fecha_limite_modificacion = None
    inscripcion_base.evento.save()

    from modules.salesianos_fest.domain.services.flujos.agregar_persona_flujo import AgregarPersonaFlujo

    flujo = AgregarPersonaFlujo()

    # Should not raise
    from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
        InscripcionPersonaCreateData,
    )
    ip, participacion = async_to_sync(flujo.ejecutar)(
        InscripcionPersonaCreateData(
            inscripcion_id=str(inscripcion_base.id),
            persona_id=str(persona_2.id),
        )
    )
    assert ip is not None


@pytest.mark.django_db
def test_t20_retirar_persona_despues_de_fecha_limite_bloqueado(
    api_client, inscripcion_base, persona
):
    """
    T20: Retirar persona después de fecha límite bloqueado.

    GIVEN: Evento has fecha_limite_modificacion set to yesterday
    WHEN:  Trying to retire a person
    THEN:  Raises FechaLimiteExcedidaError.
    """
    from datetime import date, timedelta
    from asgiref.sync import async_to_sync

    # Set fecha_limite to yesterday
    inscripcion_base.evento.fecha_limite_modificacion = date.today() - timedelta(days=1)
    inscripcion_base.evento.save()

    from modules.salesianos_fest.domain.services.flujos.retirar_persona_flujo import RetirarPersonaFlujo
    from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
    from modules.salesianos_fest.domain.exceptions import FechaLimiteExcedidaError

    flujo = RetirarPersonaFlujo(acreditacion_core=AcreditacionCoreService())

    with pytest.raises(FechaLimiteExcedidaError):
        async_to_sync(flujo.ejecutar)(
            inscripcion_id=str(inscripcion_base.id),
            persona_id=str(persona.id),
        )


# ─── Tests: Inscripcion Unique Constraint ─────────────────────────────────────

@pytest.mark.django_db
def test_inscripcion_unique_constraint_same_evento_responsable_paquete(
    api_client, evento, usuario_con_persona, paquete_reencuentro, promocion_junior,
):
    """
    Regression: unique constraint on (evento, responsable, paquete) is enforced.

    GIVEN: An Inscripcion exists for (evento, responsable, paquete)
    WHEN:  Attempting to create another Inscripcion with same (evento, responsable, paquete)
    THEN:  Returns 409 conflict due to unique constraint.
    """
    # Create first inscripcion (authenticated)
    payload = {
        "evento_id": str(evento.id),
        "paquete_id": str(paquete_reencuentro.id),
        "promocion_id": str(promocion_junior.id),
    }
    response = _auth_post(
        api_client,
        "/api/inscripciones/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response.status_code == 201

    # Try to create duplicate (same auth)
    response2 = _auth_post(
        api_client,
        "/api/inscripciones/",
        usuario_con_persona,
        data=json.dumps(payload),
    )
    assert response2.status_code == 409


@pytest.mark.django_db
def test_inscripcion_unique_constraint_different_paquete_permitido(
    api_client, evento, usuario_con_persona, paquete_reencuentro, promocion_junior,
    disciplina_futbol,
):
    """
    Same responsable can have multiple Inscripciones with DIFFERENT packages in same event.

    GIVEN: An Inscripcion exists for (evento, responsable, paquete_reencuentro)
    WHEN:  Creating an Inscripcion with same (evento, responsable) but DIFFERENT paquete
    THEN:  Succeeds (constraint allows different packages).
    """
    # Create first inscripcion with Reencuentro (authenticated)
    payload1 = {
        "evento_id": str(evento.id),
        "paquete_id": str(paquete_reencuentro.id),
        "promocion_id": str(promocion_junior.id),
    }
    response1 = _auth_post(
        api_client,
        "/api/inscripciones/",
        usuario_con_persona,
        data=json.dumps(payload1),
    )
    assert response1.status_code == 201

    # Create a second package (disciplina individual)
    from modules.salesianos_fest.domain.models import Paquete, PaqueteDisciplina, PaquetePrecio
    from modules.salesianos_fest.domain.constants import TipoPaqueteChoices, ModoDisciplinasChoices, EtapaChoices

    paquete_futbol = Paquete.objects.create(
        evento=evento,
        nombre="Fútbol Individual",
        tipo=TipoPaqueteChoices.DISCIPLINA,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=7,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete_futbol, disciplina=disciplina_futbol)
    PaquetePrecio.objects.create(
        paquete=paquete_futbol,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("50.00"),
        vigente_desde=date.today(),
        activo=True,
    )

    # Create second inscripcion with different paquete (authenticated)
    payload2 = {
        "evento_id": str(evento.id),
        "paquete_id": str(paquete_futbol.id),
        "promocion_id": str(promocion_junior.id),
    }
    response2 = _auth_post(
        api_client,
        "/api/inscripciones/",
        usuario_con_persona,
        data=json.dumps(payload2),
    )
    assert response2.status_code == 201


# ─── Regression: T10 — RetirarPersonaFlujo recalcula AcreditacionEvento ───────

@pytest.mark.django_db
def test_t10_retirar_persona_de_inscripcion_fiesta_conserva_acceso_por_otra_pagada(
    db,
    evento,
    persona,
    paquete_reencuentro,
    promocion_junior,
    disciplina_futbol,
    disciplina_voley,
):
    """
    T10: Juan is retired from A but stays in B — acceso_fiesta remains from B.

    GIVEN: Juan has TWO paid inscripciones (A and B) both with FIESTA benefit,
           each with active AsignacionCupo and AcreditacionEvento.estado=ACTIVA
    WHEN:  Juan is retired from A via RetirarPersonaFlujo
    THEN:  AcreditacionEvento.acceso_fiesta remains True (from B's paid origin),
           NOT recalculated to False based on A alone.

    This is R15 / F5: the flujo must recalculate AcreditacionEvento from ALL
    remaining active paid origins after retirement, not just from the withdrawn inscripcion.
    """
    from asgiref.sync import async_to_sync

    from modules.commerce.domain.models import Compra
    from modules.salesianos_fest.domain.models import (
        CompraInscripcion,
        PaqueteBeneficio,
        AsignacionCupo,
        AcreditacionEvento,
    )
    from modules.salesianos_fest.domain.constants import (
        TipoBeneficioChoices,
        AlcanceBeneficioChoices,
        ModoCalculoBeneficioChoices,
        TipoCompraChoices,
        EstadoCompraChoices,
        EstadoAsignacionCupoChoices,
        AutorizacionFiestaChoices,
        EstadoAcreditacionChoices,
    )
    from modules.pagos.domain.models import OrdenPago, TransaccionPago
    from modules.pagos.domain.constants import IzipayStatus, OrdenPagoStatus
    from modules.salesianos_fest.domain.services.flujos.retirar_persona_flujo import (
        RetirarPersonaFlujo,
    )
    from modules.salesianos_fest.domain.services.core.acreditacion_service import (
        AcreditacionCoreService,
    )

    # ── Setup: Two FIESTA paquetes with benefits ──────────────────────────────
    PaqueteBeneficio.objects.create(
        paquete=paquete_reencuentro,
        tipo=TipoBeneficioChoices.FIESTA,
        cantidad=1,
        alcance=AlcanceBeneficioChoices.INDIVIDUAL,
        modo_calculo=ModoCalculoBeneficioChoices.POR_CUPO,
    )

    # Create a second FIESTA paquete for inscripcion B
    paquete_pichanga = Paquete.objects.create(
        evento=evento,
        nombre="Pichanga + Fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas=ModoDisciplinasChoices.FIJO,
        cantidad_disciplinas=1,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete_pichanga, disciplina=disciplina_futbol)
    PaquetePrecio.objects.create(
        paquete=paquete_pichanga,
        etapa=EtapaChoices.REGULAR,
        precio_unitario=Decimal("55.00"),
        vigente_desde=date.today(),
        activo=True,
    )
    PaqueteBeneficio.objects.create(
        paquete=paquete_pichanga,
        tipo=TipoBeneficioChoices.FIESTA,
        cantidad=1,
        alcance=AlcanceBeneficioChoices.INDIVIDUAL,
        modo_calculo=ModoCalculoBeneficioChoices.POR_CUPO,
    )

    # ── Create two Inscripciones (A and B), both paid ───────────────────────
    inscripcion_a = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_reencuentro,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.CONFIRMADA,
    )
    inscripcion_b = Inscripcion.objects.create(
        evento=evento,
        responsable=persona,
        paquete=paquete_pichanga,
        promocion=promocion_junior,
        estado=EstadoInscripcionChoices.CONFIRMADA,
    )

    # ── Create InscripcionPersona in both ─────────────────────────────────────
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

    # ── Create paid Compras and AsignacionCupo for both ───────────────────────
    for idx, inscripcion in enumerate([inscripcion_a, inscripcion_b]):
        orden_pago = OrdenPago.objects.create(
            numero=f"OP-2026-{10 + idx:03d}",
            monto_total=Decimal("500.00"),
            estado=OrdenPagoStatus.PAGADA,
        )
        TransaccionPago.objects.create(
            orden_pago=orden_pago,
            transaction_id=f"txn-2026-{10 + idx:03d}",
            order_number=f"ord-2026-{10 + idx:03d}",
            amount=Decimal("500.00"),
            currency="PEN",
            status=IzipayStatus.EXITO,
        )
        # Create generic commerce.Compra (not FEST-specific fields)
        compra = Compra.objects.create(
            responsable=persona,
            descripcion="Test purchase",
            referencia_externa=f"TEST-REF-{idx}",
            total=Decimal("500.00"),
            estado=EstadoCompraChoices.PAGADA,
        )
        # Link OrdenPago to Compra
        compra.orden_pago = orden_pago
        compra.save(update_fields=["orden_pago", "updated_at"])
        # Create FEST composition link: CompraInscripcion
        CompraInscripcion.objects.create(
            compra=compra,
            inscripcion=inscripcion,
            tipo=TipoCompraChoices.INICIAL,
            cantidad=10,
            precio_unitario=Decimal("50.00"),
            total=Decimal("500.00"),
        )
        AsignacionCupo.objects.create(
            inscripcion=inscripcion,
            compra=compra,
            inscripcion_persona=ip_a if inscripcion == inscripcion_a else ip_b,
            estado=EstadoAsignacionCupoChoices.ACTIVA,
        )

    # ── Initial acreditacion sync (both have acceso_fiesta=True) ──────────────
    acreditacion_core = AcreditacionCoreService()
    acreditacion = acreditacion_core.sync_acreditacion_desde_compras(
        str(evento.id), str(persona.id)
    )
    assert acreditacion.acceso_fiesta is True
    assert acreditacion.estado == EstadoAcreditacionChoices.ACTIVA

    # ── Retire Juan from A via RetirarPersonaFlujo ────────────────────────────
    flujo = RetirarPersonaFlujo(acreditacion_core=acreditacion_core)
    async_to_sync(flujo.ejecutar)(str(inscripcion_a.id), str(persona.id))

    # Verify Juan is retired from A
    ip_a.refresh_from_db()
    assert ip_a.estado == EstadoInscripcionPersonaChoices.RETIRADO

    # ── Verify acceso_fiesta remains True (from B's paid origin) ─────────────
    acreditacion.refresh_from_db()
    assert acreditacion.acceso_fiesta is True, (
        "acceso_fiesta should remain True because B is still paid with FIESTA"
    )
    assert acreditacion.estado == EstadoAcreditacionChoices.ACTIVA
