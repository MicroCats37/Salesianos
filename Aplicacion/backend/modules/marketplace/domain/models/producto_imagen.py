"""`ProductoImagen` — la galería ordenada de un producto.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (FR-06 §2.6, literal):

    ProductoImagen
      producto_id: UUID    FK → Producto
      imagen: ImageField
      orden: int
      texto_alternativo: str
      es_principal: bool
      created_at, updated_at

Reglas congeladas que este modelo respeta:

- El ORDEN canónico es `orden ASC, id ASC`: dos imágenes con el mismo `orden`
  siguen teniendo un orden determinista.
- La ruta de almacenamiento es `MEDIA_ROOT/productos/<producto_id>/<uuid><ext>`
  (FR-06 §2.2). El nombre NUNCA es el enviado por el usuario y la extensión
  sale del MIME **detectado** y validado antes de persistir.
- "La primera imagen es la principal" está PROHIBIDO de forma implícita: la
  imagen principal es un campo EXPLÍCITO con `UniqueConstraint` condicional
  por entidad.
"""

from django.db import models

from core.exceptions import MediaTipoNoPermitidoError
from core.models import BaseModel


def ruta_producto_imagen(instance, filename) -> str:
    """Ruta de storage de una imagen de producto.

    Devuelve la ruta relativa precalculada por el servicio de media del
    módulo. `filename` se IGNORA a propósito: el nombre enviado por el
    cliente nunca decide la ruta (FR-06 §2.2 regla 1).

    Si la ruta no fue precalculada, la imagen no pasó por la validación de
    `core.media` y se rechaza con el código de media del catálogo público.
    """
    ruta = getattr(instance, "ruta_media_previa", None)
    if not ruta:
        raise MediaTipoNoPermitidoError()
    return ruta


class ProductoImagen(BaseModel):
    """Imagen de la galería de un producto."""

    producto = models.ForeignKey(
        "marketplace.Producto",
        on_delete=models.CASCADE,
        related_name="imagenes",
        verbose_name="Producto",
    )
    imagen = models.ImageField(
        upload_to=ruta_producto_imagen,
        verbose_name="Imagen",
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
    )
    es_principal = models.BooleanField(
        default=False,
        verbose_name="Es la imagen principal",
    )
    texto_alternativo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Texto alternativo",
    )

    class Meta:
        db_table = "marketplace_producto_imagen"
        verbose_name = "Imagen de producto"
        verbose_name_plural = "Imágenes de producto"
        ordering = ["orden", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["producto"],
                condition=models.Q(es_principal=True),
                name="marketplace_imagen_principal_unica",
            ),
        ]

    def __str__(self) -> str:
        return f"Imagen {self.orden} de {self.producto_id}"
