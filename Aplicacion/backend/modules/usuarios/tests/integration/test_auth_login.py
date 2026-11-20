"""
Inicio de sesión por username, DNI y email.

GIVEN: la cuenta `Usuario` del objetivo, con credenciales y con la
identidad civil en la `Persona` OPCIONAL.
WHEN: se intenta iniciar sesión por cada uno de los tres identificadores.
THEN: se devuelve el par de tokens y los hechos de sesión; un identificador
desconocido y una contraseña incorrecta producen EXACTAMENTE la misma
respuesta (no hay fuga de identidad); una cuenta desactivada es un estado
distinto.

Cubre `FR-03` §1.1, §1.2 · `FR-01` §4.4 · `RN-U04` · `DEC-02`.
"""

import pytest

PASSWORD = "Prueba-12345"


# ── Éxito por cada identificador ────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_login_por_username_devuelve_tokens_y_sesion(api_client, cuenta_con_persona):
    """GIVEN una cuenta con password WHEN login por username THEN 200 + tokens."""
    response = await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_con_persona.username, "password": PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["message"] == "Inicio de sesión exitoso."

    data = body["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["expires_at"]
    assert data["user"]["id"] == str(cuenta_con_persona.id)
    assert data["user"]["username"] == cuenta_con_persona.username
    assert data["user"]["email"] == cuenta_con_persona.email


@pytest.mark.django_db(transaction=True)
async def test_login_por_dni_resuelve_travesando_la_persona(api_client, cuenta_con_persona):
    """GIVEN una cuenta con persona WHEN login por DNI THEN la misma cuenta.

    El DNI resuelve por `Persona.numero_documento`: el documento es un
    IDENTIFICADOR, no una credencial (`FR-03` §1.1).
    """
    persona = cuenta_con_persona.persona_fk

    response = await api_client.post(
        "/auth/login/dni",
        json={"dni": persona.numero_documento, "password": PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user"]["id"] == str(cuenta_con_persona.id)
    assert body["data"]["user"]["persona_id"] == str(persona.id)


@pytest.mark.django_db(transaction=True)
async def test_login_por_dni_normaliza_el_documento(api_client, cuenta_con_persona):
    """GIVEN un documento con separadores WHEN login por DNI THEN resuelve igual."""
    persona = cuenta_con_persona.persona_fk
    numero = persona.numero_documento
    con_separadores = f"{numero[:4]} {numero[4:]}"

    response = await api_client.post(
        "/auth/login/dni",
        json={"dni": con_separadores, "password": PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["data"]["user"]["id"] == str(cuenta_con_persona.id)


@pytest.mark.django_db(transaction=True)
async def test_login_por_email_usa_el_email_unico_y_no_nulo(api_client, cuenta_con_persona):
    """GIVEN una cuenta con email WHEN login por email THEN la misma cuenta."""
    response = await api_client.post(
        "/auth/login/email",
        json={"email": cuenta_con_persona.email, "password": PASSWORD},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user"]["id"] == str(cuenta_con_persona.id)


@pytest.mark.django_db(transaction=True)
async def test_login_por_email_no_distingue_mayusculas(api_client, cuenta_con_persona):
    """GIVEN una cuenta con email WHEN se escribe en MAYÚSCULAS THEN resuelve."""
    response = await api_client.post(
        "/auth/login/email",
        json={"email": cuenta_con_persona.email.upper(), "password": PASSWORD},
    )

    assert response.status_code == 200
    assert response.json()["data"]["user"]["id"] == str(cuenta_con_persona.id)


@pytest.mark.django_db(transaction=True)
async def test_una_cuenta_sin_email_no_entra_por_email(api_client, cuenta_sin_persona):
    """GIVEN una cuenta SIN email WHEN login por email THEN credenciales inválidas."""
    response = await api_client.post(
        "/auth/login/email",
        json={"email": "sin.email@example.com", "password": PASSWORD},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_ERROR"


@pytest.mark.django_db(transaction=True)
async def test_una_cuenta_tecnica_no_entra_por_documento(api_client, cuenta_sin_persona):
    """GIVEN una cuenta SIN persona WHEN login por DNI THEN credenciales inválidas.

    La relación con `Persona` es OPCIONAL en los dos sentidos: una cuenta
    técnica no tiene documento que la identifique (`FR-03` §1.2).
    """
    response = await api_client.post(
        "/auth/login/dni",
        json={"dni": "12345678", "password": PASSWORD},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_ERROR"


# ── Fallo neutro: no hay fuga de identidad ──────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_identificador_desconocido_y_password_incorrecta_no_se_distinguen(
    api_client, cuenta_con_persona
):
    """GIVEN una cuenta WHEN falla el login THEN ambos fallos son idénticos.

    El backend no publica qué cuentas existen: el mismo status, el mismo
    código y la misma prosa para "no existe" y para "no cuadra" (`RN-U04`).
    """
    desconocido = await api_client.post(
        "/auth/login/username",
        json={"username": "no.existe", "password": PASSWORD},
    )
    incorrecta = await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_con_persona.username, "password": "Contraseña-mala"},
    )

    assert desconocido.status_code == incorrecta.status_code == 401
    assert desconocido.json() == incorrecta.json()
    assert desconocido.json()["error"]["code"] == "AUTH_ERROR"
    assert desconocido.json()["success"] is False
    assert desconocido.json()["data"] is None


@pytest.mark.django_db(transaction=True)
async def test_dni_desconocido_y_email_desconocido_no_se_distinguen(api_client):
    """GIVEN un documento y un email desconocidos WHEN fallan THEN son idénticos."""
    por_dni = await api_client.post(
        "/auth/login/dni",
        json={"dni": "99999999", "password": PASSWORD},
    )
    por_email = await api_client.post(
        "/auth/login/email",
        json={"email": "nadie@example.com", "password": PASSWORD},
    )

    assert por_dni.status_code == por_email.status_code == 401
    assert por_dni.json() == por_email.json()


@pytest.mark.django_db(transaction=True)
async def test_el_fallo_no_publica_datos_tecnicos(api_client, cuenta_con_persona):
    """GIVEN un fallo de login THEN la respuesta no filtra nada técnico."""
    response = await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_con_persona.username, "password": "Contraseña-mala"},
    )

    crudo = response.content.decode().lower()
    assert "pbkdf2" not in crudo
    assert "sha256" not in crudo
    assert "argon2" not in crudo
    assert str(cuenta_con_persona.id) not in crudo
    assert cuenta_con_persona.username not in crudo


# ── Cuenta desactivada ──────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_una_cuenta_inactiva_responde_403(api_client, cuenta_inactiva):
    """GIVEN una cuenta desactivada WHEN login THEN 403 con código estable.

    Es un estado DISTINTO de "credenciales inválidas": la contraseña es
    correcta, pero la cuenta no puede operar.
    """
    response = await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_inactiva.username, "password": PASSWORD},
    )

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "CUENTA_INACTIVA"


@pytest.mark.django_db(transaction=True)
async def test_una_cuenta_inactiva_con_password_incorrecta_no_revela_su_estado(
    api_client, cuenta_inactiva
):
    """GIVEN una cuenta desactivada WHEN la contraseña NO cuadra THEN 401.

    El estado "desactivada" sólo se revela a quien ACERTA la contraseña: con
    una contraseña incorrecta la respuesta es la neutra.
    """
    response = await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_inactiva.username, "password": "Contraseña-mala"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_ERROR"


# ── Tokens ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_el_token_de_acceso_autentica_la_sesion(
    api_client, cliente_con_sesion, cuenta_con_persona
):
    """GIVEN un login exitoso WHEN se usa el access token THEN abre sesión."""
    login = await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_con_persona.username, "password": PASSWORD},
    )
    token = login.json()["data"]["access_token"]

    cliente = cliente_con_sesion(cuenta_con_persona)
    cliente.headers.update({"Authorization": f"Bearer {token}"})
    respuesta = await cliente.get("/auth/me")

    assert respuesta.status_code == 200
    assert respuesta.json()["data"]["id"] == str(cuenta_con_persona.id)


