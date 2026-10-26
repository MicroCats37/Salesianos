"""
Integration tests — the `es_admin` flag of GET /api/auth/me.

The administration surface needs ONE authorization flag, computed SERVER-SIDE
with the project rule:

    admin = is_staff OR is_superuser

It is the same rule that `core.permissions.RequireAdmin` applies, so the
client can anticipate a 403 without being the authority: the backend
re-evaluates the rule on every request.

`is_superuser` is never exposed: the break-glass tier is not assignable nor
visible from the administration UI.
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from ninja_jwt.tokens import AccessToken

from modules.usuarios.domain.models.persona import Persona

URL_ME = "/api/auth/me"


@pytest.fixture
def api_client(db):
    """Django test client — the /auth/me controller is sync."""
    return Client()


def _crear_usuario(username: str, *, es_admin: bool = False, es_superuser: bool = False):
    """Create an account with its linked persona."""
    User = get_user_model()
    marca = uuid.uuid4().hex[:8]
    persona = Persona.objects.create(
        nombres="Actor",
        apellidos="Prueba",
        tipo_documento="DNI",
        numero_documento=f"{uuid.uuid4().int % 100000000:08d}",
        genero="M",
    )
    kwargs = {
        "username": f"{username}_{marca}",
        "email": f"{username}_{marca}@example.com",
        "password": "testpass123",
        "persona_fk": persona,
    }
    if es_superuser:
        return User.objects.create_superuser(**kwargs)

    usuario = User.objects.create_user(**kwargs)
    if es_admin:
        usuario.is_staff = True
        usuario.save(update_fields=["is_staff"])
    return usuario


def _auth_header(user) -> dict:
    """Build the Authorization header of an authenticated user."""
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


@pytest.mark.django_db
def test_me_de_usuario_normal_no_es_admin(api_client):
    """
    GIVEN: an authenticated user that is neither staff nor superuser
    WHEN:  GET /api/auth/me
    THEN:  es_admin is False.
    """
    usuario = _crear_usuario("normal")

    response = api_client.get(URL_ME, **_auth_header(usuario))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["es_admin"] is False


@pytest.mark.django_db
def test_me_de_staff_es_admin(api_client):
    """
    GIVEN: an authenticated user with `is_staff`
    WHEN:  GET /api/auth/me
    THEN:  es_admin is True — the flag follows the project rule, not the
            legacy three-value vocabulary.
    """
    usuario = _crear_usuario("staff", es_admin=True)

    response = api_client.get(URL_ME, **_auth_header(usuario))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["es_admin"] is True
    assert data["rol"] == "admin"


@pytest.mark.django_db
def test_me_de_superuser_es_admin(api_client):
    """
    GIVEN: an authenticated superuser
    WHEN:  GET /api/auth/me
    THEN:  es_admin is True.
    """
    usuario = _crear_usuario("super", es_superuser=True)

    response = api_client.get(URL_ME, **_auth_header(usuario))

    assert response.status_code == 200
    assert response.json()["data"]["es_admin"] is True


@pytest.mark.django_db
def test_me_no_expone_is_superuser(api_client):
    """
    GIVEN: an authenticated superuser
    WHEN:  GET /api/auth/me
    THEN:  the response exposes neither `is_superuser` nor any credential.
    """
    usuario = _crear_usuario("super", es_superuser=True)

    response = api_client.get(URL_ME, **_auth_header(usuario))

    crudo = response.content.decode().lower()
    assert "is_superuser" not in crudo
    assert "password" not in crudo
    assert "token" not in crudo


@pytest.mark.django_db
def test_me_es_admin_es_coherente_con_el_rol(api_client):
    """
    GIVEN: users of every kind
    WHEN:  GET /api/auth/me
    THEN:  `rol` and `es_admin` never disagree — the vocabulary is normalized.
    """
    normal = _crear_usuario("normal")
    staff = _crear_usuario("staff", es_admin=True)
    superusuario = _crear_usuario("super", es_superuser=True)

    for usuario in (normal, staff, superusuario):
        data = api_client.get(URL_ME, **_auth_header(usuario)).json()["data"]
        esperado = "admin" if usuario.is_staff or usuario.is_superuser else "user"
        assert data["rol"] == esperado
        assert data["es_admin"] is (esperado == "admin")
