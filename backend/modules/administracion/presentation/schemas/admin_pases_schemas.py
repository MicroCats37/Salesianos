"""
HTTP wrappers of the administrative cancellation of a pass purchase.

The motive is MANDATORY: a cancellation revokes nominative rights already
delivered, so the decision is always audited. The wrapper never carries the
QR credential nor any provider internal.
"""

from pydantic import Field

from core.types import BaseSchema


class AdminPaseCancelarIn(BaseSchema):
    """The audited motive of the administrative cancellation."""

    motivo: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Motivo de la cancelación (obligatorio, queda auditado).",
    )


class AdminPaseCanceladaOut(BaseSchema):
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


__all__ = ["AdminPaseCancelarIn", "AdminPaseCanceladaOut"]
