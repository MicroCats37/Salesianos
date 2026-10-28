"""
Result DTOs of the administrative cancellation of a pass purchase.

The wrapper is EXPLICIT: it carries the commercial state of the purchase, the
audit of the decision and the number of rights revoked. It never carries a
credential (the QR stays out of every payload) nor any provider internal.
"""

from pydantic import BaseModel


class AdminPaseCanceladaResult(BaseModel):
    """
    Outcome of the administrative cancellation of a pass purchase.

    It is NOT a monetary refund: no money is returned by this operation.
    """

    compra_id: str
    estado_compra: str
    estado_orden: str
    ya_cancelada: bool
    beneficiarios_revocados: int
    personas_afectadas: int
    motivo: str


__all__ = ["AdminPaseCanceladaResult"]
