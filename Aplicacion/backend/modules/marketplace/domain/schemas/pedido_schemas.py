"""DTOs internos del pedido de marketplace (`DOM-05`).

Contract: `contract/django-app-architecture-contract.md` §4.6

Los DTOs de esta familia tienen TRES audiencias distintas y por eso viven en
archivos separados:

| DTO | Audiencia | Regla |
|---|---|---|
| `PedidoCreateData` / `PedidoItemCreateData` | el flujo de `marketplace` | lo que el cliente declara: QUÉ pide y CUÁNTO. Nunca un precio |
| `PedidoLineaResuelta` | el flujo de `marketplace` | la línea ya resuelta contra el catálogo: precio CONGELADO |
| `CompraMarketplaceData` / `CompraMarketplaceFact` | el puerto de comercio | la frontera con `commerce`: ni una moneda ni una línea se inventan aquí |

**RN-C02 — el cliente NO impone un importe.** Ni `PedidoCreateData` ni
`PedidoItemCreateData` tienen campo de precio: el precio lo resuelve el
servidor contra el catálogo vigente y lo congela.

**RN-M03 — el histórico NO cambia.** `PedidoLineaResuelta` lleva el precio
unitario y el precio aplicado en el momento del pedido; una oferta posterior
no los cambia.
"""

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from modules.marketplace.domain.constants import MONEDA_PEDIDO


class PedidoItemCreateData(BaseModel):
    """Un artículo declarado por el cliente.

    `tipo` es el discriminante del ORIGEN del artículo: sólo `PRODUCTO` es
    admisible en un pedido de marketplace (RN-C01). `PASE` e `INSCRIPCION`
    se pueden declarar para que el rechazo sea explícito y no un 422 genérico.
    """

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
        description=(
            "Cantidad pedida. El DOMINIO la valida: el DTO no acota el rango "
            "para que el rechazo viaje con el código estable "
            "`PEDIDO_CANTIDAD_INVALIDA` y no con un error de forma."
        ),
    )


class PedidoCreateData(BaseModel):
    """La intención de compra de un pedido de marketplace."""

    items: list[PedidoItemCreateData] = Field(
        ...,
        min_length=1,
        description="Artículos del pedido.",
    )


class PedidoLineaResuelta(BaseModel):
    """Una línea ya resuelta contra el catálogo: precio CONGELADO."""

    tipo_concepto: str = Field(..., description="Tipo de concepto.")
    concepto_id: str = Field(..., description="Identificador del concepto.")
    concepto_nombre: str = Field(..., description="Nombre del concepto.")
    cantidad: int = Field(..., gt=0, description="Cantidad pedida.")
    precio_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Precio de catálogo en el momento del pedido.",
    )
    precio_aplicado: Decimal = Field(
        ...,
        ge=0,
        description="Precio realmente aplicado (con oferta) en el pedido.",
    )

    @property
    def subtotal(self) -> Decimal:
        """El subtotal de la línea: cantidad × precio aplicado."""
        return (self.precio_aplicado * self.cantidad).quantize(Decimal("0.01"))


class LineaCompraMarketplace(BaseModel):
    """Una línea del snapshot de compra, en el vocabulario del puerto."""

    concepto_tipo: str = Field(..., max_length=40, description="Tipo de concepto.")
    concepto_id: str = Field(..., max_length=64, description="Identificador.")
    concepto_nombre: str = Field(..., max_length=200, description="Nombre.")
    cantidad: int = Field(..., gt=0, description="Cantidad comprada.")
    precio_unitario: Decimal = Field(..., ge=0, description="Precio de catálogo.")
    precio_aplicado: Decimal = Field(..., ge=0, description="Precio aplicado.")


class CompraMarketplaceData(BaseModel):
    """La intención de compra que el marketplace entrega a `commerce`.

    `total` es sólo de CONTRASTE: el total que se congela lo deriva el
    servidor de las líneas (`RN-C02`).
    """

    persona_id: str = Field(..., description="Identificador de la persona compradora.")
    lineas: list[LineaCompraMarketplace] = Field(
        ...,
        min_length=1,
        description="Líneas del snapshot de la compra.",
    )
    referencia: str = Field(
        ...,
        max_length=200,
        description="Referencia estable de la intención de compra.",
    )
    moneda: str = Field(default=MONEDA_PEDIDO, max_length=3, description="Moneda.")
    total: Decimal | None = Field(
        default=None,
        ge=0,
        description="Total declarado, sólo para contraste.",
    )


class CompraMarketplaceFact(BaseModel):
    """Los hechos de la compra que el marketplace necesita conocer.

    `estado_pago` ya viene traducido al vocabulario del módulo: la
    terminología de `commerce` no cruza la frontera.
    """

    compra_id: str = Field(..., description="Identificador de la compra.")
    orden_pago_id: str | None = Field(
        None,
        description="Identificador de la orden de pago que financia la compra.",
    )
    estado_pago: str = Field(..., description="Estado del pago (vocabulario propio).")
    total: Decimal = Field(..., ge=0, description="Total congelado de la compra.")
    moneda: str = Field(..., max_length=3, description="Moneda de la compra.")
    reutilizada: bool = Field(
        default=False,
        description="Si la compra pendiente ya existía y se reutilizó.",
    )


__all__ = [
    "CompraMarketplaceData",
    "CompraMarketplaceFact",
    "LineaCompraMarketplace",
    "PedidoCreateData",
    "PedidoItemCreateData",
    "PedidoLineaResuelta",
]
