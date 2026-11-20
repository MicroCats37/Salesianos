"""Contratos HTTP del checkout Izipay de pedidos invitados."""

from decimal import Decimal

from ninja import Schema
from pydantic import AliasChoices, Field


class MarketplaceIzipayPrepareOut(Schema):
    transaction_id: str
    order_number: str
    token: str
    merchant_code: str
    amount: Decimal
    currency: str
    buyer_email: str
    buyer_name: str
    buyer_surname: str


class MarketplaceIzipayConfirmIn(Schema):
    transaction_id: str | None = Field(
        default=None, validation_alias=AliasChoices("transaction_id", "transactionId")
    )
    code: str | None = None
    message: str | None = None
    order_number: str | None = Field(
        default=None, validation_alias=AliasChoices("order_number", "orderNumber")
    )
    amount: str | None = None
    currency: str | None = None
    signature: str | None = None
    payload_http: str | None = Field(
        default=None, validation_alias=AliasChoices("payload_http", "payloadHttp")
    )
    response: dict | None = None


class MarketplaceTransaccionOut(Schema):
    transaction_id: str
    status: str
    response_message: str


__all__ = [
    "MarketplaceIzipayConfirmIn",
    "MarketplaceIzipayPrepareOut",
    "MarketplaceTransaccionOut",
]
