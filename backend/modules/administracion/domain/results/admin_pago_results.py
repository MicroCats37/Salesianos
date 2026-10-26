"""
Result DTOs of the payments (A5, A6).

The payment surface is deliberately EXPLICIT: every field is named, and the
restricted blobs of the payment module are never carried:

- `OrdenPago.metadata` — a restricted JSON blob
  (`METADATA_ALLOWED_KEYS` / `METADATA_FORBIDDEN_KEYS`): NEVER exposed,
- `TransaccionPago.metadata` — NEVER exposed,
- `TransaccionPago.token_sesion` — NEVER exposed,
- `TransaccionPago.response_message` — the raw provider message: NEVER exposed,
- `TransaccionPago.transaction_id` — a sensitive provider identifier: NEVER
  exposed.

The admin reads the FROZEN commercial snapshot of the purchase
(`CompraInscripcion.cantidad`, `precio_unitario`, `total`), never a computed
price.
"""

from datetime import datetime

from pydantic import BaseModel


class AdminPagoListItemResult(BaseModel):
    """A purchase line with its payment order."""

    compra_id: str
    orden_pago_id: str | None = None
    numero_orden: str | None = None
    inscripcion_id: str
    responsable_nombre: str
    tipo: str
    cantidad: int
    precio_unitario: float
    total: float
    estado_compra: str
    estado_orden: str | None = None
    pagada_en: datetime | None = None
    created_at: datetime


class AdminTransaccionListItemResult(BaseModel):
    """A payment attempt — explicit fields only, no provider internals."""

    id: str
    status: str
    amount: float
    currency: str
    metodo_pago: str | None = None
    response_code: str | None = None
    created_at: datetime


class AdminPagoDetalleResult(AdminPagoListItemResult):
    """The drilldown of a payment order (A6)."""

    transacciones: list[AdminTransaccionListItemResult] = []


__all__ = [
    "AdminPagoListItemResult",
    "AdminTransaccionListItemResult",
    "AdminPagoDetalleResult",
]
