"""Integration tests conftest for salesianos_fest."""

# Loads the centralized fixture modules so their @pytest.fixture definitions
# are registered for the integration suite (TEST_ARCHITECTURE_CONTRACT §3.3).
from modules.salesianos_fest.tests.fixtures import (  # noqa: F401
    genero_participacion_fixtures,
)
