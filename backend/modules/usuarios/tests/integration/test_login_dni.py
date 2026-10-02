"""
Integration tests for login-by-DNI flow.

Verifies that after registration, a user can log in by their DNI (8 digits)
plus password. Regression for the bug where the legacy `Usuario.dni` column
was never populated by the new registration flow.
"""
import pytest
from django.test import AsyncClient
from asgiref.sync import sync_to_async

from modules.usuarios.tests.fixtures.factories import make_payload_registro


@pytest.fixture
def login_client(db):
    return AsyncClient()


def _make_payload(numero: str = "76543210") -> dict:
    return make_payload_registro(numeroDocumento=numero)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_login_por_dni_despues_de_registro(login_client):
    """
    GIVEN: A user was registered with DNI 76543210
    WHEN:  POST /api/auth/login/dni with { dni: '76543210', password }
    THEN:  Returns 200 with JWT tokens and user.persona_id
    """
    # Step 1: register
    payload = _make_payload()
    response = await login_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )
    assert response.status_code == 200, (
        f"Registration failed: {response.status_code} {response.content}"
    )
    body = response.json()
    assert body.get("data", {}).get("user", {}).get("persona_id"), (
        "Registration must return user.persona_id"
    )

    # Step 2: login by DNI
    login_payload = {
        "dni": payload["numeroDocumento"],
        "password": payload["password"],
    }
    response = await login_client.post(
        "/api/auth/login/dni",
        data=login_payload,
        content_type="application/json",
    )

    assert response.status_code == 200, (
        f"Login by DNI failed: {response.status_code} {response.content}"
    )
    data = response.json()["data"]
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["persona_id"] is not None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_login_por_dni_incorrecto_devuelve_401(login_client):
    """
    GIVEN: A user was registered
    WHEN:  POST /api/auth/login/dni with wrong password
    THEN:  Returns 401
    """
    payload = _make_payload()
    await login_client.post(
        "/api/auth/register",
        data=payload,
        content_type="application/json",
    )

    login_payload = {
        "dni": payload["numeroDocumento"],
        "password": "wrong-password",
    }
    response = await login_client.post(
        "/api/auth/login/dni",
        data=login_payload,
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_login_por_dni_inexistente_devuelve_401(login_client):
    """
    GIVEN: No user with that DNI
    WHEN:  POST /api/auth/login/dni with arbitrary DNI
    THEN:  Returns 401
    """
    response = await login_client.post(
        "/api/auth/login/dni",
        data={"dni": "00000000", "password": "whatever"},
        content_type="application/json",
    )

    assert response.status_code == 401
