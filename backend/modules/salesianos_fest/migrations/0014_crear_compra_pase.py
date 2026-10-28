"""
Create the CompraPase model — commercial line of a party-pass purchase (additive).

Mirrors `CompraInscripcion` (the sports composition) but for the independent
party-pass catalogue. The model carries the frozen price snapshot and the
denormalised event scope; the commercial state lives in `Compra.estado`
(single source of truth — no duplicated state).

No backfill: the table starts empty.
"""
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commerce", "0001_initial"),
        ("eventos", "0001_initial"),
        ("salesianos_fest", "0013_crear_pase_precio"),
    ]

    operations = [
        migrations.CreateModel(
            name="CompraPase",
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
                    "cantidad",
                    models.PositiveIntegerField(verbose_name="Cantidad de pases"),
                ),
                (
                    "precio_unitario",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Precio unitario snapshot",
                    ),
                ),
                (
                    "total",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=10,
                        verbose_name="Total snapshot",
                    ),
                ),
                (
                    "compra",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compra_pase",
                        to="commerce.compra",
                        verbose_name="Compra generica",
                    ),
                ),
                (
                    "evento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compras_pase",
                        to="eventos.evento",
                        verbose_name="Evento",
                    ),
                ),
                (
                    "pase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="compras_pase",
                        to="salesianos_fest.pase",
                        verbose_name="Pase",
                    ),
                ),
            ],
            options={
                "verbose_name": "Compra Pase",
                "verbose_name_plural": "Compras Pase",
                "db_table": "salesianos_fest_compra_pase",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["evento"],
                        name="idx_compra_pase_evento",
                    ),
                    models.Index(
                        fields=["pase", "created_at"],
                        name="idx_compra_pase_pase",
                    ),
                ],
            },
        ),
        # Una compra tiene como máximo una línea de pase.
        migrations.AddConstraint(
            model_name="comprapase",
            constraint=models.UniqueConstraint(
                fields=("compra",), name="unique_compra_por_pase"
            ),
        ),
    ]
