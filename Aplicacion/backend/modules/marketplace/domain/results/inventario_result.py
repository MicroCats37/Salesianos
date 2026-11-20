"""Result objects del inventario de marketplace (`DOM-06`).

Contract: `contract/django-app-architecture-contract.md` §4.6

Los results son la frontera entre el dominio y la presentación: llevan el
hecho ya calculado para que el presenter sea un transformador puro.

Reutiliza `PedidoLineaResult` (el bloque de línea ya congelado por `DOM-05`)
en vez de duplicarlo: el detalle de la entrega es el MISMO detalle del
pedido, con el MISMO precio (SCHEMA_DRY_INTENTION).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from modules.marketplace.domain.results.pedido_result import PedidoLineaResult


class MovimientoInventarioResult(BaseModel):
    """Un movimiento de la bitácora, listo para la respuesta HTTP."""

    id: UUID = Field(..., description="Identificador del movimiento.")
    producto_id: UUID = Field(..., description="Producto afectado.")
    cantidad: int = Field(..., description="Cantidad con signo.")
    tipo: str = Field(..., description="Naturaleza del movimiento.")
    motivo: str = Field(..., description="Motivo del movimiento.")
    referencia: str = Field(..., description="Referencia de origen.")
    actor_id: UUID | None = Field(
        None,
        description="Quién lo registró. NUNCA en las ventas automáticas.",
    )
    created_at: datetime = Field(..., description="Momento del movimiento.")


class InventarioProductoResult(BaseModel):
    """El inventario de un producto: físico, reservado y disponible."""

    producto_id: UUID = Field(..., description="Identificador del producto.")
    nombre: str = Field(..., description="Nombre del producto.")
    slug: str = Field(..., description="Identificador del producto en la edición.")
    stock: int = Field(..., ge=0, description="Unidades físicas.")
    reservado: int = Field(..., ge=0, description="Unidades apartadas por pedidos.")
    disponible: int = Field(..., ge=0, description="Unidades que se pueden vender.")
    movimientos: list[MovimientoInventarioResult] = Field(
        default_factory=list,
        description="Últimos movimientos de la bitácora.",
    )


class EntregaPendienteResult(BaseModel):
    """Un pedido pagado que todavía espera su entrega."""

    pedido_id: UUID = Field(..., description="Identificador del pedido.")
    estado: str = Field(..., description="Estado del pedido.")
    estado_entrega: str = Field(..., description="Estado de la entrega.")
    total: Decimal = Field(..., ge=0, description="Total congelado del pedido.")
    moneda: str = Field(..., description="Moneda del pedido.")
    lineas: list[PedidoLineaResult] = Field(
        default_factory=list,
        description="Detalle congelado del pedido.",
    )
    created_at: datetime = Field(..., description="Momento de creación del pedido.")


class EntregaConfirmadaResult(BaseModel):
    """El acta de una entrega confirmada."""

    pedido_id: UUID = Field(..., description="Identificador del pedido.")
    estado_entrega: str = Field(..., description="Estado de la entrega.")
    cantidad_total: int = Field(..., ge=1, description="Unidades entregadas.")
    actor_id: UUID = Field(..., description="Operador que realizó la entrega.")
    entregada_en: datetime = Field(..., description="Momento de la entrega.")
    lineas: list[PedidoLineaResult] = Field(
        default_factory=list,
        description="Detalle entregado.",
    )


__all__ = [
    "EntregaConfirmadaResult",
    "EntregaPendienteResult",
    "InventarioProductoResult",
    "MovimientoInventarioResult",
]
