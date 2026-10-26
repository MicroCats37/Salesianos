"""
Shared fixtures index for the administracion tests.

Re-exports all fixtures from `fixtures/` for pytest discovery
(`contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3).
"""
from modules.administracion.tests.fixtures.evento_fixtures import evento
from modules.administracion.tests.fixtures.fest_fixtures import (
    escenario_operativo,
    escenario_otra_edicion,
    escenario_paginacion,
)
from modules.administracion.tests.fixtures.usuarios_fixtures import (
    api_client,
    usuario_admin_staff,
    usuario_admin_superuser,
    usuario_inactivo,
    usuario_no_admin,
)
