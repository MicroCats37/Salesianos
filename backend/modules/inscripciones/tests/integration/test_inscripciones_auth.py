"""
Integration tests for auth protection on protected endpoints.

Tests that lifecycle endpoints (POST /, GET /, GET /{id}, etc.)
reject unauthenticated requests and user-without-persona requests.

Uses @pytest.mark.django_db for database access.
Uses @pytest.mark.asyncio with TestAsyncClient for async controller endpoints.
"""
import pytest
from ninja.testing import TestAsyncClient
from config.api import api


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def public_api_client(db):
    """Ninja TestAsyncClient without authentication (for async controllers)."""
    return TestAsyncClient(api)


# ── Tests: Unauthenticated requests ──────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_crear_inscripcion_sin_auth_rechaza_401(public_api_client):
    """
    GIVEN: No authentication token provided
    WHEN:  POST /inscripciones/
    THEN:  Returns 401 Unauthorized
    """
    payload = {
        "paquete_id": "any-id",
        "promocion_id": "any-id",
        "equipos": [],
    }
    response = await public_api_client.post(
        "/inscripciones/",
        json=payload,
    )

    # JWT auth returns 401 when token is missing or invalid
    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.content}"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_listar_inscripciones_sin_auth_rechaza_401(public_api_client):
    """
    GIVEN: No authentication token provided
    WHEN:  GET /inscripciones/
    THEN:  Returns 401 Unauthorized
    """
    response = await public_api_client.get("/inscripciones/")

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.content}"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_obtener_inscripcion_sin_auth_rechaza_401(public_api_client):
    """
    GIVEN: No authentication token provided
    WHEN:  GET /inscripciones/{id}
    THEN:  Returns 401 Unauthorized
    """
    response = await public_api_client.get("/inscripciones/some-uuid-here")

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.content}"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_cambiar_estado_sin_auth_rechaza_401(public_api_client):
    """
    GIVEN: No authentication token provided
    WHEN:  PATCH /inscripciones/{id}/estado
    THEN:  Returns 401 Unauthorized
    """
    payload = {"nuevo_estado": "VALIDADA"}
    response = await public_api_client.patch(
        "/inscripciones/some-uuid/estado",
        json=payload,
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.content}"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_asignar_delegado_sin_auth_rechaza_401(public_api_client):
    """
    GIVEN: No authentication token provided
    WHEN:  POST /inscripciones/{id}/delegado
    THEN:  Returns 401 Unauthorized
    """
    payload = {"persona_id": "any-uuid"}
    response = await public_api_client.post(
        "/inscripciones/some-uuid/delegado",
        json=payload,
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.content}"


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_agregar_participante_sin_auth_rechaza_401(public_api_client):
    """
    GIVEN: No authentication token provided
    WHEN:  POST /inscripciones/{id}/participantes
    THEN:  Returns 401 Unauthorized
    """
    payload = {"persona_id": "any-uuid", "rol": "JUGADOR"}
    response = await public_api_client.post(
        "/inscripciones/some-uuid/participantes",
        json=payload,
    )

    assert response.status_code == 401, f"Expected 401, got {response.status_code}: {response.content}"


# ── Tests: Authenticated user WITHOUT persona ─────────────────────────────────
# OBSOLETE: Usuario.persona is NOT NULL (DB-level constraint). A user without
# persona cannot exist in the system — the DB prevents it. The guard
# _get_authenticated_persona_id is no longer needed because the constraint
# ensures every user has a persona. Tests for user-without-persona were removed.
