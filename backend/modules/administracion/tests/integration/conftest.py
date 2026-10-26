"""
Integration tests conftest — loads the fixture modules for pytest discovery
(`contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3).
"""
from modules.administracion.tests.fixtures import (
    evento_fixtures,
    fest_fixtures,
    usuarios_fixtures,
)
