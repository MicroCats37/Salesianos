"""Integration tests for the administration payment surfaces (A5, A6)."""

import pytest

from modules.administracion.tests.factories import (
    make_auth_header,
    make_forbidden_keys,
    make_list_query,
)


URL_LISTA = "/api/administracion/pagos"
URL_DETALLE = "/api/administracion/pagos/{orden_pago_id}"


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
def test_detalle_anonimo_responde_401(api_client, escenario_operativo):
    response = api_client.get(
        URL_DETALLE.format(
            orden_pago_id=escenario_operativo["orden_inicial"].id
        )
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_detalle_no_admin_responde_403(
    api_client, usuario_no_admin, escenario_operativo
):
    response = api_client.get(
        URL_DETALLE.format(
            orden_pago_id=escenario_operativo["orden_inicial"].id
        ),
        **make_auth_header(usuario_no_admin),
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_lista_admin_devuelve_snapshot_comercial(
    api_client, usuario_admin_staff, escenario_operativo
):
    response = api_client.get(URL_LISTA, **make_auth_header(usuario_admin_staff))

    assert response.status_code == 200
    data = response.json()["data"]
    assert set(data) == {"items", "total", "page", "page_size", "total_pages"}
    assert data["total"] == 5

    por_compra = {item["compra_id"]: item for item in data["items"]}
    pagada = por_compra[str(escenario_operativo["compra_inicial"].id)]
    assert pagada["cantidad"] == 2
    assert pagada["precio_unitario"] == 75.0
    assert pagada["total"] == 150.0
    assert pagada["estado_compra"] == "PAGADA"
    assert pagada["estado_orden"] == "PAGADA"


@pytest.mark.django_db
def test_filtros_y_busqueda_de_pagos(
    api_client, usuario_admin_staff, escenario_operativo
):
    headers = make_auth_header(usuario_admin_staff)

    pagadas = api_client.get(
        URL_LISTA, **headers, data=make_list_query(estado_compra="PAGADA")
    ).json()["data"]
    assert pagadas["total"] == 2
    assert {item["estado_compra"] for item in pagadas["items"]} == {"PAGADA"}

    ampliaciones = api_client.get(
        URL_LISTA, **headers, data=make_list_query(tipo="AMPLIACION")
    ).json()["data"]
    assert ampliaciones["total"] == 3

    por_orden = api_client.get(
        URL_LISTA,
        **headers,
        data=make_list_query(q=escenario_operativo["orden_inicial"].numero),
    ).json()["data"]
    assert por_orden["total"] == 1

    por_responsable = api_client.get(
        URL_LISTA, **headers, data=make_list_query(q="Torres")
    ).json()["data"]
    assert por_responsable["total"] == 3


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("parametro", "valor"),
    [
        ("estado_compra", "NO_EXISTE"),
        ("estado_orden", "NO_EXISTE"),
        ("tipo", "NO_EXISTE"),
        ("desde", "ayer"),
        ("ordering", "total; DROP TABLE pagos"),
    ],
)
def test_parametro_invalido_responde_422(
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
def test_detalle_expone_intentos_sin_internos_del_proveedor(
    api_client, usuario_admin_staff, escenario_operativo
):
    response = api_client.get(
        URL_DETALLE.format(
            orden_pago_id=escenario_operativo["orden_inicial"].id
        ),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["compra_id"] == str(escenario_operativo["compra_inicial"].id)
    assert len(data["transacciones"]) == 2
    assert {item["status"] for item in data["transacciones"]} == {
        "EXITO",
        "FALLIDO",
    }
    assert set(data["transacciones"][0]) == {
        "id",
        "status",
        "amount",
        "currency",
        "metodo_pago",
        "response_code",
        "created_at",
    }

    cuerpo = response.text.lower()
    for prohibido in make_forbidden_keys():
        assert prohibido not in cuerpo


@pytest.mark.django_db
@pytest.mark.parametrize(
    "orden_pago_id",
    ["no-es-un-uuid", "11111111-2222-3333-4444-555555555555"],
)
def test_detalle_desconocido_responde_404(
    api_client,
    usuario_admin_staff,
    escenario_operativo,
    orden_pago_id,
):
    response = api_client.get(
        URL_DETALLE.format(orden_pago_id=orden_pago_id),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.django_db
def test_endpoints_de_pago_no_mutan_datos(
    api_client, usuario_admin_staff, escenario_operativo
):
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import OrdenPago, TransaccionPago

    antes = (
        Compra.objects.count(),
        OrdenPago.objects.count(),
        TransaccionPago.objects.count(),
    )
    headers = make_auth_header(usuario_admin_staff)

    api_client.get(URL_LISTA, **headers)
    api_client.get(
        URL_DETALLE.format(
            orden_pago_id=escenario_operativo["orden_inicial"].id
        ),
        **headers,
    )

    assert antes == (
        Compra.objects.count(),
        OrdenPago.objects.count(),
        TransaccionPago.objects.count(),
    )
