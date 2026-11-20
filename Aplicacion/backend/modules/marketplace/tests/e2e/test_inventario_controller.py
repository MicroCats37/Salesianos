"""La superficie HTTP del inventario y de las entregas de marketplace.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0`

GIVEN  un administrador y un catálogo con existencias
WHEN   consulta el inventario, registra un movimiento o confirma una entrega
THEN   responde el envelope congelado con los TRES hechos del inventario
       (físico, reservado, disponible) y con el acta de la entrega.

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).
"""

import json

import pytest
from django.test import Client

from modules.marketplace.tests.factories import (
    make_movimiento_payload,
    make_reversion_payload,
)

pytestmark = [
    pytest.mark.urls("modules.marketplace.tests.urls_marketplace"),
    pytest.mark.django_db,
]


@pytest.fixture
def cliente():
    """Cliente HTTP de prueba."""
    return Client()


def _autorizacion(usuario) -> dict:
    """El header `Authorization` del usuario indicado."""
    from ninja_jwt.tokens import RefreshToken

    token = str(RefreshToken.for_user(usuario).access_token)
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _post(cliente, url, payload=None, usuario=None):
    """POST JSON con (opcionalmente) la credencial del actor."""
    cabeceras = dict(_autorizacion(usuario)) if usuario is not None else {}
    if payload is None:
        return cliente.post(url, **cabeceras)
    return cliente.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
        **cabeceras,
    )


# ── RT-MK-08 · inventario ────────────────────────────────────────────────────


