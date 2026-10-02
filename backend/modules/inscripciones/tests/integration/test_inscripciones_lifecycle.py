"""
Integration tests for authenticated inscription lifecycle.

Tests:
- Creating an inscription with valid fixtures succeeds
- Listing own inscriptions returns user's inscriptions only
- Cannot access another user's inscription (ownership check)

Uses @pytest.mark.django_db for database access.
Uses django.test.AsyncClient with @pytest.mark.asyncio for async controller.
Authentication via JWT Bearer token in the Authorization header.
"""
import pytest
from django.test import AsyncClient
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from config.api import api
from modules.inscripciones.tests.fixtures.factories import (
    make_inscripcion_payload,
    make_equipo_payload,
    make_participante_payload,
)
from modules.usuarios.domain.models import Persona
from modules.usuarios.domain.constants import GeneroChoices


# ── Fixtures ────────────────────────────────────────────────────────────────────


@pytest.fixture
def async_auth_client(db, usuario_con_persona):
    """AsyncClient for testing async endpoints with JWT Bearer token."""
    return AsyncClient()


def _make_token(user) -> str:
    """Generate JWT token for user (sync, call in thread)."""
    from ninja_jwt.tokens import AccessToken
    return str(AccessToken.for_user(user))


# ── Tests: Happy Path ──────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_inscripcion_authenticated_sin_equipos(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with persona_fk, event and package exist
    WHEN:  POST /api/inscripciones/ with minimal payload (no equipos)
    THEN:  Returns 200 and creates inscription
    """
    token = await sync_to_async(_make_token)(usuario_con_persona)
    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        observacion="Test inscription",
        equipos=[],
    )
    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    result = data["data"]
    assert "id" in result
    assert result["estado"] == "RECIBIDA"
    assert result["promocion"]["anio"] == 2025


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_inscripcion_con_equipo_y_participante(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user, all fixtures exist, Persona for participant
    WHEN:  POST /api/inscripciones/ with one equipo and one participant
    THEN:  Returns 200 and creates inscription with team
    """
    token = await sync_to_async(_make_token)(usuario_con_persona)

    @sync_to_async
    def _create_participante():
        return Persona.objects.create(
            tipo_documento="DNI",
            numero_documento="12345678",
            nombres="Jugador",
            apellidos="Test",
            genero=GeneroChoices.MASCULINO,
        )

    participante = await _create_participante()

    equipo_payload = make_equipo_payload(
        disciplina_id=str(base_inscripcion_setup["disciplina"].id),
        nombre="Equipo Ganador",
        participantes=[
            make_participante_payload(
                persona_id=str(participante.id),
                rol="CAPITAN",
                talle_camiseta="L",
            )
        ],
    )

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[equipo_payload],
    )
    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    result = data["data"]
    assert "id" in result
    assert result["estado"] == "RECIBIDA"


