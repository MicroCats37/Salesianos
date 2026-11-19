"""Esquemas HTTP del pedido de marketplace (`DOM-05`).

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0`
Contract: `contract/api-wrapper-presenter-contract.md` §2, §7

Ledger (FR-07 §3.3):

| Ruta | Método | Wrapper de entrada | Wrapper de salida | Presenter |
|---|---|---|---|---|
| `RT-CM-03` | POST `/marketplace/pedidos` | `CrearPedidoIn` | `PedidoCreadoOut` | `PedidoPresenter` |
| `RT-MK-04` | GET `/marketplace/pedidos/{token}` | — | `PedidoSeguimientoOut` | `PedidoSeguimientoPresenter` |

**El payload NO admite un importe.** Ni `CrearPedidoIn` ni `PedidoItemIn`
tienen campo de precio: el precio lo resuelve y congela el servidor
(`RN-C02`). El cliente declara QUÉ pide y CUÁNTO.

`tipo` es el discriminante del ORIGEN del artículo: sólo `PRODUCTO` es
admisible. `PASE` e `INSCRIPCION` se pueden DECLARAR para que el rechazo sea
explícito (`PEDIDO_ITEMS_MIXTOS` / `PEDIDO_ITEM_NO_PERMITIDO`) y no un 422
genérico de forma (RN-C01).

Todos heredan de `core.types.BaseSchema`. El espejo Zod 1:1 del frontend es
responsabilidad de A7 (FR-07 §1.1): este lado NO declara `z.any()` ni campos
genéricos.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema
from modules.marketplace.domain.constants import MAX_CANTIDAD_ITEM_PEDIDO


class PedidoItemIn(BaseSchema):
    """Un artículo declarado por el comprador."""

    tipo: str = Field(
        ...,
        max_length=16,
        description="Tipo de concepto pedido (PRODUCTO, PASE, INSCRIPCION).",
    )
    producto_id: UUID = Field(
        ...,
        description="Identificador del producto pedido.",
    )
    cantidad: int = Field(
        ...,
        ge=1,
        le=MAX_CANTIDAD_ITEM_PEDIDO,
        description="Cantidad pedida. La valida el servidor.",
    )


class CrearPedidoIn(BaseSchema):
    """Alta de un pedido de marketplace (`RT-CM-03`).

    El alcance (edición) NO lo declara el cliente: lo resuelve el servidor
    (RN-E01). Tampoco declara un precio: lo congela el servidor (RN-C02).
    """

    items: list[PedidoItemIn] = Field(
        ...,
        min_length=1,
        description="Artículos del pedido.",
    )


class PedidoLineaOut(BaseSchema):
    """Una línea del pedido con su precio CONGELADO (RN-M03)."""

    tipo_concepto: str = Field(..., description="Tipo de concepto pedido.")
    concepto_id: str = Field(..., description="Identificador del concepto.")
    concepto_nombre: str = Field(..., description="Nombre del concepto en el pedido.")
    cantidad: int = Field(..., description="Cantidad pedida.")
    precio_unitario: Decimal = Field(..., description="Precio de catálogo congelado.")
    precio_aplicado: Decimal = Field(..., description="Precio aplicado congelado.")
    subtotal: Decimal = Field(..., ge=0, description="Subtotal de la línea.")


class PedidoSeguimientoOut(BaseSchema):
    """El pedido con sus TRES estados (`RT-MK-04`).

    `estado`, `estado_pago` y `estado_entrega` son hechos DISTINTOS: un
    pedido pagado sigue con la entrega `PENDIENTE` (RN-M07, `QA-M04`).
    """

    id: UUID = Field(..., description="Identificador del pedido.")
    estado: str = Field(..., description="Estado del pedido.")
    estado_pago: str = Field(..., description="Estado del pago.")
    estado_entrega: str = Field(..., description="Estado de la entrega.")
    total: Decimal = Field(..., ge=0, description="Total congelado del pedido.")
    moneda: str = Field(..., max_length=3, description="Moneda del pedido.")
    lineas: list[PedidoLineaOut] = Field(
        default_factory=list,
        description="Detalle del pedido con el precio congelado.",
    )
    orden_pago_id: UUID | None = Field(
        None,
        description="Orden de pago que financia el pedido, si ya existe.",
    )
    siguientes_acciones: list[str] = Field(
        default_factory=list,
        description="Acciones seguras que el comprador puede realizar.",
    )
    created_at: datetime = Field(..., description="Momento de creación del pedido.")


class PedidoCreadoOut(PedidoSeguimientoOut):
    """La respuesta del alta del pedido (`RT-CM-03`).

    `token` viaja SÓLO aquí: es el enlace privado que el comprador guarda
    para volver al pedido. No se publica en ningún listado.
    """

    token: str = Field(..., description="Enlace privado de seguimiento del pedido.")
    recuperado: bool = Field(
        default=False,
        description="Si el pedido ya existía y se recuperó en vez de crearse.",
    )


__all__ = [
    "CrearPedidoIn",
    "PedidoCreadoOut",
    "PedidoItemIn",
    "PedidoLineaOut",
    "PedidoSeguimientoOut",
]
