"""DTOs de salida del dominio de PASES.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6

Son el contrato INTERNO entre el dominio y el presenter. El presenter los
traduce al schema HTTP; el dominio no sabe qué forma tiene el cable.

Reglas que se respetan aquí:

- **Ningún resultado lleva el token de gestión**: es una credencial y sólo
  viaja en la respuesta que la emite, nunca en un listado.
- **Los importes viajan como `Decimal`**: el presenter y `core.responses` los
  serializan.
- **La aritmética la hace el servidor**: el resultado lleva los números ya
  calculados (`cantidad`, `asignados`, `disponibles`), nunca una resta que
  el cliente tenga que hacer (`RN-I03`, `RN-C07`).
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PrecioPaseResult(BaseModel):
    """El precio vigente de un pase."""

    model_config = ConfigDict(frozen=True)

    monto: Decimal
    moneda: str
    vigente_desde: date
    vigente_hasta: date | None = None


class PaseCatalogoResult(BaseModel):
    """Un pase del catálogo, con su precio vigente."""

    model_config = ConfigDict(frozen=True)

    id: str
    created_at: datetime
    updated_at: datetime
    edicion_id: str
    edicion_nombre: str
    nombre: str
    slug: str
    descripcion: str
    estado: str
    precio: PrecioPaseResult


class PaseCatalogoListaResult(BaseModel):
    """El catálogo de pases de UNA edición."""

    model_config = ConfigDict(frozen=True)

    edicion_id: str
    edicion_nombre: str
    pases: list[PaseCatalogoResult] = Field(default_factory=list)


class PaseDetalleResult(BaseModel):
    """El detalle público de un pase.

    `precio` es `None` cuando el pase NO tiene precio vigente: no hay
    precio de reserva inventado (`FL-01` paso 3).
    """

    model_config = ConfigDict(frozen=True)

    id: str
    created_at: datetime
    updated_at: datetime
    edicion_id: str
    edicion_nombre: str
    nombre: str
    slug: str
    descripcion: str
    estado: str
    precio: PrecioPaseResult | None = None


class CompraPaseResultado(BaseModel):
    """El resultado de crear (o recuperar) la compra de un lote de pases."""

    model_config = ConfigDict(frozen=True)

    compra_pase_id: str
    compra_id: str
    orden_pago_id: str
    estado: str
    cantidad: int
    precio_unitario: Decimal
    total: Decimal
    moneda: str
    pase_id: str
    pase_nombre: str
    edicion_id: str
    edicion_nombre: str
    comprador_persona_id: str
    comprador_nombres: str
    token: str
    token_expira_en: datetime
    reutilizada: bool
    causa_operativa: str


class PaseBeneficiarioResult(BaseModel):
    """Un derecho de entrada de una persona."""

    model_config = ConfigDict(frozen=True)

    id: str
    pase_id: str
    pase_nombre: str
    edicion_id: str
    persona_id: str
    persona_nombres: str
    persona_apellidos: str
    persona_tipo_documento: str
    persona_numero_documento: str
    origen: str
    estado: str
    cantidad: int
    cantidad_consumida: int
    cantidad_disponible: int
    asignado_en: datetime
    motivo: str
    revocado_en: datetime | None = None
    motivo_revocacion: str = ""


class PaseCompraDetalleResult(BaseModel):
    """El detalle de la compra de un lote de pases, para su titular."""

    model_config = ConfigDict(frozen=True)

    compra_pase_id: str
    compra_id: str
    orden_pago_id: str
    estado: str
    pase_id: str
    pase_nombre: str
    edicion_id: str
    edicion_nombre: str
    cantidad: int
    asignados: int
    disponibles: int
    precio_unitario: Decimal
    total: Decimal
    moneda: str
    causa_operativa: str
    beneficiarios: list[PaseBeneficiarioResult] = Field(default_factory=list)


class PaseBeneficiariosResult(BaseModel):
    """Los derechos de un lote de pases."""

    model_config = ConfigDict(frozen=True)

    compra_pase_id: str
    estado: str
    cantidad: int
    asignados: int
    disponibles: int
    beneficiarios: list[PaseBeneficiarioResult] = Field(default_factory=list)


class PaseBeneficiarioRevocadoResult(BaseModel):
    """El resultado de revocar un derecho de entrada."""

    model_config = ConfigDict(frozen=True)

    compra_pase_id: str
    derecho_id: str
    persona_id: str
    estado: str
    revocado_en: datetime
    ya_revocado: bool
    motivo: str


class CortesiaPaseResult(BaseModel):
    """El acta de una cortesía."""

    model_config = ConfigDict(frozen=True)

    id: str
    edicion_id: str
    edicion_nombre: str
    pase_id: str
    pase_nombre: str
    persona_id: str
    persona_nombres: str
    persona_tipo_documento: str
    persona_numero_documento: str
    estado: str
    motivo: str
    actor_usuario_id: str | None = None
    actor_nombres: str = ""
    concedido_en: datetime
    revocado_en: datetime | None = None


class AdminPaseListItemResult(BaseModel):
    """Una fila del listado administrativo de lotes de pases."""

    model_config = ConfigDict(frozen=True)

    compra_pase_id: str
    estado: str
    pase_id: str
    pase_nombre: str
    edicion_id: str
    edicion_nombre: str
    comprador_persona_id: str
    comprador_nombres: str
    cantidad: int
    asignados: int
    total: Decimal
    moneda: str
    creado_en: datetime


class AdminPaseListaResult(BaseModel):
    """El listado administrativo de lotes de pases.

    La paginación viaja RESUELTA: el servidor no deja que el cliente calcule
    `total_pages` (`FR-01` §4.3).
    """

    model_config = ConfigDict(frozen=True)

    items: list[AdminPaseListItemResult] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 25
    total_pages: int = 0


class AdminCortesiaListItemResult(BaseModel):
    """Una fila del listado administrativo de cortesías."""

    model_config = ConfigDict(frozen=True)

    id: str
    pase_nombre: str
    edicion_nombre: str
    persona_nombres: str
    persona_tipo_documento: str
    persona_numero_documento: str
    estado: str
    motivo: str
    actor_nombres: str
    concedido_en: datetime


class AdminCortesiaListaResult(BaseModel):
    """El listado administrativo de cortesías.

    La paginación viaja RESUELTA: el servidor no deja que el cliente calcule
    `total_pages` (`FR-01` §4.3).
    """

    model_config = ConfigDict(frozen=True)

    items: list[AdminCortesiaListItemResult] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 25
    total_pages: int = 0


__all__ = [
    "AdminCortesiaListItemResult",
    "AdminCortesiaListaResult",
    "AdminPaseListItemResult",
    "AdminPaseListaResult",
    "CompraPaseResultado",
    "CortesiaPaseResult",
    "PaseBeneficiarioResult",
    "PaseBeneficiarioRevocadoResult",
    "PaseBeneficiariosResult",
    "PaseCompraDetalleResult",
    "PaseCatalogoListaResult",
    "PaseCatalogoResult",
    "PaseDetalleResult",
    "PrecioPaseResult",
]
