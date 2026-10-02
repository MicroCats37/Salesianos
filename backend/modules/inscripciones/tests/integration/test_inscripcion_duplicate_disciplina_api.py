"""
Integration tests for duplicate discipline teams via the full inscription API flow.

These tests exercise the complete HTTP API path — from controller through
CrearInscripcionFlujo to the database — proving that the backend now accepts
duplicate discipline selections when the package's cantidad_maxima_equipos
allows multiple teams (frontend permiteDuplicados=true).

Coverage:
- ELEGIBLE mode: two equipos with the same disciplina are accepted via the API
- Service-layer duplicate blocking is gone (proven by prior test)
- API-level distinct-discipline validation is replaced by team-count validation
"""
import pytest
from django.test import AsyncClient
from asgiref.sync import sync_to_async
from datetime import date, timedelta

from config.api import api
from modules.inscripciones.domain.models import (
    Paquete,
    PaqueteDisciplina,
    Disciplina,
    Evento,
    Promocion,
)
from modules.inscripciones.domain.constants import ModoDisciplinasPaqueteChoices
from modules.inscripciones.tests.fixtures.factories import (
    make_inscripcion_payload,
    make_equipo_payload,
)
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.constants import GeneroChoices


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def paquete_permite_duplicados(db):
    """
    A package in ELEGIBLE mode that has cantidad_maxima_equipos=2 (via
    cantidad_disciplinas_requeridas=2) but only 1 disciplina linked.

    This means:
    - cantidad_maxima_equipos = 2 (derived from cantidad_disciplinas_requeridas)
    - paquete_disciplinas.count() = 1
    - permiteDuplicados = 2 > 1 = True (frontend allows same disciplina twice)

    Two equipos with the same disciplina must be accepted by the API.
    """
    paquete = Paquete.objects.create(
        nombre="Paquete Duplicados Test",
        descripcion="Paquete para probar disciplinas duplicadas",
        cantidad_maxima_participantes=20,
        precio_regular=200.00,
        precio_promocional=None,
        valido_desde=date.today() - timedelta(days=30),
        valido_hasta=date.today() + timedelta(days=60),
        esta_activo=True,
        modo_disciplinas=ModoDisciplinasPaqueteChoices.ELEGIBLE,
        cantidad_disciplinas_requeridas=2,
    )
    return paquete


@pytest.fixture
def disciplina_unica(db):
    """The single disciplina linked to paquete_permite_duplicados."""
    return Disciplina.objects.create(
        nombre="Fútbol Sala",
        sigla="FS",
        modalidad="M",
        min_jugadores=5,
        max_jugadores=10,
        esta_activa=True,
    )


@pytest.fixture
def paquete_disciplina_unica(db, paquete_permite_duplicados, disciplina_unica):
    """Link the single disciplina to the package."""
    return PaqueteDisciplina.objects.create(
        paquete=paquete_permite_duplicados,
        disciplina=disciplina_unica,
    )


@pytest.fixture
def evento_test_duplicados(db):
    """Active event for duplicate discipline tests."""
    return Evento.objects.create(
        nombre="Salesianos FEST Duplicate Test",
        fecha_inicio=date.today() + timedelta(days=30),
        fecha_fin=date.today() + timedelta(days=90),
        esta_activo=True,
    )


@pytest.fixture
def promocion_duplicados(db):
    """Promocion for duplicate discipline tests."""
    return Promocion.objects.create(
        anio=2026,
        nombre="Promoción Duplicate Test",
        activa=True,
    )


@pytest.fixture
def persona_duplicados(db):
    """A Persona without linked Usuario for duplicate discipline tests."""
    return Persona.objects.create(
        tipo_documento="DNI",
        numero_documento="12345678",
        nombres="Carlos",
        apellidos="Duplicado",
        genero=GeneroChoices.MASCULINO,
    )


