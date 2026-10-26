"""
Domain exceptions for pagos module.

Two families live here:

- `IzipayError` — provider/infrastructure failures (missing settings, network
  errors, provider rejections). They are NOT public errors: the generic
  handler turns them into a safe 500.
- The typed payment errors below — stable, machine-readable codes that the
  global handler translates into a safe public message and HTTP status.
  They never carry identifiers, provider payloads or secrets.
"""
from core.exceptions import ConflictError, ForbiddenError, NotFoundError


class IzipayError(Exception):
    """Base exception for Izipay module."""
    pass


class TransaccionDuplicadaError(IzipayError):
    """Raised when a duplicate transaction_id is detected."""
    pass


# ── Typed payment errors (stable public codes) ──────────────────────────────

class TransaccionPagoNoEncontradaError(NotFoundError):
    """The referenced transaction does not exist (404)."""

    code = "TRANSACCION_PAGO_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Transacción de pago", code=self.code)


class OrdenPagoNoEncontradaError(NotFoundError):
    """The referenced payment order does not exist (404)."""

    code = "ORDEN_PAGO_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(resource="Orden de pago", code=self.code)


class PagoNoAutorizadoError(ForbiddenError):
    """
    The caller is not allowed to operate on this payment (403).

    Raised when a browser relay does not come from the owner of the order
    and the caller has no administrative authority.
    """

    code = "PAGO_NO_AUTORIZADO"

    def __init__(self):
        super().__init__("No tiene autorización para realizar esta acción.")


class PagoDatosInconsistentesError(ConflictError):
    """
    The provider payload contradicts the persisted order (409).

    The amount or the order number delivered by the provider does not match
    what was recorded when the checkout was opened. Nothing is mutated.
    """

    code = "PAGO_DATOS_INCONSISTENTES"

    def __init__(self):
        super().__init__(
            "Los datos del pago no coinciden con la orden registrada.",
            code=self.code,
        )


class PagoFirmaInvalidaError(ConflictError):
    """
    The provider signature does not verify (409).

    Either the signature is wrong, or a successful payment arrived without a
    verifiable signature while the merchant key IS configured. Nothing is
    mutated.
    """

    code = "PAGO_FIRMA_INVALIDA"

    def __init__(self):
        super().__init__(
            "No se pudo verificar la firma del pago.",
            code=self.code,
        )


class PagoNotificacionNoVerificableError(ConflictError):
    """
    A provider notification cannot be verified (409).

    The server-to-server channel has no fallback: without the merchant key
    and a valid signature the notification is refused and nothing is
    mutated.
    """

    code = "PAGO_NOTIFICACION_NO_VERIFICABLE"

    def __init__(self):
        super().__init__(
            "La notificación del pago no pudo ser verificada.",
            code=self.code,
        )
