"""
Usuarios test fixtures — api_client, auth_client, create_user.

Copied from liquidaciones/tests/fixtures/usuarios_fixtures.py.
DO NOT modify the original — this copy is for usuarios module tests.

The ONLY deviation from the original: `create_user` creates the `Persona`
first. `Usuario.persona_fk` is NOT NULL (the civil identity lives in
`Persona`), so an account cannot be created without one.
"""
import uuid

import pytest
from ninja.testing import TestClient
from ninja_jwt.tokens import AccessToken
from config.api import api
from django.contrib.auth import get_user_model

from modules.usuarios.domain.models.persona import Persona


@pytest.fixture
def api_client(db):
    """Ninja TestClient for testing Ninja API endpoints."""
    return TestClient(api)


@pytest.fixture
def create_user(db):
    """Create a test user for authenticated requests.

    The linked `Persona` is created first: `Usuario.persona_fk` is NOT NULL.
    The document number and the email are unique per call so the fixture can
    be used more than once inside the same test.
    """
    User = get_user_model()
    marca = uuid.uuid4().hex[:8]
    persona = Persona.objects.create(
        nombres="Usuario",
        apellidos="Prueba",
        tipo_documento="DNI",
        numero_documento=f"{int(marca, 16) % 100000000:08d}",
        genero="M",
    )
    return User.objects.create_user(
        username="testuser_usuarios",
        email=f"test_{marca}@example.com",
        password="testpass123",
        persona_fk=persona,
    )


@pytest.fixture
def auth_client(api_client, create_user):
    """JWT-authenticated test client."""
    user = create_user
    token = AccessToken.for_user(user)
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    api_client.user = user
    return api_client


@pytest.fixture
def usuario_admin(db, create_user):
    """Alias for create_user matching naming convention."""
    return create_user
