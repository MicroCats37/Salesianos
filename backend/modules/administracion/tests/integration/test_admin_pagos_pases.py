"""
Integration tests — the party-pass purchases in the administrative area (A5/A6).

Covers the contract of the pass purchases in the payments table:

1. the pass purchases appear as `tipo=PASE` with `pase_id` and NO
   `inscripcion_id` (the two identities are exclusive),
2. the `PASE` filter selects ONLY the pass batches and the sports kinds
   (INICIAL / AMPLIACION) keep working exactly as before,
3. the free text reaches the buyer, the order number and the pass name,
4. the payment origin stays DERIVED (IZIPAY / MANUAL / SIN_PAGO),
5. the pagination and the ordering by amount work over both populations,
6. the number of queries does NOT grow with the number of pass purchases,
7. the drilldown exposes the composition and the rights of a pass purchase
   WITHOUT exposing the QR, the provider metadata or the provider internals,
8. the pass metrics live in their OWN block of the overview and never
   contaminate the sports metrics.

The HTTP client is `django.test.Client`: the controllers are async and this is
the pattern already established by the rest of the project
(`contract/django-app-architecture-contract.md` §2.1).
"""
import json
from decimal import Decimal

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from modules.administracion.tests.factories import (
    make_auth_header,
    make_forbidden_keys,
    make_list_query,
)
from modules.pagos.domain.models import TransaccionPago
from modules.salesianos_fest.domain.models import PaseBeneficiario

URL_LISTA = "/api/administracion/pagos"
URL_DETALLE = "/api/administracion/pagos/{orden_pago_id}"
URL_RESUMEN = "/api/administracion/resumen"


def _items(response):
    """The rows of a paginated administrative answer."""
    return response.json()["data"]["items"]


def _por_compra(items, compra_id):
    """The row of one purchase."""
    return next(item for item in items if item["compra_id"] == str(compra_id))


# ── Tests: the pass rows of the payments table ──────────────────────────────


@pytest.mark.django_db
def test_la_lista_de_pagos_incluye_las_compras_de_pases(
    api_client, usuario_admin_staff, escenario_pases
):
    """
    GIVEN: a purchase of passes
    WHEN:  GET /api/administracion/pagos
    THEN:  the row answers tipo=PASE, pase_id set and inscripcion_id null
    """
    response = api_client.get(
        URL_LISTA, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200, response.content
    fila = _por_compra(_items(response), escenario_pases["compra_manual"].id)
    assert fila["tipo"] == "PASE"
    assert fila["pase_id"] == str(escenario_pases["pase"].id)
    assert fila["inscripcion_id"] is None
    assert fila["producto_nombre"] == "Pase de Fiesta"
    assert fila["cantidad"] == 1
    assert fila["precio_unitario"] == 25.0
    assert fila["total"] == 25.0


@pytest.mark.django_db
def test_la_identidad_de_la_composicion_es_excluyente(
    api_client, usuario_admin_staff, escenario_operativo, escenario_pases
):
    """
    GIVEN: a sports purchase AND a pass purchase of the same event
    WHEN:  GET /api/administracion/pagos
    THEN:  the sports row carries inscripcion_id and NO pase_id; the pass row
           carries pase_id and NO inscripcion_id
    """
    response = api_client.get(
        URL_LISTA, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200, response.content
    items = _items(response)

    deportiva = _por_compra(items, escenario_operativo["compra_inicial"].id)
    assert deportiva["tipo"] == "INICIAL"
    assert deportiva["inscripcion_id"] == str(
        escenario_operativo["inscripcion_1"].id
    )
    assert deportiva["pase_id"] is None
    assert deportiva["producto_nombre"] == "Pack FEST"

    fila_pase = _por_compra(items, escenario_pases["compra_manual"].id)
    assert fila_pase["pase_id"] is not None
    assert fila_pase["inscripcion_id"] is None


@pytest.mark.django_db
def test_el_filtro_por_tipo_pase_solo_devuelve_pases(
    api_client, usuario_admin_staff, escenario_operativo, escenario_pases
):
    """
    GIVEN: sports purchases AND pass purchases of the active event
    WHEN:  GET /api/administracion/pagos?tipo=PASE
    THEN:  only the pass purchases answer
    """
    response = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(tipo="PASE"),
    )

    assert response.status_code == 200, response.content
    body = response.json()["data"]
    assert body["total"] == 3
    assert {item["tipo"] for item in body["items"]} == {"PASE"}


@pytest.mark.django_db
def test_los_filtros_deportivos_no_regresionan(
    api_client, usuario_admin_staff, escenario_operativo, escenario_pases
):
    """
    GIVEN: sports purchases AND pass purchases of the active event
    WHEN:  GET /api/administracion/pagos?tipo=INICIAL / ?tipo=AMPLIACION
    THEN:  the sports kinds answer exactly the same rows as before
    """
    inicial = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(tipo="INICIAL"),
    )
    ampliacion = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(tipo="AMPLIACION"),
    )

    assert inicial.status_code == 200, inicial.content
    assert ampliacion.status_code == 200, ampliacion.content
    assert inicial.json()["data"]["total"] == 2
    assert ampliacion.json()["data"]["total"] == 3
    assert all(
        item["tipo"] == "INICIAL" for item in inicial.json()["data"]["items"]
    )
    assert all(
        item["pase_id"] is None
        for item in inicial.json()["data"]["items"]
    )


