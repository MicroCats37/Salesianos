"""
Domain result DTOs for pagos module.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class IzipayPrepareResult:
    """Result of preparing an Izipay Perú payment session (token generation)."""
    transaction_id: str
    order_number: str
    amount: Decimal
    currency: str
    inscripcion_id: str
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
    response_code: str | None
    response_message: str | None
    metodo_pago: str | None
    already_confirmed: bool = False
