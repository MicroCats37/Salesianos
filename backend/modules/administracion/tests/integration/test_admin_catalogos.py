"""
Integration tests — the filter catalogs (A2).

The catalogs reuse the catalog sources of the OWNING modules and scope them
to the active event; they never re-implement a business rule.

Covers:
- authorization (401 / 403 / 200),
- the event scope of the packages and the categories,
- the state vocabularies of the domain (never a second vocabulary),
- the access points read from the access log,
- no secret leakage,
- no accidental mutation,
- the typed 404 when there is no active event.
"""
import pytest
from ninja_jwt.tokens import AccessToken

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.models import Paquete

URL_CATALOGOS = "/api/administracion/catalogos"

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


# ── Authorization ─────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_catalogos_anonimo_responde_401(api_client):
    """
    GIVEN: an anonymous caller
    WHEN:  GET /api/administracion/catalogos
    THEN:  401 with the stable code AUTHENTICATION_REQUIRED.
    """
    response = api_client.get(URL_CATALOGOS)

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert body["data"] is None


@pytest.mark.django_db
def test_catalogos_no_admin_responde_403(api_client, usuario_no_admin):
    """
    GIVEN: an authenticated user that is NOT an administrator
    WHEN:  GET /api/administracion/catalogos
    THEN:  403 with the stable code ACTION_NOT_ALLOWED and no data.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_no_admin))

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "ACTION_NOT_ALLOWED"
    assert body["data"] is None


@pytest.mark.django_db
def test_catalogos_admin_responde_200(api_client, usuario_admin_staff, evento):
    """
    GIVEN: an administrator
    WHEN:  GET /api/administracion/catalogos
    THEN:  200 with the option lists of the active event.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert set(body["data"].keys()) == {
        "evento_id",
        "evento_nombre",
        "disciplinas",
        "paquetes",
        "promociones",
        "categorias",
        "puntos_acceso",
        "estados",
    }


@pytest.mark.django_db
def test_catalogos_sin_evento_activo_responde_404(api_client, usuario_admin_staff):
    """
    GIVEN: an administrator and NO active event in the database
    WHEN:  GET /api/administracion/catalogos
    THEN:  404 with the stable code EVENTO_ACTIVO_NO_ENCONTRADO.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EVENTO_ACTIVO_NO_ENCONTRADO"


# ── Catalogs ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_catalogos_lista_las_disciplinas_activas(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: two active disciplines and the hand-built scenario
    WHEN:  GET /api/administracion/catalogos
    THEN:  the disciplines are listed with their id, name and acronym.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    disciplinas = response.json()["data"]["disciplinas"]
    siglas = {item["sigla"] for item in disciplinas}
    assert siglas == {"F7", "VM"}

    futbol = next(item for item in disciplinas if item["sigla"] == "F7")
    assert futbol["id"] == str(escenario_operativo["disciplina_futbol"].id)
    assert futbol["nombre"] == "Fútbol 7"


@pytest.mark.django_db
def test_catalogos_lista_los_paquetes_del_evento_activo(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: a package of the active event and one of another edition
    WHEN:  GET /api/administracion/catalogos
    THEN:  only the package of the ACTIVE event is listed.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    paquetes = response.json()["data"]["paquetes"]
    assert [item["nombre"] for item in paquetes] == ["Pack FEST"]
    assert paquetes[0]["id"] == str(escenario_operativo["paquete"].id)
    assert paquetes[0]["tipo"] == "PACK"


@pytest.mark.django_db
def test_catalogos_lista_las_promociones_y_categorias(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an active promotion and an active category of the event
    WHEN:  GET /api/administracion/catalogos
    THEN:  both option lists are present and scoped to the active event.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert [item["nombre"] for item in data["promociones"]] == ["Promoción 2026"]
    assert [item["nombre"] for item in data["categorias"]] == ["Senior"]


@pytest.mark.django_db
def test_catalogos_lista_los_puntos_de_acceso_del_registro(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: two access points of the active event and one of another edition
    WHEN:  GET /api/administracion/catalogos
    THEN:  only the access points of the active event are offered.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    assert response.json()["data"]["puntos_acceso"] == ["Puerta 1", "Puerta 2"]


@pytest.mark.django_db
def test_catalogos_exponen_los_vocabularios_de_estado(
    api_client, usuario_admin_staff, evento
):
    """
    GIVEN: an administrator
    WHEN:  GET /api/administracion/catalogos
    THEN:  every state vocabulary of the domain is exposed, complete.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    estados = response.json()["data"]["estados"]
    assert estados["inscripcion"] == [
        "BORRADOR",
        "RECIBIDA",
        "EN_REVISION",
        "OBSERVADA",
        "VALIDADA",
        "CONFIRMADA",
        "RECHAZADA",
        "CANCELADA",
    ]
    assert estados["compra"] == ["PENDIENTE", "PAGADA", "CANCELADA"]
    assert estados["orden_pago"] == ["PENDIENTE", "PAGADA", "CANCELADA", "VENCIDA"]
    assert estados["asignacion_cupo"] == ["ACTIVA", "LIBERADA", "REVOCADA"]
    assert estados["equipo"] == ["EQUIPO_ACTIVO", "EQUIPO_CANCELADO"]
    assert estados["acreditacion"] == [
        "PENDIENTE",
        "ACTIVA",
        "SUSPENDIDA",
        "REVOCADA",
    ]
    assert estados["autorizacion_fiesta"] == [
        "AUTOMATICA",
        "AUTORIZADA",
        "BLOQUEADA",
    ]
    assert estados["acceso"] == ["PERMITIDO", "DENEGADO"]
    assert estados["pool"] == [
        "LISTO",
        "ESPERANDO_PAGO",
        "SIN_CAPACIDAD",
        "CUPO_POR_ASIGNAR",
    ]
    assert estados["rol_participante"] == ["J", "C", "D"]


@pytest.mark.django_db
def test_catalogos_identifican_el_evento_activo(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an administrator
    WHEN:  GET /api/administracion/catalogos
    THEN:  the payload identifies the ACTIVE event, resolved server-side.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    data = response.json()["data"]
    assert data["evento_id"] == str(escenario_operativo["evento"].id)
    assert data["evento_nombre"] == escenario_operativo["evento"].nombre


# ── Data-leak discipline ──────────────────────────────────────────────────────


@pytest.mark.django_db
def test_catalogos_no_expone_credenciales(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an administrator
    WHEN:  GET /api/administracion/catalogos
    THEN:  the body contains none of the forbidden keys.
    """
    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))

    crudo = response.content.decode().lower()
    for clave in CLAVES_PROHIBIDAS:
        assert clave not in crudo, f"La respuesta filtró la clave '{clave}'."


# ── No accidental mutation ────────────────────────────────────────────────────


@pytest.mark.django_db
def test_catalogos_no_muta_ninguna_tabla(
    api_client, usuario_admin_staff, escenario_operativo
):
    """
    GIVEN: an administrator and a populated database
    WHEN:  GET /api/administracion/catalogos
    THEN:  no row changed.
    """
    antes = {
        "eventos": Evento.objects.count(),
        "paquetes": Paquete.objects.count(),
    }

    response = api_client.get(URL_CATALOGOS, **_auth_header(usuario_admin_staff))
    assert response.status_code == 200

    assert {
        "eventos": Evento.objects.count(),
        "paquetes": Paquete.objects.count(),
    } == antes