@pytest.mark.django_db
def test_la_busqueda_alcanza_el_comprador_el_orden_y_el_pase(
    api_client, usuario_admin_staff, escenario_pases
):
    """
    GIVEN: a purchase of passes of a buyer
    WHEN:  GET /api/administracion/pagos?q=<documento | numero de orden | nombre del
           pase>
    THEN:  the free text reaches the buyer, the order and the pass
    """
    por_comprador = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(q="12345678"),
    )
    por_orden = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(q="ORD-PASE-MANU"),
    )
    por_pase = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(q="Pase de Fiesta"),
    )

    assert por_comprador.status_code == 200, por_comprador.content
    assert por_orden.status_code == 200, por_orden.content
    assert por_pase.status_code == 200, por_pase.content
    assert por_comprador.json()["data"]["total"] == 3
    assert por_orden.json()["data"]["total"] == 1
    assert por_pase.json()["data"]["total"] == 3


@pytest.mark.django_db
def test_el_origen_del_pago_es_derivado(
    api_client, usuario_admin_staff, escenario_pases
):
    """
    GIVEN: pass purchases paid with the provider, paid manually and unpaid
    WHEN:  GET /api/administracion/pagos
    THEN:  the origin is DERIVED from the evidence: IZIPAY, MANUAL, SIN_PAGO
    """
    response = api_client.get(
        URL_LISTA, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200, response.content
    items = _items(response)

    assert (
        _por_compra(items, escenario_pases["compra_izipay"].id)["origen_pago"]
        == "IZIPAY"
    )
    assert (
        _por_compra(items, escenario_pases["compra_manual"].id)["origen_pago"]
        == "MANUAL"
    )
    assert (
        _por_compra(items, escenario_pases["compra_pendiente"].id)["origen_pago"]
        == "SIN_PAGO"
    )


@pytest.mark.django_db
def test_la_paginacion_y_el_orden_por_cantidad_son_estables(
    api_client, usuario_admin_staff, escenario_operativo, escenario_pases
):
    """
    GIVEN: sports purchases AND pass purchases of the active event
    WHEN:  GET /api/administracion/pagos?ordering=cantidad&page_size=2
    THEN:  the page is ordered by the amount of the COMPOSITION (sports and
           pass rows together) and it never repeats a row
    """
    primera = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(ordering="cantidad", page_size=2),
    )
    segunda = api_client.get(
        URL_LISTA,
        **make_auth_header(usuario_admin_staff),
        data=make_list_query(ordering="cantidad", page_size=2, page=2),
    )

    assert primera.status_code == 200, primera.content
    assert segunda.status_code == 200, segunda.content
    assert primera.json()["data"]["total"] == 8

    ids_primera = [item["compra_id"] for item in primera.json()["data"]["items"]]
    ids_segunda = [item["compra_id"] for item in segunda.json()["data"]["items"]]
    assert len(ids_primera) == 2
    assert not set(ids_primera) & set(ids_segunda)


