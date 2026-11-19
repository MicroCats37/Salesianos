"""Helpers de parseo de la capa HTTP del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.8 ·
          `contract/PLAN_REFACTORIZACION.md` §3.B (helpers)

Son funciones **puras** de utilidad: no tocan la base de datos, no construyen
respuestas y no conocen el dominio. Existen para que el controlador siga
siendo "sagrado": parsea la entrada, llama al orquestador y devuelve el
éxito formateado por el presenter.

Dos helpers:

- `construir_payload_proveedor` — normaliza el cuerpo de la confirmación en el
  diccionario que consume el flujo. Cuando el proveedor entrega el payload
  crudo firmado (`payloadHttp`), ese texto se **preserva byte a byte**: es lo
  que se verifica contra la clave del comercio.
- `extraer_notificacion` — extrae el par (payload crudo, firma) de la
  notificación servidor a servidor, venga en JSON o en formulario.
"""

import json


def construir_payload_proveedor(
    *,
    payload_http: str | None = None,
    transaction_id: str | None = None,
    code: str | None = None,
    message: str | None = None,
    order_number: str | None = None,
    amount: str | None = None,
    currency: str | None = None,
    signature: str | None = None,
    respuesta: dict | None = None,
) -> dict:
    """Normaliza el cuerpo de una confirmación en un diccionario de proveedor.

    El `payload_http` crudo se parsea (si es JSON válido) para no perder los
    campos que el proveedor anida, y sus valores se combinan con los campos
    tipados del cuerpo.

    Args:
        payload_http: el texto crudo y firmado del proveedor.
        transaction_id: identificador del intento.
        code: código de respuesta del proveedor.
        message: mensaje de respuesta del proveedor.
        order_number: referencia de orden del proveedor.
        amount: monto del proveedor.
        currency: moneda del proveedor.
        signature: la firma del proveedor sobre el payload crudo.
        respuesta: bloque `response` del proveedor.

    Returns:
        El diccionario de proveedor. Nunca contiene credenciales.
    """
    payload: dict = {}

    if payload_http:
        try:
            crudo = json.loads(payload_http)
        except (ValueError, TypeError):
            crudo = None
        if isinstance(crudo, dict):
            payload.update(crudo)

    if transaction_id:
        payload.setdefault("transactionId", transaction_id)
    if code:
        payload.setdefault("code", code)
    if message:
        payload.setdefault("message", message)
    if order_number:
        payload.setdefault("orderNumber", order_number)
    if amount:
        payload.setdefault("amount", amount)
    if currency:
        payload.setdefault("currency", currency)
    if respuesta:
        payload.setdefault("response", respuesta)

    # El payload crudo y su firma viajan al flujo: son lo que se verifica
    # contra la clave del comercio. El saneado los elimina antes de
    # persistirlos (`sanitizar_payload_proveedor`).
    if payload_http:
        payload["payloadHttp"] = payload_http
    if signature:
        payload["signature"] = signature

    return payload


def extraer_notificacion(request) -> tuple[str, str]:
    """Extrae el par (payload crudo, firma) de la notificación del proveedor.

    Acepta el cuerpo en JSON (`{"payloadHttp": ..., "signature": ...}`) y en
    formulario (`payloadHttp=...&signature=...`).

    Args:
        request: la petición HTTP.

    Returns:
        La tupla `(payload_http, signature)`. Si falta alguna parte, la
        cadena vacía.
    """
    payload_http = ""
    signature = ""

    post = getattr(request, "POST", None)
    if post:
        payload_http = str(post.get("payloadHttp") or post.get("payload_http") or "")
        signature = str(post.get("signature") or "")

    if not payload_http:
        cuerpo = _cuerpo_texto(request)
        if cuerpo:
            try:
                datos = json.loads(cuerpo)
            except (ValueError, TypeError):
                datos = None
            if isinstance(datos, dict):
                payload_http = str(
                    datos.get("payloadHttp") or datos.get("payload_http") or ""
                )
                if not signature:
                    signature = str(datos.get("signature") or "")

    return payload_http.strip(), signature.strip()


def _cuerpo_texto(request) -> str:
    """El cuerpo crudo de la petición, decodificado como texto."""
    try:
        cuerpo = request.body
    except Exception:  # pragma: no cover - depende del cliente de prueba
        return ""
    if not cuerpo:
        return ""
    if isinstance(cuerpo, bytes):
        try:
            return cuerpo.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    return str(cuerpo)


__all__ = ["construir_payload_proveedor", "extraer_notificacion"]
