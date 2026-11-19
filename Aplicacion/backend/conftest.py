"""
conftest.py — Fixtures globales para tests de CAM.

Inspirado en: centro-de-esparcimiento/backend/conftest.py
"""
import os

os.environ.setdefault("NINJA_SKIP_REGISTRY", "1")

# Force CIP simulator in tests to avoid real HTTP calls to external CIP API.
# This overrides development.py's CIP_USE_SIMULATOR = False so that
# test_ingeniero_habilitado_integration.py and other tests using the
# ICipClient dependency get CipClientSimulator instead of RealCipClient.
os.environ["CIP_USE_SIMULATOR"] = "True"

import pytest
from pathlib import Path


# ── Test database cleanup ───────────────────────────────────────────
@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    """Remove stale test_db.sqlite3 before the test session to avoid stale row collisions."""
    test_db = Path(__file__).resolve().parent.parent / "test_db.sqlite3"
    if test_db.exists():
        os.remove(test_db)
    yield
    # No post-run cleanup — keep it for debugging if tests fail


# ── Django test client (sync) ───────────────────────────────────────

@pytest.fixture
def client(db):
    """Django test client (sync) — usa Django's test Client, no Ninja TestClient.

    Para tests de integración que usan Django test Client (no NinjaExtra).
    El db fixture asegura que la base SQLite en memoria esté lista.
    """
    from django.test import Client
    return Client()


# ── Clientes de prueba HTTP (FREEZE-TC-1.0.0) ───────────────────────────────
#
# FREEZE-TC-1.0.0 (evidence/contracts/FR-01 §7.2) fija el cliente por tipo de
# controller:
#
#   controller `async def` (regla por defecto del proyecto)
#       → ninja_extra.testing.TestAsyncClient(api)
#   controller `def` síncrono
#       → ninja_extra.testing.TestClient(api)  (o ninja.testing.TestClient)
#
# PROHIBIDO, sin excepción, contra un controller `async def`:
# `ninja.testing.TestClient` y `ninja_extra.testing.TestClient`. El primero
# además es incompatible con `NinjaExtraAPI` (`build_routers`). La alternativa
# síncrona permitida para controllers async es `django.test.Client`.
#
# La deuda documentada (GOV-01-OPEN-01): el texto de
# `contract/TEST_ARCHITECTURE_CONTRACT.md` §2 y §10.5 sigue mandando el cliente
# síncrono; su enmienda corresponde a GAP-2 (A0 + producto) y NO se modifica
# `contract/**` desde aquí.

def _get_ninja_api():
    """Obtiene la instancia de NinjaExtraAPI para usar en tests."""
    from config.api import api
    return api


def _get_override_dict():
    """Resolve dependency_overrides dict for NinjaExtraAPI."""
    ninja_api = _get_ninja_api()
    if hasattr(ninja_api, 'dependency_overrides'):
        return ninja_api.dependency_overrides
    app = getattr(ninja_api, 'app', None)
    if app is not None and hasattr(app, 'dependency_overrides'):
        return app.dependency_overrides
    return {}


@pytest.fixture
def test_sync_client(db):
    """Cliente Django (síncrono) sin autenticación.

    Es la alternativa síncrona PERMITIDA por FREEZE-TC-1.0.0 para controllers
    `async def`: maneja las corrutinas internamente.
    """
    from django.test import Client
    return Client()


@pytest.fixture
def api():
    """NinjaExtraAPI instance from config/api.py."""
    return _get_ninja_api()


@pytest.fixture
def test_async_client(db):
    """Cliente asíncrono OBLIGATORIO para controllers `async def`.

    `ninja_extra.testing.TestAsyncClient` espera la corrutina del controller;
    `ninja.testing.TestAsyncClient` no es el cliente que fija FREEZE-TC-1.0.0.
    """
    from ninja_extra.testing import TestAsyncClient
    return TestAsyncClient(_get_ninja_api())
