"""Result objects del pedido de marketplace (`DOM-05`).

Contract: `contract/django-app-architecture-contract.md` §4.6

Los results son la frontera entre el dominio y la presentación: llevan el
hecho ya calculado para que el presenter sea un transformador puro.

**TRES estados, TRES campos.** El result expone el estado del pedido, el
estado del pago y el estado de la entrega POR SEPARADO: un pedido pagado
sigue con la entrega `PENDIENTE` (RN-M07, `QA-M04`). El presenter no puede
confundirlos porque no tienen el mismo origen.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PedidoLineaResult(BaseModel):
    """Una línea del pedido con su precio CONGELADO (RN-M03)."""

    id: UUID = Field(..., description="Identificador de la línea.")
    tipo_concepto: str = Field(..., description="Tipo de concepto pedido.")
    concepto_id: str = Field(..., description="Identificador del concepto.")
    concepto_nombre: str = Field(..., description="Nombre del concepto en el pedido.")
    cantidad: int = Field(..., description="Cantidad pedida.")
    precio_unitario: Decimal = Field(..., description="Precio de catálogo congelado.")
    precio_aplicado: Decimal = Field(..., description="Precio aplicado congelado.")
    subtotal: Decimal = Field(..., ge=0, description="Subtotal de la línea.")


class PedidoSeguimientoResult(BaseModel):
    """El pedido con sus tres estados y la acción segura que sigue.

    No lleva el `token`: es la credencial del enlace y viaja en el path.
    """

    id: UUID = Field(..., description="Identificador del pedido.")
    edicion_id: UUID = Field(..., description="Edición de alcance del pedido.")
    estado: str = Field(..., description="Estado del pedido.")
    estado_pago: str = Field(..., description="Estado del pago (hecho de `commerce`).")
    estado_entrega: str = Field(..., description="Estado de la entrega (hecho propio).")
    total: Decimal = Field(..., ge=0, description="Total congelado del pedido.")
    moneda: str = Field(..., max_length=3, description="Moneda del pedido.")
    lineas: list[PedidoLineaResult] = Field(
        default_factory=list,
        description="Detalle del pedido con el precio congelado.",
    )
    orden_pago_id: str | None = Field(
        None,
        description="Orden de pago que financia el pedido, si ya existe.",
    )
    compra_id: str | None = Field(
        None,
        description="Compra de `commerce` que financia el pedido, si ya existe.",
    )
    siguientes_acciones: list[str] = Field(
        default_factory=list,
        description="Acciones seguras que el comprador puede realizar.",
    )
    created_at: datetime = Field(..., description="Momento de creación del pedido.")


class PedidoCreadoResult(PedidoSeguimientoResult):
    """La respuesta del alta del pedido.

    `token` viaja SÓLO aquí: es el enlace privado que el comprador guarda
    para volver al pedido (`/marketplace/pedidos/{token}`).
    """

    token: str = Field(..., description="Enlace privado de seguimiento del pedido.")
    recuperado: bool = Field(
        default=False,
        description="Si el pedido ya existía y se recuperó en vez de crearse.",
    )


__all__ = [
    "PedidoCreadoResult",
    "PedidoLineaResult",
    "PedidoSeguimientoResult",
]
