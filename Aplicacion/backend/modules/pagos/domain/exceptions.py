"""Excepciones de dominio del módulo `pagos`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Reglas que se aplican a TODAS estas excepciones
(`contract/django-app-architecture-contract.md` §10,
`contract/api-wrapper-presenter-contract.md` §8):

- Declaran un `code` estable y legible por máquina.
- El TEXTO que construyen es técnico: **nunca** sale al cliente.
- El mensaje público lo decide el catálogo `core/exceptions.py` a partir del
  `code`. Un código que todavía no está catalogado devuelve la prosa genérica
  del status HTTP, nunca el texto crudo de la excepción.
- No interpolan UUIDs, ids internos, montos, SQL, rutas ni payloads del
  proveedor.

Los códigos que YA están en el catálogo público de A0:
`ORDEN_PAGO_NO_ENCONTRADA`, `TRANSACCION_PAGO_NO_ENCONTRADA`,
`PAGO_NO_AUTORIZADO`, `PAGO_FIRMA_INVALIDA`, `PAGO_NOTIFICACION_NO_VERIFICABLE`,
`PAGO_DATOS_INCONSISTENTES`, `MONTO_NO_COINCIDE`, `ORDEN_YA_PAGADA_CON_IZIPAY`,
`COMPRA_YA_CANCELADA`, `PAGO_NO_VERIFICADO`.

Los códigos que este paquete **solicita a A0** (aún no catalogados, ver la
evidencia del paquete FND-04): `IDEMPOTENCY_KEY_REUTILIZADA`,
`IDEMPOTENCY_KEY_INVALIDA`, `ORDEN_PAGO_NO_PAGABLE`. Hasta que A0 los añada, su
prosa pública es la genérica del status HTTP y el código sigue viajando en
`error.code` para diagnóstico.
"""

from core.exceptions import ConflictError, ForbiddenError, NotFoundError
from ninja.errors import HttpError


# ── Base 400 ────────────────────────────────────────────────────────────────


class ErrorPago400(HttpError):
    """Base de los errores de pago que responden 400.

    El status 400 es el del ledger congelado (`FR-07` §3.3) para
    `PAGO_FIRMA_INVALIDA` y `PAGO_NOTIFICACION_NO_VERIFICABLE`: la petición es
    malformada o no verificable, no un conflicto de negocio.
    """

    code = "PAGO_INVALIDO"

    def __init__(self, code: str | None = None, message: str = ""):
        self.code = code or self.code
        super().__init__(400, message)


# ── Errores tipados de pago ─────────────────────────────────────────────────


class OrdenPagoNoEncontradaError(NotFoundError):
    """La orden de pago referenciada no existe (404)."""

    code = "ORDEN_PAGO_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Orden de pago", code=self.code)


class TransaccionPagoNoEncontradaError(NotFoundError):
    """El intento de pago referenciado no existe (404)."""

    code = "TRANSACCION_PAGO_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Intento de pago", code=self.code)


class PagoNoAutorizadoError(ForbiddenError):
    """El actor no puede operar sobre este pago (403).

    Se lanza cuando un reenvío desde el navegador no viene del titular de la
    orden. El documento de identidad NO es una credencial (RN-U04): la
    titularidad se comprueba contra la persona compradora de la compra.
    """

    code = "PAGO_NO_AUTORIZADO"

    def __init__(self):
        super().__init__("No tiene autorización para realizar esta acción.")


class PagoFirmaInvalidaError(ErrorPago400):
    """La firma del proveedor no verifica (400).

    O la firma es incorrecta, o llegó un pago exitoso sin firma verificable
    mientras la clave del comercio SÍ está configurada. En ambos casos **no se
    muta ninguna fila**: la verificación ocurre antes de escribir.
    """

    code = "PAGO_FIRMA_INVALIDA"

    def __init__(self):
        super().__init__(
            code=self.code,
            message="No se pudo verificar la firma del pago.",
        )


class PagoNotificacionNoVerificableError(ErrorPago400):
    """La notificación del proveedor no puede verificarse (400).

    El canal servidor-a-servidor NO tiene fallback: sin clave del comercio y
    sin firma válida la notificación se rechaza y no se muta nada.
    """

    code = "PAGO_NOTIFICACION_NO_VERIFICABLE"

    def __init__(self):
        super().__init__(
            code=self.code,
            message="La notificación del pago no pudo ser verificada.",
        )


