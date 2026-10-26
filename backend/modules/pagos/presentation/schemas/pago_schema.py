"""
HTTP schemas for pagos module — Ninja/Schema request and response shapes.

These are the schemas the HTTP layer (presentation) uses.
Naming follows: *In for requests, *Out for responses.
"""
from decimal import Decimal
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from modules.pagos.domain.constants import SettlementStatus


def _a_texto(valor: Any) -> Any:
    """The provider may send numbers; the contract of this API is text."""
    if valor is None or isinstance(valor, str):
        return valor
    if isinstance(valor, (dict, list)):
        return None
    return str(valor)


# A provider value that the contract declares as text.
TextoOpcional = Annotated[str | None, BeforeValidator(_a_texto)]


# ── OrdenPago ───────────────────────────────────────────────────────────────

class OrdenPagoOut(BaseModel):
    """Output schema for an OrdenPago record."""
    id: str = Field(..., description="OrdenPago UUID")
    numero: str = Field(..., description="Human-readable order number")
    monto_total: Decimal = Field(..., description="Total amount")
    moneda: str = Field(..., description="Currency code")
    estado: str = Field(..., description="Order status")
    pagada_en: str | None = Field(None, description="Payment timestamp")
    expires_at: str | None = Field(None, description="Expiration timestamp")
    descripcion: str = Field(..., description="Order description snapshot")
    referencia_externa: str | None = Field(None, description="Business reference snapshot")
    created_at: str = Field(..., description="Creation timestamp")


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
        description="Total amount from OrdenPago"
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

class IzipayOrdenDetalleIn(BaseModel):
    """One order entry of the provider payload."""

    model_config = ConfigDict(extra="allow")

    orderNumber: TextoOpcional = Field(None, description="Provider order number")
    amount: TextoOpcional = Field(None, description="Amount of the order")
    currency: TextoOpcional = Field(None, description="Currency of the order")


class IzipayRespuestaIn(BaseModel):
    """The `response` bag of the provider payload."""

    model_config = ConfigDict(extra="allow")

    payMethod: TextoOpcional = Field(None, description="Payment method used")
    paymentMethodType: TextoOpcional = Field(
        None, description="Alternative name of the payment method"
    )
    transactionId: TextoOpcional = Field(
        None, description="Transaction id reported inside the response bag"
    )
    order: list[IzipayOrdenDetalleIn] = Field(
        default_factory=list, description="Orders covered by the transaction"
    )

    @field_validator("order", mode="before")
    @classmethod
    def _ordenes_lista(cls, valor: Any) -> Any:
        """A provider that does not send a list must not break the relay."""
        if valor is None:
            return []
        if isinstance(valor, list):
            return valor
        return []


class IzipayCallbackIn(BaseModel):
    """
    The provider payload delivered by the Izipay Perú frontend SDK.

    Shape (per Izipay Perú docs):
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

    Unknown fields are preserved: the provider owns the shape of its own
    payload and we keep every value it sends for the audit metadata.
    """

    model_config = ConfigDict(extra="allow")

    code: Annotated[str, BeforeValidator(_a_texto)] = Field(
        "", description="Provider response code ('00' = approved)"
    )
    message: TextoOpcional = Field(None, description="Provider response message")
    transactionId: TextoOpcional = Field(
        None, description="Provider transaction id"
    )
    orderNumber: TextoOpcional = Field(None, description="Provider order number")
    amount: TextoOpcional = Field(None, description="Provider amount")
    signature: TextoOpcional = Field(
        None, description="HMAC-SHA256 signature of payloadHttp (Base64)"
    )
    payloadHttp: TextoOpcional = Field(
        None, description="Raw signed payload of the provider"
    )
    response: IzipayRespuestaIn | None = Field(
        None, description="Provider response bag"
    )

    @field_validator("response", mode="before")
    @classmethod
    def _respuesta_mapa(cls, valor: Any) -> Any:
        """A provider that does not send a bag must not break the relay."""
        if valor is None or isinstance(valor, dict):
            return valor
        return None


class IzipayConfirmIn(BaseModel):
    """
    Input for confirming an Izipay Perú payment.

    The frontend SDK relays the provider payload to this endpoint after the
    popup closes. The endpoint requires an authenticated caller that owns the
    order, and cross-checks the payload against the persisted transaction.
    """
    kr_answer: IzipayCallbackIn = Field(
        ...,
        description="Izipay Perú callback payload (kr_answer) from frontend SDK"
    )


class IzipayNotificacionIn(BaseModel):
    """
    Input of the server-to-server provider notification.

    Izipay Perú posts the raw signed payload (`payloadHttp`) together with
    its Base64 `signature`. The notification is refused unless the merchant
    key is configured and the signature verifies.
    """

    model_config = ConfigDict(extra="allow")

    payloadHttp: Annotated[str, BeforeValidator(_a_texto)] = Field(
        ...,
        description="Raw signed payload of the provider (exact bytes)",
        min_length=1,
    )
    signature: Annotated[str, BeforeValidator(_a_texto)] = Field(
        ...,
        description="HMAC-SHA256 signature of payloadHttp (Base64)",
        min_length=1,
    )
    transactionId: TextoOpcional = Field(
        None, description="Transaction id delivered next to the payload"
    )


class IzipayConfirmOut(BaseModel):
    """Output from confirm step."""
    transaction_id: str = Field(..., description="Transaction ID")
    success: bool = Field(..., description="Whether the payment succeeded")
    status: str = Field(
        ...,
        description="TransaccionPago status: EXITO, FALLIDO, CANCELADO"
    )
    orden_pago_id: str | None = Field(
        None,
        description="OrdenPago UUID (available after successful payment)"
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
    settlement_status: str = Field(
        default=SettlementStatus.NOT_APPLICABLE,
        description=(
            "Commercial settlement state of the paid order: "
            "SETTLED (purchase paid and rights allocated), "
            "PENDING (payment recorded, activation pending) or "
            "NOT_APPLICABLE (there was no settlement to perform)"
        ),
    )


# ── Transaccion output ─────────────────────────────────────────────────────────

class TransaccionPagoOut(BaseModel):
    """
    Output schema for a TransaccionPago record.

    Used for transaction detail / history endpoints.
    """
    id: str = Field(..., description="Transaction UUID")
    orden_pago_id: str = Field(..., description="Related OrdenPago UUID")
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
