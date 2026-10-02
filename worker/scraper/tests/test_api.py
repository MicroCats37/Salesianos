"""
test_api.py — Pruebas de integración y E2E para el microservicio de scraping.

Incluye:
  1. Validaciones locales (health, formato, longitud) sin red
  2. Pruebas reales E2E con el portal de consultas (RUC, DNI, No encontrado)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from main import app
from documento_scraper import (
    DocumentNotFoundError,
    ScraperFormatError,
    ScraperTimeoutError,
    ScraperUnavailableError,
    TipoDocumento,
)

client = TestClient(app)


# ──────────────────────────────────────────────
# 1. Pruebas de Validación / Unitarias API
# ──────────────────────────────────────────────

def test_health_endpoint():
    """Verifica que /health responda status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_consultar_longitud_invalida():
    """Verifica error 422 cuando la longitud no es 8 ni 11 dígitos."""
    response = client.get("/consultar/12345")
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "INVALID_LENGTH"
    assert "8 (DNI) o 11 (RUC)" in data["detail"]


def test_consultar_formato_invalido():
    """Verifica error 422 cuando contiene caracteres no numéricos."""
    response = client.get("/consultar/1234567a")
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "INVALID_FORMAT"


# ──────────────────────────────────────────────
# 2. Pruebas E2E Reales (Red Externa)
# ──────────────────────────────────────────────

@pytest.mark.e2e
def test_e2e_consulta_ruc_real():
    """Consulta real E2E por RUC (Banco de Crédito del Perú - 20100047218)."""
    response = client.get("/consultar/20100047218")
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_documento"] == "RUC"
    assert data["numero_documento"] == "20100047218"
    assert "BANCO DE CREDITO" in data["razon_social"]


@pytest.mark.e2e
def test_e2e_consulta_dni_real():
    """Consulta real E2E por DNI (74827847)."""
    response = client.get("/consultar/74827847")
    assert response.status_code == 200
    data = response.json()
    assert data["tipo_documento"] == "DNI"
    assert data["numero_documento"] == "74827847"
    assert "CALLIRGOS" in data["razon_social"]


@pytest.mark.e2e
def test_e2e_consulta_ruc_no_existente():
    """Consulta real E2E con un RUC que no existe (11111111111)."""
    response = client.get("/consultar/11111111111")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "NOT_FOUND"


# ──────────────────────────────────────────────
# 3. Pruebas de Caminos de Error (Mock)
# ──────────────────────────────────────────────

def test_consultar_timeout_returns_504():
    """ScraperTimeoutError returns 504 with retryable=True."""
    with patch("main.consultar", side_effect=ScraperTimeoutError(timeout_type="read")):
        response = client.get("/consultar/20100047218")
        assert response.status_code == 504
        data = response.json()
        assert data["error"] == "TIMEOUT"
        assert data["retryable"] is True


def test_consultar_unavailable_returns_503():
    """ScraperUnavailableError returns 503 with retryable=True."""
    with patch("main.consultar", side_effect=ScraperUnavailableError(reason="connection_error")):
        response = client.get("/consultar/20100047218")
        assert response.status_code == 503
        data = response.json()
        assert data["error"] == "UNAVAILABLE"
        assert data["retryable"] is True


def test_consultar_format_error_returns_502():
    """ScraperFormatError returns 502 with retryable=False."""
    with patch("main.consultar", side_effect=ScraperFormatError(parser_hint="h4")):
        response = client.get("/consultar/20100047218")
        assert response.status_code == 502
        data = response.json()
        assert data["error"] == "FORMAT_ERROR"
        assert data["retryable"] is False


def test_consultar_document_not_found_returns_404():
    """DocumentNotFoundError returns 404."""
    with patch(
        "main.consultar",
        side_effect=DocumentNotFoundError("00000000", TipoDocumento.DNI),
    ):
        response = client.get("/consultar/00000000")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "NOT_FOUND"


def test_consultar_validation_error_returns_422():
    """ValueError raised by consultar() (e.g. non-numeric internally) returns 422."""
    with patch("main.consultar", side_effect=ValueError("no digits")):
        response = client.get("/consultar/00000000")
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "INVALID_DOCUMENT"


def test_consultar_internal_error_returns_500():
    """Unexpected exception (logic bug) returns 500."""
    with patch("main.consultar", side_effect=RuntimeError("unexpected")):
        response = client.get("/consultar/20100047218")
        assert response.status_code == 500
        data = response.json()
        assert data["error"] == "INTERNAL_ERROR"
