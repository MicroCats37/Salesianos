"""Result DTOs for the independent party-pass catalogue."""
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


@dataclass
class PasePrecioCatalogoResult:
    """Result for a pass price row (stage calendar)."""

    etapa: str
    precio_unitario: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date]


@dataclass
class PaseCatalogoResult:
    """Result for a pass in the public catalogue.

    `precio_preventa` / `precio_regular` expose ONLY the price of that stage
    that is currently inside its validity window (None otherwise) and
    `precio_vigente` is the effective unit price right now (preventa first,
    then regular, then None). `precios[]` is the full calendar of the ACTIVE
    price rows of the pass.
    """

    id: str
    evento_id: str
    nombre: str
    descripcion: str
    cantidad_maxima: int
    activo: bool
    precio_preventa: Optional[Decimal]
    precio_regular: Optional[Decimal]
    precio_vigente: Optional[Decimal]
    precios: list[PasePrecioCatalogoResult]


@dataclass
class PaseCompraCreadaResult:
    """Result of creating a pass purchase (Compra + OrdenPago + CompraPase).

    The frozen values are the ones the SERVER computed: the client never
    sends a price or a total.
    """

    compra_id: str
    compra_pase_id: str
    orden_pago_id: str
    numero_orden: str
    pase_id: str
    pase_nombre: str
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    estado_compra: str
    estado_orden: str


@dataclass
class PaseCompraDetalleResult:
    """Detail of a pass purchase, as seen by its owner.

    `origen_pago` is DERIVED from the payment evidence of the order
    (`IZIPAY`, `MANUAL` or `SIN_PAGO`); it is never typed by anybody.

    `responsable_id` is INTERNAL: it backs the ownership check and is never
    published in the HTTP payload.
    """

    compra_id: str
    compra_pase_id: str
    orden_pago_id: str
    numero_orden: str
    pase_id: str
    pase_nombre: str
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    estado_compra: str
    estado_orden: str
    moneda: str
    origen_pago: str
    created_at: datetime
    responsable_id: str
    beneficiarios_asignados: int
    beneficiarios_pendientes: int


@dataclass
class PaseBeneficiarioResult:
    """One nominative entitlement of a batch."""

    persona_id: str
    nombre_completo: str
    tipo_documento: str
    numero_documento: str
    slot: int
    estado: str
    asignado_en: Optional[datetime]
    revocado_en: Optional[datetime]
    motivo_revocacion: Optional[str]


@dataclass
class PaseConteosBeneficiariosResult:
    """
    The immutable slot accounting of a batch.

    `slots_usados` counts the rows of the batch — ACTIVE **and** REVOCATED: a
    revoked slot is consumed forever and is NEVER restored. `activos` and
    `revocados` are reported separately so the UI can tell them apart.
    """

    cantidad_pases: int
    activos: int
    revocados: int
    slots_usados: int
    slots_disponibles: int


@dataclass
class PaseBeneficiariosListaResult(PaseConteosBeneficiariosResult):
    """The beneficiaries of a batch with the slot accounting."""

    compra_id: str
    beneficiarios: list[PaseBeneficiarioResult]


@dataclass
class PaseBeneficiariosAsignadosResult(PaseConteosBeneficiariosResult):
    """The outcome of an assignment of beneficiaries."""

    compra_id: str
    asignados: int
    ya_asignados: int
    beneficiarios: list[PaseBeneficiarioResult]


@dataclass
class PaseBeneficiarioRevocadoResult(PaseConteosBeneficiariosResult):
    """The outcome of a permanent revocation."""

    compra_id: str
    persona_id: str
    estado: str
    revocado_en: Optional[datetime]
    ya_revocado: bool


@dataclass
class PaseCompraCanceladaResult:
    """The outcome of the administrative cancellation of a pass purchase.

    It is NOT a monetary refund: it cancels the purchase and the order and
    revokes the nominative rights it funded.
    """

    compra_id: str
    estado_compra: str
    estado_orden: str
    ya_cancelada: bool
    beneficiarios_revocados: int
    personas_afectadas: int
    motivo: str
