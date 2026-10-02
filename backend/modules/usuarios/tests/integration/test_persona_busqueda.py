"""
Integration tests for persona busqueda endpoint.

Tests the /personas/busqueda/{documento} endpoint owned by usuarios.
"""
import pytest
from django.test import AsyncClient

# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def busqueda_api_client(db):
    """Django AsyncClient for testing async /personas/busqueda endpoint."""
    return AsyncClient()


# ── Tests ───────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_busqueda_dni_existente_devuelve_razon_social(busqueda_api_client):
    """
    GIVEN: A DNI that exists in the simulator (45406196)
    WHEN:  GET /api/personas/busqueda/45406196
    THEN:  Returns 200 with tipo_documento=DNI, numero_documento=45406196,
            and razon_social matching the simulator data
    """
    response = await busqueda_api_client.get(
        "/api/personas/busqueda/45406196",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    result = data["data"]
    # Verify shape matches entidades endpoint
    assert "tipo_documento" in result
    assert "numero_documento" in result
    assert "razon_social" in result
    # Verify values
    assert result["tipo_documento"] == "DNI"
    assert result["numero_documento"] == "45406196"
    assert result["razon_social"] == "ZARATE TORRES, DENNIS JOEL"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_busqueda_dni_otro_existente(busqueda_api_client):
    """
    GIVEN: Another DNI that exists in the simulator (12345678)
    WHEN:  GET /api/personas/busqueda/12345678
    THEN:  Returns 200 with tipo_documento=DNI
    """
    response = await busqueda_api_client.get(
        "/api/personas/busqueda/12345678",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    result = data["data"]
    assert result["tipo_documento"] == "DNI"
    assert result["numero_documento"] == "12345678"
    assert result["razon_social"] == "PEREZ GOMEZ, CARLOS MANUEL"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_busqueda_dni_no_hardcoded_devuelve_dni_deterministico(busqueda_api_client):
    """
    GIVEN: A valid DNI that is not hardcoded in the simulator
    WHEN:  GET /api/personas/busqueda/99999999
    THEN:  Returns 200 with tipo_documento=DNI
    """
    response = await busqueda_api_client.get(
        "/api/personas/busqueda/99999999",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    result = data["data"]
    assert result["tipo_documento"] == "DNI"
    assert result["numero_documento"] == "99999999"
    assert isinstance(result["razon_social"], str)
    assert result["razon_social"]


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_busqueda_ruc_existente(busqueda_api_client):
    """
    GIVEN: A RUC that exists in the simulator (20492913151)
    WHEN:  GET /api/personas/busqueda/20492913151
    THEN:  Returns 200 with tipo_documento=RUC and razon_social from simulator
    """
    response = await busqueda_api_client.get(
        "/api/personas/busqueda/20492913151",
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    result = data["data"]
    assert result["tipo_documento"] == "RUC"
    assert result["numero_documento"] == "20492913151"
    assert result["razon_social"] == "MUNICIPALIDAD PROVINCIAL DE LIMA"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_busqueda_longitud_invalida_devuelve_422(busqueda_api_client):
    """
    GIVEN: A documento with invalid length (7 digits)
    WHEN:  GET /api/personas/busqueda/1234567
    THEN:  Returns 422 (Path validator rejects min_length=8)
    """
    response = await busqueda_api_client.get(
        "/api/personas/busqueda/1234567",
    )

    assert response.status_code == 422, f"Expected 422 for length 7, got {response.status_code}"


@pytest.mark.django_db
@pytest.mark.asyncio
async def test_busqueda_endpoint_devuelve_forma_contractual(busqueda_api_client):
    """
    GIVEN: Any valid DNI
    WHEN:  GET /api/personas/busqueda/45406196
    THEN:  Response shape matches the document lookup contract:
            { success: true, data: { tipo_documento, numero_documento, razon_social }, error: null }
    """
    response = await busqueda_api_client.get(
        "/api/personas/busqueda/45406196",
    )

    assert response.status_code == 200
    data = response.json()
    # Verify exact shape expected by frontend
    assert set(data.keys()) == {"success", "data", "error"}
    assert data["success"] is True
    assert data["error"] is None
    result = data["data"]
    assert set(result.keys()) == {"tipo_documento", "numero_documento", "razon_social"}
    assert isinstance(result["tipo_documento"], str)
    assert isinstance(result["numero_documento"], str)
    assert isinstance(result["razon_social"], str)
