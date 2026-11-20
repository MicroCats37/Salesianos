"""Esquemas HTTP del inventario y de las entregas de marketplace (`DOM-06`).

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-CM-1.0.0`
Contract: `contract/api-wrapper-presenter-contract.md` §2, §7

Ledger provisional (SH-05 §1.6 · RB-07):

| Ruta | Método | Wrapper de entrada | Wrapper de salida | Presenter |
|---|---|---|---|---|
| `RT-MK-08` | GET `/administracion/marketplace/inventario` | — | `InventarioProductoOut` | `InventarioPresenter` |
| `RT-MK-09` | POST `/administracion/marketplace/inventario/movimientos` | `RegistrarMovimientoInventarioIn` | `MovimientoInventarioOut` | `InventarioPresenter` |
| `RT-MK-12` | POST `/administracion/marketplace/inventario/movimientos/{movimiento_id}/revertir` | `RevertirMovimientoInventarioIn` | `MovimientoInventarioOut` | `InventarioPresenter` |
| `RT-MK-10` | GET `/administracion/marketplace/entregas` | — | `EntregaPendienteOut` | `EntregaPresenter` |
| `RT-MK-11` | POST `/administracion/marketplace/entregas/{pedido_id}/confirmar` | — | `EntregaConfirmadaOut` | `EntregaPresenter` |

**EL WIRE NO DECIDE REGLAS.** La cantidad del movimiento es CON SIGNO y la
valida el DOMINIO contra la naturaleza del movimiento (`RN-M04`); el precio,
el stock disponible y la autorización los decide el servidor, nunca el
cliente (`RN-C02` · `RN-M06`).

`PedidoLineaOut` se REUTILIZA: el detalle de una entrega es el detalle del
pedido, con su precio congelado (SCHEMA_DRY_INTENTION).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema

from modules.marketplace.presentation.schemas.pedido_schemas import PedidoLineaOut


class RegistrarMovimientoInventarioIn(BaseSchema):
    """El registro de un movimiento manual de inventario (`RT-MK-09`)."""

    producto_id: UUID = Field(..., description="Producto del movimiento.")
    tipo: str = Field(
        ...,
        max_length=24,
        description=(
            "Naturaleza del movimiento (REPOSICION, MERMA, CONSUMO_INTERNO, "
            "AJUSTE, SALIDA_SIN_VENTA)."
        ),
    )
    cantidad: int = Field(
        ...,
        description=(
            "Cantidad CON signo: positiva entra, negativa sale. La naturaleza "
            "impone el signo y el dominio lo valida."
        ),
    )
    motivo: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Motivo del movimiento. Es obligatorio.",
    )


class RevertirMovimientoInventarioIn(BaseSchema):
    """La compensación de un movimiento ya registrado (`RT-MK-12`)."""

    motivo: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Motivo de la reversa.",
    )


class MovimientoInventarioOut(BaseSchema):
    """Un movimiento de la bitácora de inventario."""

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


class InventarioProductoOut(BaseSchema):
    """El inventario de un producto: físico, reservado y disponible."""

    producto_id: UUID = Field(..., description="Identificador del producto.")
    nombre: str = Field(..., description="Nombre del producto.")
    slug: str = Field(..., description="Identificador del producto en la edición.")
    stock: int = Field(..., ge=0, description="Unidades físicas.")
    reservado: int = Field(..., ge=0, description="Unidades apartadas por pedidos.")
    disponible: int = Field(..., ge=0, description="Unidades que se pueden vender.")
    movimientos: list[MovimientoInventarioOut] = Field(
        default_factory=list,
        description="Últimos movimientos de la bitácora.",
    )


class EntregaPendienteOut(BaseSchema):
    """Un pedido pagado que todavía espera su entrega."""

    pedido_id: UUID = Field(..., description="Identificador del pedido.")
    comprador_nombres: str = Field(..., description="Nombres del comprador del pedido.")
    comprador_apellidos: str = Field(..., description="Apellidos del comprador del pedido.")
    comprador_documento: str = Field(..., description="Documento del comprador.")
    estado: str = Field(..., description="Estado del pedido.")
    estado_entrega: str = Field(..., description="Estado de la entrega.")
    total: Decimal = Field(..., ge=0, description="Total congelado del pedido.")
    moneda: str = Field(..., description="Moneda del pedido.")
    lineas: list[PedidoLineaOut] = Field(
        default_factory=list,
        description="Detalle congelado del pedido.",
    )
    created_at: datetime = Field(..., description="Momento de creación del pedido.")


class EntregaEntregadaOut(BaseSchema):
    """Un pedido cuya entrega física ya fue registrada."""

    pedido_id: UUID = Field(..., description="Identificador del pedido.")
    comprador_nombres: str = Field(..., description="Nombres del comprador del pedido.")
    comprador_apellidos: str = Field(..., description="Apellidos del comprador del pedido.")
    comprador_documento: str = Field(..., description="Documento del comprador.")
    total: Decimal = Field(..., ge=0, description="Total congelado del pedido.")
    moneda: str = Field(..., description="Moneda del pedido.")
    lineas: list[PedidoLineaOut] = Field(default_factory=list)
    entregada_en: datetime = Field(..., description="Momento del acta de entrega.")


class EntregasOut(BaseSchema):
    """Las dos colas operativas de recogidas de una edición."""

    pendientes: list[EntregaPendienteOut] = Field(default_factory=list)
    entregadas: list[EntregaEntregadaOut] = Field(default_factory=list)


class EntregaConfirmadaOut(BaseSchema):
    """El acta de una entrega confirmada."""

    pedido_id: UUID = Field(..., description="Identificador del pedido.")
    estado_entrega: str = Field(..., description="Estado de la entrega.")
    cantidad_total: int = Field(..., ge=1, description="Unidades entregadas.")
    actor_id: UUID = Field(..., description="Operador que realizó la entrega.")
    entregada_en: datetime = Field(..., description="Momento de la entrega.")
    lineas: list[PedidoLineaOut] = Field(
        default_factory=list,
        description="Detalle entregado.",
    )


__all__ = [
    "EntregaEntregadaOut",
    "EntregaConfirmadaOut",
    "EntregaPendienteOut",
    "EntregasOut",
    "InventarioProductoOut",
    "MovimientoInventarioOut",
    "RegistrarMovimientoInventarioIn",
    "RevertirMovimientoInventarioIn",
]
