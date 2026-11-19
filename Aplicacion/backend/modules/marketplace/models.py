"""Re-export puro de los modelos del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta `domain/models/`.
"""

from modules.marketplace.domain.models import (
    CategoriaProducto,
    Pedido,
    PedidoDetalle,
    Producto,
    ProductoImagen,
)

__all__ = [
    "CategoriaProducto",
    "Pedido",
    "PedidoDetalle",
    "Producto",
    "ProductoImagen",
]
