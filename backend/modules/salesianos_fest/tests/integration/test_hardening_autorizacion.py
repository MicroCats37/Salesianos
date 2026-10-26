"""
Integration tests for the Phase 0 security hardening of the FEST endpoints.

Covers the authorization contract of every endpoint touched by the hardening:

- 401 `AUTHENTICATION_REQUIRED` for anonymous callers.
- 403 `ACTION_NOT_ALLOWED` for an authenticated non-owner / non-admin.
- 200/201 for the responsable of the inscripcion and for a Django admin.
- No mutation whatsoever when the call is denied.
- No credential leakage in the response body (the live QR never travels in a
  general read payload).

The HTTP client is `django.test.Client`: the controllers are async and this is
the pattern already established by the rest of the module
(`contract/django-app-architecture-contract.md` §2.1 — `ninja.testing.TestClient`
must NOT be used with async controllers).
"""
import json
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from ninja_jwt.tokens import AccessToken

from modules.commerce.domain.models import Compra
from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
    EstadoInscripcionChoices,
    ModalidadChoices,
    TipoPaqueteChoices,
)
from modules.salesianos_fest.domain.models import (
    AcreditacionEvento,
    AsignacionCupo,
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
from modules.salesianos_fest.tests.factories import (
    make_acreditacion_override_payload,
    make_actualizar_inscripcion_payload,
    make_equipo_payload,
)
from modules.usuarios.domain.models.persona import Persona


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def api_client(db):
    """Django test client — handles the async controllers in the test transaction."""
    return Client()


@pytest.fixture
def evento(db):
    """Activo evento of the test."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def disciplina(db):
    """Disciplina with a minimum roster."""
    return Disciplina.objects.create(
        nombre="Fútbol 7 Masculino",
        sigla="F7M",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=7,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def promocion(db):
    """Promocion of the test."""
    return Promocion.objects.create(anio=2012, nombre="Junior", activa=True)


@pytest.fixture
def paquete(db, evento, disciplina):
    """Paquete of the test (with the disciplina linked, as the business rule requires)."""
    paquete = Paquete.objects.create(
        evento=evento,
        nombre="Reencuentro + Fiesta",
        descripcion="Pack con fiesta",
        tipo=TipoPaqueteChoices.PACK,
        modo_disciplinas="ELEGIBLE",
        cantidad_disciplinas=1,
        minimo_compra_inicial=10,
        activo=True,
    )
    PaquetePrecio.objects.create(
        paquete=paquete,
        etapa="REGULAR",
        precio_unitario=Decimal("50.00"),
        vigente_desde=date.today(),
        vigente_hasta=None,
        activo=True,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina)
    return paquete


@pytest.fixture
def responsable(db):
    """Persona that owns the inscripcion."""
    return Persona.objects.create(
        nombres="Juan",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="12345678",
        genero="M",
    )


@pytest.fixture
def persona_ajena(db):
    """Persona that does NOT own the inscripcion."""
    return Persona.objects.create(
        nombres="María",
        apellidos="García",
        tipo_documento="DNI",
        numero_documento="87654321",
        genero="F",
    )


@pytest.fixture
def usuario_responsable(db, responsable):
    """Authenticated user linked to the responsable persona."""
    User = get_user_model()
    return User.objects.create_user(
        username="responsable",
        email="responsable@example.com",
        password="testpass123",
        persona_fk=responsable,
    )


@pytest.fixture
def usuario_ajeno(db, persona_ajena):
    """Authenticated user linked to an unrelated persona."""
    User = get_user_model()
    return User.objects.create_user(
        username="ajeno",
        email="ajeno@example.com",
        password="testpass123",
        persona_fk=persona_ajena,
    )


@pytest.fixture
def usuario_admin(db, persona_ajena):
    """Authenticated Django admin (is_staff AND is_superuser)."""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
        persona_fk=persona_ajena,
    )


@pytest.fixture
def usuario_tercero(db):
    """Authenticated user that is neither the responsable nor the accredited person."""
    persona = Persona.objects.create(
        nombres="Pedro",
        apellidos="Torres",
        tipo_documento="DNI",
        numero_documento="11223344",
        genero="M",
    )
    User = get_user_model()
    return User.objects.create_user(
        username="tercero",
        email="tercero@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def inscripcion(db, evento, responsable, paquete, promocion):
    """Inscripcion owned by the responsable."""
    return Inscripcion.objects.create(
        evento=evento,
        responsable=responsable,
        paquete=paquete,
        promocion=promocion,
        estado=EstadoInscripcionChoices.RECIBIDA,
        observacion="",
    )


@pytest.fixture
def equipo(db, inscripcion, disciplina):
    """Equipo inside the inscripcion."""
    return Equipo.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        nombre="Los Tigres FC",
        estado="EQUIPO_ACTIVO",
    )


@pytest.fixture
def inscripcion_persona(db, inscripcion, persona_ajena):
    """Roster member of the inscripcion."""
    return InscripcionPersona.objects.create(
        inscripcion=inscripcion,
        persona=persona_ajena,
        estado="A",
    )


@pytest.fixture
def participacion(db, inscripcion_persona, equipo, evento, disciplina, persona_ajena):
    """Active participation of the roster member."""
    return Participacion.objects.create(
        inscripcion_persona=inscripcion_persona,
        equipo=equipo,
        evento=evento,
        disciplina=disciplina,
        persona=persona_ajena,
        rol="J",
        talla_camiseta="M",
        estado="A",
    )


@pytest.fixture
def compra(db, responsable):
    """Paid purchase that backs the cup assignment."""
    return Compra.objects.create(
        responsable=responsable,
        descripcion="Compra de prueba",
        referencia_externa="TEST-HARDENING-001",
        total=Decimal("500.00"),
        estado=EstadoCompraChoices.PAGADA,
    )


@pytest.fixture
def asignacion(db, inscripcion, compra, inscripcion_persona):
    """Cup assignment of the roster member."""
    return AsignacionCupo.objects.create(
        inscripcion=inscripcion,
        compra=compra,
        inscripcion_persona=inscripcion_persona,
        estado=EstadoAsignacionCupoChoices.ACTIVA,
    )


@pytest.fixture
def acreditacion(db, evento, persona_ajena):
    """Accreditation of the roster member."""
    return AcreditacionEvento.objects.create(
        evento=evento,
        persona=persona_ajena,
        estado="ACTIVA",
        acceso_fiesta=True,
        autorizacion_fiesta=AutorizacionFiestaChoices.AUTOMATICA,
    )


# ── Auth helpers ────────────────────────────────────────────────────────────


def _auth_header(user) -> dict:
    """Build the Authorization header of an authenticated user."""
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _auth_get(client, path, user):
    return client.get(path, **_auth_header(user))


def _auth_patch(client, path, user, payload):
    return client.patch(
        path,
        data=json.dumps(payload),
        content_type="application/json",
        **_auth_header(user),
    )


def _auth_post(client, path, user, payload=None):
    return client.post(
        path,
        data=json.dumps(payload) if payload is not None else None,
        content_type="application/json",
        **_auth_header(user),
    )


# ── Task 0.1 — mutations must require JWT + owner-or-admin ──────────────────


@pytest.mark.django_db
def test_patch_inscripcion_anonimo_responde_401(api_client, inscripcion):
    """
    GIVEN: an anonymous caller
    WHEN:  PATCH /api/inscripciones/{id}
    THEN:  401 with the stable code AUTHENTICATION_REQUIRED and no mutation.
    """
    payload = make_actualizar_inscripcion_payload(estado="VALIDADA")

    response = api_client.patch(
        f"/api/inscripciones/{inscripcion.id}",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"

    inscripcion.refresh_from_db()
    assert inscripcion.estado == EstadoInscripcionChoices.RECIBIDA


@pytest.mark.django_db
def test_patch_inscripcion_ajeno_responde_403_sin_mutar(
    api_client, inscripcion, usuario_ajeno
):
    """
    GIVEN: an authenticated user that is not the responsable
    WHEN:  PATCH /api/inscripciones/{id}
    THEN:  403 with the stable code ACTION_NOT_ALLOWED and no mutation.
    """
    payload = make_actualizar_inscripcion_payload(
        estado="VALIDADA", observacion="Intento no autorizado"
    )

    response = _auth_patch(
        api_client, f"/api/inscripciones/{inscripcion.id}", usuario_ajeno, payload
    )

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "ACTION_NOT_ALLOWED"

    inscripcion.refresh_from_db()
    assert inscripcion.estado == EstadoInscripcionChoices.RECIBIDA
    assert inscripcion.observacion == ""


@pytest.mark.django_db
def test_patch_inscripcion_responsable_responde_200(
    api_client, inscripcion, usuario_responsable
):
    """
    GIVEN: the responsable of the inscripcion
    WHEN:  PATCH /api/inscripciones/{id}
    THEN:  200 and the inscripcion is updated.
    """
    payload = make_actualizar_inscripcion_payload(estado="VALIDADA")

    response = _auth_patch(
        api_client, f"/api/inscripciones/{inscripcion.id}", usuario_responsable, payload
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["success"] is True
    assert body["data"]["estado"] == "VALIDADA"

    inscripcion.refresh_from_db()
    assert inscripcion.estado == "VALIDADA"


@pytest.mark.django_db
def test_patch_inscripcion_admin_responde_200(api_client, inscripcion, usuario_admin):
    """
    GIVEN: a Django admin
    WHEN:  PATCH /api/inscripciones/{id}
    THEN:  200 and the inscripcion is updated.
    """
    payload = make_actualizar_inscripcion_payload(estado="EN_REVISION")

    response = _auth_patch(
        api_client, f"/api/inscripciones/{inscripcion.id}", usuario_admin, payload
    )

    assert response.status_code == 200, response.json()

    inscripcion.refresh_from_db()
    assert inscripcion.estado == "EN_REVISION"


@pytest.mark.django_db
def test_post_equipo_anonimo_responde_401(api_client, inscripcion, disciplina):
    """
    GIVEN: an anonymous caller
    WHEN:  POST /api/equipos/
    THEN:  401 and NO equipo is created.
    """
    payload = make_equipo_payload(
        inscripcion_id=str(inscripcion.id),
        disciplina_id=str(disciplina.id),
        nombre="Equipo Infiltrado",
    )

    response = api_client.post(
        "/api/equipos/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert Equipo.objects.filter(nombre="Equipo Infiltrado").count() == 0


@pytest.mark.django_db
def test_post_equipo_ajeno_responde_403_sin_crear(
    api_client, inscripcion, disciplina, usuario_ajeno
):
    """
    GIVEN: an authenticated user that is not the responsable
    WHEN:  POST /api/equipos/
    THEN:  403 and NO equipo is created.
    """
    payload = make_equipo_payload(
        inscripcion_id=str(inscripcion.id),
        disciplina_id=str(disciplina.id),
        nombre="Equipo Infiltrado",
    )

    response = _auth_post(api_client, "/api/equipos/", usuario_ajeno, payload)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert Equipo.objects.filter(nombre="Equipo Infiltrado").count() == 0


@pytest.mark.django_db
def test_post_equipo_responsable_responde_201(
    api_client, inscripcion, disciplina, usuario_responsable
):
    """
    GIVEN: the responsable of the inscripcion
    WHEN:  POST /api/equipos/
    THEN:  201 and the equipo exists.
    """
    payload = make_equipo_payload(
        inscripcion_id=str(inscripcion.id),
        disciplina_id=str(disciplina.id),
        nombre="Los Leones FC",
    )

    response = _auth_post(api_client, "/api/equipos/", usuario_responsable, payload)

    assert response.status_code == 201, response.json()
    assert response.json()["success"] is True
    assert Equipo.objects.filter(nombre="Los Leones FC").count() == 1


# ── Task 0.2 — private reads require the ownership/admin policy ─────────────


@pytest.mark.django_db
def test_get_inscripcion_anonimo_responde_401(api_client, inscripcion):
    """GIVEN: an anonymous caller WHEN: GET /api/inscripciones/{id} THEN: 401."""
    response = api_client.get(f"/api/inscripciones/{inscripcion.id}")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_get_inscripcion_ajeno_responde_403(api_client, inscripcion, usuario_ajeno):
    """GIVEN: a non-owner WHEN: GET /api/inscripciones/{id} THEN: 403."""
    response = _auth_get(api_client, f"/api/inscripciones/{inscripcion.id}", usuario_ajeno)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_get_inscripcion_responsable_responde_200(
    api_client, inscripcion, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET /api/inscripciones/{id} THEN: 200."""
    response = _auth_get(
        api_client, f"/api/inscripciones/{inscripcion.id}", usuario_responsable
    )

    assert response.status_code == 200, response.json()
    assert response.json()["data"]["id"] == str(inscripcion.id)


@pytest.mark.django_db
def test_get_inscripcion_admin_responde_200(api_client, inscripcion, usuario_admin):
    """GIVEN: a Django admin WHEN: GET /api/inscripciones/{id} THEN: 200."""
    response = _auth_get(api_client, f"/api/inscripciones/{inscripcion.id}", usuario_admin)

    assert response.status_code == 200, response.json()


@pytest.mark.django_db
def test_get_inscripcion_detalle_anonimo_responde_401(api_client, inscripcion):
    """GIVEN: an anonymous caller WHEN: GET .../detalle THEN: 401."""
    response = api_client.get(f"/api/inscripciones/{inscripcion.id}/detalle")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_get_inscripcion_detalle_ajeno_responde_403(
    api_client, inscripcion, usuario_ajeno
):
    """GIVEN: a non-owner WHEN: GET .../detalle THEN: 403 (full roster is private)."""
    response = _auth_get(
        api_client, f"/api/inscripciones/{inscripcion.id}/detalle", usuario_ajeno
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_get_inscripcion_detalle_responsable_responde_200(
    api_client, inscripcion, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET .../detalle THEN: 200."""
    response = _auth_get(
        api_client, f"/api/inscripciones/{inscripcion.id}/detalle", usuario_responsable
    )

    assert response.status_code == 200, response.json()
    assert response.json()["success"] is True


@pytest.mark.django_db
def test_get_equipo_anonimo_responde_401(api_client, equipo):
    """GIVEN: an anonymous caller WHEN: GET /api/equipos/{id} THEN: 401."""
    response = api_client.get(f"/api/equipos/{equipo.id}")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_get_equipo_ajeno_responde_403(api_client, equipo, usuario_ajeno):
    """GIVEN: a non-owner WHEN: GET /api/equipos/{id} THEN: 403."""
    response = _auth_get(api_client, f"/api/equipos/{equipo.id}", usuario_ajeno)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_get_equipo_responsable_responde_200(api_client, equipo, usuario_responsable):
    """GIVEN: the responsable WHEN: GET /api/equipos/{id} THEN: 200."""
    response = _auth_get(api_client, f"/api/equipos/{equipo.id}", usuario_responsable)

    assert response.status_code == 200, response.json()


@pytest.mark.django_db
def test_get_equipos_por_inscripcion_anonimo_responde_401(api_client, inscripcion):
    """GIVEN: an anonymous caller WHEN: GET /api/equipos/inscripcion/{id} THEN: 401."""
    response = api_client.get(f"/api/equipos/inscripcion/{inscripcion.id}")

    assert response.status_code == 401


@pytest.mark.django_db
def test_get_equipos_por_inscripcion_ajeno_responde_403(
    api_client, inscripcion, usuario_ajeno
):
    """GIVEN: a non-owner WHEN: GET /api/equipos/inscripcion/{id} THEN: 403."""
    response = _auth_get(
        api_client, f"/api/equipos/inscripcion/{inscripcion.id}", usuario_ajeno
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_get_equipos_por_inscripcion_responsable_responde_200(
    api_client, inscripcion, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET /api/equipos/inscripcion/{id} THEN: 200."""
    response = _auth_get(
        api_client, f"/api/equipos/inscripcion/{inscripcion.id}", usuario_responsable
    )

    assert response.status_code == 200, response.json()


@pytest.mark.django_db
def test_get_participacion_anonimo_responde_401(api_client, participacion):
    """GIVEN: an anonymous caller WHEN: GET /api/participaciones/{id} THEN: 401."""
    response = api_client.get(f"/api/participaciones/{participacion.id}")

    assert response.status_code == 401


@pytest.mark.django_db
def test_get_participacion_ajeno_responde_403(api_client, participacion, usuario_ajeno):
    """GIVEN: a non-owner WHEN: GET /api/participaciones/{id} THEN: 403."""
    response = _auth_get(
        api_client, f"/api/participaciones/{participacion.id}", usuario_ajeno
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_get_participacion_responsable_responde_200(
    api_client, participacion, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET /api/participaciones/{id} THEN: 200."""
    response = _auth_get(
        api_client, f"/api/participaciones/{participacion.id}", usuario_responsable
    )

    assert response.status_code == 200, response.json()


@pytest.mark.django_db
def test_get_participaciones_por_equipo_anonimo_responde_401(api_client, equipo):
    """GIVEN: an anonymous caller WHEN: GET /api/participaciones/equipo/{id} THEN: 401."""
    response = api_client.get(f"/api/participaciones/equipo/{equipo.id}")

    assert response.status_code == 401


@pytest.mark.django_db
def test_get_participaciones_por_equipo_ajeno_responde_403(
    api_client, equipo, usuario_ajeno
):
    """GIVEN: a non-owner WHEN: GET /api/participaciones/equipo/{id} THEN: 403."""
    response = _auth_get(api_client, f"/api/participaciones/equipo/{equipo.id}", usuario_ajeno)

    assert response.status_code == 403


@pytest.mark.django_db
def test_get_participaciones_por_equipo_responsable_responde_200(
    api_client, equipo, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET /api/participaciones/equipo/{id} THEN: 200."""
    response = _auth_get(
        api_client, f"/api/participaciones/equipo/{equipo.id}", usuario_responsable
    )

    assert response.status_code == 200, response.json()


@pytest.mark.django_db
def test_get_asignacion_anonimo_responde_401(api_client, asignacion):
    """GIVEN: an anonymous caller WHEN: GET /api/asignaciones/{id} THEN: 401."""
    response = api_client.get(f"/api/asignaciones/{asignacion.id}")

    assert response.status_code == 401


@pytest.mark.django_db
def test_get_asignacion_ajeno_responde_403(api_client, asignacion, usuario_ajeno):
    """GIVEN: a non-owner WHEN: GET /api/asignaciones/{id} THEN: 403."""
    response = _auth_get(api_client, f"/api/asignaciones/{asignacion.id}", usuario_ajeno)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_get_asignacion_responsable_responde_200(
    api_client, asignacion, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET /api/asignaciones/{id} THEN: 200."""
    response = _auth_get(
        api_client, f"/api/asignaciones/{asignacion.id}", usuario_responsable
    )

    assert response.status_code == 200, response.json()


@pytest.mark.django_db
def test_get_asignaciones_por_inscripcion_anonimo_responde_401(api_client, inscripcion):
    """GIVEN: an anonymous caller WHEN: GET /api/asignaciones/inscripciones/{id}/... THEN: 401."""
    response = api_client.get(
        f"/api/asignaciones/inscripciones/{inscripcion.id}/asignaciones"
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_get_asignaciones_por_inscripcion_ajeno_responde_403(
    api_client, inscripcion, usuario_ajeno
):
    """GIVEN: a non-owner WHEN: GET /api/asignaciones/inscripciones/{id}/... THEN: 403."""
    response = _auth_get(
        api_client,
        f"/api/asignaciones/inscripciones/{inscripcion.id}/asignaciones",
        usuario_ajeno,
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_get_asignaciones_por_inscripcion_responsable_responde_200(
    api_client, inscripcion, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET /api/asignaciones/inscripciones/{id}/... THEN: 200."""
    response = _auth_get(
        api_client,
        f"/api/asignaciones/inscripciones/{inscripcion.id}/asignaciones",
        usuario_responsable,
    )

    assert response.status_code == 200, response.json()


@pytest.mark.django_db
def test_get_saldo_ajeno_responde_403(api_client, inscripcion, usuario_ajeno):
    """GIVEN: a non-owner WHEN: GET /api/inscripciones/{id}/saldo THEN: 403."""
    response = _auth_get(
        api_client, f"/api/inscripciones/{inscripcion.id}/saldo", usuario_ajeno
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_get_saldo_responsable_responde_200(
    api_client, inscripcion, usuario_responsable
):
    """GIVEN: the responsable WHEN: GET /api/inscripciones/{id}/saldo THEN: 200."""
    response = _auth_get(
        api_client, f"/api/inscripciones/{inscripcion.id}/saldo", usuario_responsable
    )

    assert response.status_code == 200, response.json()


# ── Task 0.3 — accreditation: admin-only mutations, no live QR in reads ─────


@pytest.mark.django_db
def test_override_fiesta_anonimo_responde_401(api_client, evento, persona_ajena):
    """GIVEN: an anonymous caller WHEN: PATCH .../override-fiesta THEN: 401."""
    payload = make_acreditacion_override_payload()

    response = api_client.patch(
        f"/api/acreditaciones/{evento.id}/{persona_ajena.id}/override-fiesta",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_override_fiesta_no_admin_responde_403_sin_mutar(
    api_client, evento, persona_ajena, usuario_ajeno, acreditacion
):
    """
    GIVEN: an authenticated non-admin
    WHEN:  PATCH .../override-fiesta
    THEN:  403 and the accreditation is NOT mutated.
    """
    payload = make_acreditacion_override_payload(autorizacion="BLOQUEADA")

    response = _auth_patch(
        api_client,
        f"/api/acreditaciones/{evento.id}/{persona_ajena.id}/override-fiesta",
        usuario_ajeno,
        payload,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"

    acreditacion.refresh_from_db()
    assert acreditacion.autorizacion_fiesta == AutorizacionFiestaChoices.AUTOMATICA
    assert acreditacion.acceso_fiesta is True


@pytest.mark.django_db
def test_override_fiesta_admin_responde_200(
    api_client, evento, persona_ajena, usuario_admin, acreditacion
):
    """GIVEN: a Django admin WHEN: PATCH .../override-fiesta THEN: 200."""
    payload = make_acreditacion_override_payload(autorizacion="BLOQUEADA")

    response = _auth_patch(
        api_client,
        f"/api/acreditaciones/{evento.id}/{persona_ajena.id}/override-fiesta",
        usuario_admin,
        payload,
    )

    assert response.status_code == 200, response.json()
    assert response.json()["data"]["autorizacion_fiesta"] == "BLOQUEADA"


@pytest.mark.django_db
def test_generar_qr_anonimo_responde_401(api_client, evento, persona_ajena):
    """GIVEN: an anonymous caller WHEN: POST .../generar-qr THEN: 401."""
    response = api_client.post(
        f"/api/acreditaciones/{evento.id}/{persona_ajena.id}/generar-qr"
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_generar_qr_no_admin_responde_403_sin_rotar(
    api_client, evento, persona_ajena, usuario_ajeno, acreditacion
):
    """
    GIVEN: an authenticated non-admin
    WHEN:  POST .../generar-qr
    THEN:  403 and the live QR credential is NOT rotated.
    """
    codigo_original = acreditacion.codigo_qr

    response = _auth_post(
        api_client,
        f"/api/acreditaciones/{evento.id}/{persona_ajena.id}/generar-qr",
        usuario_ajeno,
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"

    acreditacion.refresh_from_db()
    assert acreditacion.codigo_qr == codigo_original


@pytest.mark.django_db
def test_generar_qr_admin_responde_200_con_credencial(
    api_client, evento, persona_ajena, usuario_admin, acreditacion
):
    """
    GIVEN: a Django admin
    WHEN:  POST .../generar-qr
    THEN:  200 and the explicit QR-delivery action returns the live credential.
    """
    response = _auth_post(
        api_client,
        f"/api/acreditaciones/{evento.id}/{persona_ajena.id}/generar-qr",
        usuario_admin,
    )

    assert response.status_code == 200, response.json()
    assert response.json()["data"]["codigo_qr"]


@pytest.mark.django_db
def test_get_acreditacion_anonimo_responde_401(api_client, evento, persona_ajena):
    """GIVEN: an anonymous caller WHEN: GET /api/acreditaciones/{e}/{p} THEN: 401."""
    response = api_client.get(f"/api/acreditaciones/{evento.id}/{persona_ajena.id}")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_get_acreditacion_ajeno_responde_403(
    api_client, evento, persona_ajena, usuario_tercero, acreditacion
):
    """
    GIVEN: an authenticated third party (neither the accredited person nor an admin)
    WHEN:  GET /api/acreditaciones/{e}/{p}
    THEN:  403.
    """
    response = _auth_get(
        api_client, f"/api/acreditaciones/{evento.id}/{persona_ajena.id}", usuario_tercero
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_get_acreditacion_admin_responde_200_sin_codigo_qr(
    api_client, evento, persona_ajena, usuario_admin, acreditacion
):
    """
    GIVEN: a Django admin
    WHEN:  GET /api/acreditaciones/{e}/{p}
    THEN:  200 and the live QR credential is NOT part of the payload.
    """
    response = _auth_get(
        api_client, f"/api/acreditaciones/{evento.id}/{persona_ajena.id}", usuario_admin
    )

    assert response.status_code == 200, response.json()
    body = response.json()
    assert body["success"] is True
    assert "codigo_qr" not in body["data"]
    assert str(acreditacion.codigo_qr) not in response.content.decode()


@pytest.mark.django_db
def test_get_acreditacion_propia_persona_responde_200(
    api_client, evento, persona_ajena, usuario_ajeno, acreditacion
):
    """
    GIVEN: the accredited person
    WHEN:  GET /api/acreditaciones/{e}/{p}
    THEN:  200 — the owner of the record is the accredited person itself.
    """
    response = _auth_get(
        api_client, f"/api/acreditaciones/{evento.id}/{persona_ajena.id}", usuario_ajeno
    )

    assert response.status_code == 200, response.json()
    assert "codigo_qr" not in response.json()["data"]


# ── Task 0.4 — no credential leakage on the error envelope ──────────────────


@pytest.mark.django_db
def test_errores_no_exponen_credenciales(
    api_client, inscripcion, equipo, asignacion, usuario_ajeno
):
    """
    GIVEN: a denied caller
    WHEN:  several denied reads are attempted
    THEN:  no response body leaks a credential, a token or an internal id.
    """
    paths = [
        f"/api/inscripciones/{inscripcion.id}",
        f"/api/inscripciones/{inscripcion.id}/detalle",
        f"/api/equipos/{equipo.id}",
        f"/api/asignaciones/{asignacion.id}",
    ]

    for path in paths:
        response = _auth_get(api_client, path, usuario_ajeno)
        assert response.status_code == 403, path
        content = response.content.decode().lower()
        for forbidden in (
            "password",
            "password_hash",
            "codigo_qr",
            "token",
            "access_token",
            "refresh_token",
            "metadata",
            "transaction_id",
            "traceback",
        ):
            assert forbidden not in content, f"{forbidden} leaked in {path}"
