"""`CategoriaProducto` — la categoría de un producto del catálogo.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (plan `funcional/03` §1, RN-M02):

    CategoriaProducto
      id: UUID            (pk)
      edicion_id: UUID     FK → Edicion
      nombre: str
      slug: str           único por edición
      orden: int
      created_at, updated_at

La coherencia de edición es estructural: una categoría pertenece a UNA
edición y un producto que la referencie tiene que pertenecer a la MISMA
edición. La regla se comprueba en el servicio de escritura (y no puede
expresarse con una `UniqueConstraint` de Django, que sólo abarca una tabla).
"""

from django.db import models

from core.models import BaseModel


class CategoriaProducto(BaseModel):
    """Categoría de un producto, acotada a una edición."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="categorias_producto",
        verbose_name="Edición",
    )
    nombre = models.CharField(
        max_length=120,
        verbose_name="Nombre de la categoría",
    )
    slug = models.SlugField(
        max_length=120,
        verbose_name="Identificador de la categoría",
        help_text="Identificador único dentro de la edición.",
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
    )

    class Meta:
        db_table = "marketplace_categoria_producto"
        verbose_name = "Categoría de producto"
        verbose_name_plural = "Categorías de producto"
        ordering = ["orden", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "slug"],
                name="marketplace_categoria_slug_unico_edicion",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre
