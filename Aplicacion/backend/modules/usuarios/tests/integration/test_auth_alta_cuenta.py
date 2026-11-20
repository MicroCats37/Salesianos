"""
El ALTA PÚBLICA de una cuenta: `POST /api/auth/register`.

GIVEN: una identidad civil que todavía no tiene cuenta.
WHEN: se registra la cuenta con su identidad.
THEN: nace la cuenta, nace o se reutiliza la persona, se le asigna el grupo
funcional `Normal` y la respuesta abre la SESIÓN del actor recién creado
(tokens + hechos de sesión).

El alta es el ÚNICO camino de nacimiento de una cuenta: nadie la crea como
efecto lateral de consultar un documento (`FR-03` §1.2). El nombre de usuario
lo DERIVA el servidor del documento; el cliente no lo elige.

Cubre `FR-03` §1.1 y §1.2 · `FR-01` §4.4 (envoltura y errores) · `RN-U04`
(el fallo no publica datos técnicos) · `DEC-02` (el grupo funcional `Normal`).
"""

import pytest

PASSWORD = "Prueba-12345"

#: Un payload de alta válido: es el contrato HTTP de `RegisterIn`.
def _payload(**cambios) -> dict:
    """El payload de alta con las sustituciones que pida el caso."""
    payload = {
        "email": "nueva.cuenta@example.com",
        "password": PASSWORD,
        "confirmPassword": PASSWORD,
        "tipoDocumento": "DNI",
        "numeroDocumento": "12345678",
        "nombres": "ANA",
        "apellidos": "PEREZ",
        "genero": "F",
        "telefono": "987654321",
        "whatsapp": "987654321",
        "contactoEmergenciaNombre": "LUIS PEREZ",
        "contactoEmergenciaTelefono": "987654321",
        "acceptedBases": True,
    }
    payload.update(cambios)
    return payload


# ── La ruta ──────────────────────────────────────────────────────────────────


def test_la_ruta_de_alta_esta_registrada_y_es_publica():
    """GIVEN la API viva WHEN se publica el esquema THEN el alta existe y es pública.

    Una ruta no existe hasta que su controller está registrado
    (`FR-07` §3.1.2): el alta sin registrar sería código muerto.
    """
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    assert "/api/auth/register" in paths
    assert "post" in paths["/api/auth/register"]
    assert not paths["/api/auth/register"]["post"].get("security")


