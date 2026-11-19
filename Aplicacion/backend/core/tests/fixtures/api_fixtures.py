"""Fixtures de API compartidas del núcleo (A0).

Freeze: `FREEZE-TC-1.0.0` (evidence/contracts/FR-01 §7.2).
"""

import pytest


@pytest.fixture
def api_client():
    """Cliente HTTP asíncrono del API, sin autenticación.

    `ninja_extra.testing.TestAsyncClient` es el cliente que FREEZE-TC-1.0.0
    fija para los controllers `async def` (la regla por defecto del proyecto).
    `ninja.testing.TestClient` y `ninja_extra.testing.TestClient` están
    PROHIBIDOS contra un controller async.
    """
    from ninja_extra.testing import TestAsyncClient

    from config.api import api

    return TestAsyncClient(api)


@pytest.fixture
def django_client(db):
    """Cliente HTTP síncrono de Django, sin autenticación.

    Alternativa síncrona permitida por FREEZE-TC-1.0.0 para controllers
    `async def` (los tests son `def` normales).
    """
    from django.test import Client

    return Client()


@pytest.fixture
def api():
    """Instancia viva de `NinjaExtraAPI` (`config/api.py`)."""
    from config.api import api as ninja_api

    return ninja_api
