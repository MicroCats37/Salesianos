"""
Internal DTOs of the manual approval of a payment.

They are NOT HTTP schemas: they carry exactly what the flow needs. The
presentation layer of the administration area maps them into the public
wrapper (`contract/django-app-architecture-contract.md` §4.6).
"""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    SettlementStatus,
)


class EstadoCompraOrdenPago(BaseModel):
    """
    State of the purchase that funds a payment order.

    The payment module never imports the commerce module: it asks for this
    tiny projection through a port. The commercial vocabulary belongs to
    `commerce`, so the port answers a QUESTION (`cancelada`) instead of
    repeating a state that the payment module would have to interpret.
    """

    existe: bool = Field(..., description="Whether a purchase funds the order.")
    estado: str | None = Field(
        None, description="Commercial state of the purchase (PENDIENTE/PAGADA/CANCELADA)."
    )
    cancelada: bool = Field(
        False, description="Whether the purchase was already cancelled."
    )


class AprobacionPagoManualData(BaseModel):
    """The evidence an administrator registers for a payment."""

    canal: str = Field(..., description="Closed channel of the payment.")
    referencia: str = Field(..., description="External reference of the payment.")
    monto: Decimal = Field(..., description="Approved amount.")
    moneda: str = Field(..., description="Currency of the approved amount.")
    motivo: str = Field(..., description="Why the payment is approved.")


class AprobarPagoManualResult(BaseModel):
    """
    Outcome of the manual approval of a payment order.

    `resultado` is `APROBADA` when this call registered the evidence and
    `YA_APROBADA` when the order already carried an active approval (the
    operation is idempotent and never duplicates rights).

    `settlement_status` is `SETTLED` when the commercial settlement of the
    purchase completed and `PENDING` when it did not: the evidence stays
    durable and a later retry converges it.
    """

    resultado: str = Field(..., description="APROBADA or YA_APROBADA.")
    settlement_status: str = Field(
        ...,
        description=f"{SettlementStatus.SETTLED} or {SettlementStatus.PENDING}.",
    )
    orden_pago_id: str = Field(..., description="Payment order identifier.")
    numero_orden: str = Field(..., description="Human readable order number.")
    estado_orden: str = Field(..., description="State of the payment order.")
    aprobacion_id: str = Field(..., description="Identifier of the approval.")
    estado_aprobacion: str = Field(
        ...,
        description=f"{EstadoAprobacionPagoManual.APROBADA} or "
        f"{EstadoAprobacionPagoManual.ANULADA}.",
    )
    canal: str = Field(..., description="Channel of the payment.")
    referencia: str = Field(..., description="External reference of the payment.")
    monto: Decimal = Field(..., description="Approved amount.")
    moneda: str = Field(..., description="Currency of the approved amount.")
    motivo: str = Field(..., description="Why the payment was approved.")
    actor: str = Field(..., description="Display name of the administrator.")
    approved_at: datetime = Field(..., description="When the approval was recorded.")


__all__ = [
    "AprobacionPagoManualData",
    "AprobarPagoManualResult",
    "EstadoCompraOrdenPago",
]
