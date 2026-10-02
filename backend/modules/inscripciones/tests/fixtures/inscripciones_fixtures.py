"""
Inscripciones-specific fixtures — domain entity factories for tests.

Provides fixtures for creating:
- Disciplina, Categoria (sport/discipline)
- Paquete, PaqueteDisciplina (package/product)
- Evento (event)
- Persona, Usuario with persona_fk (authenticated user with linked persona)
"""
import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model

from modules.inscripciones.domain.models import (
    Disciplina,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    Evento,
    Promocion,
)
from modules.inscripciones.domain.constants import ModalidadChoices, ModoDisciplinasPaqueteChoices
from modules.usuarios.domain.constants import GeneroChoices
from ninja_jwt.tokens import AccessToken


# ── Discipline & Category Fixtures ────────────────────────────────────────────


@pytest.fixture
def disciplina_futbol(db):
    """Active Futbol (Futsal) discipline."""
    return Disciplina.objects.create(
        nombre="Fútbol Sala",
        sigla="FS",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=5,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def disciplina_basket(db):
    """Active Basketball discipline."""
    return Disciplina.objects.create(
        nombre="Básquet",
        sigla="BK",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=5,
        max_jugadores=12,
        esta_activa=True,
    )


@pytest.fixture
def categoria_senior(db, disciplina_futbol):
    """Senior category for Futbol discipline."""
    return Categoria.objects.create(
        disciplina=disciplina_futbol,
        nombre="Senior",
        anio_minimo=2003,
        anio_maximo=2005,
        esta_activa=True,
    )


@pytest.fixture
def categoria_junior(db, disciplina_futbol):
    """Junior category for Futbol discipline."""
    return Categoria.objects.create(
        disciplina=disciplina_futbol,
        nombre="Junior",
        anio_minimo=2006,
        anio_maximo=2008,
        esta_activa=True,
    )


# ── Package Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def paquete_basic(db):
    """Basic inscription package."""
    return Paquete.objects.create(
        nombre="Paquete Basic",
        descripcion="Paquete básico para una disciplina",
        cantidad_maxima_participantes=15,
        precio_regular=150.00,
        precio_promocional=120.00,
        valido_desde=date.today() - timedelta(days=30),
        valido_hasta=date.today() + timedelta(days=60),
        esta_activo=True,
        modo_disciplinas=ModoDisciplinasPaqueteChoices.ELEGIBLE,
        cantidad_disciplinas_requeridas=1,
    )


@pytest.fixture
def paquete_disciplina_futbol(db, paquete_basic, disciplina_futbol):
    """Link pacote_basic to futbol discipline."""
    return PaqueteDisciplina.objects.create(
        paquete=paquete_basic,
        disciplina=disciplina_futbol,
    )


# ── Evento Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def evento_activo(db):
    """Active Salesianos FEST event."""
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date.today() + timedelta(days=30),
        fecha_fin=date.today() + timedelta(days=90),
        esta_activo=True,
    )


@pytest.fixture
def promocion_test(db):
    """Test promotion."""
    return Promocion.objects.create(
        anio=2025,
        nombre="Promoción 2025",
        activa=True,
    )


# ── Persona + Usuario Fixtures ─────────────────────────────────────────────────


@pytest.fixture
def persona_simple(db):
    """A Persona without linked Usuario (just identity data)."""
    from modules.usuarios.domain.models import Persona
    return Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="87654321",
        nombres="Carlos",
        apellidos="Responsable",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def usuario_con_persona(db, persona_simple):
    """A Usuario with persona_fk linked — for authenticated requests."""
    User = get_user_model()
    user = User.objects.create_user(
        username="user_con_persona",
        email="user_persona@example.com",
        password="testpass123",
        persona_fk=persona_simple,
    )
    return user


@pytest.fixture
def auth_client_con_persona(api_client, usuario_con_persona):
    """JWT-authenticated client with a user that has persona_fk linked."""
    token = AccessToken.for_user(usuario_con_persona)
    api_client.headers.update({"Authorization": f"Bearer {token}"})
    api_client.user = usuario_con_persona
    return api_client


# ── Composite Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def base_inscripcion_setup(
    db,
    evento_activo,
    paquete_basic,
    paquete_disciplina_futbol,
    disciplina_futbol,
    categoria_senior,
    promocion_test,
):
    """Base setup for inscription tests: event + package + discipline + category + promocion."""
    return {
        "evento": evento_activo,
        "paquete": paquete_basic,
        "paquete_disciplina": paquete_disciplina_futbol,
        "disciplina": disciplina_futbol,
        "categoria": categoria_senior,
        "promocion": promocion_test,
    }