# ── Tests: List Own Inscriptions ───────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_listar_inscripciones_devuelve_vacio_sin_inscripciones(
    async_auth_client,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user has no inscriptions
    WHEN:  GET /api/inscripciones/
    THEN:  Returns 200 with empty list
    """
    token = await sync_to_async(_make_token)(usuario_con_persona)
    response = await async_auth_client.get(
        "/api/inscripciones/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_listar_inscripciones_devuelve_solo_del_usuario(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: User has created one inscription
    WHEN:  GET /api/inscripciones/
    THEN:  Returns list with exactly that inscription
    """
    token = await sync_to_async(_make_token)(usuario_con_persona)

    # First create an inscription
    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[],
    )
    create_resp = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 200, f"Create failed: {create_resp.content}"
    inscripcion_id = create_resp.json()["data"]["id"]

    # Now list
    response = await async_auth_client.get(
        "/api/inscripciones/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == inscripcion_id


# ── Tests: Ownership ──────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_obtener_inscripcion_inexistente_devuelve_404(
    async_auth_client,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with valid token
    WHEN:  GET /api/inscripciones/{random-uuid} — non-existent UUID
    THEN:  Returns 404 Not Found (auth is fine, resource not found)
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)
    response = await async_auth_client.get(
        f"/api/inscripciones/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Should return 404 not 401 (auth is fine, resource not found)
    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.content}"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_obtener_inscripcion_existente_ajena_rechaza(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Another user has an inscription
    WHEN:  Attempting to GET that inscription with our authenticated client
    THEN:  Returns 400 (BusinessError "No tienes permiso") or 404 if ownership not enforced

    This test exposes whether the controller properly checks ownership.
    """
    @sync_to_async
    def _setup_other_user():
        other_persona = Persona.objects.create(
            tipo_documento="DNI",
            numero_documento="99998888",
            nombres="Otro",
            apellidos="Usuario",
            genero=GeneroChoices.MASCULINO,
        )
        User = get_user_model()
        other_user = User.objects.create_user(
            username="other_user_inscripciones",
            email="other@example.com",
            password="testpass123",
            persona_fk=other_persona,
        )
        return other_user

    other_user = await _setup_other_user()
    other_token = await sync_to_async(_make_token)(other_user)

    # Create inscription AS the other user
    other_client = AsyncClient()
    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[],
    )
    other_resp = await other_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_resp.status_code == 200, f"Other user inscription creation failed: {other_resp.content}"
    other_inscripcion_id = other_resp.json()["data"]["id"]

    # Now try to access it with our auth client (different user)
    token = await sync_to_async(_make_token)(usuario_con_persona)
    response = await async_auth_client.get(
        f"/api/inscripciones/{other_inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Controller should check ownership and reject
    # Returns 400 if BusinessError is raised for "No tienes permiso"
    # Returns 404 if not found (if ownership check is missing)
    assert response.status_code in (400, 404), \
        f"Expected 400/404, got {response.status_code}: {response.content}"


# ── Tests: Inline Participants ────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_inscripcion_con_participante_inline_nuevo(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with persona_fk, event and package exist
    WHEN:  POST /api/inscripciones/ with inline participant data (new persona)
    THEN:  Returns 200 and creates a new Persona + inscription with team
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    equipo_payload = make_equipo_payload(
        disciplina_id=str(base_inscripcion_setup["disciplina"].id),
        nombre="Equipo Inline Nuevo",
        participantes=[
            make_participante_payload(
                tipoDocumento="DNI",
                numeroDocumento=f"{uuid.uuid4().int % 100000000:08d}",
                nombres="Nuevo",
                apellidos="Participante",
                genero="M",
                telefono="999888777",
                whatsapp="999888777",
                rol="JUGADOR",
                talle_camiseta="XL",
            )
        ],
    )

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[equipo_payload],
    )
    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"
    data = response.json()
    assert data["success"] is True
    result = data["data"]
    assert result["estado"] == "RECIBIDA"

    # Verify persona was created (use sync_to_async for ORM calls)
    from modules.inscripciones.domain.models import ParticipacionDisciplina

    @sync_to_async
    def _get_participacion():
        pds = ParticipacionDisciplina.objects.filter(equipo__inscripcion_id=result["id"])
        assert pds.count() == 1
        persona = pds.first().persona
        assert persona.nombres == "Nuevo"
        assert persona.apellidos == "Participante"
        assert persona.telefono == "999888777"
        assert persona.whatsapp == "999888777"

    await _get_participacion()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_inscripcion_con_participante_inline_existente(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user + existing Persona in DB
    WHEN:  POST /api/inscripciones/ with inline participant matching that DNI
    THEN:  Returns 200 and reuses the existing Persona (no new one created)
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    # Create persona beforehand (existing by document)
    doc_number = f"{uuid.uuid4().int % 100000000:08d}"

    @sync_to_async
    def _create_persona():
        return Persona.objects.create(
            tipo_documento="DNI",
            numero_documento=doc_number,
            nombres="Ya",
            apellidos="Existe",
            genero=GeneroChoices.MASCULINO,
            telefono="111222333",
        )

    existing_persona = await _create_persona()

    equipo_payload = make_equipo_payload(
        disciplina_id=str(base_inscripcion_setup["disciplina"].id),
        nombre="Equipo Inline Existente",
        participantes=[
            make_participante_payload(
                tipoDocumento="DNI",
                numeroDocumento=doc_number,
                nombres="Actualizado",  # Should NOT overwrite nombres
                apellidos="Existe",
                genero="M",
                rol="CAPITAN",
            )
        ],
    )

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[equipo_payload],
    )
    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.content}"

    # Verify the existing persona was reused (count should still be 1)
    @sync_to_async
    def _verify_reuse():
        personas_count = Persona.objects.filter(
            tipo_documento="DNI",
            numero_documento=doc_number,
        ).count()
        assert personas_count == 1
        # Verify the names were NOT overwritten (nombres is core identity, not updated)
        existing_persona.refresh_from_db()
        assert existing_persona.nombres == "Ya"  # Unchanged
        # telefono already had value, should not be changed
        assert existing_persona.telefono == "111222333"

    await _verify_reuse()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_inscripcion_falla_inline_incompleto(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with persona_fk
    WHEN:  POST /api/inscripciones/ with inline participant missing nombres
    THEN:  Returns 422 with validation error
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    # Build inline participant manually so we can omit nombres entirely
    # (factory would default nombres="Juan", making payload complete)
    inline_participante = {
        "tipoDocumento": "DNI",
        "numeroDocumento": f"{uuid.uuid4().int % 100000000:08d}",
        # nombres deliberately omitted
        "apellidos": "SinNombre",
        "genero": "M",
        "rol": "JUGADOR",
    }

    equipo_payload = make_equipo_payload(
        disciplina_id=str(base_inscripcion_setup["disciplina"].id),
        nombre="Equipo Fallido",
        participantes=[inline_participante],
    )

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[equipo_payload],
    )
    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_inscripcion_falla_documento_invalido(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with persona_fk
    WHEN:  POST /api/inscripciones/ with inline participant DNI=7digits (invalid)
    THEN:  Returns 422 with document validation error
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    equipo_payload = make_equipo_payload(
        disciplina_id=str(base_inscripcion_setup["disciplina"].id),
        nombre="Equipo Fallido",
        participantes=[
            make_participante_payload(
                tipoDocumento="DNI",
                numeroDocumento="1234567",  # 7 digits = invalid for DNI
                nombres="Bad",
                apellidos="Doc",
                genero="M",
                rol="JUGADOR",
            )
        ],
    )

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[equipo_payload],
    )
    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422, f"Expected 422, got {response.status_code}: {response.content}"
    error_data = response.json()
    assert "PARTICIPANTE_INLINE_ERROR" in str(error_data) or "VALIDATION_ERROR" in str(error_data)


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_crear_inscripcion_falla_persona_id_inexistente(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with persona_fk
    WHEN:  POST /api/inscripciones/ with legacy persona_id that doesn't exist
    THEN:  Returns 404 with PersonaNotFoundError
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    equipo_payload = make_equipo_payload(
        disciplina_id=str(base_inscripcion_setup["disciplina"].id),
        nombre="Equipo Fallido",
        participantes=[
            make_participante_payload(
                persona_id=str(uuid.uuid4()),  # Non-existent UUID
                rol="JUGADOR",
            )
        ],
    )

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[equipo_payload],
    )
    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.content}"


# ── Tests: PATCH Add Participants to Existing Equipo ───────────────────────────


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_patch_agregar_participante_inline_a_equipo_existente(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with an inscription containing one equipo (no participants)
    WHEN:  PATCH /api/inscripciones/{id}/equipos/{equipo_id}/participantes with one inline participant
    THEN:  Returns 200 and creates the participant linked to the team
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    # Create inscription with empty equipo
    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[
            make_equipo_payload(
                disciplina_id=str(base_inscripcion_setup["disciplina"].id),
                nombre="Equipo Patch Test",
                participantes=[],
            )
        ],
    )
    create_resp = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 200, f"Create failed: {create_resp.content}"
    inscripcion_id = create_resp.json()["data"]["id"]

    # Get the equipo_id from the detail
    detail_resp = await async_auth_client.get(
        f"/api/inscripciones/{inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert detail_resp.status_code == 200
    equipos = detail_resp.json()["data"]["equipos"]
    assert len(equipos) == 1
    equipo_id = equipos[0]["id"]

    # PATCH add one inline participant
    patch_payload = {
        "participantes": [
            {
                "tipoDocumento": "DNI",
                "numeroDocumento": f"{uuid.uuid4().int % 100000000:08d}",
                "nombres": "Jugador",
                "apellidos": "Nuevo",
                "genero": "M",
                "rol": "JUGADOR",
                "talle_camiseta": "L",
            }
        ]
    }
    patch_resp = await async_auth_client.patch(
        f"/api/inscripciones/{inscripcion_id}/equipos/{equipo_id}/participantes",
        data=patch_payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert patch_resp.status_code == 200, f"Expected 200, got {patch_resp.status_code}: {patch_resp.content}"
    patch_data = patch_resp.json()
    assert patch_data["success"] is True
    assert "1 participante(s) agregado(s)" in patch_data["data"]["mensaje"]

    # Verify the participant was added
    detail_resp2 = await async_auth_client.get(
        f"/api/inscripciones/{inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    equipos_updated = detail_resp2.json()["data"]["equipos"]
    assert len(equipos_updated[0]["participantes"]) == 1
    assert equipos_updated[0]["participantes"][0]["persona"]["nombres"] == "Jugador"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_patch_agregar_participante_duplicado_idempotente(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with an inscription containing one equipo with one participant
    WHEN:  PATCH adding the SAME participant again to the same equipo
    THEN:  Returns 200 but does not duplicate (idempotent)
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    doc_num = f"{uuid.uuid4().int % 100000000:08d}"

    # Create inscription with one participant already
    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[
            make_equipo_payload(
                disciplina_id=str(base_inscripcion_setup["disciplina"].id),
                nombre="Equipo Idempotente",
                participantes=[
                    make_participante_payload(
                        tipoDocumento="DNI",
                        numeroDocumento=doc_num,
                        nombres="Ya",
                        apellidos="Existe",
                        genero="M",
                        rol="JUGADOR",
                    )
                ],
            )
        ],
    )
    create_resp = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 200, f"Create failed: {create_resp.content}"
    inscripcion_id = create_resp.json()["data"]["id"]

    # Get equipo_id
    detail_resp = await async_auth_client.get(
        f"/api/inscripciones/{inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    equipo_id = detail_resp.json()["data"]["equipos"][0]["id"]
    initial_count = len(detail_resp.json()["data"]["equipos"][0]["participantes"])
    assert initial_count == 1

    # Try to add the same person again (same DNI)
    patch_payload = {
        "participantes": [
            {
                "tipoDocumento": "DNI",
                "numeroDocumento": doc_num,
                "nombres": "Ya",
                "apellidos": "Existe",
                "genero": "M",
                "rol": "CAPITAN",
            }
        ]
    }
    patch_resp = await async_auth_client.patch(
        f"/api/inscripciones/{inscripcion_id}/equipos/{equipo_id}/participantes",
        data=patch_payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Should succeed (idempotent) but not duplicate
    assert patch_resp.status_code == 200, f"Expected 200, got {patch_resp.status_code}: {patch_resp.content}"

    # Verify no new participant was added
    detail_resp2 = await async_auth_client.get(
        f"/api/inscripciones/{inscripcion_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    final_count = len(detail_resp2.json()["data"]["equipos"][0]["participantes"])
    assert final_count == 1  # Still exactly 1


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_patch_equipo_no_pertenece_inscripcion_rechaza(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: Authenticated user with an inscription
    WHEN:  PATCH /api/inscripciones/{id}/equipos/{wrong_equipo_id}/participantes
    THEN:  Returns 400/404 because equipo doesn't belong to inscription
    """
    import uuid
    token = await sync_to_async(_make_token)(usuario_con_persona)

    # Create inscription with empty equipo
    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[
            make_equipo_payload(
                disciplina_id=str(base_inscripcion_setup["disciplina"].id),
                nombre="Equipo Correcto",
                participantes=[],
            )
        ],
    )
    create_resp = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 200
    inscripcion_id = create_resp.json()["data"]["id"]

    # Try to PATCH with a random equipo_id (not belonging to this inscription)
    random_equipo_id = str(uuid.uuid4())

    patch_payload = {
        "participantes": [
            {
                "tipoDocumento": "DNI",
                "numeroDocumento": f"{uuid.uuid4().int % 100000000:08d}",
                "nombres": "Jugador",
                "apellidos": "Falso",
                "genero": "M",
                "rol": "JUGADOR",
            }
        ]
    }
    patch_resp = await async_auth_client.patch(
        f"/api/inscripciones/{inscripcion_id}/equipos/{random_equipo_id}/participantes",
        data=patch_payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Should return 400 (BusinessError) or 404 (NotFoundError)
    assert patch_resp.status_code in (400, 404), \
        f"Expected 400/404, got {patch_resp.status_code}: {patch_resp.content}"
