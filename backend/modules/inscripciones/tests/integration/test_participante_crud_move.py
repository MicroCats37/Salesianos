"""
Integration tests for participant CRUD/move operations.

Tests:
- Edit participant rol/talle success
- Delete participant removes link and detail no longer lists it
- Move participant to another equipo same inscription success
- Move to equipo from another inscription rejected
- Move to target discipline where R11 duplicate exists returns controlled error

Uses @pytest.mark.django_db for database access.
Authentication via JWT Bearer token in the Authorization header.
"""
import json
import pytest
from asgiref.sync import sync_to_async

from config.api import api
from django.test import AsyncClient
from ninja_jwt.tokens import AccessToken
from django.contrib.auth import get_user_model

from modules.inscripciones.domain.models import (
    Disciplina,
    Paquete,
    PaqueteDisciplina,
    Evento,
    Promocion,
    Categoria,
    EquipoInscrito,
    ParticipacionDisciplina,
    ParticipanteInscripcion,
    Inscripcion,
)
from modules.inscripciones.domain.constants import ModalidadChoices, ModoDisciplinasPaqueteChoices
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.constants import GeneroChoices


# ── Sync Helpers ───────────────────────────────────────────────────────────────


def _make_token(user) -> str:
    """Generate JWT token for user (sync)."""
    return str(AccessToken.for_user(user))


def _create_discIPLINA_futbol():
    """Create Futbol discipline."""
    return Disciplina.objects.create(
        nombre="Fútbol Sala",
        sigla="FS",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=5,
        max_jugadores=10,
        esta_activa=True,
    )


def _create_discIPLINA_basket():
    """Create Basketball discipline."""
    return Disciplina.objects.create(
        nombre="Básquet",
        sigla="BK",
        modalidad=ModalidadChoices.MASCULINO,
        min_jugadores=5,
        max_jugadores=12,
        esta_activa=True,
    )


def _create_paquete_multi(disciplina_futbol, disciplina_basket):
    """Create package with both disciplines."""
    from datetime import date, timedelta
    paquete = Paquete.objects.create(
        nombre="Paquete Multi",
        descripcion="Paquete para dos disciplinas",
        cantidad_maxima_participantes=20,
        precio_regular=250.00,
        precio_promocional=200.00,
        valido_desde=date.today() - timedelta(days=30),
        valido_hasta=date.today() + timedelta(days=60),
        esta_activo=True,
        modo_disciplinas=ModoDisciplinasPaqueteChoices.ELEGIBLE,
        cantidad_disciplinas_requeridas=2,
    )
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_futbol)
    PaqueteDisciplina.objects.create(paquete=paquete, disciplina=disciplina_basket)
    return paquete


def _create_evento():
    """Create active event."""
    from datetime import date, timedelta
    return Evento.objects.create(
        nombre="Salesianos FEST 2026",
        fecha_inicio=date.today() + timedelta(days=30),
        fecha_fin=date.today() + timedelta(days=90),
        esta_activo=True,
    )


def _create_promocion():
    """Create test promotion."""
    return Promocion.objects.create(
        anio=2025,
        nombre="Promoción 2025",
        activa=True,
    )


def _create_categoria(disciplina, nombre="Senior"):
    """Create a category for a discipline."""
    return Categoria.objects.create(
        disciplina=disciplina,
        nombre=nombre,
        anio_minimo=2003,
        anio_maximo=2005,
        esta_activa=True,
    )


def _create_persona(tipo_documento, numero_documento, nombres, apellidos, genero):
    """Create a persona."""
    return Persona.objects.create(
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
        nombres=nombres,
        apellidos=apellidos,
        genero=genero,
    )


def _create_usuario_con_persona(persona):
    """Create user with persona."""
    User = get_user_model()
    user = User.objects.create_user(
        username="user_con_persona",
        email="user_persona@example.com",
        password="testpass123",
        persona_fk=persona,
    )
    return user


def _create_inscripcion(evento, paquete, promocion, responsable):
    """Create inscription."""
    return Inscripcion.objects.create(
        evento=evento,
        paquete=paquete,
        promocion=promocion,
        responsable=responsable,
        estado="RECIBIDA",
    )


