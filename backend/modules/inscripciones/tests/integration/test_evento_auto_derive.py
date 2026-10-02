"""
Integration tests for `inscripcion-evento-auto-derive`.

Covers:
- Auto-resolution of the active event from `settings.EVENTO_ACTIVO_NOMBRE`.
- Backend validation: a discipline not in the package's allowed set is rejected.
- Multiple active events without constant configuration => backend error.
"""
import pytest
from django.test import AsyncClient
from asgiref.sync import sync_to_async

from modules.inscripciones.domain.models import Evento
from modules.inscripciones.tests.fixtures.factories import (
    make_inscripcion_payload,
    make_equipo_payload,
)


def _make_token(user) -> str:
    from ninja_jwt.tokens import AccessToken
    return str(AccessToken.for_user(user))


@pytest.fixture
def async_auth_client(db, usuario_con_persona):
    """AsyncClient with JWT Bearer token."""
    return AsyncClient()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_evento_auto_resuelto_desde_settings(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
):
    """
    GIVEN: `EVENTO_ACTIVO_NOMBRE` matches the seeded evento (or only one active)
    WHEN: POST /api/inscripciones/ without evento_id
    THEN: Backend resolves evento automatically and inscription is created.
    """
    token = await sync_to_async(_make_token)(usuario_con_persona)

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[],
    )

    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.content}"
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_disciplina_no_en_paquete_rechazada(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
    disciplina_basket,
):
    """
    GIVEN: A disciplina NOT linked to the selected paquete
    WHEN: POST /api/inscripciones/ with that disciplina in equipos
    THEN: Backend rejects with 400/422 (DisciplinaNoEnPaqueteError).
    """
    token = await sync_to_async(_make_token)(usuario_con_persona)

    equipo = make_equipo_payload(
        disciplina_id=str(disciplina_basket.id),
        participantes=[],
    )

    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[equipo],
    )

    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for invalid disciplina, got {response.status_code}: "
        f"{response.content}"
    )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_multiples_eventos_sin_constante_falla(
    async_auth_client,
    base_inscripcion_setup,
    usuario_con_persona,
    settings,
):
    """
    GIVEN: Two active eventos and no `EVENTO_ACTIVO_NOMBRE` matching
    WHEN: POST /api/inscripciones/ without evento_id
    THEN: Backend rejects with 400/422 because it can't auto-resolve.
    """
    settings.EVENTO_ACTIVO_NOMBRE = None

    @sync_to_async
    def _create_second_event():
        return Evento.objects.create(
            nombre="Salesianos FEST 2027",
            fecha_inicio=base_inscripcion_setup["evento"].fecha_inicio,
            fecha_fin=base_inscripcion_setup["evento"].fecha_fin,
            esta_activo=True,
        )

    await _create_second_event()

    token = await sync_to_async(_make_token)(usuario_con_persona)
    payload = make_inscripcion_payload(
        paquete_id=str(base_inscripcion_setup["paquete"].id),
        promocion_id=str(base_inscripcion_setup["promocion"].id),
        equipos=[],
    )

    response = await async_auth_client.post(
        "/api/inscripciones/",
        data=payload,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code in (400, 422), (
        f"Expected 400/422 for multiple active eventos, got {response.status_code}"
    )
