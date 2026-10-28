"""
Integration tests — the authorization flags of GET /api/auth/me.

The administration surface needs ONE authorization flag, computed SERVER-SIDE
with the project rule:

    admin = is_staff OR is_superuser

It is the same rule that `core.permissions.RequireAdmin` applies, so the
client can anticipate a 403 without being the authority: the backend
re-evaluates the rule on every request.

The endpoint ALSO publishes the tier of the CALLER (`is_staff`,
`is_superuser`, `nivel`) and its capabilities. They are self-scoped: the
own privilege level is not a disclosure, it is the base of the interface.
The vocabulary comes from `core.capacidades`, the single map of the project.
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from ninja_jwt.tokens import AccessToken

from core.capacidades import (
    CAP_ADMIN_VER,
    CAP_PAGOS_APROBAR,
    CAP_PAGOS_VER,
    CAP_USUARIOS_VER,
    TODAS_LAS_CAPACIDADES,
)
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
def test_me_publica_el_nivel_del_propio_usuario(api_client):
    """
    GIVEN: an authenticated superuser
    WHEN:  GET /api/auth/me
    THEN:  the response publishes the tier of the CALLER (`is_staff`,
            `is_superuser`, `nivel`) and NEVER a credential.
    """
    usuario = _crear_usuario("super", es_superuser=True)

    response = api_client.get(URL_ME, **_auth_header(usuario))

    data = response.json()["data"]
    assert data["is_staff"] is True
    assert data["is_superuser"] is True
    assert data["nivel"] == "superusuario"

    crudo = response.content.decode().lower()
    assert "password" not in crudo
    assert "token" not in crudo


@pytest.mark.django_db
def test_me_publica_el_nivel_del_staff(api_client):
    """
    GIVEN: an authenticated operational staff
    WHEN:  GET /api/auth/me
    THEN:  the tier is `staff` and the capabilities are the operational ones.
    """
    usuario = _crear_usuario("staff", es_admin=True)

    response = api_client.get(URL_ME, **_auth_header(usuario))

    data = response.json()["data"]
    assert data["is_staff"] is True
    assert data["is_superuser"] is False
    assert data["nivel"] == "staff"

    capacidades = set(data["capacidades"])
    assert CAP_ADMIN_VER in capacidades
    assert CAP_PAGOS_VER in capacidades
    assert CAP_USUARIOS_VER in capacidades
    # The operational staff does NOT approve or annul payments.
    assert CAP_PAGOS_APROBAR not in capacidades


@pytest.mark.django_db
def test_me_de_usuario_normal_no_tiene_capacidades(api_client):
    """
    GIVEN: an authenticated user that is neither staff nor superuser
    WHEN:  GET /api/auth/me
    THEN:  the tier is `usuario` and the capability set is EMPTY.
    """
    usuario = _crear_usuario("normal")

    response = api_client.get(URL_ME, **_auth_header(usuario))

    data = response.json()["data"]
    assert data["nivel"] == "usuario"
    assert data["capacidades"] == []


@pytest.mark.django_db
def test_me_del_superuser_publica_todas_las_capacidades(api_client):
    """
    GIVEN: an authenticated superuser
    WHEN:  GET /api/auth/me
    THEN:  the capability set is the COMPLETE one (Django bypasses every
            check, so our map must never be narrower).
    """
    usuario = _crear_usuario("super", es_superuser=True)

    response = api_client.get(URL_ME, **_auth_header(usuario))

    capacidades = set(response.json()["data"]["capacidades"])
    assert capacidades == set(TODAS_LAS_CAPACIDADES)


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
