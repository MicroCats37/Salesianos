"""Superficie HTTP de los pagos: `RT-PG-01`, `RT-PG-02` y `RT-PG-03`.

Freeze: `FREEZE-CM-1.0.0` · `FREEZE-PS-1.0.0` (ledger FR-07 §3.3)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

GIVEN  una orden de pago con su compra, su intento y su veredicto
WHEN   se consulta o se confirma la orden por HTTP
THEN   responde el envelope congelado con el veredicto operativo y el
       historial de intentos, y los errores viajan con su código estable.

Cliente: `django.test.Client`, la alternativa SINCRÓNICA permitida por
FREEZE-TC-1.0.0 para controllers `async def`
(`contract/django-app-architecture-contract.md` §2.1).
"""

import json

import pytest
from django.test import Client

from modules.pagos.domain.constants import (
    EstadoOperativoPago,
    EstadoOrdenPago,
    EstadoTransaccionPago,
)
from modules.pagos.domain.models import TransaccionPago
from modules.pagos.tests.fixtures.pagos_fixtures import (
    firmar,
    payload_confirmacion,
    payload_http,
)

pytestmark = [
    pytest.mark.urls("modules.pagos.tests.urls_pagos"),
    pytest.mark.django_db,
]


@pytest.fixture
def cliente():
    """Cliente HTTP de prueba."""
    return Client()


def _token(usuario) -> str:
    """Un token de acceso para el usuario indicado."""
    from ninja_jwt.tokens import RefreshToken

    return str(RefreshToken.for_user(usuario).access_token)


def _autorizacion(usuario) -> dict:
    """El header `Authorization` del usuario indicado."""
    return {"HTTP_AUTHORIZATION": f"Bearer {_token(usuario)}"}


# ── RT-PG-03 · Lectura del estado de una orden ─────────────────────────────


