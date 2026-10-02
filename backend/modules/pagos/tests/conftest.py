"""
Conftest for pagos integration tests.

Re-exports fixtures from Inscripciones tests that are needed for Izipay testing.
Provides a mock IzipayClient to bypass settings validation in tests.
"""
import pytest
from unittest.mock import MagicMock, patch

from modules.inscripciones.tests.fixtures.inscripciones_fixtures import (
    evento_activo,
    paquete_basic,
    paquete_disciplina_futbol,
    disciplina_futbol,
    disciplina_basket,
    categoria_senior,
    categoria_junior,
    promocion_test,
    persona_simple,
    base_inscripcion_setup,
    usuario_con_persona,
)
from modules.inscripciones.tests.fixtures.usuarios_fixtures import (
    api_client,
    create_user,
    auth_client,
    usuario_admin,
)


@pytest.fixture(autouse=True)
def mock_izipay_client():
    """
    Mock IzipayClient.__init__ to bypass settings validation (IZIPAY_SHOP_ID, IZIPAY_KEY)
    during tests. Without this, DI construction of PagosOrchestrator fails because
    IzipayClient.__init__ raises IzipayError when settings are not set.

    Patches __init__ (method patch survives class-object identity in injector bindings)
    at TWO locations to cover all import paths used by the injector.
    """
    # Mock __init__ so it doesn't validate settings
    def noop_init(self):
        # Skip the real __init__ that calls _validate_settings()
        # Just set dummy attributes the service might access
        self.shop_id = "TEST_SHOP_ID"
        self.api_key = "TEST_API_KEY"
        self.api_url = "https://test.example.com"
        self.callback_url = "https://test.example.com/callback"

    with patch(
        "modules.pagos.infrastructure.services.IzipayClient.__init__",
        noop_init,
    ), patch(
        "modules.pagos.infrastructure.IzipayClient.__init__",
        noop_init,
    ):
        yield
