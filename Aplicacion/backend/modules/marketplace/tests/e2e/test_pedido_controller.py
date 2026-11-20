"""Superficie HTTP del pedido de marketplace (`DOM-05`).

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0` · `FREEZE-MD-1.0.0`

GIVEN  un comprador autenticado y un catálogo
WHEN   se crea el pedido y después se consulta su enlace privado
THEN   responde el envelope congelado con el SNAPSHOT del precio y con los
       TRES estados por separado: un pedido pagado NO es un pedido entregado
       (`RT-CM-03`, `RT-MK-04` · RN-M03 · RN-M07 · `QA-M03` · `QA-M04`).

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).

**El dinero viaja como cadena decimal.** El backend objetivo publica el
`Decimal` como texto (`core/responses.py` serializa con `model_dump(mode="json")`
y la clave `ser_json_decimal_to_float` no existe en Pydantic v2): es el
comportamiento OBSERVADO y CONGELADO del backend, con la decisión de contrato
`OD-A0R2-01` todavía ABIERTA. Las aserciones de este archivo lo fijan tal
como sale, sin inventar un tipo nuevo.
"""

import json
import uuid

import pytest
from django.test import Client

from modules.marketplace.tests.factories import make_item_pedido, make_pedido_payload

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


# ── RT-CM-03 · alta del pedido ──────────────────────────────────────────────


def test_el_alta_devuelve_el_pedido_con_su_snapshot(
    cliente, usuario_comprador, producto_con_oferta
):
    """GIVEN un producto con oferta vigente
    WHEN  el comprador crea el pedido
    THEN  responde 201 con el precio APLICADO congelado, el total derivado y
          el token del enlace privado (RN-C02, RN-M03).
    """
    respuesta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(
            make_pedido_payload(make_item_pedido(producto_con_oferta.id, 2))
        ),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 201, respuesta.content
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True

    datos = cuerpo["data"]
    assert datos["estado"] == "PENDIENTE"
    assert datos["estado_pago"] == "PENDIENTE"
    assert datos["estado_entrega"] == "PENDIENTE"
    assert datos["total"] == "14.00"
    assert datos["moneda"] == "PEN"
    assert datos["siguientes_acciones"] == ["REALIZAR_PAGO"]
    assert datos["recuperado"] is False

    linea = datos["lineas"][0]
    assert linea["tipo_concepto"] == "PRODUCTO"
    assert linea["concepto_id"] == str(producto_con_oferta.id)
    assert linea["cantidad"] == 2
    assert linea["precio_unitario"] == "10.00"
    assert linea["precio_aplicado"] == "7.00"
    assert linea["subtotal"] == "14.00"

    assert isinstance(datos["token"], str)
    assert datos["token"]


def test_sin_sesion_el_alta_responde_401(cliente, producto):
    """GIVEN una petición sin credencial
    WHEN  se crea el pedido
    THEN  responde 401 `AUTHENTICATION_REQUIRED`: la autenticación se
          resuelve ANTES que cualquier permiso (FR-01 §4.4).
    """
    respuesta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(make_pedido_payload(make_item_pedido(producto.id))),
        content_type="application/json",
    )

    assert respuesta.status_code == 401, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_un_reintento_devuelve_el_mismo_pedido(
    cliente, usuario_comprador, producto
):
    """GIVEN un pedido ya creado
    WHEN  se repite EXACTAMENTE la misma petición
    THEN  responde 201 con el MISMO pedido y `recuperado` en `true`: un
          reintento no duplica ni el pedido ni la compra (RN-C03, RN-C04).
    """
    payload = json.dumps(make_pedido_payload(make_item_pedido(producto.id, 2)))

    primero = cliente.post(
        "/api/marketplace/pedidos",
        data=payload,
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )
    segundo = cliente.post(
        "/api/marketplace/pedidos",
        data=payload,
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )

    assert primero.status_code == 201, primero.content
    assert segundo.status_code == 201, segundo.content
    datos_primero = json.loads(primero.content)["data"]
    datos_segundo = json.loads(segundo.content)["data"]
    assert datos_segundo["id"] == datos_primero["id"]
    assert datos_segundo["token"] == datos_primero["token"]
    assert datos_segundo["recuperado"] is True


def test_un_carrito_mixto_responde_422(cliente, usuario_comprador, producto):
    """GIVEN una intención con un producto y un pase
    WHEN  se crea el pedido
    THEN  responde 422 `PEDIDO_ITEMS_MIXTOS`: no hay carrito combinado
          (RN-C01).
    """
    respuesta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(
            make_pedido_payload(
                make_item_pedido(producto.id),
                make_item_pedido(producto.id, tipo="PASE"),
            )
        ),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 422, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "PEDIDO_ITEMS_MIXTOS"


