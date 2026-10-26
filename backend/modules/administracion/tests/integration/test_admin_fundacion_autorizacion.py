"""
Integration tests — authorization contract of the administration foundation.

The whole `/administracion` namespace is gated by `RequireAdmin`
(admin = `is_staff OR is_superuser`), evaluated SERVER-SIDE on every request:

- anonymous caller → 401 `AUTHENTICATION_REQUIRED` (JWT answers first),
- authenticated non-admin → 403 `ACTION_NOT_ALLOWED`,
- administrator → 200.

The endpoint is READ-ONLY: the test also asserts that calling it mutates
nothing.

The HTTP client is `django.test.Client`: the controllers are async and this is
the pattern already established by the rest of the project
(`contract/django-app-architecture-contract.md` §2.1).
"""
import pytest
from ninja_jwt.tokens import AccessToken

from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models import Persona, Usuario

URL_HEALTH = "/api/administracion/health"

# Palabras que NUNCA deben viajar en una respuesta del área de administración.
CLAVES_PROHIBIDAS = (
    "password",
    "password_hash",
    "token",
    "codigo_qr",
    "metadata",
    "token_sesion",
    "transaction_id",
    "response_message",
    "is_superuser",
)


def _auth_header(user) -> dict:
    """Build the Authorization header of an authenticated user."""
    token = AccessToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


# ── 401 — anonymous ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_health_anonimo_responde_401(api_client):
    """
    GIVEN: an anonymous caller
    WHEN:  GET /api/administracion/health
    THEN:  401 with the stable code AUTHENTICATION_REQUIRED.
    """
    response = api_client.get(URL_HEALTH)

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_health_anonimo_no_recibe_datos(api_client):
    """
    GIVEN: an anonymous caller
    WHEN:  GET /api/administracion/health
    THEN:  the body carries no payload of the module.
    """
    response = api_client.get(URL_HEALTH)

    body = response.json()
    assert body["data"] is None


# ── 403 — authenticated non-admin ─────────────────────────────────────────────


@pytest.mark.django_db
def test_health_no_admin_responde_403(api_client, usuario_no_admin):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  GET /api/administracion/health
    THEN:  403 with the stable code ACTION_NOT_ALLOWED and no data.
    """
    response = api_client.get(URL_HEALTH, **_auth_header(usuario_no_admin))

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert body["data"] is None


@pytest.mark.django_db
def test_health_no_admin_no_recibe_el_estado_del_modulo(
    api_client, usuario_no_admin
):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  GET /api/administracion/health
    THEN:  the response body exposes none of the module's data.
    """
    response = api_client.get(URL_HEALTH, **_auth_header(usuario_no_admin))

    crudo = response.content.decode()
    assert "administracion" not in crudo
    assert "estado" not in crudo


# ── 200 — administrators ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_health_admin_staff_responde_200(api_client, usuario_admin_staff, evento):
    """
    GIVEN: an administrator (`is_staff`)
    WHEN:  GET /api/administracion/health
    THEN:  200 with the typed wrapper and the resolved active event.
    """
    response = api_client.get(URL_HEALTH, **_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["data"]["modulo"] == "administracion"
    assert body["data"]["estado"] == "ok"
    assert body["data"]["evento_activo_nombre"] == evento.nombre
    assert body["data"]["evento_activo_id"] == str(evento.id)


@pytest.mark.django_db
def test_health_admin_superuser_responde_200(
    api_client, usuario_admin_superuser, evento
):
    """
    GIVEN: an administrator (`is_superuser`)
    WHEN:  GET /api/administracion/health
    THEN:  200 — the break-glass tier is admin too.
    """
    response = api_client.get(URL_HEALTH, **_auth_header(usuario_admin_superuser))

    assert response.status_code == 200
    assert response.json()["data"]["modulo"] == "administracion"


@pytest.mark.django_db
def test_health_sin_evento_activo_devuelve_200_sin_evento(
    api_client, usuario_admin_staff
):
    """
    GIVEN: an administrator and NO active event in the database
    WHEN:  GET /api/administracion/health
    THEN:  200 with a null event — the module is wired even without data.
    """
    response = api_client.get(URL_HEALTH, **_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["evento_activo_id"] is None
    assert data["evento_activo_nombre"] is None


# ── Data-leak discipline ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_health_no_expone_credenciales_ni_controles_de_superusuario(
    api_client, usuario_admin_staff, evento
):
    """
    GIVEN: an administrator
    WHEN:  GET /api/administracion/health
    THEN:  the body contains none of the forbidden keys.
    """
    response = api_client.get(URL_HEALTH, **_auth_header(usuario_admin_staff))

    crudo = response.content.decode().lower()
    for clave in CLAVES_PROHIBIDAS:
        assert clave not in crudo, f"La respuesta filtró la clave '{clave}'."


# ── No accidental mutation ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_health_no_muta_ninguna_tabla(api_client, usuario_admin_staff, evento):
    """
    GIVEN: an administrator and a populated database
    WHEN:  GET /api/administracion/health
    THEN:  no row of the touched tables changed.
    """
    antes = {
        "eventos": Evento.objects.count(),
        "usuarios": Usuario.objects.count(),
        "personas": Persona.objects.count(),
    }

    response = api_client.get(URL_HEALTH, **_auth_header(usuario_admin_staff))
    assert response.status_code == 200

    assert {
        "eventos": Evento.objects.count(),
        "usuarios": Usuario.objects.count(),
        "personas": Persona.objects.count(),
    } == antes
