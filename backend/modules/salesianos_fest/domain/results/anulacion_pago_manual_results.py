"""
Result DTOs of the audited annulment of a manual payment approval.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class AnularPagoManualResult(BaseModel):
    """
    Outcome of the administrative annulment of a manual payment approval.

    `resultado` is `ANULADA` when this call revoked the evidence and
    `YA_ANULADA` when the approval was already annulled (the operation is
    idempotent: repeating it never revokes anything twice).

    The annulment is NOT a monetary refund: it revokes the commercial rights
    that the approval funded and keeps the audit trail forever.
    """

    resultado: str = Field(..., description="ANULADA or YA_ANULADA.")
    orden_pago_id: str = Field(..., description="Payment order identifier.")
    compra_id: str = Field(..., description="Purchase identifier.")
    estado_compra: str = Field(..., description="Commercial state of the purchase.")
    estado_orden: str = Field(..., description="State of the payment order.")
    estado_aprobacion: str = Field(..., description="State of the approval.")
    asignaciones_revocadas: int = Field(
        ..., description="Sports rights revoked by this annulment."
    )
    beneficiarios_revocados: int = Field(
        ...,
        description="Pass rights revoked by this annulment (reported apart).",
    )
    personas_afectadas: int = Field(
        ..., description="People whose access was recalculated."
    )
    anulada_por: str = Field(..., description="Display name of the administrator.")
    anulada_en: datetime = Field(..., description="When the annulment happened.")
    motivo_anulacion: str = Field(..., description="Why the approval was annulled.")


__all__ = ["AnularPagoManualResult"]
