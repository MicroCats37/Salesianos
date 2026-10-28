"""
Create the Pase model — the independent party-pass catalogue (additive).

The pass catalogue is PARALLEL to the sports catalogue: `Paquete` is NOT
altered and `Paquete.tipo` does NOT gain a `PASE` value. The pass carries no
sports semantics (no disciplines, no teams, no package benefits).

No backfill: the table starts empty. The rollout is driven by
`PASES_FIESTA_ENABLED` plus the `activo` flag of each pass.
"""
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eventos", "0001_initial"),
        ("salesianos_fest", "0011_rename_asignacioncupo_inscripcion_index"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pase",
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
                    models.CharField(max_length=200, verbose_name="Nombre del pase"),
                ),
                (
                    "descripcion",
                    models.TextField(
                        blank=True, default="", verbose_name="Descripción"
                    ),
                ),
                (
                    "cantidad_maxima",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Cantidad máxima"
                    ),
                ),
                (
                    "activo",
                    models.BooleanField(default=True, verbose_name="¿Está activo?"),
                ),
                (
                    "evento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pases",
                        to="eventos.evento",
                        verbose_name="Evento",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pase",
                "verbose_name_plural": "Pases",
                "db_table": "pases",
                "ordering": ["evento", "nombre"],
            },
        ),
        # Un pase se identifica por su nombre dentro del evento.
        migrations.AddConstraint(
            model_name="pase",
            constraint=models.UniqueConstraint(
                fields=("evento", "nombre"), name="unique_pase_evento_nombre"
            ),
        ),
    ]