@pytest.fixture
def usuario_duplicados(db, persona_duplicados):
    """A Usuario linked to persona_duplicados for authenticated requests."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    user = User.objects.create_user(
        username="user_duplicados",
        email="duplicados@example.com",
        password="testpass123",
        persona_fk=persona_duplicados,
    )
    return user


@pytest.fixture
def async_auth_client_duplicados(db, usuario_duplicados):
    """AsyncClient with JWT token for duplicate discipline tests."""
    return AsyncClient()


def _make_token(user) -> str:
    """Generate JWT token for user (sync, call in thread)."""
    from ninja_jwt.tokens import AccessToken
    return str(AccessToken.for_user(user))


# ── Tests ───────────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_api_acepta_dos_equipos_misma_disciplina_cuando_permite_duplicados(
    async_auth_client_duplicados,
    paquete_permite_duplicados,
    paquete_disciplina_unica,
    disciplina_unica,
    evento_test_duplicados,
    promocion_duplicados,
    usuario_duplicados,
):
    """
    GIVEN: An ELEGIBLE package with cantidad_maxima_equipos=2 but only 1 disciplina linked.
           (frontend permiteDuplicados=true — user can select same disciplina twice)
    WHEN:  POST /api/inscripciones/ with two equipos BOTH using the same disciplina
    THEN:  Returns 200 and both equipos are created successfully

    This proves the API-level validar_cantidad_disciplinas_paquete no longer blocks
    duplicate discipline selections when the package allows it.
    """
    token = await sync_to_async(_make_token)(usuario_duplicados)

    # Two equipos, same disciplina (Futbol Sala)
    payload = make_inscripcion_payload(
        paquete_id=str(paquete_permite_duplicados.id),
        promocion_id=str(promocion_duplicados.id),
        observacion="Inscripción con disciplinas duplicadas — permiteDuplicados=true",
        equipos=[
            make_equipo_payload(
                disciplina_id=str(disciplina_unica.id),
                nombre="Equipo Tigres FC",
            ),
            make_equipo_payload(
                disciplina_id=str(disciplina_unica.id),
                nombre="Equipo Leones FC",
            ),
        ],
    )

    response = await async_auth_client_duplicados.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.content}"
    )
    data = response.json()
    assert data["success"] is True, f"API returned failure: {data}"

    result = data["data"]
    assert "id" in result
    assert result["estado"] == "RECIBIDA"
    inscripcion_id = result["id"]

    # Fetch detail to get equipos (InscripcionOut doesn't include equipos)
    detail_resp = await async_auth_client_duplicados.get(
        f"/api/inscripciones/{inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_resp.status_code == 200, f"Detail fetch failed: {detail_resp.content}"
    detail_data = detail_resp.json()
    assert detail_data["success"] is True

    equipos = detail_data["data"].get("equipos", [])
    assert len(equipos) == 2, f"Expected 2 equipos, got {len(equipos)}: {detail_data}"

    disciplina_ids = {eq["disciplina"]["id"] for eq in equipos}
    assert len(disciplina_ids) == 1, (
        f"Both equipos should have the same disciplina, got ids: {disciplina_ids}"
    )
    assert list(disciplina_ids)[0] == str(disciplina_unica.id)

    equipo_nombres = {eq["nombre"] for eq in equipos}
    assert equipo_nombres == {"Equipo Tigres FC", "Equipo Leones FC"}


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_api_acepta_equipos_misma_disciplina_fijo_cuando_permite_duplicados(
    async_auth_client_duplicados,
    paquete_permite_duplicados,
    paquete_disciplina_unica,
    disciplina_unica,
    evento_test_duplicados,
    promocion_duplicados,
    usuario_duplicados,
):
    """
    GIVEN: An ELEGIBLE package allowing duplicate disciplines
    WHEN:  POST /api/inscripciones/ with one equipo only (edge case: partial fill)
    THEN:  Returns 200 and the equipo is created successfully
    """
    token = await sync_to_async(_make_token)(usuario_duplicados)

    # Single equipo with the only available disciplina
    payload = make_inscripcion_payload(
        paquete_id=str(paquete_permite_duplicados.id),
        promocion_id=str(promocion_duplicados.id),
        observacion="Un solo equipo con la unica disciplina disponible",
        equipos=[
            make_equipo_payload(
                disciplina_id=str(disciplina_unica.id),
                nombre="Equipo Unico FC",
            ),
        ],
    )

    response = await async_auth_client_duplicados.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.content}"
    )
    data = response.json()
    assert data["success"] is True

    result = data["data"]
    inscripcion_id = result["id"]

    # Fetch detail to get equipos (InscripcionOut doesn't include equipos)
    detail_resp = await async_auth_client_duplicados.get(
        f"/api/inscripciones/{inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_resp.status_code == 200, f"Detail fetch failed: {detail_resp.content}"
    detail_data = detail_resp.json()

    equipos = detail_data["data"].get("equipos", [])
    assert len(equipos) == 1, f"Expected 1 equipo, got {len(equipos)}: {detail_data}"
    assert equipos[0]["nombre"] == "Equipo Unico FC"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_api_rechaza_mas_equipos_que_permitido(
    async_auth_client_duplicados,
    paquete_permite_duplicados,
    paquete_disciplina_unica,
    disciplina_unica,
    evento_test_duplicados,
    promocion_duplicados,
    usuario_duplicados,
):
    """
    GIVEN: An ELEGIBLE package with cantidad_maxima_equipos=2 (via cantidad_disciplinas_requeridas=2)
    WHEN:  POST /api/inscripciones/ with 3 equipos (exceeds maximum)
    THEN:  Returns 400 and the error message mentions the team count limit
    """
    token = await sync_to_async(_make_token)(usuario_duplicados)

    payload = make_inscripcion_payload(
        paquete_id=str(paquete_permite_duplicados.id),
        promocion_id=str(promocion_duplicados.id),
        observacion="Excede cantidad maxima de equipos",
        equipos=[
            make_equipo_payload(
                disciplina_id=str(disciplina_unica.id),
                nombre=f"Equipo Exceso {i}",
            )
            for i in range(3)
        ],
    )

    response = await async_auth_client_duplicados.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}: {response.content}"
    )
    data = response.json()
    # Should mention the team count limit
    content_lower = str(response.content).lower()
    assert "equipo" in content_lower or "máximo" in content_lower, (
        f"Error should mention team count limit, got: {response.content}"
    )
