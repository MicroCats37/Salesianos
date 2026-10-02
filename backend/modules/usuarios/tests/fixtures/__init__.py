"""
Fixtures package — all test fixtures for usuarios module.
"""
from modules.usuarios.tests.fixtures.usuarios_fixtures import (
    api_client,
    create_user,
    auth_client,
    usuario_admin,
)
from modules.usuarios.tests.fixtures.registro_fixtures import (
    registro_api_client,
    registro_base_setup,
)

__all__ = [
    "api_client",
    "create_user",
    "auth_client",
    "usuario_admin",
    "registro_api_client",
    "registro_base_setup",
]
