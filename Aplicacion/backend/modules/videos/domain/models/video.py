"""`Video` — un video de la sala de proyección.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (APROBADO — sin añadidos):

    Video
      id: UUID             (pk)
      titulo: str
      descripcion: str
      url: str
      created_at, updated_at

`id`, `created_at` y `updated_at` los hereda de `core.models.BaseModel`: una
fila tiene EXACTAMENTE seis columnas. **NO** hay `es_publico` (todos los
videos son públicos por definición), **NO** hay columna de proveedor, **NO**
hay subidas, **NO** hay categorías, **NO** hay clave foránea a la edición y
**NO** hay columna de bloqueo optimista.

La URL es un `URLField` restringido a `http` y `https`. El validador por
defecto de Django acepta también `ftp`/`ftps`: la lista explícita de esquemas
es la que hace que `javascript:`, `data:` y `ftp:` queden FUERA del dominio.

El validador del MODELO documenta el invariante (y lo aplica el formulario del
admin); la comprobación que el SERVIDOR ejecuta al escribir es la del servicio
de dominio (`domain/services/core/video_service.py`), porque el ORM de Django
no valida en `create()`.
"""

from django.core.validators import URLValidator
from django.db import models

from core.models import BaseModel


class Video(BaseModel):
    """Un video público de la sala de proyección."""

    titulo = models.CharField(
        max_length=200,
        verbose_name="Título",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
    )
    url = models.URLField(
        max_length=500,
        verbose_name="URL del video",
        help_text=(
            "Dirección pública del video. Sólo se admiten http y https: "
            "el servidor rechaza cualquier otro esquema."
        ),
        validators=[URLValidator(schemes=["http", "https"])],
    )

    class Meta:
        db_table = "videos_video"
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.titulo
