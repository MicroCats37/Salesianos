"""
Sesión actual (`GET /auth/me`).

GIVEN: una cuenta autenticada con un JWT válido.
WHEN: se consulta la sesión actual.
THEN: el backend publica los hechos de rol del propio actor; sin token, la
ruta responde 401 y nunca entra.

Cubre `FR-03` §1.2 · `contratos/02` §3 (la autorización la resuelve el
backend, no el cliente) · `FR-01` §4.4 (401 antes que 403).
"""

import pytest

from modules.usuarios.domain.constants import GrupoFuncionalChoices


@pytest.mark.django_db(transaction=True)
async def test_auth_me_sin_token_responde_401(api_client):
    """GIVEN una petición sin token WHEN se pide la sesión THEN 401."""
    response = await api_client.get("/auth/me")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db(transaction=True)
async def test_auth_me_con_token_invalido_responde_401(api_client):
    """GIVEN un token corrupto WHEN se pide la sesión THEN 401."""
    api_client.headers.update({"Authorization": "Bearer token.invalido"})

    response = await api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db(transaction=True)
async def test_auth_me_publica_los_hechos_de_sesion(
    api_client, cliente_con_sesion, usuario_normal
):
    """GIVEN una cuenta `Normal` WHEN se pide la sesión THEN sus hechos."""
    cliente = cliente_con_sesion(usuario_normal)

    response = await cliente.get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None

    data = body["data"]
    assert data["id"] == str(usuario_normal.id)
    assert data["username"] == usuario_normal.username
    assert data["email"] == usuario_normal.email
    assert data["nombres"] == usuario_normal.persona_fk.nombres
    assert data["apellidos"] == usuario_normal.persona_fk.apellidos
    assert data["persona_id"] == str(usuario_normal.persona_fk.id)
    assert data["rol"] == "normal"
    assert GrupoFuncionalChoices.NORMAL.value in data["grupos"]
    assert data["es_admin"] is False
    assert data["is_staff"] is False
    assert data["is_superuser"] is False
    assert data["nivel"] == "usuario"
    assert data["capacidades"] == []


@pytest.mark.django_db(transaction=True)
async def test_auth_me_de_un_administrador_publica_el_rol_del_backend(
    api_client, cliente_con_sesion, usuario_administrador
):
    """GIVEN una cuenta `Administrador` WHEN se pide la sesión THEN su rol.

    El rol lo decide el BACKEND (el grupo funcional Django), no el cliente:
    la cookie o el store del front pintan, no autorizan (`contratos/02` §3).
    """
    cliente = cliente_con_sesion(usuario_administrador)

    response = await cliente.get("/auth/me")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["rol"] == "administrador"
    assert GrupoFuncionalChoices.ADMINISTRADOR.value in data["grupos"]


@pytest.mark.django_db(transaction=True)
async def test_auth_me_de_un_superusuario_publica_el_nivel_tecnico(
    api_client, cliente_con_sesion, superusuario_tecnico
):
    """GIVEN una cuenta técnica WHEN se pide la sesión THEN nivel y capacidades.

    `is_superuser` es el nivel TÉCNICO (`DEC-02`) y una cuenta técnica no
    tiene por qué tener `Persona` vinculada (`FR-03` §1.2).
    """
    cliente = cliente_con_sesion(superusuario_tecnico)

    response = await cliente.get("/auth/me")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["nivel"] == "superusuario"
    assert data["is_superuser"] is True
    assert data["es_admin"] is True
    assert data["rol"] == "administrador"
    assert data["persona_id"] is None
    assert data["nombres"] is None
    assert data["email"] is None
    assert data["capacidades"]


@pytest.mark.django_db(transaction=True)
async def test_auth_me_de_una_cuenta_sin_persona_no_falla(
    api_client, cliente_con_sesion, cuenta_sin_persona
):
    """GIVEN una cuenta sin persona WHEN se pide la sesión THEN 200 con nulos."""
    cliente = cliente_con_sesion(cuenta_sin_persona)

    response = await cliente.get("/auth/me")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["persona_id"] is None
    assert data["nombres"] is None
    assert data["apellidos"] is None
    assert data["rol"] == "sin_rol"
