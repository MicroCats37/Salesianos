"""
HTTP schemas for the party-pass catalogue endpoints.

Composed over reusable blocks (SCHEMA_DRY_INTENTION): the general block
carries the identity/descriptive data and the specific block carries the
commercial data that varies per use case.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import Field

from core.types import BaseSchema


class PasePrecioOut(BaseSchema):
    """Schema for a pass price row (the stage calendar of a pass)."""

    etapa: str
    precio_unitario: float
    vigente_desde: date
    vigente_hasta: Optional[date]


class PaseCatalogoBaseOut(BaseSchema):
    """General block: identity and descriptive data of a pass.

    `descripcion` is nullable on purpose: the public copy of a pass is
    optional and `BaseSchema` normalizes an empty string to `None` — a
    required `str` would reject a pass without description.
    """

    id: str
    evento_id: str
    nombre: str
    descripcion: Optional[str] = None
    activo: bool


class PaseListOut(PaseCatalogoBaseOut):
    """
    Schema for a pass in the public catalogue response.

    `precio_preventa` / `precio_regular` expose ONLY the price of that stage
    that is currently inside its validity window (None otherwise) and
    `precio_vigente` is the effective unit price right now (preventa first,
    then regular, then None when no price is vigente). `precios[]` is the
    full calendar of the ACTIVE price rows of the pass.
    """

    precio_preventa: Optional[float]
    precio_regular: Optional[float]
    precio_vigente: Optional[float]
    cantidad_maxima: int
    precios: list[PasePrecioOut]


# ── Compra de pases ──────────────────────────────────────────────────────────
#
# Los schemas de compra se componen por bloques: el bloque general lleva la
# identidad de la compra y del pase, el bloque de montos lleva los valores
# CONGELADOS y cada endpoint añade sólo lo que le es propio.


class PaseComprarIn(BaseSchema):
    """
    Input for buying a batch of passes.

    The client sends ONLY the pass and the quantity: the price and the total
    are always computed by the server.
    """

    pase_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="UUID of the pass to buy",
    )
    cantidad: int = Field(
        ...,
        gt=0,
        description="Number of passes to buy",
    )


class PaseCompraBaseOut(BaseSchema):
    """General block: identity of the purchase and of the purchased pass."""

    compra_id: str
    orden_pago_id: str
    numero_orden: str
    pase_id: str
    pase_nombre: str


class PaseCompraMontosOut(BaseSchema):
    """Business block: the values FROZEN at purchase time."""

    cantidad: int
    precio_unitario: float
    total: float


class PaseCompraEstadoBaseOut(PaseCompraBaseOut, PaseCompraMontosOut):
    """Common block: identity, frozen amounts and commercial state."""

    estado_compra: str
    estado_orden: str


class PaseCompraCreadaOut(PaseCompraEstadoBaseOut):
    """Output of creating a pass purchase."""


class PaseCompraEstadoOut(PaseCompraEstadoBaseOut):
    """
    Output of reading a pass purchase.

    `origen_pago` is DERIVED from the payment evidence of the order
    (`IZIPAY`, `MANUAL` or `SIN_PAGO`) — it is never a field the client can
    send nor the provider can impose.

    `beneficiarios_asignados` / `beneficiarios_pendientes` describe the
    nominative rights of the batch: `asignados` counts the ACTIVE rights and
    `pendientes` the slots that are still free (a revoked slot is consumed
    forever and is never restored).
    """

    moneda: str
    origen_pago: str
    created_at: datetime
    beneficiarios_asignados: int
    beneficiarios_pendientes: int


# ── Derechos nominativos ─────────────────────────────────────────────────────
#
# Los schemas de beneficiarios se componen por bloques: el bloque general
# dice QUIÉN tiene el slot y en qué estado, el bloque de auditoría dice
# CUÁNDO y POR QUÉ, y el bloque de conteos describe la contabilidad INMUTABLE
# de los slots.


class PaseBeneficiarioBaseOut(BaseSchema):
    """General block: who holds the slot and in which state."""

    persona_id: str
    nombre_completo: str
    tipo_documento: str
    numero_documento: str
    slot: int
    estado: str


class PaseBeneficiarioAuditadoOut(PaseBeneficiarioBaseOut):
    """Specific block: the audit trail of the entitlement."""

    asignado_en: datetime
    revocado_en: Optional[datetime]
    motivo_revocacion: Optional[str]


class PaseConteosBeneficiariosOut(BaseSchema):
    """
    Business block: the IMMUTABLE slot accounting of a batch.

    `slots_usados` counts the rows of the batch — ACTIVE **and** REVOCATED.
    A revoked slot is consumed forever: `slots_disponibles` never grows back
    after a revocation.
    """

    cantidad_pases: int
    activos: int
    revocados: int
    slots_usados: int
    slots_disponibles: int


class PaseBeneficiariosAsignarIn(BaseSchema):
    """
    Input for assigning the persons of a batch.

    Each id is the UUID of an EXISTING `Persona`, already resolved by the
    client: the API NEVER creates a person out of free text.
    """

    beneficiario_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="UUIDs of the existing personas that receive the passes",
    )


class PaseBeneficiarioRevocarIn(BaseSchema):
    """Input for the permanent revocation of a right."""

    motivo: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Why the right is revoked (mandatory)",
    )


class PaseBeneficiariosListaOut(PaseConteosBeneficiariosOut):
    """Output of listing the beneficiaries of a batch."""

    compra_id: str
    beneficiarios: list[PaseBeneficiarioAuditadoOut]


class PaseBeneficiariosAsignadosOut(PaseConteosBeneficiariosOut):
    """Output of assigning the persons of a batch."""

    compra_id: str
    asignados: int
    ya_asignados: int
    beneficiarios: list[PaseBeneficiarioAuditadoOut]


class PaseBeneficiarioRevocadoOut(PaseConteosBeneficiariosOut):
    """Output of the permanent revocation of a right."""

    compra_id: str
    persona_id: str
    estado: str
    revocado_en: Optional[datetime]
    ya_revocado: bool
