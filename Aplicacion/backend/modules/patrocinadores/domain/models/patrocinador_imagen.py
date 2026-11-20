"""`PatrocinadorImagen` — la galería ordenada de un patrocinador.

Freeze: `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (FR-06 §2.6, literal):

    PatrocinadorImagen
      patrocinador_id: UUID   FK → Patrocinador
      imagen: ImageField
      orden: int
      texto_alternativo: str
      created_at, updated_at

Reglas congeladas que este modelo respeta:

- El ORDEN canónico es `orden ASC, id ASC`: dos imágenes con el mismo `orden`
  siguen teniendo un orden determinista.
- La ruta de almacenamiento es
  `MEDIA_ROOT/patrocinadores/<patrocinador_id>/<uuid><ext>` (FR-06 §2.2). El
  nombre NUNCA es el enviado por el usuario y la extensión sale del MIME
  **detectado** y validado antes de persistir.
- La galería NO tiene `es_principal`: el logo del patrocinador ES la imagen
  de identidad, y la galería es un carrusel ordenado. FR-06 §2.6 sólo declara
  el campo `es_principal?` (con interrogación) para `ProductoImagen`; aquí la
  identidad la cubre `Patrocinador.logo`.

La imagen cuelga del patrocinador con `CASCADE`: si el patrocinador se borra,
sus imágenes se borran con él (y el servicio de media borra los ARCHIVOS,
que la base de datos no deshace).
"""

from django.db import models

from core.exceptions import MediaTipoNoPermitidoError
from core.models import BaseModel


def ruta_patrocinador_imagen(instance, filename) -> str:
    """Ruta de storage de una imagen de la galería de un patrocinador.

    Devuelve la ruta relativa precalculada por el servicio de media del
    módulo. `filename` se IGNORA a propósito: el nombre enviado por el cliente
    nunca decide la ruta (FR-06 §2.2 regla 1).

    Si la ruta no fue precalculada, la imagen no pasó por la validación de
    `core.media` y se rechaza con el código de media del catálogo público.
    """
    ruta = getattr(instance, "ruta_media_previa", None)
    if not ruta:
        raise MediaTipoNoPermitidoError()
    return ruta


class PatrocinadorImagen(BaseModel):
    """Imagen de la galería ordenada de un patrocinador."""

    patrocinador = models.ForeignKey(
        "patrocinadores.Patrocinador",
        on_delete=models.CASCADE,
        related_name="imagenes",
        verbose_name="Patrocinador",
    )
    imagen = models.ImageField(
        upload_to=ruta_patrocinador_imagen,
        verbose_name="Imagen",
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden",
    )
    texto_alternativo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Texto alternativo",
    )

    class Meta:
        db_table = "patrocinadores_patrocinador_imagen"
        verbose_name = "Imagen de patrocinador"
        verbose_name_plural = "Imágenes de patrocinador"
        ordering = ["orden", "id"]

    def __str__(self) -> str:
        return f"Imagen {self.orden} de {self.patrocinador_id}"
