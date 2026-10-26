"""
Integration tests — EventoSelector (read-only query surface of the eventos
module).

The active-event resolution belongs to the `eventos` module: the frontend
never sends `evento_id`, the backend derives it from
`settings.EVENTO_ACTIVO_NOMBRE`.
"""
from datetime import date

import pytest

from modules.eventos.domain.models import Evento
from modules.eventos.domain.selectors.evento_selector import EventoSelector


@pytest.fixture
def evento(db):
    """Active event of the test."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )


@pytest.fixture
def evento_inactivo(db):
    """Inactive event of the test."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2025",
        fecha_inicio=date(2025, 11, 15),
        fecha_fin=date(2025, 11, 20),
        esta_activo=False,
    )


@pytest.fixture
def selector():
    """The event selector."""
    return EventoSelector()


# ── obtener_por_id ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_obtener_por_id_devuelve_el_evento(selector, evento):
    """GIVEN: an existing event WHEN: fetched by id THEN: it is returned."""
    assert selector.obtener_por_id(str(evento.id)) == evento


@pytest.mark.django_db
def test_obtener_por_id_desconocido_devuelve_none(selector, db):
    """GIVEN: an unknown id WHEN: fetched THEN: None (never an exception)."""
    assert selector.obtener_por_id("00000000-0000-0000-0000-000000000000") is None


# ── obtener_por_nombre / obtener_activo_por_nombre ───────────────────────────


@pytest.mark.django_db
def test_obtener_por_nombre(selector, evento):
    """GIVEN: an existing event WHEN: fetched by name THEN: it is returned."""
    assert selector.obtener_por_nombre("Salesianos FEST 2026") == evento


@pytest.mark.django_db
def test_obtener_activo_por_nombre(selector, evento):
    """GIVEN: an ACTIVE event WHEN: fetched by name THEN: it is returned."""
    assert selector.obtener_activo_por_nombre("Salesianos FEST 2026") == evento


@pytest.mark.django_db
def test_obtener_activo_por_nombre_ignora_los_inactivos(
    selector, evento_inactivo
):
    """
    GIVEN: an INACTIVE event
    WHEN:  it is fetched as the active one
    THEN:  None — the active flag is respected.
    """
    assert selector.obtener_activo_por_nombre("Salesianos FEST 2025") is None


@pytest.mark.django_db
def test_obtener_activo_por_nombre_inexistente_devuelve_none(selector, db):
    """GIVEN: an unknown name WHEN: fetched THEN: None."""
    assert selector.obtener_activo_por_nombre("No existe") is None


# ── obtener_activo ────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_obtener_activo_devuelve_el_evento_activo(selector, evento, evento_inactivo):
    """GIVEN: one active and one inactive event WHEN: fetched THEN: the active."""
    assert selector.obtener_activo() == evento


@pytest.mark.django_db
def test_obtener_activo_sin_eventos_devuelve_none(selector, db):
    """GIVEN: an empty database WHEN: fetched THEN: None."""
    assert selector.obtener_activo() is None


# ── listar ────────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_listar_devuelve_todos_los_eventos(selector, evento, evento_inactivo):
    """GIVEN: two events WHEN: listed THEN: both are returned."""
    assert list(selector.listar()) == [evento, evento_inactivo]


@pytest.mark.django_db
def test_listar_solo_activos_excluye_los_inactivos(
    selector, evento, evento_inactivo
):
    """GIVEN: two events WHEN: listed as active only THEN: only the active one."""
    assert list(selector.listar(solo_activos=True)) == [evento]


@pytest.mark.django_db
def test_listar_ordena_por_edicion_mas_reciente(selector, evento, evento_inactivo):
    """
    GIVEN: two events of different editions
    WHEN:  listed
    THEN:  the most recent edition comes first.
    """
    assert list(selector.listar()) == [evento, evento_inactivo]
