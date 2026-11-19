"""Fixtures compartidas del módulo `eventos`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3

Las fixtures viven aquí; `modules/eventos/tests/conftest.py` sólo las importa y
registra.
"""

import pytest

from modules.eventos.domain.constants import EstadoEdicion
from modules.eventos.domain.models import Edicion, Evento
from modules.eventos.domain.selectors.edicion_selector import EdicionSelector
from modules.eventos.domain.selectors.evento_selector import EventoSelector
from modules.eventos.domain.services.core.edicion_core_service import EdicionCoreService
from modules.eventos.domain.services.core.edicion_scope_service import EdicionScopeService


# ── Datos ───────────────────────────────────────────────────────────────────


@pytest.fixture
def evento(db):
    """Evento propietario de las ediciones del test."""
    return Evento.objects.create(nombre="Salesianos FEST", slug="salesianos-fest")


@pytest.fixture
def evento_otro(db):
    """Segundo evento: permite comprobar el aislamiento entre familias."""
    return Evento.objects.create(nombre="Otro FEST", slug="otro-fest")


@pytest.fixture
def edicion_borrador(db, evento):
    """Edición en `BORRADOR` (estado por defecto)."""
    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
    )


@pytest.fixture
def edicion_publicada(db, evento):
    """Edición `PUBLICADA` del evento principal."""
    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2027",
        slug="2027",
        anio=2027,
        estado=EstadoEdicion.PUBLICADA,
    )


@pytest.fixture
def edicion_cerrada(db, evento):
    """Edición `CERRADA`: el histórico que debe seguir siendo consultable."""
    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2025",
        slug="2025",
        anio=2025,
        estado=EstadoEdicion.CERRADA,
    )


# ── Servicios ───────────────────────────────────────────────────────────────


@pytest.fixture
def evento_selector():
    """Selector de eventos."""
    return EventoSelector()


@pytest.fixture
def edicion_selector():
    """Selector de ediciones."""
    return EdicionSelector()


@pytest.fixture
def scope_service(edicion_selector):
    """Servicio de resolución de alcance."""
    return EdicionScopeService(selector=edicion_selector)


@pytest.fixture
def core_service(edicion_selector, evento_selector):
    """Servicio de escritura."""
    return EdicionCoreService(
        edicion_selector=edicion_selector,
        evento_selector=evento_selector,
    )
