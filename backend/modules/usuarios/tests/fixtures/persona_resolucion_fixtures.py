"""
Fixtures for the exact identity lookup of an existing `Persona`.

The persons are created with a KNOWN civil identity so the tests can assert
the EXACT match (and the absence of any fuzzy behaviour).
"""
import pytest

from modules.usuarios.domain.models.persona import Persona


@pytest.fixture
def persona_registrada(db):
    """A registered person with a known DNI."""
    return Persona.objects.create(
        nombres="Ana",
        apellidos="Pérez",
        tipo_documento="DNI",
        numero_documento="79000001",
        genero="F",
    )


@pytest.fixture
def persona_registrada_ce(db):
    """A registered person with a known CE (same number, other type)."""
    return Persona.objects.create(
        nombres="Luis",
        apellidos="Quispe",
        tipo_documento="CE",
        numero_documento="79000001",
        genero="M",
    )