def _create_equipo(inscripcion, disciplina, categoria, nombre):
    """Create equipo."""
    return EquipoInscrito.objects.create(
        inscripcion=inscripcion,
        disciplina=disciplina,
        categoria=categoria,
        nombre=nombre,
    )


def _create_participacion(evento, disciplina, persona, equipo):
    """Create participacion."""
    return ParticipacionDisciplina.objects.create(
        evento=evento,
        disciplina=disciplina,
        persona=persona,
        equipo=equipo,
    )


def _create_participante(participacion, equipo, rol, talle_camiseta=None):
    """Create participante."""
    return ParticipanteInscripcion.objects.create(
        participacion=participacion,
        equipo=equipo,
        rol=rol,
        talle_camiseta=talle_camiseta,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_editar_participante_rol_talle_success():
    """
    GIVEN: Authenticated user, inscription with one equipo and one participant
    WHEN:  PATCH /api/inscripciones/{id}/participantes/{pid} with rol and talle_camiseta
    THEN:  Returns 200 and participant is updated
    """
    # Setup data in thread
    disciplina_futbol = await sync_to_async(_create_discIPLINA_futbol)()
    disciplina_basket = await sync_to_async(_create_discIPLINA_basket)()
    paquete = await sync_to_async(_create_paquete_multi)(disciplina_futbol, disciplina_basket)
    evento = await sync_to_async(_create_evento)()
    promocion = await sync_to_async(_create_promocion)()
    categoria = await sync_to_async(_create_categoria)(disciplina_futbol)
    persona_responsable = await sync_to_async(_create_persona)(
        "DNI", "87654321", "Carlos", "Responsable", GeneroChoices.MASCULINO
    )
    persona_participante = await sync_to_async(_create_persona)(
        "DNI", "12345678", "Juan", "Jugador", GeneroChoices.MASCULINO
    )
    usuario = await sync_to_async(_create_usuario_con_persona)(persona_responsable)

    inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, persona_responsable
    )
    equipo = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_futbol, categoria, "Equipo Fútbol"
    )
    participacion = await sync_to_async(_create_participacion)(
        evento, disciplina_futbol, persona_participante, equipo
    )
    participante = await sync_to_async(_create_participante)(
        participacion, equipo, "JUGADOR"
    )

    # Make request
    async_client = AsyncClient()
    token = await sync_to_async(_make_token)(usuario)

    response = await async_client.patch(
        f"/api/inscripciones/{inscripcion.id}/participantes/{participante.id}",
        data=json.dumps({"rol": "CAPITAN", "talle_camiseta": "L"}),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    result = data["data"]
    assert result["rol"] == "CAPITAN"
    assert result["talle_camiseta"] == "L"

    # Verify DB was updated
    await sync_to_async(participante.refresh_from_db)()
    assert participante.rol == "CAPITAN"
    assert participante.talle_camiseta == "L"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_editar_participante_solo_talle():
    """
    GIVEN: Authenticated user, inscription with participant
    WHEN:  PATCH with only talle_camiseta (rol unchanged)
    THEN:  Returns 200 and only talle_camiseta is updated
    """
    disciplina_futbol = await sync_to_async(_create_discIPLINA_futbol)()
    disciplina_basket = await sync_to_async(_create_discIPLINA_basket)()
    paquete = await sync_to_async(_create_paquete_multi)(disciplina_futbol, disciplina_basket)
    evento = await sync_to_async(_create_evento)()
    promocion = await sync_to_async(_create_promocion)()
    categoria = await sync_to_async(_create_categoria)(disciplina_futbol)
    persona_responsable = await sync_to_async(_create_persona)(
        "DNI", "87654321", "Carlos", "Responsable", GeneroChoices.MASCULINO
    )
    persona_participante = await sync_to_async(_create_persona)(
        "DNI", "12345678", "Juan", "Jugador", GeneroChoices.MASCULINO
    )
    usuario = await sync_to_async(_create_usuario_con_persona)(persona_responsable)

    inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, persona_responsable
    )
    equipo = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_futbol, categoria, "Equipo Fútbol"
    )
    participacion = await sync_to_async(_create_participacion)(
        evento, disciplina_futbol, persona_participante, equipo
    )
    participante = await sync_to_async(_create_participante)(
        participacion, equipo, "CAPITAN"
    )

    async_client = AsyncClient()
    token = await sync_to_async(_make_token)(usuario)

    response = await async_client.patch(
        f"/api/inscripciones/{inscripcion.id}/participantes/{participante.id}",
        data=json.dumps({"talle_camiseta": "XL"}),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    await sync_to_async(participante.refresh_from_db)()
    assert participante.rol == "CAPITAN"  # Unchanged
    assert participante.talle_camiseta == "XL"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_eliminar_participante_success():
    """
    GIVEN: Authenticated user, inscription with one participant
    WHEN:  DELETE /api/inscripciones/{id}/participantes/{pid}
    THEN:  Returns 200 and participant is removed from DB
    """
    disciplina_futbol = await sync_to_async(_create_discIPLINA_futbol)()
    disciplina_basket = await sync_to_async(_create_discIPLINA_basket)()
    paquete = await sync_to_async(_create_paquete_multi)(disciplina_futbol, disciplina_basket)
    evento = await sync_to_async(_create_evento)()
    promocion = await sync_to_async(_create_promocion)()
    categoria = await sync_to_async(_create_categoria)(disciplina_futbol)
    persona_responsable = await sync_to_async(_create_persona)(
        "DNI", "87654321", "Carlos", "Responsable", GeneroChoices.MASCULINO
    )
    persona_participante = await sync_to_async(_create_persona)(
        "DNI", "12345678", "Juan", "Jugador", GeneroChoices.MASCULINO
    )
    usuario = await sync_to_async(_create_usuario_con_persona)(persona_responsable)

    inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, persona_responsable
    )
    equipo = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_futbol, categoria, "Equipo Fútbol"
    )
    participacion = await sync_to_async(_create_participacion)(
        evento, disciplina_futbol, persona_participante, equipo
    )
    participante = await sync_to_async(_create_participante)(
        participacion, equipo, "JUGADOR"
    )
    participante_id = str(participante.id)

    async_client = AsyncClient()
    token = await sync_to_async(_make_token)(usuario)

    response = await async_client.delete(
        f"/api/inscripciones/{inscripcion.id}/participantes/{participante.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"

    # Verify deleted from DB
    exists = await sync_to_async(ParticipanteInscripcion.objects.filter(id=participante_id).exists)()
    assert not exists


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mover_participante_diferente_disciplina_success():
    """
    GIVEN: Authenticated user, inscription with equipos in different disciplines
           and participant in one disciplina
    WHEN:  PATCH .../participantes/{pid}/mover to equipo in different disciplina
    THEN:  Returns 200 and participant is moved with new ParticipacionDisciplina
    """
    disciplina_futbol = await sync_to_async(_create_discIPLINA_futbol)()
    disciplina_basket = await sync_to_async(_create_discIPLINA_basket)()
    paquete = await sync_to_async(_create_paquete_multi)(disciplina_futbol, disciplina_basket)
    evento = await sync_to_async(_create_evento)()
    promocion = await sync_to_async(_create_promocion)()
    categoria_futbol = await sync_to_async(_create_categoria)(disciplina_futbol)
    categoria_basket = await sync_to_async(_create_categoria)(disciplina_basket)
    persona_responsable = await sync_to_async(_create_persona)(
        "DNI", "87654321", "Carlos", "Responsable", GeneroChoices.MASCULINO
    )
    persona_participante = await sync_to_async(_create_persona)(
        "DNI", "12345678", "Juan", "Jugador", GeneroChoices.MASCULINO
    )
    usuario = await sync_to_async(_create_usuario_con_persona)(persona_responsable)

    inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, persona_responsable
    )
    # Source equipo in futbol
    equipo_origen = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_futbol, categoria_futbol, "Equipo Fútbol"
    )
    # Target equipo in basket
    equipo_destino = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_basket, categoria_basket, "Equipo Basket"
    )
    participacion = await sync_to_async(_create_participacion)(
        evento, disciplina_futbol, persona_participante, equipo_origen
    )
    participante = await sync_to_async(_create_participante)(
        participacion, equipo_origen, "JUGADOR"
    )

    async_client = AsyncClient()
    token = await sync_to_async(_make_token)(usuario)

    response = await async_client.patch(
        f"/api/inscripciones/{inscripcion.id}/participantes/{participante.id}/mover",
        data=json.dumps({"equipo_destino_id": str(equipo_destino.id)}),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    result = data["data"]
    assert result["equipo_id"] == str(equipo_destino.id)

    # Verify DB - refresh and check equipo was updated
    await sync_to_async(participante.refresh_from_db)()
    assert str(participante.equipo_id) == str(equipo_destino.id)
    # The participacion_id should now point to a new participation in basket discipline
    # We can verify by checking the response's participacion_id matches
    assert result["participacion_id"] == str(participante.participacion_id)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mover_participante_otro_equipo_diferente_inscripcion_rechazado():
    """
    GIVEN: Authenticated user, inscription with equipo, and another inscription with equipo
    WHEN:  PATCH .../participantes/{pid}/mover to equipo from different inscription
    THEN:  Returns 400 error (BusinessError)
    """
    disciplina_futbol = await sync_to_async(_create_discIPLINA_futbol)()
    disciplina_basket = await sync_to_async(_create_discIPLINA_basket)()
    paquete = await sync_to_async(_create_paquete_multi)(disciplina_futbol, disciplina_basket)
    evento = await sync_to_async(_create_evento)()
    promocion = await sync_to_async(_create_promocion)()
    categoria_futbol = await sync_to_async(_create_categoria)(disciplina_futbol)
    categoria_basket = await sync_to_async(_create_categoria)(disciplina_basket)
    persona_responsable = await sync_to_async(_create_persona)(
        "DNI", "87654321", "Carlos", "Responsable", GeneroChoices.MASCULINO
    )
    persona_participante = await sync_to_async(_create_persona)(
        "DNI", "12345678", "Juan", "Jugador", GeneroChoices.MASCULINO
    )
    otra_persona = await sync_to_async(_create_persona)(
        "DNI", "99999999", "Otro", "Usuario", GeneroChoices.MASCULINO
    )
    usuario = await sync_to_async(_create_usuario_con_persona)(persona_responsable)

    # User's inscription
    inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, persona_responsable
    )
    equipo_origen = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_futbol, categoria_futbol, "Equipo Origen"
    )

    # Another inscription (different user)
    otra_inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, otra_persona
    )
    equipo_externo = await sync_to_async(_create_equipo)(
        otra_inscripcion, disciplina_basket, categoria_basket, "Equipo Externo"
    )

    participacion = await sync_to_async(_create_participacion)(
        evento, disciplina_futbol, persona_participante, equipo_origen
    )
    participante = await sync_to_async(_create_participante)(
        participacion, equipo_origen, "JUGADOR"
    )

    async_client = AsyncClient()
    token = await sync_to_async(_make_token)(usuario)

    response = await async_client.patch(
        f"/api/inscripciones/{inscripcion.id}/participantes/{participante.id}/mover",
        data=json.dumps({"equipo_destino_id": str(equipo_externo.id)}),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Should return error (400 or 409 depending on where validation happens)
    assert response.status_code in (400, 409), f"Expected 400/409, got {response.status_code}: {response.content}"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_editar_participante_inscripcion_ajena_rechazado():
    """
    GIVEN: Authenticated user tries to edit a participant from another user's inscription
    WHEN:  PATCH /api/inscripciones/{id}/participantes/{pid}
    THEN:  Returns 404 or 400 (participant not found in user's inscription)
    """
    disciplina_futbol = await sync_to_async(_create_discIPLINA_futbol)()
    disciplina_basket = await sync_to_async(_create_discIPLINA_basket)()
    paquete = await sync_to_async(_create_paquete_multi)(disciplina_futbol, disciplina_basket)
    evento = await sync_to_async(_create_evento)()
    promocion = await sync_to_async(_create_promocion)()
    categoria_futbol = await sync_to_async(_create_categoria)(disciplina_futbol)
    persona_responsable = await sync_to_async(_create_persona)(
        "DNI", "87654321", "Carlos", "Responsable", GeneroChoices.MASCULINO
    )
    persona_participante = await sync_to_async(_create_persona)(
        "DNI", "12345678", "Juan", "Jugador", GeneroChoices.MASCULINO
    )
    otra_persona = await sync_to_async(_create_persona)(
        "DNI", "99999999", "Otro", "Usuario", GeneroChoices.MASCULINO
    )
    usuario = await sync_to_async(_create_usuario_con_persona)(persona_responsable)

    # Another user's inscription
    otra_inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, otra_persona
    )
    equipo = await sync_to_async(_create_equipo)(
        otra_inscripcion, disciplina_futbol, categoria_futbol, "Equipo"
    )
    participacion = await sync_to_async(_create_participacion)(
        evento, disciplina_futbol, persona_participante, equipo
    )
    participante = await sync_to_async(_create_participante)(
        participacion, equipo, "JUGADOR"
    )

    async_client = AsyncClient()
    token = await sync_to_async(_make_token)(usuario)

    # Try to edit using user's own inscripcion_id but other's participante_id
    response = await async_client.patch(
        f"/api/inscripciones/{otra_inscripcion.id}/participantes/{participante.id}",
        data=json.dumps({"rol": "CAPITAN"}),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Should return error (404 or 400)
    assert response.status_code in (400, 404), f"Expected 400/404, got {response.status_code}: {response.content}"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_mover_participante_r11_duplicado_retorna_error_controlado():
    """
    GIVEN: Authenticated user, inscription with participant in disciplina_futbol
           and another equipo in disciplina_basket where persona already exists
    WHEN:  Move participant to disciplina_basket equipo (R11 duplicate)
    THEN:  Returns 409 Conflict with ParticipacionDuplicadaError
    """
    disciplina_futbol = await sync_to_async(_create_discIPLINA_futbol)()
    disciplina_basket = await sync_to_async(_create_discIPLINA_basket)()
    paquete = await sync_to_async(_create_paquete_multi)(disciplina_futbol, disciplina_basket)
    evento = await sync_to_async(_create_evento)()
    promocion = await sync_to_async(_create_promocion)()
    categoria_futbol = await sync_to_async(_create_categoria)(disciplina_futbol)
    categoria_basket = await sync_to_async(_create_categoria)(disciplina_basket)
    persona_responsable = await sync_to_async(_create_persona)(
        "DNI", "87654321", "Carlos", "Responsable", GeneroChoices.MASCULINO
    )
    persona_participante = await sync_to_async(_create_persona)(
        "DNI", "12345678", "Juan", "Jugador", GeneroChoices.MASCULINO
    )
    usuario = await sync_to_async(_create_usuario_con_persona)(persona_responsable)

    inscripcion = await sync_to_async(_create_inscripcion)(
        evento, paquete, promocion, persona_responsable
    )
    equipo_futbol = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_futbol, categoria_futbol, "Equipo Fútbol"
    )
    equipo_basket = await sync_to_async(_create_equipo)(
        inscripcion, disciplina_basket, categoria_basket, "Equipo Basket"
    )

    # Participant in futbol
    participacion_futbol = await sync_to_async(_create_participacion)(
        evento, disciplina_futbol, persona_participante, equipo_futbol
    )
    participante = await sync_to_async(_create_participante)(
        participacion_futbol, equipo_futbol, "JUGADOR"
    )

    # Same persona already in basket (R11 violation)
    await sync_to_async(_create_participacion)(
        evento, disciplina_basket, persona_participante, equipo_basket
    )

    async_client = AsyncClient()
    token = await sync_to_async(_make_token)(usuario)

    response = await async_client.patch(
        f"/api/inscripciones/{inscripcion.id}/participantes/{participante.id}/mover",
        data=json.dumps({"equipo_destino_id": str(equipo_basket.id)}),
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Should return 409 Conflict
    assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.content}"
