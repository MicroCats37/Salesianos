"""Selectores de las categorías de producto.

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

REGLA (F-26): los selectores devuelven LISTAS evaluadas, nunca `QuerySet`.
"""

from modules.marketplace.domain.models import CategoriaProducto


class CategoriaProductoSelector:
    """Consultas de lectura sobre `CategoriaProducto`."""

    def listar_por_edicion(self, edicion_id) -> list[CategoriaProducto]:
        """Categorías de una edición, en el orden canónico (`orden`, `nombre`)."""
        return list(CategoriaProducto.objects.filter(edicion_id=edicion_id))

    def obtener_por_id(self, categoria_id) -> CategoriaProducto | None:
        """Una categoría por identificador, o `None`."""
        return CategoriaProducto.objects.filter(id=categoria_id).first()

    def obtener_por_slug(self, edicion_id, slug: str) -> CategoriaProducto | None:
        """Una categoría por slug DENTRO de una edición, o `None`."""
        return CategoriaProducto.objects.filter(edicion_id=edicion_id, slug=slug).first()


__all__ = ["CategoriaProductoSelector"]
