"""
HTTP wrappers of the payments (A5, A6) and of the manual approval of a payment.

The wrapper is EXPLICIT field by field: the restricted blobs of the payment
module (`metadata`, `token_sesion`, `response_message`, `transaction_id`)
have NO place in it — they are not even declared, so they can never be
serialized by accident.
"""
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import Field

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
    """A purchase line with its payment order.

    ONE row is ONE purchase with exactly ONE supported composition: a sports
    registration (`inscripcion_id`) OR a pass batch (`pase_id`). The two
    identities are never both present.
    """

    compra_id: str
    orden_pago_id: Optional[str] = None
    numero_orden: Optional[str] = None
    inscripcion_id: Optional[str] = None
    pase_id: Optional[str] = None
    responsable_nombre: str
    tipo: str
    producto_nombre: str
    cantidad: int
    precio_unitario: float
    total: float
    estado_compra: str
    estado_orden: Optional[str] = None
    pagada_en: Optional[datetime] = None
    origen_pago: str = "SIN_PAGO"
    monto_orden: Optional[float] = None
    moneda_orden: Optional[str] = None
    beneficiarios_activos: int = 0
    beneficiarios_revocados: int = 0
    created_at: datetime


class AdminAprobacionManualOut(BaseSchema):
    """One entry of the manual approval history of an order."""

    id: str
    estado: str
    canal: str
    referencia: str
    monto: float
    moneda: str
    motivo: str
    actor: str
    anulada_por: Optional[str] = None
    anulada_en: Optional[datetime] = None
    motivo_anulacion: Optional[str] = None
    created_at: datetime


class AdminPaseBeneficiarioOut(BaseSchema):
    """
    One nominative right of a pass purchase.

    Only the SLOT, the state and the internal identifier of the holder
    travel: no names, no documents and never the QR credential.
    """

    persona_id: str
    slot: int
    estado: str


class AdminPagoDetailOut(AdminPagoListItemOut):
    """The drilldown of a payment order (A6)."""

    transacciones: list[AdminTransaccionListItemOut] = []
    aprobaciones: list[AdminAprobacionManualOut] = []
    beneficiarios: list[AdminPaseBeneficiarioOut] = []


# ── Aprobación manual ───────────────────────────────────────────────────────

class AdminPagoAprobarManualIn(BaseSchema):
    """
    The evidence an administrator registers for a payment received outside
    the payment provider.

    The channel is a CLOSED set and the reference and the motive are
    mandatory: an approval without evidence is not an approval.
    """

    canal: Literal[
        "TRANSFERENCIA_BANCARIA",
        "EFECTIVO",
        "YAPE",
        "PLIN",
        "OTRO",
    ] = Field(
        ...,
        description=(
            "Canal del pago: TRANSFERENCIA_BANCARIA, EFECTIVO, YAPE, PLIN u OTRO."
        ),
    )
    referencia: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Referencia externa del pago.",
    )
    monto: Decimal = Field(
        ...,
        gt=0,
        description="Monto aprobado; debe coincidir exactamente con la orden.",
    )
    moneda: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Moneda del pago; debe coincidir exactamente con la orden.",
    )
    motivo: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Motivo de la aprobación.",
    )


class AdminPagoAnularManualIn(BaseSchema):
    """The audited reason of the administrative annulment."""

    motivo: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Motivo de la anulación.",
    )


class AdminPagoAprobarManualOut(BaseSchema):
    """Outcome of the administrative approval of a manual payment."""

    resultado: str = Field(..., description="APROBADA o YA_APROBADA.")
    settlement_status: str = Field(
        ..., description="SETTLED (activación completada) o PENDING (pendiente)."
    )
    orden_pago_id: str
    numero_orden: str
    estado_orden: str
    aprobacion_id: str
    estado_aprobacion: str
    canal: str
    referencia: str
    monto: float
    moneda: str
    motivo: str
    actor: str
    approved_at: datetime


class AdminPagoAnularManualOut(BaseSchema):
    """Outcome of the administrative annulment of a manual payment approval."""

    resultado: str
    orden_pago_id: str
    compra_id: str
    estado_compra: str
    estado_orden: str
    estado_aprobacion: str
    asignaciones_revocadas: int
    beneficiarios_revocados: int
    personas_afectadas: int
    anulada_por: str
    anulada_en: datetime
    motivo_anulacion: str


__all__ = [
    "AdminTransaccionListItemOut",
    "AdminPagoListItemOut",
    "AdminAprobacionManualOut",
    "AdminPaseBeneficiarioOut",
    "AdminPagoDetailOut",
    "AdminPagoAprobarManualIn",
    "AdminPagoAnularManualIn",
    "AdminPagoAprobarManualOut",
    "AdminPagoAnularManualOut",
]
