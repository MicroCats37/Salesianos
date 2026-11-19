"""Contrato HTTP del módulo `marketplace` y su versión de schema.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

`SCHEMA_VERSION` es el REGISTRO que A0 mantiene en
`core/contract_versions.py` y que el espejo Zod del frontend declara. No es
un campo del wire: es el mecanismo de detección de drift (FR-07 §1.3).

El valor declarado aquí debe coincidir con
`core.contract_versions.SCHEMA_VERSIONS["marketplace"]`. Un test de contrato
falla si difieren.
"""

from modules.marketplace.presentation.schemas.pedido_schemas import (
    CrearPedidoIn,
    PedidoCreadoOut,
    PedidoItemIn,
    PedidoLineaOut,
    PedidoSeguimientoOut,
)
from modules.marketplace.presentation.schemas.producto_schemas import (
    CategoriaListaOut,
    CrearProductoIn,
    ImagenProductoIn,
    ProductoDetalleOut,
    ProductoEspecificaOut,
    ProductoGeneralOut,
    ProductoIdentidadOut,
    ProductoImagenOut,
    ProductoListItemOut,
    ProductoOut,
)

#: Versión congelada del contrato de presenters/schemas del módulo `marketplace`.
SCHEMA_VERSION = "1.0.0"

__all__ = [
    "SCHEMA_VERSION",
    "CategoriaListaOut",
    "CrearPedidoIn",
    "CrearProductoIn",
    "ImagenProductoIn",
    "PedidoCreadoOut",
    "PedidoItemIn",
    "PedidoLineaOut",
    "PedidoSeguimientoOut",
    "ProductoDetalleOut",
    "ProductoEspecificaOut",
    "ProductoGeneralOut",
    "ProductoIdentidadOut",
    "ProductoImagenOut",
    "ProductoListItemOut",
    "ProductoOut",
]
