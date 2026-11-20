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

from modules.marketplace.presentation.schemas.inventario_schemas import (
    EntregaConfirmadaOut,
    EntregaPendienteOut,
    InventarioProductoOut,
    MovimientoInventarioOut,
    RegistrarMovimientoInventarioIn,
    RevertirMovimientoInventarioIn,
)
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
#:
#: `1.0.0` — el catálogo (DOM-04): `RT-MD-01`, `RT-MK-01`, `RT-MK-02`,
#: `RT-MK-03`.
#:
#: `1.1.0` — el pedido (DOM-05): `RT-CM-03` y `RT-MK-04` con sus wrappers
#: (`CrearPedidoIn`, `PedidoCreadoOut`, `PedidoSeguimientoOut`,
#: `PedidoLineaOut`). Es un cambio **aditivo** (MINOR): no se elimina ni se
#: renombra ningún campo, wrapper ni ruta (FR-07 §1.2).
#:
#: `1.2.0` — el inventario y las entregas (DOM-06): cinco rutas
#: **PROVISIONALES** (`RT-MK-08`, `RT-MK-09`, `RT-MK-10`, `RT-MK-11`,
#: `RT-MK-12`) y sus wrappers (`InventarioProductoOut`,
#: `MovimientoInventarioOut`, `EntregaPendienteOut`, `EntregaConfirmadaOut`,
#: `RegistrarMovimientoInventarioIn`, `RevertirMovimientoInventarioIn`).
#: También es un cambio **aditivo** (MINOR): no se elimina ni se renombra
#: ningún campo, wrapper ni ruta (FR-07 §1.2).
#:
#: El registro global `core.contract_versions.SCHEMA_VERSIONS["marketplace"]`
#: es de **A0**: su actualización es la petición A0-02 del evidence de DOM-06.
SCHEMA_VERSION = "1.2.0"

__all__ = [
    "SCHEMA_VERSION",
    "CategoriaListaOut",
    "CrearPedidoIn",
    "CrearProductoIn",
    "EntregaConfirmadaOut",
    "EntregaPendienteOut",
    "ImagenProductoIn",
    "InventarioProductoOut",
    "MovimientoInventarioOut",
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
    "RegistrarMovimientoInventarioIn",
    "RevertirMovimientoInventarioIn",
]
