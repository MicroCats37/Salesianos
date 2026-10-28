"""
Create the PasePrecio model — stage prices of a party pass (additive).

Same shape and same partial unique constraint as `PaquetePrecio`, so the
stage calendar and the "one ACTIVE price per stage" rule are identical in
both catalogues. The stage choices are the existing `EtapaChoices`.

No backfill: the table starts empty.
"""
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salesianos_fest", "0012_crear_pase"),
    ]

    operations = [
        migrations.CreateModel(
            name="PasePrecio",
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
                    "etapa",
                    models.CharField(
                        choices=[
                            ("PREVENTA", "Preventa"),
                            ("REGULAR", "Regular"),
                        ],
                        max_length=10,
                        verbose_name="Etapa",
                    ),
                ),
                (
                    "precio_unitario",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Precio unitario (S/)",
                    ),
                ),
                (
                    "vigente_desde",
                    models.DateField(verbose_name="Vigente desde"),
                ),
                (
                    "vigente_hasta",
                    models.DateField(
                        blank=True, null=True, verbose_name="Vigente hasta"
                    ),
                ),
                (
                    "activo",
                    models.BooleanField(default=True, verbose_name="¿Está activo?"),
                ),
                (
                    "pase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="precios",
                        to="salesianos_fest.pase",
                        verbose_name="Pase",
                    ),
                ),
            ],
            options={
                "verbose_name": "Precio de pase",
                "verbose_name_plural": "Precios de pases",
                "db_table": "pases_precios",
                "ordering": ["pase", "etapa"],
            },
        ),
        # Un solo precio ACTIVO por etapa y pase (misma regla que PaquetePrecio).
        migrations.AddConstraint(
            model_name="paseprecio",
            constraint=models.UniqueConstraint(
                condition=models.Q(("activo", True)),
                fields=("pase", "etapa"),
                name="unique_pase_precio_vigente_etapa",
            ),
        ),
    ]