@pytest.mark.django_db(transaction=True)
async def test_la_respuesta_no_trae_campos_de_compatibilidad(api_client, cuenta_con_persona):
    """GIVEN un login exitoso THEN no hay `dni` ni `dni_legacy` en la respuesta.

    El modelo de usuario del objetivo no tiene columna de DNI: el documento
    vive en `Persona.numero_documento` y no se duplica ni se restaura.
    """
    response = await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_con_persona.username, "password": PASSWORD},
    )

    data = response.json()["data"]
    assert "dni" not in data["user"]
    assert "dni_legacy" not in data["user"]
    assert "password" not in data["user"]


@pytest.mark.django_db(transaction=True)
async def test_el_login_no_crea_una_cuenta_ni_una_persona(api_client, cuenta_con_persona):
    """GIVEN un login WHEN ocurre THEN no nace ninguna identidad (`FR-03` §1.2)."""
    from asgiref.sync import sync_to_async

    from modules.usuarios.domain.models import Persona, Usuario

    async def _contar() -> tuple[int, int]:
        def _cuentas() -> tuple[int, int]:
            return Persona.objects.count(), Usuario.objects.count()

        return await sync_to_async(_cuentas)()

    antes_personas, antes_cuentas = await _contar()

    await api_client.post(
        "/auth/login/username",
        json={"username": cuenta_con_persona.username, "password": PASSWORD},
    )

    despues_personas, despues_cuentas = await _contar()
    assert despues_personas == antes_personas
    assert despues_cuentas == antes_cuentas
