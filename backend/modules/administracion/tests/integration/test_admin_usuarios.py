"""Integration tests for the administration account surfaces (A13, A14)."""

import pytest
from django.contrib.auth import get_user_model

from modules.administracion.tests.factories import (
    make_auth_header,
    make_forbidden_keys_de_cuentas,
    make_list_query,
)


URL_LISTA = "/api/administracion/usuarios"
URL_DETALLE = "/api/administracion/usuarios/{usuario_id}"


@pytest.mark.django_db
def test_lista_anonimo_responde_401(api_client):
    response = api_client.get(URL_LISTA)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
def test_lista_no_admin_responde_403(api_client, usuario_no_admin):
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_no_admin))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_detalle_requiere_admin(
    api_client, usuario_no_admin, escenario_operativo
):
    url = URL_DETALLE.format(usuario_id=usuario_no_admin.id)

    assert api_client.get(url).status_code == 401
    assert api_client.get(
        url, **make_auth_header(usuario_no_admin)
    ).status_code == 403


@pytest.mark.django_db
def test_lista_expone_cuentas_globales_sin_credenciales(
    api_client,
    usuario_admin_staff,
    usuario_admin_superuser,
    usuario_no_admin,
    usuario_inactivo,
    escenario_operativo,
):
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 4
    por_id = {item["id"]: item for item in data["items"]}
    assert por_id[str(usuario_admin_staff.id)]["es_admin"] is True
    assert por_id[str(usuario_admin_superuser.id)]["es_admin"] is True
    assert por_id[str(usuario_no_admin.id)]["es_admin"] is False
    assert por_id[str(usuario_inactivo.id)]["is_active"] is False

    cuerpo = response.text.lower()
    for prohibido in make_forbidden_keys_de_cuentas():
        assert prohibido not in cuerpo


@pytest.mark.django_db
def test_lista_publica_el_nivel_de_cada_cuenta(
    api_client,
    usuario_admin_staff,
    usuario_admin_superuser,
    usuario_no_admin,
    escenario_operativo,
):
    """
    GIVEN: accounts of every tier
    WHEN:  GET /api/administracion/usuarios
    THEN:  every account publishes `is_staff`, `is_superuser` and `nivel`.
    """
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    por_id = {item["id"]: item for item in response.json()["data"]["items"]}

    staff = por_id[str(usuario_admin_staff.id)]
    assert staff["is_staff"] is True
    assert staff["is_superuser"] is False
    assert staff["nivel"] == "staff"

    superusuario = por_id[str(usuario_admin_superuser.id)]
    assert superusuario["is_staff"] is True
    assert superusuario["is_superuser"] is True
    assert superusuario["nivel"] == "superusuario"

    normal = por_id[str(usuario_no_admin.id)]
    assert normal["is_staff"] is False
    assert normal["is_superuser"] is False
    assert normal["nivel"] == "usuario"


@pytest.mark.django_db
def test_filtros_y_busqueda_de_usuarios(
    api_client,
    usuario_admin_staff,
    usuario_admin_superuser,
    usuario_no_admin,
    usuario_inactivo,
    escenario_operativo,
):
    headers = make_auth_header(usuario_admin_staff)

    activos = api_client.get(
        URL_LISTA, **headers, data=make_list_query(estado="activo")
    ).json()["data"]
    assert activos["total"] == 3

    inactivos = api_client.get(
        URL_LISTA, **headers, data=make_list_query(estado="inactivo")
    ).json()["data"]
    assert inactivos["total"] == 1
    assert inactivos["items"][0]["id"] == str(usuario_inactivo.id)

    admins = api_client.get(
        URL_LISTA, **headers, data=make_list_query(es_admin="true")
    ).json()["data"]
    assert admins["total"] == 2
    assert all(item["es_admin"] for item in admins["items"])

    por_username = api_client.get(
        URL_LISTA,
        **headers,
        data=make_list_query(q=usuario_no_admin.username),
    ).json()["data"]
    assert por_username["total"] == 1

    por_documento = api_client.get(
        URL_LISTA,
        **headers,
        data=make_list_query(q=usuario_no_admin.persona_fk.numero_documento),
    ).json()["data"]
    assert por_documento["total"] == 1


@pytest.mark.django_db
def test_detalle_limita_inscripciones_al_evento_activo(
    api_client,
    usuario_admin_staff,
    usuario_no_admin,
    escenario_operativo,
):
    usuario_no_admin.persona_fk = escenario_operativo["responsable_1"]
    usuario_no_admin.save(update_fields=["persona_fk"])

    response = api_client.get(
        URL_DETALLE.format(usuario_id=usuario_no_admin.id),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(usuario_no_admin.id)
    assert data["persona_id"] == str(escenario_operativo["responsable_1"].id)
    assert data["personas"] == [
        {
            "inscripcion_id": str(escenario_operativo["inscripcion_1"].id),
            "estado": "RECIBIDA",
            "created_at": data["personas"][0]["created_at"],
        }
    ]
    assert str(escenario_operativo["inscripcion_fuera"].id) not in response.text

    cuerpo = response.text.lower()
    for prohibido in make_forbidden_keys_de_cuentas():
        assert prohibido not in cuerpo


@pytest.mark.django_db
@pytest.mark.parametrize(
    "usuario_id",
    ["no-es-un-uuid", "11111111-2222-3333-4444-555555555555"],
)
def test_detalle_desconocido_responde_404(
    api_client,
    usuario_admin_staff,
    escenario_operativo,
    usuario_id,
):
    response = api_client.get(
        URL_DETALLE.format(usuario_id=usuario_id),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("parametro", "valor"),
    [
        ("estado", "bloqueado"),
        ("es_admin", "quizas"),
        ("ordering", "username; DROP TABLE usuarios"),
    ],
)
def test_filtros_invalidos_responden_422(
    api_client,
    usuario_admin_staff,
    escenario_operativo,
    parametro,
    valor,
):
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(**{parametro: valor}),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.django_db
def test_endpoints_de_usuario_no_mutan_datos(
    api_client, usuario_admin_staff, escenario_operativo
):
    from modules.salesianos_fest.domain.models import Inscripcion

    User = get_user_model()
    antes = (User.objects.count(), Inscripcion.objects.count())
    headers = make_auth_header(usuario_admin_staff)

    api_client.get(URL_LISTA, **headers)
    api_client.get(
        URL_DETALLE.format(usuario_id=usuario_admin_staff.id),
        **headers,
    )

    assert antes == (User.objects.count(), Inscripcion.objects.count())
