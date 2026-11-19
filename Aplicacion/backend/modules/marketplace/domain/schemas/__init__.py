"""DTOs internos del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.6
"""

from modules.marketplace.domain.schemas.pedido_schemas import (
    CompraMarketplaceData,
    CompraMarketplaceFact,
    LineaCompraMarketplace,
    PedidoCreateData,
    PedidoItemCreateData,
    PedidoLineaResuelta,
)
from modules.marketplace.domain.schemas.producto_schemas import (
    CategoriaProductoCreateData,
    ImagenProductoData,
    ImagenProductoUploadData,
    ProductoCreateData,
    ProductoUpdateData,
)

__all__ = [
    "CategoriaProductoCreateData",
    "CompraMarketplaceData",
    "CompraMarketplaceFact",
    "ImagenProductoData",
    "ImagenProductoUploadData",
    "LineaCompraMarketplace",
    "PedidoCreateData",
    "PedidoItemCreateData",
    "PedidoLineaResuelta",
    "ProductoCreateData",
    "ProductoUpdateData",
]
