"""Infraestructura del módulo `pagos` — la frontera con el proveedor de pago.

Contract: `contract/django-app-architecture-contract.md` §4.10

Este módulo contiene:

- `ProveedorPagoIzipayAdapter` — la implementación de
  `IProveedorPagoService`: verifica la firma del proveedor **en servidor**
  con la clave del comercio (HMAC-SHA256, Base64).
- `sanitizar_payload_proveedor` — el saneado del payload del proveedor antes
  de guardarlo: ninguna credencial, ningún token de sesión, ningún dato de
  tarjeta llega a la base de datos.

Dos prohibiciones del contrato se respetan aquí de forma estricta:

1. **La clave del comercio es un SECRETO.** Se lee de los settings, nunca sale
   del servidor y nunca se escribe en un log, en una respuesta HTTP ni en una
   excepción.
2. **El payload firmado no se persiste ni se registra.** Sólo sobrevive su
   forma saneada: los hechos que el operador necesita para auditar.
"""

import base64
import hashlib
import hmac
import logging

from django.conf import settings

from modules.pagos.domain.ports import IProveedorPagoService

logger = logging.getLogger(__name__)


# ── Saneado del payload del proveedor ──────────────────────────────────────

#: Campos que NUNCA deben persistirse ni registrarse.
#:
#: Incluyen datos de tarjeta, claves y tokens de sesión/autenticación del
#: proveedor, y los payloads crudos completos.
_CAMPOS_SENSIBLES = frozenset(
    {
        # Datos de tarjeta
        "pan",
        "cardnumber",
        "card_number",
        "cvv",
        "cvc",
        "cvv2",
        "cardholdername",
        "card_holder_name",
        "cardtoken",
        "card_token",
        "cardalias",
        "card_association",
        # Claves y tokens de sesión/autenticación
        "privatekey",
        "private_key",
        "secretkey",
        "secret_key",
        "apikey",
        "api_key",
        "encryptionkey",
        "encryption_key",
        "tokenizationkey",
        "izipaykey",
        "izipay_key",
        "shopid",
        "shop_id",
        "sessiontoken",
        "session_token",
        "authtoken",
        "auth_token",
        "accesstoken",
        "access_token",
        "idtoken",
        "id_token",
        # Material de 3-D Secure
        "eci",
        "xid",
        "cavv",
        "cavvalgorithm",
        # La firma y el payload firmado
        "signature",
        "firma",
        "payloadhttp",
        "payload_http",
        "keyhash",
        "key_hash",
        # Payloads crudos
        "raw_request",
        "raw_response",
        "raw",
        "full_card_data",
    }
)


def _es_clave_segura(clave: str) -> bool:
    """Si la clave del payload no parece un campo sensible."""
    minuscula = str(clave).lower()
    return not any(sensible in minuscula for sensible in _CAMPOS_SENSIBLES)


def sanitizar_payload_proveedor(payload) -> dict:
    """Sanea el payload del proveedor antes de guardarlo.

    Elimina recursivamente los campos sensibles (datos de tarjeta, claves,
    tokens de sesión, la firma y el payload firmado) conservando el resto.

    Nunca lanza: si el payload no es un diccionario devuelve `{}`.

    Args:
        payload: el payload crudo que entregó el proveedor.

    Returns:
        Una copia saneada, apta para persistir.
    """
    if not isinstance(payload, dict):
        return {}

    def _saneado(valor):
        if isinstance(valor, dict):
            return {
                clave: _saneado(contenido)
                for clave, contenido in valor.items()
                if _es_clave_segura(clave)
            }
        if isinstance(valor, list):
            return [_saneado(item) for item in valor]
        return valor

    return _saneado(payload)


# ── Verificación de la firma del proveedor ─────────────────────────────────


class ProveedorPagoIzipayAdapter(IProveedorPagoService):
    """Verifica la firma del proveedor con la clave del comercio.

    El proveedor firma el payload **crudo** con la clave del comercio
    (HMAC-SHA256, codificado en Base64). La firma viaja junto al payload, tanto
    en el reenvío del navegador como en la notificación servidor-a-servidor.

    La clave se lee de los settings **en cada acceso**: el grafo de
    dependencias se construye una vez, así que la clave nunca queda capturada
    en una instancia obsoleta, y jamás se escribe en un log.

    Sin clave configurada la verificación NO está disponible: no existe un
    fallback que convierta un payload no verificable en verificado. La
    notificación servidor-a-servidor falla cerrada.
    """

    @property
    def key_hash(self) -> str:
        """La clave del comercio. Vacía si no está configurada."""
        return getattr(settings, "IZIPAY_KEY_HASH", "") or ""

    @property
    def disponible(self) -> bool:
        """Si el proveedor puede autenticarse."""
        return bool(self.key_hash)

    def calcular_firma(self, payload_http: str) -> str:
        """Calcula la firma esperada sobre el payload crudo.

        El payload debe ser el texto EXACTO recibido: re-serializar el JSON
        cambia los bytes y rompe la firma.
        """
        resumen = hmac.new(
            self.key_hash.encode("utf-8"),
            payload_http.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(resumen).decode("ascii")

    def verificar_firma(self, payload_http: str, signature: str) -> bool:
        """Compara la firma recibida con la esperada.

        La comparación es de **tiempo constante** para no filtrar información
        sobre la firma esperada.

        Returns:
            `True` sólo si la firma verifica. Sin clave configurada el
            resultado es siempre `False`.
        """
        if not self.disponible or not payload_http or not signature:
            return False
        esperado = self.calcular_firma(payload_http)
        return hmac.compare_digest(
            esperado.encode("utf-8"),
            str(signature).encode("utf-8"),
        )


__all__ = [
    "ProveedorPagoIzipayAdapter",
    "sanitizar_payload_proveedor",
]
