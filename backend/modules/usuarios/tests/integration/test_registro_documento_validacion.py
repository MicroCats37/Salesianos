"""
Integration tests for document validation in registration.

Uses django.test.AsyncClient with @pytest.mark.asyncio for async controller.
Tests use @pytest.mark.django_db for database access.
Validation rules:
- DNI: exactly 8 digits
- CE: exactly 9 digits
- PAS: min 4 alphanumeric chars
"""
import pytest
from django.test import AsyncClient


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def registro_api_client(db):
    """Django AsyncClient for testing async /auth/register endpoint."""
    return AsyncClient()


# ── Tests: DNI ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_dni_valido_8_digitos(registro_api_client):
    """
    GIVEN: Payload with valid 8-digit DNI
    WHEN:  POST /api/auth/register
    THEN:  Returns 200 with access_token, refresh_token and user data
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni
    payload = make_payload_registro_dni(numero="12345678")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert "data" in data
    result = data["data"]
    assert "access_token" in result
    assert "refresh_token" in result
    assert "user" in result
    assert result["user"]["persona_id"] is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_dni_formato_invalido_7_digitos(registro_api_client):
    """
    GIVEN: Payload with 7-digit DNI (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422 with validation error
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni
    payload = make_payload_registro_dni(numero="1234567")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_dni_formato_invalido_9_digitos(registro_api_client):
    """
    GIVEN: Payload with 9-digit DNI (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422 with validation error
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni
    payload = make_payload_registro_dni(numero="123456789")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_dni_formato_invalido_con_letras(registro_api_client):
    """
    GIVEN: Payload with DNI containing letters (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422 with validation error
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni
    payload = make_payload_registro_dni(numero="1234567A")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_dni_formato_invalido_vacio(registro_api_client):
    """
    GIVEN: Payload with empty DNI (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422 with validation error
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni
    payload = make_payload_registro_dni(numero="")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


# ── Tests: CE ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_ce_valido_9_digitos(registro_api_client):
    """
    GIVEN: Payload with valid 9-digit CE
    WHEN:  POST /api/auth/register
    THEN:  Returns 200
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_ce
    payload = make_payload_registro_ce(numero="123456789")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_ce_formato_invalido_8_digitos(registro_api_client):
    """
    GIVEN: Payload with 8-digit CE (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_ce
    payload = make_payload_registro_ce(numero="12345678")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_ce_formato_invalido_10_digitos(registro_api_client):
    """
    GIVEN: Payload with 10-digit CE (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_ce
    payload = make_payload_registro_ce(numero="1234567890")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_ce_formato_invalido_con_letras(registro_api_client):
    """
    GIVEN: Payload with CE containing letters (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_ce
    payload = make_payload_registro_ce(numero="12345678A")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


# ── Tests: PAS ─────────────────────────────────────────────────────────────--


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_pas_valido_min_4_alfanum(registro_api_client):
    """
    GIVEN: Payload with valid PAS (min 4 alphanumeric chars)
    WHEN:  POST /api/auth/register
    THEN:  Returns 200
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_pas
    payload = make_payload_registro_pas(numero="AB1234")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_pas_valido_4_chars(registro_api_client):
    """
    GIVEN: Payload with valid 4-char PAS
    WHEN:  POST /api/auth/register
    THEN:  Returns 200
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_pas
    payload = make_payload_registro_pas(numero="AB12")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_pas_formato_invalido_3_chars(registro_api_client):
    """
    GIVEN: Payload with 3-char PAS (invalid, min 4 required)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_pas
    payload = make_payload_registro_pas(numero="AB1")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_pas_formato_invalido_2_chars(registro_api_client):
    """
    GIVEN: Payload with 2-char PAS (invalid, min 4 required)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_pas
    payload = make_payload_registro_pas(numero="AB")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_pas_formato_invalido_guiones(registro_api_client):
    """
    GIVEN: Payload with PAS containing special chars like hyphens (invalid)
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_pas
    payload = make_payload_registro_pas(numero="AB-123")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


# ── Tests: Cross-Field Validations ─────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_passwords_no_coinciden(registro_api_client):
    """
    GIVEN: Payload with non-matching password and confirmPassword
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
    payload = make_payload_registro(password="pass123", confirmPassword="pass124")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_acceptedBases_false(registro_api_client):
    """
    GIVEN: Payload with acceptedBases=False
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
    payload = make_payload_registro(acceptedBases=False)
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_telefono_no_9_digitos(registro_api_client):
    """
    GIVEN: Payload with phone number that is not 9 digits
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
    payload = make_payload_registro(telefono="1234567890")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_whatsapp_no_9_digitos(registro_api_client):
    """
    GIVEN: Payload with WhatsApp number that is not 9 digits
    WHEN:  POST /api/auth/register
    THEN:  Returns 422
    """
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
    payload = make_payload_registro(whatsapp="12345678")
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


# ── Tests: Happy Path ───────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_happy_path_dni(registro_api_client):
    """
    GIVEN: Valid DNI payload with all required fields
    WHEN:  POST /api/auth/register
    THEN:  Returns 200 with tokens and persona_id
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni
    payload = make_payload_registro_dni(
        numero=f"{uuid.uuid4().int % 100000000:08d}",
        email="happy_dni@example.com",
    )
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert data["user"]["persona_id"] is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_happy_path_ce(registro_api_client):
    """
    GIVEN: Valid CE payload with all required fields
    WHEN:  POST /api/auth/register
    THEN:  Returns 200 with tokens and persona_id
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_ce
    payload = make_payload_registro_ce(
        numero=f"{uuid.uuid4().int % 1000000000:09d}",
        email="happy_ce@example.com",
    )
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert "access_token" in data
    assert data["user"]["persona_id"] is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_happy_path_pas(registro_api_client):
    """
    GIVEN: Valid PAS payload with all required fields
    WHEN:  POST /api/auth/register
    THEN:  Returns 200 with tokens and persona_id
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_pas
    payload = make_payload_registro_pas(
        numero=f"PS{uuid.uuid4().hex[:4].upper()}",
        email="happy_pas@example.com",
    )
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert "access_token" in data
    assert data["user"]["persona_id"] is not None


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_con_telefono_y_whatsapp(registro_api_client):
    """
    GIVEN: Valid payload with optional phone and WhatsApp
    WHEN:  POST /api/auth/register
    THEN:  Returns 200
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
    payload = make_payload_registro(
        email=f"contact_{uuid.uuid4().hex[:8]}@example.com",
        telefono="987654321",
        whatsapp="987654322",
    )
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"


# ── Tests: Conflicts ─────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_email_duplicado(registro_api_client):
    """
    GIVEN: A user already registered with email X
    WHEN:  Attempting to register another user with the same email
    THEN:  Returns 409 Conflict
    """
    import uuid
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
    payload = make_payload_registro(
        email=f"dup_{uuid.uuid4().hex[:8]}@example.com",
        numeroDocumento=f"{uuid.uuid4().int % 100000000:08d}",
    )
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == 200, f"First registration failed: {response.content}"

    # Second registration with same email but different document
    payload2 = make_payload_registro(
        email=payload["email"],
        numeroDocumento=f"{uuid.uuid4().int % 100000000:08d}",
    )
    response2 = await registro_api_client.post(
        "/api/auth/register",
        data=payload2,
        content_type="application/json",
    )
    assert response2.status_code == 409, f"Expected 409, got {response2.status_code}: {response2.content}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_registro_documento_duplicado_crea_usuario_logueado(registro_api_client):
    """
    GIVEN: A Persona exists with a document but no associated user
    WHEN:  Registering with the same document
    THEN:  Returns 200 and links to existing Persona
    """
    import uuid
    from asgiref.sync import sync_to_async
    from modules.usuarios.domain.models.persona import Persona
    from modules.usuarios.tests.fixtures.factories import make_payload_registro_dni

    doc_num = f"{uuid.uuid4().int % 100000000:08d}"

    @sync_to_async
    def _create_persona():
        # Create Persona directly (no User) to simulate the "persona without user" state.
        # Using a decorated function instead of sync_to_async(obj.method) to ensure
        # proper database connection context within Django's thread-local storage.
        Persona.objects.create(
            tipo_documento="DNI",
            numero_documento=doc_num,
            nombres="Juan",
            apellidos="Pérez",
            genero="M",
        )

    await _create_persona()

    # Registration with the existing document should link to the Persona
    payload = make_payload_registro_dni(
        numero=doc_num,
        email=f"new_{uuid.uuid4().hex[:8]}@example.com",
    )
    response = await registro_api_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )
    # Per flow: persona exists without user -> creates new user linked to existing persona
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert "access_token" in data
    assert "user" in data
    assert data["user"]["persona_id"] is not None
