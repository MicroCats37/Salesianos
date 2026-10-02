"""
Usuarios fixtures — auth client, user creation.

Copied from liquidaciones/tests/fixtures/usuarios_fixtures.py.
DO NOT modify the original — this copy is for inscripciones module tests.
"""
import pytest
from ninja.testing import TestClient
from ninja_jwt.tokens import AccessToken
from config.api import api
from django.contrib.auth import get_user_model


@pytest.fixture
def api_client(db):
    """Ninja TestClient for testing Ninja endpoints with proper async handling."""
    return TestClient(api)


@pytest.fixture
def create_user(db):
    """Create a test user without persona_fk (user without Persona)."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser_inscripciones",
        email="test_inscripciones@example.com",
        password="testpass123",
    )


@pytest.fixture
def auth_client(api_client, create_user):
    """JWT-authenticated test client (user without persona_fk)."""
    user = create_user
    token = AccessToken.for_user(user)
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    api_client.user = user
    return api_client


@pytest.fixture
def usuario_admin(db, create_user):
    """Alias for create_user to match naming convention."""
    return create_user