# ── El alta que funciona ────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_el_alta_crea_la_cuenta_y_abre_la_sesion(api_client):
    """GIVEN una identidad sin cuenta WHEN se registra THEN 201 + tokens + sesión."""
    response = await api_client.post("/auth/register", json=_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["message"] == "El registro se completó correctamente."

    data = body["data"]
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["expires_at"]

    usuario = data["user"]
    assert usuario["email"] == "nueva.cuenta@example.com"
    assert usuario["persona_id"], "El alta debe vincular la cuenta con su persona."
    assert usuario["nombres"] == "ANA"
    assert usuario["apellidos"] == "PEREZ"
    assert usuario["es_admin"] is False
    assert "password" not in usuario
    assert "dni" not in usuario


@pytest.mark.django_db(transaction=True)
async def test_el_alta_deriva_el_nombre_de_usuario_del_documento(api_client):
    """GIVEN un DNI WHEN se registra THEN el usuario es `{tipo}_{documento}`.

    El nombre de usuario NO lo elige el cliente: lo deriva el servidor del
    documento, en minúsculas (`modules/usuarios/domain/services/core/
    registro_core_service.py`).
    """
    response = await api_client.post("/auth/register", json=_payload())

    assert response.status_code == 201
    assert response.json()["data"]["user"]["username"] == "dni_12345678"


@pytest.mark.django_db(transaction=True)
async def test_el_alta_asigna_el_grupo_funcional_normal(api_client):
    """GIVEN un alta WHEN se responde THEN la cuenta queda en el grupo `Normal`.

    `Normal` y `Administrador` son los DOS grupos funcionales de negocio
    (`FR-03` §1.2 · `DEC-02`): el alta NUNCA concede el de administrador.
    """
    from asgiref.sync import sync_to_async

    from modules.usuarios.domain.models import Usuario

    response = await api_client.post("/auth/register", json=_payload())

    assert response.status_code == 201
    assert "Normal" in response.json()["data"]["user"]["grupos"]

    usuario_id = response.json()["data"]["user"]["id"]

    def _grupos() -> list[str]:
        return list(
            Usuario.objects.get(id=usuario_id).groups.values_list("name", flat=True)
        )

    assert "Normal" in await sync_to_async(_grupos)()


@pytest.mark.django_db(transaction=True)
async def test_el_alta_no_crea_la_persona_si_ya_existe_sin_cuenta(
    api_client, persona_registrada_sin_cuenta
):
    """GIVEN una persona SIN cuenta WHEN se registra con su documento THEN la reutiliza.

    La identidad NO se duplica ni se reescribe: el alta crea la CUENTA y
    vincula la persona que ya existía (`FR-03` §1.2).
    """
    from asgiref.sync import sync_to_async

    from modules.usuarios.domain.models import Persona

    response = await api_client.post(
        "/auth/register",
        json=_payload(
            numeroDocumento=persona_registrada_sin_cuenta.numero_documento,
            email="reutiliza@example.com",
        ),
    )

    assert response.status_code == 201
    assert (
        response.json()["data"]["user"]["persona_id"]
        == str(persona_registrada_sin_cuenta.id)
    )

    def _personas() -> int:
        return Persona.objects.filter(
            numero_documento=persona_registrada_sin_cuenta.numero_documento
        ).count()

    assert await sync_to_async(_personas)() == 1


# ── Los conflictos ──────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_el_alta_rechaza_un_email_ya_registrado(api_client, cuenta_con_persona):
    """GIVEN un email ya vinculado WHEN se registra con él THEN 409.

    El email es la clave ÚNICA y NO NULA de la cuenta: dos cuentas no pueden
    compartirlo (`FR-03` §1.2).
    """
    response = await api_client.post(
        "/auth/register",
        json=_payload(
            email=cuenta_con_persona.email,
            numeroDocumento="44555666",
        ),
    )

    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["error"]["code"]


@pytest.mark.django_db(transaction=True)
async def test_el_alta_rechaza_un_documento_que_ya_tiene_cuenta(
    api_client, cuenta_con_persona
):
    """GIVEN un documento ya vinculado a una cuenta WHEN se registra THEN 409.

    El código es `PERSONA_DUPLICADA`: el conflicto es de IDENTIDAD, no de
    correo (`FR-01` §4.4).
    """
    persona = cuenta_con_persona.persona_fk

    response = await api_client.post(
        "/auth/register",
        json=_payload(
            numeroDocumento=persona.numero_documento,
            email="otro.correo@example.com",
        ),
    )

    assert response.status_code == 409
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "PERSONA_DUPLICADA"


# ── El contrato HTTP ────────────────────────────────────────────────────────


@pytest.mark.django_db(transaction=True)
async def test_el_alta_exige_que_las_contrasenas_coincidan(api_client):
    """GIVEN dos contraseñas distintas WHEN se registra THEN 422."""
    response = await api_client.post(
        "/auth/register",
        json=_payload(confirmPassword="Otra-clave-12345"),
    )

    assert response.status_code == 422
    assert response.json()["success"] is False


@pytest.mark.django_db(transaction=True)
async def test_el_alta_exige_la_aceptacion_de_las_bases(api_client):
    """GIVEN `acceptedBases = false` WHEN se registra THEN 422."""
    response = await api_client.post("/auth/register", json=_payload(acceptedBases=False))

    assert response.status_code == 422
    assert response.json()["success"] is False


@pytest.mark.django_db(transaction=True)
async def test_el_alta_exige_el_formato_del_documento_segun_su_tipo(api_client):
    """GIVEN un DNI que no tiene 8 dígitos WHEN se registra THEN 422.

    El FORMATO se valida en la capa HTTP, con el tipo ya conocido
    (`RegisterIn._validar_documento_segun_tipo`).
    """
    response = await api_client.post(
        "/auth/register",
        json=_payload(numeroDocumento="1234"),
    )

    assert response.status_code == 422
    assert response.json()["success"] is False


@pytest.mark.django_db(transaction=True)
async def test_el_alta_no_filtra_datos_tecnicos_en_el_conflicto(api_client, cuenta_con_persona):
    """GIVEN un conflicto WHEN se responde THEN la prosa no filtra nada técnico.

    El fallo publica el código estable y la prosa pública del catálogo; nunca
    el hash, la restricción SQL ni el identificador interno (`FR-01` §4.4).
    """
    persona = cuenta_con_persona.persona_fk

    response = await api_client.post(
        "/auth/register",
        json=_payload(
            numeroDocumento=persona.numero_documento,
            email="otro.correo@example.com",
        ),
    )

    crudo = response.content.decode().lower()
    assert "pbkdf2" not in crudo
    assert "sha256" not in crudo
    assert "argon2" not in crudo
    assert "integrityerror" not in crudo
    assert str(cuenta_con_persona.id) not in crudo