@pytest.mark.django_db
def test_el_conteo_de_consultas_no_crece_con_las_compras_de_pases(
    api_client, usuario_admin_staff, escenario_operativo, escenario_pases
):
    """
    GIVEN: the same event with more rows
    WHEN:  GET /api/administracion/pagos before and after adding pass purchases
    THEN:  the number of queries is the SAME — the table never grows an N+1
           over the pass purchases
    """
    with CaptureQueriesContext(connection) as contexto_inicial:
        respuesta = api_client.get(
            URL_LISTA, **make_auth_header(usuario_admin_staff)
        )
    assert respuesta.status_code == 200, respuesta.content
    consultas_iniciales = len(contexto_inicial)

    # More pass purchases of the SAME event.
    from modules.commerce.domain.models import Compra
    from modules.pagos.domain.models import OrdenPago
    from modules.salesianos_fest.domain.models import CompraPase

    for indice in range(4):
        orden = OrdenPago.objects.create(
            numero=f"ORD-PASE-EXTRA-{indice}",
            monto_total=Decimal("25.00"),
            moneda="PEN",
            estado="PENDIENTE",
        )
        compra = Compra.objects.create(
            responsable=escenario_pases["comprador"],
            descripcion="Compra de pases extra",
            total=Decimal("25.00"),
            estado="PENDIENTE",
            orden_pago=orden,
        )
        CompraPase.objects.create(
            compra=compra,
            pase=escenario_pases["pase"],
            evento=escenario_pases["evento"],
            cantidad=1,
            precio_unitario=Decimal("25.00"),
            total=Decimal("25.00"),
        )

    with CaptureQueriesContext(connection) as contexto_final:
        respuesta = api_client.get(
            URL_LISTA, **make_auth_header(usuario_admin_staff)
        )
    assert respuesta.status_code == 200, respuesta.content
    assert len(contexto_final) == consultas_iniciales


