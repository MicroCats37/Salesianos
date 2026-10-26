"""
Administracion test fixtures — anonymous, non-admin and admin actors.

`django.test.Client` is used on purpose: the controllers are async and this is
the pattern established by the rest of the project
(`contract/django-app-architecture-contract.md` §2.1 — `ninja.testing.TestClient`
must NOT be used with async controllers).
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from modules.usuarios.domain.models.persona import Persona


def _documento_unico() -> str:
    """Return a unique 8-digit document number."""
    return f"{uuid.uuid4().int % 100000000:08d}"


def _crear_usuario(username: str, *, es_admin: bool = False, es_superuser: bool = False):
    """Create an account with its linked persona.

    `Usuario.persona_fk` is NOT NULL, so the persona is created first.
    """
    User = get_user_model()
    marca = uuid.uuid4().hex[:8]
    persona = Persona.objects.create(
        nombres="Actor",
        apellidos="Prueba",
        tipo_documento="DNI",
        numero_documento=_documento_unico(),
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


@pytest.fixture
def api_client(db):
    """Django test client — handles the async controllers in the test transaction."""
    return Client()


@pytest.fixture
def usuario_no_admin(db):
    """Authenticated user that is NOT an administrator."""
    return _crear_usuario("usuario_normal")


@pytest.fixture
def usuario_admin_staff(db):
    """Authenticated administrator (`is_staff`)."""
    return _crear_usuario("usuario_staff", es_admin=True)


@pytest.fixture
def usuario_admin_superuser(db):
    """Authenticated administrator (`is_superuser`)."""
    return _crear_usuario("usuario_super", es_superuser=True)


@pytest.fixture
def usuario_inactivo(db):
    """Authenticated user that was DEACTIVATED."""
    usuario = _crear_usuario("usuario_inactivo")
    usuario.is_active = False
    usuario.save(update_fields=["is_active"])
    return usuario
