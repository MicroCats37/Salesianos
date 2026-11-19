"""Selectores del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §8
"""

from modules.marketplace.domain.selectors.categoria_selector import (
    CategoriaProductoSelector,
)
from modules.marketplace.domain.selectors.pedido_selector import PedidoSelector
from modules.marketplace.domain.selectors.producto_selector import ProductoSelector

__all__ = [
    "CategoriaProductoSelector",
    "PedidoSelector",
    "ProductoSelector",
]
