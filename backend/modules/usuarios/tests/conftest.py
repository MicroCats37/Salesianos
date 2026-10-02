"""
Shared fixtures index for usuarios integration tests.

Re-exports all fixtures from fixtures/ subpackage for pytest discovery.

Factories (make_payload_*) are NOT re-exported — import directly:
    from modules.usuarios.tests.fixtures.factories import make_payload_registro
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