def test_un_producto_inexistente_responde_404(
    cliente, usuario_comprador, edicion_publicada
):
    """GIVEN un producto que no existe
    WHEN  se crea el pedido
    THEN  responde 404 `PRODUCTO_NO_ENCONTRADO`: el catálogo se resuelve en
          el servidor y el rechazo no filtra información interna.
    """
    respuesta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(make_pedido_payload(make_item_pedido(uuid.uuid4()))),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 404, respuesta.content
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "PRODUCTO_NO_ENCONTRADO"
    assert "Traceback" not in json.dumps(cuerpo)


def test_una_cantidad_invalida_responde_422(cliente, usuario_comprador, producto):
    """GIVEN una cantidad fuera de rango
    WHEN  se crea el pedido
    THEN  responde 422 `PEDIDO_CANTIDAD_INVALIDA`: la regla la aplica el
          servidor, con su código estable.
    """
    respuesta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(make_pedido_payload(make_item_pedido(producto.id, 0))),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 422, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "PEDIDO_CANTIDAD_INVALIDA"


# ── RT-MK-04 · seguimiento por el enlace privado ─────────────────────────────


def test_el_seguimiento_muestra_los_tres_estados_por_separado(
    cliente, usuario_comprador, producto
):
    """GIVEN un pedido creado
    WHEN  el comprador abre su enlace privado
    THEN  responde 200 con `estado`, `estado_pago` y `estado_entrega` POR
          SEPARADO: pagada y entregada son hechos distintos (RN-M07).
    """
    alta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(make_pedido_payload(make_item_pedido(producto.id))),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )
    token = json.loads(alta.content)["data"]["token"]

    respuesta = cliente.get(f"/api/marketplace/pedidos/{token}")

    assert respuesta.status_code == 200, respuesta.content
    datos = json.loads(respuesta.content)["data"]
    assert datos["estado"] == "PENDIENTE"
    assert datos["estado_pago"] == "PENDIENTE"
    assert datos["estado_entrega"] == "PENDIENTE"
    assert datos["siguientes_acciones"] == ["REALIZAR_PAGO"]
    # El token NO vuelve en el seguimiento: viaja en el path.
    assert "token" not in datos


def test_el_enlace_privado_lo_abre_un_invitado_sin_sesion(
    cliente, usuario_comprador, producto
):
    """GIVEN un pedido creado por un comprador
    WHEN  un INVITADO (sin sesión) abre el enlace
    THEN  responde 200: el token ES la credencial del enlace (P-01).
    """
    alta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(make_pedido_payload(make_item_pedido(producto.id))),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )
    token = json.loads(alta.content)["data"]["token"]

    respuesta = cliente.get(f"/api/marketplace/pedidos/{token}")

    assert respuesta.status_code == 200, respuesta.content


def test_otro_usuario_no_puede_ver_el_pedido(
    cliente, usuario_comprador, usuario_ajeno, producto
):
    """GIVEN un pedido de un comprador
    WHEN  OTRO actor autenticado abre el enlace
    THEN  responde 403 `PEDIDO_NO_AUTORIZADO`: la titularidad no se
          sustituye (RN-U02, FR-03 §2.1).
    """
    alta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(make_pedido_payload(make_item_pedido(producto.id))),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )
    token = json.loads(alta.content)["data"]["token"]

    respuesta = cliente.get(
        f"/api/marketplace/pedidos/{token}",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "PEDIDO_NO_AUTORIZADO"


def test_un_token_desconocido_responde_404(cliente):
    """GIVEN un token que no existe
    WHEN  se consulta el enlace
    THEN  responde 404 `PEDIDO_NO_ENCONTRADO`: la denegación es NEUTRAL, el
          mismo código para un enlace inválido y para uno ajeno.
    """
    respuesta = cliente.get(f"/api/marketplace/pedidos/{uuid.uuid4().hex}")

    assert respuesta.status_code == 404, respuesta.content
    assert json.loads(respuesta.content)["error"]["code"] == "PEDIDO_NO_ENCONTRADO"


def test_la_respuesta_no_expone_internos_del_pago(
    cliente, usuario_comprador, producto
):
    """GIVEN un pedido recién creado
    WHEN  se lee su enlace
    THEN  la respuesta NO expone referencias técnicas, intentos ni
          evidencias del proveedor: sólo los hechos del pedido y la acción
          segura (FR-01 §4).
    """
    alta = cliente.post(
        "/api/marketplace/pedidos",
        data=json.dumps(make_pedido_payload(make_item_pedido(producto.id))),
        content_type="application/json",
        **_autorizacion(usuario_comprador),
    )
    token = json.loads(alta.content)["data"]["token"]

    respuesta = cliente.get(f"/api/marketplace/pedidos/{token}")

    assert respuesta.status_code == 200, respuesta.content
    cuerpo = json.loads(respuesta.content)
    datos = cuerpo["data"]
    assert "referencia_proveedor" not in json.dumps(cuerpo)
    assert "evidencia" not in json.dumps(cuerpo)
    assert "intento" not in json.dumps(cuerpo)
    assert set(datos) == {
        "id",
        "estado",
        "estado_pago",
        "estado_entrega",
        "total",
        "moneda",
        "lineas",
        "orden_pago_id",
        "siguientes_acciones",
        "created_at",
    }
