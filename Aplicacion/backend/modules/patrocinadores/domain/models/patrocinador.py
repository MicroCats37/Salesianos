"""`Patrocinador` — la ficha de un patrocinador, con logo y galería.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-06-media.md`
Contract: `contract/django-app-architecture-contract.md` §4.2, §6

Contrato de datos (plan `funcional/03` §1 y §4, ADM-21):

    Patrocinador
      id: UUID             (pk)
      edicion_id: UUID      FK → Edicion   (PROTECT)
      nombre: str
      slug: str            único por edición
      descripcion: str
      sitio_web: str       (opcional)
      visible: bool        visibilidad pública (ADM-21)
      logo: ImageField     imagen única de identidad (opcional)
      created_at, updated_at

Reglas congeladas que este modelo respeta:

- **Alcance de EDICIÓN** (FR-02 §3 · RN-E01): el patrocinador cuelga de una
  edición y su galería cuelga de él. El cliente NUNCA elige la edición.
- **Ruta de almacenamiento** (FR-06 §2.2):
  `MEDIA_ROOT/patrocinadores/<patrocinador_id>/<uuid><ext>`. El nombre NUNCA
  es el enviado por el usuario y la extensión sale del MIME **detectado**,
  validado antes de persistir.
- **Visibilidad** (ADM-21): un patrocinador invisible no se expone al
  consumo público. Es un hecho del propio patrocinador, no una configuración
  de despliegue.
- **SIN FINANZAS.** Este modelo NO declara aportaciones, comisiones, pagos,
  facturas ni ningún hecho económico o contable: ADM-21 lo prohíbe mientras no
  sea requisito, y el plan lo confirma (`funcional/01` §`patrocinadores`:
  "Ventas o facturación de terceros (no pedidas)").

Sobre `logo`: es la imagen ÚNICA de identidad. No tiene `es_principal` porque
NO es una galería: la galería es `PatrocinadorImagen` y su orden es explícito
(FR-06 §2.6).
"""

from django.db import models

from core.exceptions import MediaTipoNoPermitidoError
from core.models import BaseModel


def ruta_patrocinador_logo(instance, filename) -> str:
    """Ruta de storage del logo de un patrocinador.

    Devuelve la ruta relativa precalculada por el servicio de media del
    módulo. `filename` se IGNORA a propósito: el nombre enviado por el cliente
    nunca decide la ruta (FR-06 §2.2 regla 1).

    Si la ruta no fue precalculada, el archivo no pasó por la validación de
    `core.media` y se rechaza con el código de media del catálogo público.
    """
    ruta = getattr(instance, "ruta_media_previa", None)
    if not ruta:
        raise MediaTipoNoPermitidoError()
    return ruta


class Patrocinador(BaseModel):
    """Patrocinador del evento, acotado a una edición."""

    edicion = models.ForeignKey(
        "eventos.Edicion",
        on_delete=models.PROTECT,
        related_name="patrocinadores",
        verbose_name="Edición",
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del patrocinador",
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name="Identificador del patrocinador",
        help_text="Identificador único dentro de la edición.",
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción",
    )
    sitio_web = models.URLField(
        max_length=300,
        blank=True,
        verbose_name="Sitio web",
    )
    visible = models.BooleanField(
        default=True,
        verbose_name="Visible públicamente",
        help_text=(
            "Un patrocinador invisible no se expone al consumo público "
            "(ADM-21)."
        ),
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden del banner",
        help_text="Posición persistida en el carrusel público.",
    )
    logo = models.ImageField(
        upload_to=ruta_patrocinador_logo,
        blank=True,
        verbose_name="Logo",
        help_text="Imagen única de identidad del patrocinador.",
    )

    class Meta:
        db_table = "patrocinadores_patrocinador"
        verbose_name = "Patrocinador"
        verbose_name_plural = "Patrocinadores"
        ordering = ["orden", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["edicion", "slug"],
                name="patrocinadores_patrocinador_slug_unico_edicion",
            ),
        ]

    def __str__(self) -> str:
        return self.nombre
