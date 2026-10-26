"""E2E tests conftest for the competencias module."""

# Loads the centralized fixture modules so their @pytest.fixture definitions
# are registered for the E2E suite (TEST_ARCHITECTURE_CONTRACT §3.3).
from modules.competencias.tests.fixtures import (  # noqa: F401
    competencias_fixtures,
    e2e_competencias_fixtures,
)
