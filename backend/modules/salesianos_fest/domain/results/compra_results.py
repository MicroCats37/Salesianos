"""
Result DTOs for Compra operations — returned by services to orchestrators.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class CompraCreatedResult:
    """Result of creating a Compra and its OrdenPago."""
    compra_id: str
    compra_inscripcion_id: str
    orden_pago_id: str
    tipo: str
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    estado: str


@dataclass
class CompraIzipayPreparedResult:
    """Result of preparing Izipay payment for a Compra."""
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


@dataclass
class CompraConfirmedResult:
    """Result of confirming a Compra payment."""
    compra_id: str
    success: bool
    already_confirmed: bool
    transaction_id: str | None = None


@dataclass
class CompraCanceladaResult:
    """Result of cancelling a Compra (refund / abandoned payment)."""

    compra_id: str
    inscripcion_id: str
    estado: str
    ya_cancelada: bool
    asignaciones_revocadas: int
    personas_afectadas: int
