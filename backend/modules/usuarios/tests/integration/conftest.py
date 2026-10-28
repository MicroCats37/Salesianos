"""
Integration tests conftest — loads fixture modules for pytest discovery.
"""
from modules.usuarios.tests.fixtures.persona_resolucion_fixtures import (  # noqa: F401
    persona_registrada,
    persona_registrada_ce,
)
from modules.usuarios.tests.fixtures import (
    usuarios_fixtures,
    registro_fixtures,
)
