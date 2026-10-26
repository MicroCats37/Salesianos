"""
Administracion test fixtures — the active event of the test.

The administration surface resolves the active event SERVER-SIDE from
`settings.EVENTO_ACTIVO_NOMBRE`; the fixture creates the event with exactly
that name so the resolution finds it.
"""
from datetime import date

import pytest
from django.conf import settings

from modules.eventos.domain.models import Evento


@pytest.fixture
def evento(db):
    """Active event matching `EVENTO_ACTIVO_NOMBRE`."""
    return Evento.objects.create(
        nombre=settings.EVENTO_ACTIVO_NOMBRE,
        fecha_inicio=date(2026, 11, 15),
        fecha_fin=date(2026, 11, 20),
        esta_activo=True,
    )
