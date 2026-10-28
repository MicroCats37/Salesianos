"""
Result DTOs of the payments (A5, A6) and of the manual approval of a payment.

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
    """A purchase line with its payment order.

    ONE row is ONE generic purchase with exactly ONE supported composition:
    a sports `CompraInscripcion` (inscripcion_id) OR a pass batch
    `CompraPase` (pase_id). The two identities are never both present and
    never both absent.
    """

    compra_id: str
    orden_pago_id: str | None = None
    numero_orden: str | None = None
    inscripcion_id: str | None = None
    pase_id: str | None = None
    responsable_nombre: str
    tipo: str
    producto_nombre: str
    cantidad: int
    precio_unitario: float
    total: float
    estado_compra: str
    estado_orden: str | None = None
    pagada_en: datetime | None = None
    origen_pago: str = "SIN_PAGO"
    monto_orden: float | None = None
    moneda_orden: str | None = None
    beneficiarios_activos: int = 0
    beneficiarios_revocados: int = 0
    created_at: datetime


class AdminPaseBeneficiarioConteoResult(BaseModel):
    """
    The nominative rights of a pass purchase, counted by state.

    It is an EXPLICIT typed result, never an anonymous mapping: the selector
    returns one instance per purchase and the mapper reads its typed
    attributes.

    `activos`   — rights that still grant the fiesta access.
    `revocados` — rights already revoked: their slot stays consumed forever,
                  but they grant nothing.
    """

    activos: int = 0
    revocados: int = 0


class AdminPagoComposiciónResult(BaseModel):
    """
    The commercial composition of a purchase.

    ONE purchase has exactly ONE supported composition: a sports
    `CompraInscripcion` (inscripcion_id) OR a pass batch `CompraPase`
    (pase_id). The two identities are never both present.

    It is an EXPLICIT typed result: the selector bulk-loads it and the mapper
    reads its typed attributes.
    """

    tipo: str
    inscripcion_id: str | None = None
    pase_id: str | None = None
    producto_nombre: str = ""
    cantidad: int = 0
    precio_unitario: float = 0.0
    total: float = 0.0


class AdminTransaccionListItemResult(BaseModel):
    """A payment attempt — explicit fields only, no provider internals."""

    id: str
    status: str
    amount: float
    currency: str
    metodo_pago: str | None = None
    response_code: str | None = None
    created_at: datetime


class AdminAprobacionManualResult(BaseModel):
    """
    One entry of the manual approval history of an order.

    The history is the audit trail of the administrative decisions: who
    approved, how, when — and who annulled it, why and when. It NEVER
    carries a provider credential.
    """

    id: str
    estado: str
    canal: str
    referencia: str
    monto: float
    moneda: str
    motivo: str
    actor: str
    anulada_por: str | None = None
    anulada_en: datetime | None = None
    motivo_anulacion: str | None = None
    created_at: datetime


class AdminPaseBeneficiarioResult(BaseModel):
    """
    One nominative right of a pass purchase.

    Only the SLOT, the state and the internal identifier of the holder
    travel: no names, no documents and never the QR credential.
    """

    persona_id: str
    slot: int
    estado: str


class AdminPagoDetalleResult(AdminPagoListItemResult):
    """The drilldown of a payment order (A6)."""

    transacciones: list[AdminTransaccionListItemResult] = []
    aprobaciones: list[AdminAprobacionManualResult] = []
    beneficiarios: list[AdminPaseBeneficiarioResult] = []


class AdminPagoAprobarManualResult(BaseModel):
    """Outcome of the administrative approval of a manual payment."""

    resultado: str
    settlement_status: str
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


class AdminPagoAnularManualResult(BaseModel):
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
    "AdminPagoListItemResult",
    "AdminPagoComposiciónResult",
    "AdminPaseBeneficiarioConteoResult",
    "AdminTransaccionListItemResult",
    "AdminAprobacionManualResult",
    "AdminPaseBeneficiarioResult",
    "AdminPagoDetalleResult",
    "AdminPagoAprobarManualResult",
    "AdminPagoAnularManualResult",
]
