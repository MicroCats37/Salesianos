"""
HTTP wrappers of the payments (A5, A6).

The wrapper is EXPLICIT field by field: the restricted blobs of the payment
module (`metadata`, `token_sesion`, `response_message`, `transaction_id`)
have NO place in it — they are not even declared, so they can never be
serialized by accident.
"""
from datetime import datetime
from typing import Optional

from core.types import BaseSchema


class AdminTransaccionListItemOut(BaseSchema):
    """A payment attempt — explicit fields only, no provider internals."""

    id: str
    status: str
    amount: float
    currency: str
    metodo_pago: Optional[str] = None
    response_code: Optional[str] = None
    created_at: datetime


class AdminPagoListItemOut(BaseSchema):
    """A purchase line with its payment order."""

    compra_id: str
    orden_pago_id: Optional[str] = None
    numero_orden: Optional[str] = None
    inscripcion_id: str
    responsable_nombre: str
    tipo: str
    cantidad: int
    precio_unitario: float
    total: float
    estado_compra: str
    estado_orden: Optional[str] = None
    pagada_en: Optional[datetime] = None
    created_at: datetime


class AdminPagoDetailOut(AdminPagoListItemOut):
    """The drilldown of a payment order (A6)."""

    transacciones: list[AdminTransaccionListItemOut] = []


__all__ = [
    "AdminTransaccionListItemOut",
    "AdminPagoListItemOut",
    "AdminPagoDetailOut",
]