class PagoDatosInconsistentesError(ConflictError):
    """El payload del proveedor contradice la orden registrada (409).

    El monto o la referencia de la orden que entrega el proveedor no coinciden
    con lo que se guardó al abrir el checkout. Nada se muta.
    """

    code = "PAGO_DATOS_INCONSISTENTES"

    def __init__(self):
        super().__init__(
            "Los datos del pago no coinciden con la orden registrada.",
            code=self.code,
        )


class MontoNoCoincideError(ConflictError):
    """El monto o la moneda no coinciden exactamente con la orden (409).

    El monto de una orden es un **snapshot congelado**: ni el navegador ni el
    administrador pueden ajustarlo después.
    """

    code = "MONTO_NO_COINCIDE"

    def __init__(self):
        super().__init__(
            "El monto y la moneda no coinciden con la orden de pago.",
            code=self.code,
        )


class OrdenYaPagadaConIzipayError(ConflictError):
    """La orden ya fue pagada mediante el proveedor (409).

    Una confirmación repetida NO vuelve a cobrar ni a duplicar: la orden ya
    pagada es un hecho, y la segunda confirmación es idempotente.
    """

    code = "ORDEN_YA_PAGADA_CON_IZIPAY"

    def __init__(self):
        super().__init__(
            "La orden de pago ya fue pagada mediante el proveedor.",
            code=self.code,
        )


class OrdenPagoNoPagableError(ConflictError):
    """La orden no admite una confirmación de pago (409).

    Una orden `CANCELADA` o `VENCIDA` no puede confirmarse: el intento de pago
    corresponde a una obligación de pago que ya no está vigente. El código
    está REQUESTED a A0 (ver la evidencia del paquete FND-04).
    """

    code = "ORDEN_PAGO_NO_PAGABLE"

    def __init__(self):
        super().__init__(
            "La orden de pago no admite una confirmación en su estado actual.",
            code=self.code,
        )


class IdempotencyKeyReutilizadaError(ConflictError):
    """La misma clave de idempotencia llegó con un payload distinto (409).

    Una clave identifica **una intención**, no una sesión: reutilizarla para
    otra operación es un error del cliente, no una repetición tolerada. El
    código está REQUESTED a A0 (ver la evidencia del paquete FND-04).
    """

    code = "IDEMPOTENCY_KEY_REUTILIZADA"

    def __init__(self):
        super().__init__(
            "La clave de idempotencia ya se usó con una operación diferente.",
            code=self.code,
        )


class IdempotencyKeyInvalidaError(ConflictError):
    """La clave de idempotencia no cumple el contrato (409).

    Vacía, con longitud excesiva o con caracteres no admitidos. El código está
    REQUESTED a A0 (ver la evidencia del paquete FND-04).
    """

    code = "IDEMPOTENCY_KEY_INVALIDA"

    def __init__(self):
        super().__init__(
            "La clave de idempotencia no es válida.",
            code=self.code,
        )


class CompraYaCanceladaError(ConflictError):
    """La compra que financia la orden ya fue cancelada (409).

    Una compra cancelada no vuelve a pagarse: la aprobación resucitaría
    derechos comerciales ya revocados.
    """

    code = "COMPRA_YA_CANCELADA"

    def __init__(self):
        super().__init__(
            "La compra asociada ya se encuentra cancelada.",
            code=self.code,
        )


__all__ = [
    "CompraYaCanceladaError",
    "ErrorPago400",
    "IdempotencyKeyInvalidaError",
    "IdempotencyKeyReutilizadaError",
    "MontoNoCoincideError",
    "OrdenPagoNoEncontradaError",
    "OrdenPagoNoPagableError",
    "OrdenYaPagadaConIzipayError",
    "PagoDatosInconsistentesError",
    "PagoFirmaInvalidaError",
    "PagoNoAutorizadoError",
    "PagoNotificacionNoVerificableError",
    "TransaccionPagoNoEncontradaError",
]
