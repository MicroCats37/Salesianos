"""
Domain result DTOs for pagos module.
"""
from dataclasses import dataclass
from decimal import Decimal

from modules.pagos.domain.constants import SettlementStatus


@dataclass
class SettlementResult:
    """
    Outcome of a commercial settlement attempt for a paid order.

    `settled=False` means the provider found nothing to settle (e.g. no
    purchase is linked to the order). `already_settled=True` means the
    purchase was already paid before this call — the settlement is idempotent.
    """
    settled: bool
    already_settled: bool = False


@dataclass
class OrdenPagoCreateResult:
    """Result of creating an OrdenPago."""
    orden_pago_id: str
    numero: str
    monto_total: Decimal
    currency: str
    expires_at: str


@dataclass
class IzipayPrepareResult:
    """Result of preparing an Izipay Perú payment session (token generation)."""
    transaction_id: str
    order_number: str
    amount: Decimal
    currency: str
    orden_pago_id: str
    token: str
    merchant_code: str
    buyer_email: str
    buyer_name: str
    buyer_surname: str


@dataclass
class IzipayConfirmResult:
    """Result of confirming an Izipay Perú payment from kr_answer callback."""
    transaction_id: str
    success: bool
    status: str
    orden_pago_id: str | None
    response_code: str | None
    response_message: str | None
    metodo_pago: str | None
    already_confirmed: bool = False
    settlement_status: str = SettlementStatus.NOT_APPLICABLE
