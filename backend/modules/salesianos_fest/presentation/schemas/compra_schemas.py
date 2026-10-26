"""
HTTP schemas for Compra — Ninja/Schema request and response shapes.

Now operates on commerce.Compra + CompraInscripcion composition.
"""
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Create ─────────────────────────────────────────────────────────────────

class CompraCreateIn(BaseModel):
    """Input for creating a Compra."""
    inscripcion_id: str = Field(..., description="UUID of the Inscripcion")
    tipo: str = Field(..., description="INICIAL or AMPLIACION")
    cantidad: int = Field(..., gt=0, description="Number of cupos to purchase")


class CompraCreateOut(BaseModel):
    """Output from creating a Compra."""
    compra_id: str = Field(..., description="UUID of the created commerce.Compra")
    compra_inscripcion_id: str = Field(..., description="UUID of the CompraInscripcion")
    orden_pago_id: str = Field(..., description="UUID of the associated OrdenPago")
    tipo: str = Field(..., description="INICIAL or AMPLIACION")
    cantidad: int = Field(..., description="Number of cupos purchased")
    precio_unitario: Decimal = Field(..., description="Frozen unit price")
    total: Decimal = Field(..., description="Frozen total amount")
    estado: str = Field(..., description="Initial state (PENDIENTE)")
    message: str = Field(..., description="Success message")


# ── Detail ──────────────────────────────────────────────────────────────────

class CompraDetailOut(BaseModel):
    """Output for Compra detail."""
    id: str = Field(..., description="Compra UUID")
    inscripcion_id: str = Field(..., description="Inscripcion UUID")
    orden_pago_id: str = Field(..., description="OrdenPago UUID")
    tipo: str = Field(..., description="INICIAL or AMPLIACION")
    cantidad: int = Field(..., description="Number of cupos")
    precio_unitario: Decimal = Field(..., description="Frozen unit price")
    total: Decimal = Field(..., description="Frozen total")
    estado: str = Field(..., description="Commercial state")
    created_at: str = Field(..., description="Creation timestamp")


class CompraListOut(BaseModel):
    """Output for listing Compras."""
    compras: list[CompraDetailOut] = Field(..., description="List of compras")


# ── Iniciar pago ─────────────────────────────────────────────────────────────

class IniciarPagoOut(BaseModel):
    """Output from initiating Izipay payment for a Compra."""
    compra_id: str = Field(..., description="commerce.Compra UUID")
    orden_pago_id: str = Field(..., description="OrdenPago UUID")
    transaction_id: str = Field(..., description="14-digit transaction ID")
    order_number: str = Field(..., description="10-digit order number")
    token: str = Field(..., description="Izipay session token for SDK")
    merchant_code: str = Field(..., description="Izipay merchant code")
    amount: Decimal = Field(..., description="Total amount")
    currency: str = Field(..., description="Currency code")
    buyer_email: str = Field(..., description="Buyer email")
    buyer_name: str = Field(..., description="Buyer first name")
    buyer_surname: str = Field(..., description="Buyer last name")


# ── Confirmar pago ────────────────────────────────────────────────────────────

class ConfirmarPagoOut(BaseModel):
    """Output from confirming a Compra payment."""
    compra_id: str = Field(..., description="commerce.Compra UUID")
    success: bool = Field(..., description="Whether confirmation succeeded")
    already_confirmed: bool = Field(..., description="Whether it was already confirmed")


# ── Cancelar compra ──────────────────────────────────────────────────────────

class CompraCanceladaOut(BaseModel):
    """Output from cancelling a Compra (refund)."""
    compra_id: str = Field(..., description="commerce.Compra UUID")
    inscripcion_id: str = Field(..., description="Inscripcion UUID")
    estado: str = Field(..., description="Commercial state after cancellation")
    ya_cancelada: bool = Field(..., description="Whether it was already cancelled")
    asignaciones_revocadas: int = Field(
        ..., description="Number of paid rights revoked by this cancellation"
    )
    personas_afectadas: int = Field(
        ..., description="Number of people whose access was recalculated"
    )
