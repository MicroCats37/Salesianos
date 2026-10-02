"""
E2E tests for complete registration flow.

Mimics real frontend flow:
1. POST /api/auth/register with valid payload
2. Verify response structure includes tokens and user data
3. Verify persona was created in DB

Uses django.test.AsyncClient with @pytest.mark.asyncio for async controller.
"""
import pytest
from django.test import AsyncClient


@pytest.fixture
def registro_api_client(db):
    """Django AsyncClient for testing async /auth/register endpoint."""
    return AsyncClient()


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_e2e_registro_dni_flow(registro_api_client):
    """
    GIVEN: User navigates to registration page with DNI
    WHEN:  Submitting valid DNI registration form
    THEN:  Account is created and tokens are returned
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni
    payload = make_payload_registro_dni(
        numero=f"{uuid.uuid4().int % 100000000:08d}",
        email=f"e2e_dni_{uuid.uuid4().hex[:8]}@example.com",
        nombres="Juan",
        apellidos="E2E Test",
    )

    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"E2E DNI registration failed: {response.content}"
    data = response.json()

    # Verify response structure
    assert "data" in data, "Response should have 'data' key"
    result = data["data"]
    assert "access_token" in result, "Should return access_token"
    assert "refresh_token" in result, "Should return refresh_token"
    assert "user" in result, "Should return user data"
    assert result["user"]["persona_id"] is not None, "Should have persona_id"

    # Verify user fields
    user = result["user"]
    assert user["email"] == payload["email"]
    assert user["is_staff"] is False
    assert user["is_superuser"] is False


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_e2e_registro_ce_flow(registro_api_client):
    """
    GIVEN: Foreign user navigating to registration page with CE
    WHEN:  Submitting valid CE registration form
    THEN:  Account is created and tokens are returned
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_ce
    payload = make_payload_registro_ce(
        numero=f"{uuid.uuid4().int % 1000000000:09d}",
        email=f"e2e_ce_{uuid.uuid4().hex[:8]}@example.com",
        nombres="Carlos",
        apellidos="Extranjero",
    )

    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"E2E CE registration failed: {response.content}"
    data = response.json()["data"]
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["persona_id"] is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_e2e_registro_pas_flow(registro_api_client):
    """
    GIVEN: User navigating to registration page with Passport
    WHEN:  Submitting valid PAS registration form
    THEN:  Account is created and tokens are returned
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_pas
    payload = make_payload_registro_pas(
        numero=f"PS{uuid.uuid4().hex[:4].upper()}",
        email=f"e2e_pas_{uuid.uuid4().hex[:8]}@example.com",
        nombres="Passport",
        apellidos="User",
    )

    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"E2E PAS registration failed: {response.content}"
    data = response.json()["data"]
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["persona_id"] is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_e2e_registro_full_wizard_payload(registro_api_client):
    """
    GIVEN: User completing full registration with all optional fields
    WHEN:  Submitting complete registration form
    THEN:  All fields are accepted and stored correctly
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
    unique_suffix = uuid.uuid4().hex[:8]
    payload = make_payload_registro(
        email=f"full_wizard_{unique_suffix}@example.com",
        tipoDocumento="DNI",
        numeroDocumento=f"{uuid.uuid4().int % 100000000:08d}",
        nombres="Maria del Carmen",
        apellidos="Registro Completo",
        genero="F",
        telefono="987654321",
        whatsapp="987654320",
        contactoEmergenciaNombre="Emergencia Contact",
        contactoEmergenciaTelefono="987654319",
        aceptacionVersion="BASES-SF26-2026-09-06",
        acceptedBases=True,
    )

    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Full wizard registration failed: {response.content}"
    data = response.json()["data"]
    assert "user" in data
    assert data["user"]["persona_id"] is not None
