"""Integration tests for accreditations and access records (A10-A12)."""

import pytest

from modules.administracion.tests.factories import (
    make_auth_header,
    make_forbidden_keys,
    make_list_query,
)


URL_ACREDITACIONES = "/api/administracion/acreditaciones"
URL_DETALLE = "/api/administracion/acreditaciones/{acreditacion_id}"
URL_ACCESOS = "/api/administracion/accesos"


@pytest.mark.django_db
@pytest.mark.parametrize("url", [URL_ACREDITACIONES, URL_ACCESOS])
def test_listas_anonimo_responden_401(api_client, url):
    response = api_client.get(url)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


@pytest.mark.django_db
@pytest.mark.parametrize("url", [URL_ACREDITACIONES, URL_ACCESOS])
def test_listas_no_admin_responden_403(api_client, usuario_no_admin, url):
    response = api_client.get(url, **make_auth_header(usuario_no_admin))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACTION_NOT_ALLOWED"


@pytest.mark.django_db
def test_detalle_requiere_admin(api_client, usuario_no_admin, escenario_operativo):
    url = URL_DETALLE.format(
        acreditacion_id=escenario_operativo["acreditacion_1"].id
    )

    assert api_client.get(url).status_code == 401
    assert api_client.get(
        url, **make_auth_header(usuario_no_admin)
    ).status_code == 403


@pytest.mark.django_db
def test_lista_acreditaciones_respeta_evento_y_contadores(
    api_client, usuario_admin_staff, escenario_operativo
):
    response = api_client.get(
        URL_ACREDITACIONES, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 4
    ids = {item["id"] for item in data["items"]}
    assert str(escenario_operativo["acreditacion_fuera"].id) not in ids

    por_documento = {item["persona_documento"]: item for item in data["items"]}
    assert por_documento["33333333"]["estado"] == "ACTIVA"
    assert por_documento["33333333"]["accesos_permitidos"] == 1
    assert por_documento["44444444"]["estado"] == "PENDIENTE"
    assert por_documento["66666666"]["autorizacion_fiesta"] == "BLOQUEADA"
    assert por_documento["66666666"]["habilitado"] is False

    cuerpo = response.text.lower()
    for prohibido in make_forbidden_keys():
        assert prohibido not in cuerpo


@pytest.mark.django_db
def test_filtros_de_acreditacion(
    api_client, usuario_admin_staff, escenario_operativo
):
    headers = make_auth_header(usuario_admin_staff)

    activas = api_client.get(
        URL_ACREDITACIONES,
        **headers,
        data=make_list_query(estado="ACTIVA"),
    ).json()["data"]
    assert activas["total"] == 2

    bloqueadas = api_client.get(
        URL_ACREDITACIONES,
        **headers,
        data=make_list_query(autorizacion_fiesta="BLOQUEADA"),
    ).json()["data"]
    assert bloqueadas["total"] == 1

    con_acceso = api_client.get(
        URL_ACREDITACIONES,
        **headers,
        data=make_list_query(acceso_fiesta="true"),
    ).json()["data"]
    assert con_acceso["total"] == 3

    por_persona = api_client.get(
        URL_ACREDITACIONES,
        **headers,
        data=make_list_query(q="Alvarez"),
    ).json()["data"]
    assert por_persona["total"] == 1
    assert por_persona["items"][0]["persona_documento"] == "33333333"


@pytest.mark.django_db
def test_detalle_incluye_accesos_sin_exponer_qr(
    api_client, usuario_admin_staff, escenario_operativo
):
    response = api_client.get(
        URL_DETALLE.format(
            acreditacion_id=escenario_operativo["acreditacion_1"].id
        ),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["persona_documento"] == "33333333"
    assert data["accesos_permitidos"] == 1
    assert len(data["accesos"]) == 1
    assert data["accesos"][0]["resultado"] == "PERMITIDO"
    assert "codigo_qr" not in response.text.lower()


@pytest.mark.django_db
@pytest.mark.parametrize("clave", ["acreditacion_fuera", None])
def test_detalle_fuera_de_alcance_o_inexistente_responde_404(
    api_client,
    usuario_admin_staff,
    escenario_operativo,
    clave,
):
    acreditacion_id = (
        escenario_operativo[clave].id
        if clave
        else "11111111-2222-3333-4444-555555555555"
    )
    response = api_client.get(
        URL_DETALLE.format(acreditacion_id=acreditacion_id),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.django_db
def test_lista_accesos_respeta_evento_y_filtros(
    api_client, usuario_admin_staff, escenario_operativo
):
    headers = make_auth_header(usuario_admin_staff)
    response = api_client.get(URL_ACCESOS, **headers)

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 3
    assert {item["punto_acceso"] for item in data["items"]} == {
        "Puerta 1",
        "Puerta 2",
    }

    denegados = api_client.get(
        URL_ACCESOS,
        **headers,
        data=make_list_query(resultado="DENEGADO"),
    ).json()["data"]
    assert denegados["total"] == 2

    puerta_1 = api_client.get(
        URL_ACCESOS,
        **headers,
        data=make_list_query(punto_acceso="Puerta 1"),
    ).json()["data"]
    assert puerta_1["total"] == 2

    por_persona = api_client.get(
        URL_ACCESOS,
        **headers,
        data=make_list_query(q="Mendoza"),
    ).json()["data"]
    assert por_persona["total"] == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("url", "parametro", "valor"),
    [
        (URL_ACREDITACIONES, "estado", "NO_EXISTE"),
        (URL_ACREDITACIONES, "autorizacion_fiesta", "NO_EXISTE"),
        (URL_ACREDITACIONES, "acceso_fiesta", "quizas"),
        (URL_ACCESOS, "resultado", "NO_EXISTE"),
        (URL_ACCESOS, "desde", "ayer"),
        (URL_ACCESOS, "ordering", "fecha_hora; DROP TABLE accesos"),
    ],
)
def test_filtros_invalidos_responden_422(
    api_client,
    usuario_admin_staff,
    escenario_operativo,
    url,
    parametro,
    valor,
):
    response = api_client.get(
        url,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(**{parametro: valor}),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.django_db
def test_endpoints_de_acreditacion_no_mutan_datos(
    api_client, usuario_admin_staff, escenario_operativo
):
    from modules.salesianos_fest.domain.models import AcreditacionEvento, ControlAcceso

    antes = (AcreditacionEvento.objects.count(), ControlAcceso.objects.count())
    headers = make_auth_header(usuario_admin_staff)

    api_client.get(URL_ACREDITACIONES, **headers)
    api_client.get(URL_ACCESOS, **headers)
    api_client.get(
        URL_DETALLE.format(
            acreditacion_id=escenario_operativo["acreditacion_1"].id
        ),
        **headers,
    )

    assert antes == (AcreditacionEvento.objects.count(), ControlAcceso.objects.count())
