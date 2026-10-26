"""
Internal DTOs for Compra domain operations.
"""
from decimal import Decimal
from pydantic import BaseModel


class CompraCreateData(BaseModel):
    """Data needed to create a Compra."""
    inscripcion_id: str
    tipo: str  # TipoCompraChoices
    cantidad: int


class CompraResult(BaseModel):
    """Result of a Compra operation."""
    compra_id: str
    inscripcion_id: str
    orden_pago_id: str
    tipo: str
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    estado: str


class CompraPrepareResult(BaseModel):
    """Result of initiating payment for a Compra."""
    compra_id: str
    orden_pago_id: str
    transaction_id: str
    order_number: str
    token: str
    merchant_code: str
    amount: Decimal
    currency: str
    buyer_email: str
    buyer_name: str
    buyer_surname: str


class CompraConfirmResult(BaseModel):
    """Result of confirming a Compra payment."""
    compra_id: str
    success: bool
    already_confirmed: bool
