"""Selectores del catálogo de productos.

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

REGLA (F-26): un selector que devuelve un `QuerySet` es una mina en un
contexto async: la consulta es perezosa y recorrerla dentro de una función
async lanza `SynchronousOnlyOperation`. Por eso TODOS los selectores de este
módulo devuelven LISTAS ya evaluadas.

Las consultas son de lectura y no modifican el alcance: el filtro por edición
es siempre explícito (`edicion_id`), nunca implícito.
"""

from modules.marketplace.domain.models import Producto, ProductoImagen


class ProductoSelector:
    """Consultas de lectura sobre `Producto` y su galería."""

    def listar_por_edicion(self, edicion_id, estado: str | None = None) -> list[Producto]:
        """Productos de una edición, evaluados en lista.

        El orden es el canónico del modelo (`nombre`). `estado` filtra el
        catálogo público a `ACTIVO`.
        """
        consulta = Producto.objects.filter(edicion_id=edicion_id)
        if estado is not None:
            consulta = consulta.filter(estado=estado)
        return list(consulta.select_related("categoria", "edicion"))

    def obtener_por_id(self, producto_id) -> Producto | None:
        """Un producto por identificador, o `None`."""
        return Producto.objects.filter(id=producto_id).first()

    def obtener_por_slug(self, edicion_id, slug: str) -> Producto | None:
        """Un producto por slug DENTRO de una edición, o `None`."""
        return (
            Producto.objects.filter(edicion_id=edicion_id, slug=slug)
            .select_related("categoria", "edicion")
            .first()
        )

    def listar_imagenes(self, producto_id) -> list[ProductoImagen]:
        """La galería de un producto en el orden canónico (`orden`, `id`)."""
        return list(ProductoImagen.objects.filter(producto_id=producto_id))

    def contar_por_edicion(self, edicion_id, estado: str | None = None) -> int:
        """Cuántos productos hay en una edición."""
        consulta = Producto.objects.filter(edicion_id=edicion_id)
        if estado is not None:
            consulta = consulta.filter(estado=estado)
        return consulta.count()


__all__ = ["ProductoSelector"]
