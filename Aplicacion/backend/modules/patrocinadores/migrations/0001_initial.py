"""Migración inicial del módulo `patrocinadores`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/domains/DOM-08-patrocinadores-logo-galeria.md`

Contiene:

- `Patrocinador` — la ficha con alcance de edición, logo y visibilidad.
- `PatrocinadorImagen` — la galería ordenada.

Depende de `eventos.0001_initial` (la FK de alcance) y es REVERSIBLE: el
`migrate patrocinadores zero` deshace las dos tablas y sus restricciones.

SIN FINANZAS: esta migración NO declara aportaciones, comisiones, pagos,
facturas ni contabilidad de terceros (ADM-21, `funcional/01`).
"""

import django.db.models.deletion
import modules.patrocinadores.domain.models.patrocinador
import modules.patrocinadores.domain.models.patrocinador_imagen
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("eventos", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Patrocinador",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de creación"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Última actualización"
                    ),
                ),
                (
                    "nombre",
                    models.CharField(
                        max_length=200, verbose_name="Nombre del patrocinador"
                    ),
                ),
                (
                    "slug",
                    models.SlugField(
                        help_text="Identificador único dentro de la edición.",
                        max_length=200,
                        verbose_name="Identificador del patrocinador",
                    ),
                ),
                (
                    "descripcion",
                    models.TextField(blank=True, verbose_name="Descripción"),
                ),
                (
                    "sitio_web",
                    models.URLField(
                        blank=True, max_length=300, verbose_name="Sitio web"
                    ),
                ),
                (
                    "visible",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Un patrocinador invisible no se expone al consumo "
                            "público (ADM-21)."
                        ),
                        verbose_name="Visible públicamente",
                    ),
                ),
                (
                    "logo",
                    models.ImageField(
                        blank=True,
                        help_text="Imagen única de identidad del patrocinador.",
                        upload_to=modules.patrocinadores.domain.models.patrocinador.ruta_patrocinador_logo,
                        verbose_name="Logo",
                    ),
                ),
                (
                    "edicion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="patrocinadores",
                        to="eventos.edicion",
                        verbose_name="Edición",
                    ),
                ),
            ],
            options={
                "verbose_name": "Patrocinador",
                "verbose_name_plural": "Patrocinadores",
                "db_table": "patrocinadores_patrocinador",
                "ordering": ["nombre", "id"],
            },
        ),
        migrations.CreateModel(
            name="PatrocinadorImagen",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de creación"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="Última actualización"
                    ),
                ),
                (
                    "imagen",
                    models.ImageField(
                        upload_to=modules.patrocinadores.domain.models.patrocinador_imagen.ruta_patrocinador_imagen,
                        verbose_name="Imagen",
                    ),
                ),
                ("orden", models.PositiveIntegerField(default=0, verbose_name="Orden")),
                (
                    "texto_alternativo",
                    models.CharField(
                        blank=True, max_length=200, verbose_name="Texto alternativo"
                    ),
                ),
                (
                    "patrocinador",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="imagenes",
                        to="patrocinadores.patrocinador",
                        verbose_name="Patrocinador",
                    ),
                ),
            ],
            options={
                "verbose_name": "Imagen de patrocinador",
                "verbose_name_plural": "Imágenes de patrocinador",
                "db_table": "patrocinadores_patrocinador_imagen",
                "ordering": ["orden", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="patrocinador",
            constraint=models.UniqueConstraint(
                fields=("edicion", "slug"),
                name="patrocinadores_patrocinador_slug_unico_edicion",
            ),
        ),
    ]
