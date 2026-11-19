"""Result objects del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.6
"""

from modules.marketplace.domain.results.pedido_result import (
    PedidoCreadoResult,
    PedidoLineaResult,
    PedidoSeguimientoResult,
)
from modules.marketplace.domain.results.producto_result import (
    CategoriaProductoResult,
    ProductoImagenResult,
    ProductoListItemResult,
    ProductoResult,
)

__all__ = [
    "CategoriaProductoResult",
    "PedidoCreadoResult",
    "PedidoLineaResult",
    "PedidoSeguimientoResult",
    "ProductoImagenResult",
    "ProductoListItemResult",
    "ProductoResult",
]
