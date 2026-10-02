"""
HTTP schemas for pagos module — Ninja/Schema request and response shapes.

These are the schemas the HTTP layer (presentation) uses.
Naming follows: *In for requests, *Out for responses.
"""
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


# ── Prepare output ─────────────────────────────────────────────────────────

class IzipayPrepareOut(BaseModel):
    """
    Output from prepare step — token + SDK configuration for Web Core 2.0 popup.

    Contains the data the frontend needs to call:
      checkout.LoadForm({ authorization: token, merchantCode, orderNumber,
                          amount, currency, transactionId })

    No secrets are included — token is the session token for the popup,
    not an API key.
    """
    transaction_id: str = Field(
        ...,
        description="14-digit unique transaction ID (idempotency key)"
    )
    order_number: str = Field(
        ...,
        description="10-digit order number"
    )
    token: str = Field(
        ...,
        description="Izipay Perú session token for the frontend SDK popup"
    )
    merchant_code: str = Field(
        ...,
        description="Izipay Perú merchant/shop code"
    )
    amount: Decimal = Field(
        ...,
        description="Snaphotted amount from paquete.precio_promocional | precio_regular"
    )
    currency: str = Field(
        default="PEN",
        description="ISO currency code"
    )
    buyer_email: str = Field(
        ...,
        description="Email passed to Izipay Perú"
    )
    buyer_name: str = Field(
        ...,
        description="First name passed to Izipay Perú (sanitized)"
    )
    buyer_surname: str = Field(
        ...,
        description="Last name passed to Izipay Perú (sanitized)"
    )


# ── Confirm ───────────────────────────────────────────────────────────────────

class IzipayConfirmIn(BaseModel):
    """
    Input for confirming an Izipay Perú payment.

    The frontend SDK sends kr_answer directly to this endpoint after the popup closes.
    This is NOT a server-to-server retrieval — Izipay Perú Web Core 2.0 uses
    a direct callback from the browser.

    kr_answer shape (per Izipay Perú docs):
      {
        "code": "00",
        "message": "Operación exitosa",
        "transactionId": "17370677285350",
        "response": {
          "payMethod": "CARD",
          "order": [{ "orderNumber": "...", "amount": "...", ... }]
        },
        "signature": "...",
        "payloadHttp": "..."
      }
    """
    kr_answer: dict = Field(
        ...,
        description="Izipay Perú callback payload (kr_answer) from frontend SDK"
    )


class IzipayConfirmOut(BaseModel):
    """Output from confirm step."""
    transaction_id: str = Field(..., description="Transaction ID")
    success: bool = Field(..., description="Whether the payment succeeded")
    status: str = Field(
        ...,
        description="IzipayTransaccion status: EXITO, FALLIDO, CANCELADO"
    )
    response_code: str | None = Field(
        None,
        description="Provider response code (code from kr_answer)"
    )
    response_message: str | None = Field(
        None,
        description="Provider response message"
    )
    metodo_pago: str | None = Field(
        None,
        description="Payment method used (e.g. CARD, YAPE, PLIN)"
    )
    already_confirmed: bool = Field(
        default=False,
        description="True if this transaction was already confirmed (idempotent hit)"
    )


# ── Transaction output ─────────────────────────────────────────────────────────

class IzipayTransaccionOut(BaseModel):
    """
    Output schema for an IzipayTransaccion record.

    Used for transaction detail / history endpoints (future phase).
    """
    id: str = Field(..., description="Transaction UUID")
    inscripcion_id: str = Field(..., description="Related inscription UUID")
    transaction_id: str = Field(..., description="14-digit idempotency key")
    order_number: str = Field(..., description="Order number")
    amount: Decimal = Field(..., description="Snaphotted amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Transaction status")
    response_code: str | None = Field(None, description="Provider response code")
    response_message: str | None = Field(
        None,
        description="Provider response message"
    )
    metodo_pago: str | None = Field(None, description="Payment method used")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
