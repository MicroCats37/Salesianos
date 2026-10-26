"""
Conftest for pagos integration tests.

Provides standalone fixtures for Izipay testing without depending on modules.inscripciones.
Provides a mock IzipayClient to bypass settings validation in tests.
"""
import pytest
from unittest.mock import patch

from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.infrastructure import VerificadorFirmaIzipay
from modules.pagos.tests.fixtures.ownership_fakes import PropietarioOrdenPagoFake
from modules.pagos.tests.fixtures.settlement_fakes import ConfirmadorOrdenPagoFake


@pytest.fixture
def confirmador_orden_pago():
    """
    Fake commercial settlement port.

    Records the calls it receives and never touches the DB — the real
    settlement is covered by the salesianos_fest adapter tests.
    """
    return ConfirmadorOrdenPagoFake()


@pytest.fixture
def propietario_orden_pago():
    """
    Fake payment-order ownership port.

    By default it owns every order, so the tests that are not about
    ownership do not need to model a purchase.
    """
    return PropietarioOrdenPagoFake()


@pytest.fixture
def verificador_firma():
    """Signature verifier without a merchant key (verification unavailable)."""
    return VerificadorFirmaIzipay(key_hash="")


@pytest.fixture
def verificacion_pago():
    """Pure correlation helper of the provider payload."""
    return VerificacionPagoService()


@pytest.fixture
def api_client(db):
    """Django test client — it handles the async controllers correctly."""
    from django.test import Client

    return Client()


@pytest.fixture(autouse=True)
def mock_izipay_client():
    """
    Mock IzipayClient.__init__ to bypass settings validation (IZIPAY_SHOP_ID, IZIPAY_KEY)
    during tests. Without this, DI construction of PagosOrchestrator fails because
    IzipayClient.__init__ raises IzipayError when settings are not set.
    """
    def noop_init(self):
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
