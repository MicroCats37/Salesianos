"""Modelos del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.2
"""

from modules.marketplace.domain.models.categoria_producto import CategoriaProducto
from modules.marketplace.domain.models.pedido import Pedido, PedidoDetalle
from modules.marketplace.domain.models.producto import Producto
from modules.marketplace.domain.models.producto_imagen import ProductoImagen

__all__ = [
    "CategoriaProducto",
    "Pedido",
    "PedidoDetalle",
    "Producto",
    "ProductoImagen",
]