def test_la_lectura_devuelve_el_veredicto_y_el_historial(
    cliente, orden_pago, compra, intento, usuario_comprador
):
    """GIVEN una orden pendiente con un intento
    WHEN  el comprador consulta su orden
    THEN  responde el envelope con el veredicto y el historial de intentos.
    """
    respuesta = cliente.get(
        f"/api/pagos/ordenes/{orden_pago.id}",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["error"] is None
    assert cuerpo["data"]["referencia"] == orden_pago.referencia
    assert cuerpo["data"]["estado"] == EstadoOrdenPago.PENDIENTE
    assert (
        cuerpo["data"]["estado_operativo"]["codigo"]
        == EstadoOperativoPago.PENDIENTE
    )
    assert cuerpo["data"]["estado_operativo"]["etiqueta"]
    assert cuerpo["data"]["estado_operativo"]["descripcion"]
    assert len(cuerpo["data"]["intentos"]) == 1
    assert cuerpo["data"]["intentos"][0]["intento"] == 1


def test_la_lectura_no_expone_la_referencia_tecnica_del_proveedor(
    cliente, orden_pago, compra, intento, usuario_comprador
):
    """GIVEN una orden con su intento
    WHEN  el comprador consulta su orden
    THEN  la referencia técnica del proveedor NO viaja en la respuesta.
    """
    respuesta = cliente.get(
        f"/api/pagos/ordenes/{orden_pago.id}",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 200
    assert intento.referencia_proveedor not in respuesta.content.decode("utf-8")


def test_la_lectura_de_otra_persona_es_403(
    cliente, orden_pago, compra, intento, usuario_ajeno
):
    """GIVEN una orden de otra persona
    WHEN  un tercero la consulta
    THEN  responde 403 con el código estable del catálogo.

    El código es `PAGO_NO_AUTORIZADO`: es el error de dominio de la
    titularidad de la orden, no el genérico de la capa HTTP.
    """
    respuesta = cliente.get(
        f"/api/pagos/ordenes/{orden_pago.id}",
        **_autorizacion(usuario_ajeno),
    )

    assert respuesta.status_code == 403
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is False
    assert cuerpo["error"]["code"] == "PAGO_NO_AUTORIZADO"


def test_la_lectura_de_una_orden_inexistente_es_404(
    cliente, usuario_comprador
):
    """GIVEN una orden que no existe
    WHEN  se consulta
    THEN  responde 404 ORDEN_PAGO_NO_ENCONTRADA.
    """
    respuesta = cliente.get(
        "/api/pagos/ordenes/00000000-0000-0000-0000-000000000000",
        **_autorizacion(usuario_comprador),
    )

    assert respuesta.status_code == 404
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "ORDEN_PAGO_NO_ENCONTRADA"


def test_la_lectura_sin_sesion_es_401(cliente, orden_pago, compra, intento):
    """GIVEN una petición sin sesión
    WHEN  se consulta la orden
    THEN  responde 401: la autenticación va antes que la autorización.
    """
    respuesta = cliente.get(f"/api/pagos/ordenes/{orden_pago.id}")

    assert respuesta.status_code == 401
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "AUTHENTICATION_REQUIRED"


# ── RT-PG-01 · Confirmación desde el navegador ─────────────────────────────


def test_la_confirmacion_devuelve_el_veredicto(cliente, orden_pago, compra, intento,
                                               usuario_comprador, clave_comercio):
    """GIVEN un reenvío firmado del navegador
    WHEN  se confirma la orden
    THEN  responde 200 con el veredicto `PAGADA`.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    respuesta = cliente.post(
        f"/api/pagos/ordenes/{orden_pago.id}/confirmar",
        data=json.dumps(
            {
                **payload,
                "payloadHttp": crudo,
                "signature": firmar(crudo, clave_comercio),
            }
        ),
        content_type="application/json",
        **{
            **_autorizacion(usuario_comprador),
            "HTTP_IDEMPOTENCY_KEY": "clave-de-idempotencia-e2e-0001",
        },
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert cuerpo["data"]["estado_orden"] == EstadoOrdenPago.CONFIRMADA
    assert (
        cuerpo["data"]["estado_operativo"]["codigo"] == EstadoOperativoPago.PAGADA
    )


def test_la_confirmacion_repetida_devuelve_el_mismo_resultado(
    cliente, orden_pago, compra, intento, usuario_comprador, clave_comercio
):
    """GIVEN un reenvío firmado ya procesado
    WHEN  se repite la misma operación con la misma clave
    THEN  devuelve el MISMO resultado y no hay un segundo hecho de pago.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)
    cuerpo_envio = {
        **payload,
        "payloadHttp": crudo,
        "signature": firmar(crudo, clave_comercio),
    }
    cabeceras = {
        **_autorizacion(usuario_comprador),
        "HTTP_IDEMPOTENCY_KEY": "clave-de-idempotencia-e2e-0002",
    }

    primera = cliente.post(
        f"/api/pagos/ordenes/{orden_pago.id}/confirmar",
        data=json.dumps(cuerpo_envio),
        content_type="application/json",
        **cabeceras,
    )
    segunda = cliente.post(
        f"/api/pagos/ordenes/{orden_pago.id}/confirmar",
        data=json.dumps(cuerpo_envio),
        content_type="application/json",
        **cabeceras,
    )

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert json.loads(primera.content)["data"] == json.loads(segunda.content)["data"]
    assert (
        TransaccionPago.objects.filter(
            orden_pago=orden_pago,
            estado=EstadoTransaccionPago.EXITO,
        ).count()
        == 1
    )


def test_la_confirmacion_con_firma_invalida_es_400(
    cliente, orden_pago, compra, intento, usuario_comprador, clave_comercio
):
    """GIVEN un reenvío con una firma que NO verifica
    WHEN  se confirma
    THEN  responde 400 PAGO_FIRMA_INVALIDA y no se muta nada.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    respuesta = cliente.post(
        f"/api/pagos/ordenes/{orden_pago.id}/confirmar",
        data=json.dumps(
            {
                **payload,
                "payloadHttp": crudo,
                "signature": "firma-que-no-verifica",
            }
        ),
        content_type="application/json",
        **{
            **_autorizacion(usuario_comprador),
            "HTTP_IDEMPOTENCY_KEY": "clave-de-idempotencia-e2e-0003",
        },
    )

    assert respuesta.status_code == 400
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "PAGO_FIRMA_INVALIDA"

    orden_pago.refresh_from_db()
    assert orden_pago.estado == EstadoOrdenPago.PENDIENTE


# ── RT-PG-02 · Notificación del proveedor ──────────────────────────────────


def test_la_notificacion_del_proveedor_confirma_el_pago(
    cliente, orden_pago, compra, intento, clave_comercio
):
    """GIVEN una notificación firmada del proveedor
    WHEN  llega por HTTP
    THEN  responde 200 con el veredicto y la orden queda confirmada.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    respuesta = cliente.post(
        "/api/pagos/izipay/notificacion",
        data=json.dumps({"payloadHttp": crudo, "signature": firmar(crudo, clave_comercio)}),
        content_type="application/json",
    )

    assert respuesta.status_code == 200
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["success"] is True
    assert (
        cuerpo["data"]["estado_operativo"]["codigo"] == EstadoOperativoPago.PAGADA
    )

    orden_pago.refresh_from_db()
    assert orden_pago.estado == EstadoOrdenPago.CONFIRMADA


def test_la_notificacion_sin_firma_es_400(cliente, orden_pago, compra, intento,
                                          clave_comercio):
    """GIVEN una notificación sin firma
    WHEN  llega por HTTP
    THEN  responde 400 PAGO_NOTIFICACION_NO_VERIFICABLE.
    """
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    respuesta = cliente.post(
        "/api/pagos/izipay/notificacion",
        data=json.dumps({"payloadHttp": crudo, "signature": ""}),
        content_type="application/json",
    )

    assert respuesta.status_code == 400
    cuerpo = json.loads(respuesta.content)
    assert cuerpo["error"]["code"] == "PAGO_NOTIFICACION_NO_VERIFICABLE"


def test_la_respuesta_no_expone_secretos_ni_trazas(
    cliente, orden_pago, compra, intento, usuario_comprador, clave_comercio
):
    """El envelope público no filtra claves, firmas ni trazas (FR-01 §4)."""
    payload = payload_confirmacion(transaction_id=intento.referencia_proveedor)
    crudo = payload_http(payload)

    respuesta = cliente.post(
        f"/api/pagos/ordenes/{orden_pago.id}/confirmar",
        data=json.dumps(
            {
                **payload,
                "payloadHttp": crudo,
                "signature": firmar(crudo, clave_comercio),
            }
        ),
        content_type="application/json",
        **{
            **_autorizacion(usuario_comprador),
            "HTTP_IDEMPOTENCY_KEY": "clave-de-idempotencia-e2e-0004",
        },
    )

    contenido = respuesta.content.decode("utf-8")
    assert respuesta.status_code == 200
    assert "Traceback" not in contenido
    assert clave_comercio not in contenido
    assert intento.referencia_proveedor not in contenido
