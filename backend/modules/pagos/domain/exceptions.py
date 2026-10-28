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


# ── Aprobación manual de pago (administrador) ──────────────────────────────

class PagoNoVerificadoError(ConflictError):
    """
    The order carries NO verifiable payment evidence (409).

    The commercial settlement only turns a purchase into `PAGADA` when the
    order proves it was paid: a correlated successful provider transaction or
    an active manual approval. Without that evidence nothing is settled and
    no right is granted.
    """

    code = "PAGO_NO_VERIFICADO"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "El pago no cuenta con evidencia verificable.",
            code=self.code,
        )


class MontoNoCoincideError(ConflictError):
    """
    The approved amount or currency does not match the order (409).

    The approval is a FROZEN snapshot of what was proved: an administrator
    can never adjust the amount of an order. Nothing is mutated.
    """

    code = "MONTO_NO_COINCIDE"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "El monto y la moneda no coinciden con la orden de pago.",
            code=self.code,
        )


class OrdenYaPagadaConIzipayError(ConflictError):
    """
    The order was already paid through the provider (409).

    A manual approval NEVER replaces a provider payment: it would create a
    second, contradictory evidence of the same order.
    """

    code = "ORDEN_YA_PAGADA_CON_IZIPAY"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "La orden de pago ya fue pagada mediante el proveedor.",
            code=self.code,
        )


class CompraYaCanceladaError(ConflictError):
    """
    The purchase that funds the order was already cancelled (409).

    A cancelled purchase never becomes paid again: the approval would
    resurrect commercial rights that were already revoked.
    """

    code = "COMPRA_YA_CANCELADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "La compra asociada ya se encuentra cancelada.",
            code=self.code,
        )


class AprobacionPagoManualDeshabilitadaError(ConflictError):
    """
    The manual approval of payments is disabled in this environment (409).

    The capability is rolled out behind a setting: the model and the audit
    can be deployed first and the action enabled later.
    """

    code = "PAGO_MANUAL_APROBACION_DESHABILITADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            "La aprobación manual de pagos no está habilitada.",
            code=self.code,
        )


class AprobacionPagoManualNoEncontradaError(NotFoundError):
    """
    The order carries no manual approval to annul (404).

    Only an ACTIVE approval can be annulled: the annulled ones are kept as
    the audit trail of the decision.
    """

    code = "APROBACION_PAGO_MANUAL_NO_ENCONTRADA"

    def __init__(self):
        self.code = self.code
        super().__init__(
            resource="Aprobación de pago manual",
            code=self.code,
        )