@pytest.mark.django_db
def test_el_detalle_de_una_compra_de_pases_expone_su_composicion(
    api_client, usuario_admin_staff, escenario_pases
):
    """
    GIVEN: a PAID pass purchase with an active and a revoked right
    WHEN:  GET /api/administracion/pagos/{orden_pago_id}
    THEN:  the drilldown exposes the pass composition and the rights (slot and
           state), without any name, document or credential
    """
    response = api_client.get(
        URL_DETALLE.format(orden_pago_id=escenario_pases["orden_manual"].id),
        **make_auth_header(usuario_admin_staff),
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["tipo"] == "PASE"
    assert data["pase_id"] == str(escenario_pases["pase"].id)
    assert data["inscripcion_id"] is None
    assert data["producto_nombre"] == "Pase de Fiesta"
    assert data["beneficiarios_activos"] == 1
    assert data["beneficiarios_revocados"] == 1

    slots = sorted(item["slot"] for item in data["beneficiarios"])
    assert slots == [1, 2]
    assert all("nombre" not in item for item in data["beneficiarios"])
    assert all("numero_documento" not in item for item in data["beneficiarios"])


@pytest.mark.django_db
def test_las_compras_de_pases_no_exponen_secretos(
    api_client, usuario_admin_staff, escenario_pases
):
    """
    GIVEN: a pass purchase with a provider transaction that carries secrets
    WHEN:  GET /api/administracion/pagos and its drilldown
    THEN:  no credential, provider internal or QR travels in the payload
    """
    lista = api_client.get(
        URL_LISTA, **make_auth_header(usuario_admin_staff)
    )
    detalle = api_client.get(
        URL_DETALLE.format(orden_pago_id=escenario_pases["orden_izipay"].id),
        **make_auth_header(usuario_admin_staff),
    )

    assert lista.status_code == 200, lista.content
    assert detalle.status_code == 200, detalle.content

    crudo = json.dumps(lista.json()) + json.dumps(detalle.json())
    for prohibido in make_forbidden_keys():
        assert prohibido not in crudo


@pytest.mark.django_db
def test_el_resumen_reporta_las_metricas_de_pases_en_un_bloque_propio(
    api_client, usuario_admin_staff, escenario_operativo, escenario_pases
):
    """
    GIVEN: the sports scenario AND the pass scenario of the active event
    WHEN:  GET /api/administracion/resumen
    THEN:  the `pases` block answers its own metrics and the sports blocks are
           exactly the ones of the sports scenario
    """
    response = api_client.get(
        URL_RESUMEN, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]

    esperado = escenario_pases["esperado"]["pases"]
    assert data["pases"] == esperado

    # The pass revenue NEVER contaminates the sports metrics.
    assert data["pagos"] == escenario_operativo["esperado"]["pagos"]
    assert data["cupos"] == escenario_operativo["esperado"]["cupos"]


@pytest.mark.django_db
def test_el_resumen_excluye_las_compras_de_pases_de_otra_edicion(
    api_client, usuario_admin_staff, escenario_pases
):
    """
    GIVEN: a pass purchase of ANOTHER edition
    WHEN:  GET /api/administracion/resumen
    THEN:  the pass block of the ACTIVE event never counts it
    """
    response = api_client.get(
        URL_RESUMEN, **make_auth_header(usuario_admin_staff)
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    # The scenario creates 6 sold passes of the active event; the 50 passes of
    # the other edition are never counted.
    assert data["pases"]["pases_vendidos"] == 6


# ── Tests: the cancellation of a pass purchase ──────────────────────────────


@pytest.mark.django_db
def test_la_cancelacion_administrativa_de_pases_anula_la_aprobacion_manual_activa(
    api_client, usuario_admin_superuser, escenario_pases
):
    """
    GIVEN: a pass purchase paid with an ACTIVE manual approval
    WHEN:  a break-glass administrator cancels the purchase
    THEN:  the approval is ANULADA in the SAME operation: a cancelled order
           never keeps ACTIVE evidence of a payment
    """
    orden = escenario_pases["orden_manual"]

    response = api_client.post(
        "/api/administracion/pases/compras/"
        f"{escenario_pases['compra_manual'].id}/cancelar",
        data=json.dumps({"motivo": "Cancelación administrativa"}),
        content_type="application/json",
        **make_auth_header(usuario_admin_superuser),
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["estado_compra"] == "CANCELADA"
    assert data["estado_orden"] == "CANCELADA"
    assert data["beneficiarios_revocados"] == 1

    orden.refresh_from_db()
    assert orden.estado == "CANCELADA"
    aprobacion = orden.aprobaciones_manuales.order_by("-created_at").first()
    assert aprobacion.estado == "ANULADA"
    assert aprobacion.motivo_anulacion == "Cancelación administrativa"


@pytest.mark.django_db
def test_la_cancelacion_administrativa_de_pases_no_toca_la_transaccion_del_proveedor(
    api_client, usuario_admin_superuser, escenario_pases
):
    """
    GIVEN: a pass purchase paid with the PROVIDER
    WHEN:  a break-glass administrator cancels the purchase
    THEN:  the provider transaction stays IMMUTABLE: the cancellation is a
           commercial cancellation, never a monetary refund
    """
    antes = TransaccionPago.objects.count()

    response = api_client.post(
        "/api/administracion/pases/compras/"
        f"{escenario_pases['compra_izipay'].id}/cancelar",
        data=json.dumps({"motivo": "Cancelación administrativa"}),
        content_type="application/json",
        **make_auth_header(usuario_admin_superuser),
    )

    assert response.status_code == 200, response.content
    assert TransaccionPago.objects.count() == antes
    transaccion = TransaccionPago.objects.get(
        orden_pago=escenario_pases["orden_izipay"]
    )
    assert transaccion.status == "EXITO"


@pytest.mark.django_db
def test_la_anulacion_de_un_pago_manual_reporta_los_derechos_de_pase(
    api_client, usuario_admin_superuser, escenario_pases, settings
):
    """
    GIVEN: a pass purchase paid manually with an active right
    WHEN:  a break-glass administrator annuls the manual approval
    THEN:  the answer reports the revoked PASS rights apart from the sports
           assignments
    """
    settings.PAGO_MANUAL_APROBACION_ENABLED = True

    response = api_client.post(
        f"/api/administracion/pagos/{escenario_pases['orden_manual'].id}/anular-manual",
        data=json.dumps({"motivo": "El abono no se verificó"}),
        content_type="application/json",
        **make_auth_header(usuario_admin_superuser),
    )

    assert response.status_code == 200, response.content
    data = response.json()["data"]
    assert data["resultado"] == "ANULADA"
    assert data["asignaciones_revocadas"] == 0
    assert data["beneficiarios_revocados"] == 1

    fila = PaseBeneficiario.objects.get(
        compra_pase__compra=escenario_pases["compra_manual"],
        estado="REVOCADA",
        motivo_revocacion="El abono no se verificó",
    )
    assert fila.motivo_revocacion == "El abono no se verificó"
