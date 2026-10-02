"""
Integration tests for public catalog endpoints (no auth required).

Tests:
- GET /inscripciones/disciplinas/ — returns list (empty or populated)
- GET /inscripciones/disciplinas/{id}/categorias — returns categories
- GET /inscripciones/paquetes/ — returns list (empty or populated)
- GET /inscripciones/paquetes/{id}/disciplinas — returns disciplines in package
- GET /inscripciones/eventos/ — returns list (empty or populated)

Uses @pytest.mark.django_db for database access.
Uses ninja.testing.TestClient per TEST_ARCHITECTURE_CONTRACT.md.
"""
import pytest
from ninja.testing import TestClient
from config.api import api


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def catalog_api_client(db):
    """Ninja TestClient for testing catalog endpoints (no auth)."""
    return TestClient(api)


# ── Tests: Disciplinas ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_disciplinas_lista_vacia(catalog_api_client):
    """
    GIVEN: No disciplines exist in the database
    WHEN:  GET /inscripciones/disciplinas/
    THEN:  Returns 200 with empty data list
    """
    response = catalog_api_client.get("/inscripciones/disciplinas/")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.django_db
def test_disciplinas_lista_con_datos(catalog_api_client, disciplina_futbol, disciplina_basket):
    """
    GIVEN: Disciplinas (Futbol and Basketball) exist
    WHEN:  GET /inscripciones/disciplinas/
    THEN:  Returns 200 with list of active disciplines
    """
    response = catalog_api_client.get("/inscripciones/disciplinas/")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert len(data) == 2
    nombres = {d["nombre"] for d in data}
    assert "Fútbol Sala" in nombres
    assert "Básquet" in nombres


@pytest.mark.django_db
def test_disciplinas_categorias_vacias(catalog_api_client, disciplina_futbol):
    """
    GIVEN: Disciplina exists but has no categories
    WHEN:  GET /inscripciones/disciplinas/{id}/categorias
    THEN:  Returns 200 with empty list
    """
    response = catalog_api_client.get(f"/inscripciones/disciplinas/{disciplina_futbol.id}/categorias")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    assert response.json()["data"] == []


@pytest.mark.django_db
def test_disciplinas_categorias_con_datos(catalog_api_client, disciplina_futbol, categoria_senior, categoria_junior):
    """
    GIVEN: Disciplina has Senior and Junior categories
    WHEN:  GET /inscripciones/disciplinas/{id}/categorias
    THEN:  Returns 200 with list of categories
    """
    response = catalog_api_client.get(f"/inscripciones/disciplinas/{disciplina_futbol.id}/categorias")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert len(data) == 2
    nombres = {c["nombre"] for c in data}
    assert "Senior" in nombres
    assert "Junior" in nombres


# ── Tests: Paquetes ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_paquetes_lista_vacia(catalog_api_client):
    """
    GIVEN: No packages exist
    WHEN:  GET /inscripciones/paquetes/
    THEN:  Returns 200 with empty list
    """
    response = catalog_api_client.get("/inscripciones/paquetes/")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.django_db
def test_paquetes_lista_con_datos(catalog_api_client, paquete_basic):
    """
    GIVEN: Active package exists
    WHEN:  GET /inscripciones/paquetes/
    THEN:  Returns 200 with package data
    """
    response = catalog_api_client.get("/inscripciones/paquetes/")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["nombre"] == "Paquete Basic"
    assert data[0]["esta_activo"] is True


@pytest.mark.django_db
def test_paquetes_disciplinas_vacias(catalog_api_client, paquete_basic):
    """
    GIVEN: Package has no linked disciplines
    WHEN:  GET /inscripciones/paquetes/{id}/disciplinas
    THEN:  Returns 200 with empty list
    """
    response = catalog_api_client.get(f"/inscripciones/paquetes/{paquete_basic.id}/disciplinas")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    assert response.json()["data"] == []


@pytest.mark.django_db
def test_paquetes_disciplinas_con_datos(catalog_api_client, paquete_disciplina_futbol, paquete_basic, disciplina_futbol):
    """
    GIVEN: Package is linked to Futbol discipline
    WHEN:  GET /inscripciones/paquetes/{id}/disciplinas
    THEN:  Returns 200 with discipline info
    """
    response = catalog_api_client.get(f"/inscripciones/paquetes/{paquete_basic.id}/disciplinas")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["disciplina_nombre"] == "Fútbol Sala"


# ── Tests: Eventos ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_eventos_lista_vacia(catalog_api_client):
    """
    GIVEN: No events exist
    WHEN:  GET /inscripciones/eventos/
    THEN:  Returns 200 with empty list
    """
    response = catalog_api_client.get("/inscripciones/eventos/")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.django_db
def test_eventos_lista_con_datos(catalog_api_client, evento_activo):
    """
    GIVEN: Active event exists
    WHEN:  GET /inscripciones/eventos/
    THEN:  Returns 200 with event data
    """
    response = catalog_api_client.get("/inscripciones/eventos/")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["nombre"] == "Salesianos FEST 2026"
    assert data[0]["esta_activo"] is True