def test_el_inventario_requiere_administracion(cliente, producto_con_stock):
    """GIVEN una petición sin credencial
    WHEN  se consulta el inventario
    THEN  responde 401 `AUTHENTICATION_REQUIRED`: la autenticación se resuelve
          ANTES que cualquier permiso (FR-01 §4.4).
    """
    respuesta = cliente.get("/api/administracion/marketplace/inventario")

    assert respuesta.status_code == 401, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_un_usuario_normal_no_administra_el_inventario(
    cliente, usuario_comprador, producto_con_stock
):
    """GIVEN una cuenta autenticada que NO es administradora
    WHEN  se consulta el inventario
    THEN  responde 403 `ACTION_NOT_ALLOWED`: el backend autoriza
          definitivamente (RN-A01).
    """
    respuesta = cliente.get(
        "/api/administracion/marketplace/inventario",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 403, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "ACTION_NOT_ALLOWED"


def test_el_inventario_muestra_los_tres_hechos(
    cliente, usuario_admin, producto_con_stock
):
    """GIVEN un producto con 10 existencias
    WHEN  el administrador consulta el inventario
    THEN  responde 200 con el stock FÍSICO, lo RESERVADO y lo DISPONIBLE: el
          cliente no calcula ninguno (RN-M06).
    """
    respuesta = cliente.get(
        "/api/administracion/marketplace/inventario",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True

    inventario = cuerpo["data"][0]
    assert inventario["producto_id"] == str(producto_con_stock.id)
    assert inventario["stock"] == 10
    assert inventario["reservado"] == 0
    assert inventario["disponible"] == 10
    assert inventario["movimientos"] == []


# ── RT-MK-09 · movimiento manual ─────────────────────────────────────────────


def test_un_movimiento_actualiza_el_stock_y_la_bitacora(
    cliente, usuario_admin, producto_con_stock
):
    """GIVEN un producto con 10 existencias
    WHEN  el administrador registra una salida de 3 unidades
    THEN  responde 201 con el movimiento y el stock pasa a 7 (RN-M04).
    """
    respuesta = _post(
        cliente,
        "/api/administracion/marketplace/inventario/movimientos",
        make_movimiento_payload(
            producto_con_stock.id,
            "MERMA",
            -3,
            "Merma por rotura",
        ),
        usuario_admin,
    )

    assert respuesta.status_code == 201, respuesta.content
    datos = json.loads(respuesta.content)["data"]
    assert datos["tipo"] == "MERMA"
    assert datos["cantidad"] == -3
    assert datos["motivo"] == "Merma por rotura"
    assert datos["referencia"]

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 7


def test_un_movimiento_con_el_signo_incoherente_responde_422(
    cliente, usuario_admin, producto_con_stock
):
    """GIVEN una reposición (que ENTRA)
    WHEN  se declara con cantidad negativa
    THEN  responde 422 `MOVIMIENTO_INVENTARIO_INVALIDO`: el signo lo impone la
          naturaleza del movimiento (RN-M04).
    """
    respuesta = _post(
        cliente,
        "/api/administracion/marketplace/inventario/movimientos",
        make_movimiento_payload(
            producto_con_stock.id,
            "REPOSICION",
            -3,
            "Entrada con signo invertido",
        ),
        usuario_admin,
    )

    assert respuesta.status_code == 422, respuesta.content
    assert (
        json.loads(respuesta.content)["error"]["code"]
        == "MOVIMIENTO_INVENTARIO_INVALIDO"
    )


def test_una_venta_no_se_puede_registrar_a_mano(
    cliente, usuario_admin, producto_con_stock
):
    """GIVEN una venta (que la genera el pago confirmado)
    WHEN  un administrador intenta registrarla a mano
    THEN  responde 422: la venta sólo la produce la activación (RN-M06).
    """
    respuesta = _post(
        cliente,
        "/api/administracion/marketplace/inventario/movimientos",
        make_movimiento_payload(
            producto_con_stock.id,
            "VENTA",
            -1,
            "Venta inventada",
        ),
        usuario_admin,
    )

    assert respuesta.status_code == 422, respuesta.content


def test_la_reversa_compensa_el_movimiento(cliente, usuario_admin, producto_con_stock):
    """GIVEN una reposición de 5 unidades
    WHEN  el administrador la compensa con una reversa
    THEN  responde 201 con la reversa y el stock vuelve al punto de partida
          (RN-M04).
    """
    original = _post(
        cliente,
        "/api/administracion/marketplace/inventario/movimientos",
        make_movimiento_payload(
            producto_con_stock.id,
            "REPOSICION",
            5,
            "Recepción de mercadería",
        ),
        usuario_admin,
    )
    assert original.status_code == 201, original.content
    movimiento_id = json.loads(original.content)["data"]["id"]

    respuesta = _post(
        cliente,
        f"/api/administracion/marketplace/inventario/movimientos/{movimiento_id}/revertir",
        make_reversion_payload("Recepción duplicada"),
        usuario_admin,
    )

    assert respuesta.status_code == 201, respuesta.content
    datos = json.loads(respuesta.content)["data"]
    assert datos["tipo"] == "REVERSION"
    assert datos["cantidad"] == -5

    producto_con_stock.refresh_from_db()
    assert producto_con_stock.stock == 10


# ── RT-MK-10 / RT-MK-11 · entregas ───────────────────────────────────────────


def test_la_cola_de_entregas_no_incluye_los_pedidos_pendientes_de_pago(
    cliente, usuario_admin, pedido_pagado
):
    """GIVEN un pedido PAGADO
    WHEN  el administrador lista las entregas
    THEN  el pedido aparece: la cola se decide por el estado de la ENTREGA
          (RN-M07 · `QA-M04`).
    """
    respuesta = cliente.get(
        "/api/administracion/marketplace/entregas",
        **_autorizacion(usuario_admin),
    )

    assert respuesta.status_code == 200, respuesta.content
    datos = json.loads(respuesta.content)["data"]
    assert len(datos) == 1
    assert datos[0]["pedido_id"] == str(pedido_pagado.id)
    assert datos[0]["estado"] == "PAGADO"
    assert datos[0]["estado_entrega"] == "PENDIENTE"
    assert datos[0]["lineas"][0]["concepto_id"] == str(
        pedido_pagado.detalles.first().concepto_id
    )


def test_la_entrega_se_confirma_y_es_reintentable(
    cliente, usuario_admin, pedido_pagado
):
    """GIVEN un pedido pagado
    WHEN  el operador confirma la entrega y la REINTENTA
    THEN  ambas respuestas son 201 con el MISMO pedido y el mismo momento: la
          entrega no se duplica (QA-M04).
    """
    url = f"/api/administracion/marketplace/entregas/{pedido_pagado.id}/confirmar"

    primera = _post(cliente, url, None, usuario_admin)
    assert primera.status_code == 201, primera.content
    datos = json.loads(primera.content)["data"]
    assert datos["estado_entrega"] == "ENTREGADO"
    assert datos["cantidad_total"] == 1

    segunda = _post(cliente, url, None, usuario_admin)
    assert segunda.status_code == 201, segunda.content
    datos2 = json.loads(segunda.content)["data"]
    assert datos2["pedido_id"] == datos["pedido_id"]
    assert datos2["entregada_en"] == datos["entregada_en"]


def test_no_se_confirma_la_entrega_de_un_pedido_no_pagado(
    cliente,
    usuario_admin,
    usuario_comprador,
    pedido_orchestrator,
    producto_con_stock,
):
    """GIVEN un producto con existencias
    WHEN  se crea un pedido PENDIENTE y se intenta entregar
    THEN  responde 409 `PEDIDO_NO_PAGADO`: entregado exige pagado (RN-M07).
    """
    from asgiref.sync import async_to_sync

    from modules.marketplace.domain.schemas.pedido_schemas import (
        PedidoCreateData,
        PedidoItemCreateData,
    )

    resultado = async_to_sync(pedido_orchestrator.crear_pedido)(
        usuario_comprador,
        PedidoCreateData(
            items=[
                PedidoItemCreateData(
                    tipo="PRODUCTO",
                    producto_id=producto_con_stock.id,
                    cantidad=1,
                )
            ]
        ),
    )

    respuesta = _post(
        cliente,
        f"/api/administracion/marketplace/entregas/{resultado.id}/confirmar",
        None,
        usuario_admin,
    )

    assert respuesta.status_code == 409, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "PEDIDO_NO_PAGADO"
