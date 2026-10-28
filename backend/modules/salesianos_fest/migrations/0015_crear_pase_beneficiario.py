"""
Create the PaseBeneficiario model — the nominative entitlement of a pass (additive).

One row = one immutable slot of one batch held by one Persona. The three
constraints are the guarantees the database itself enforces:

- unique (compra_pase, slot) — UNCONDITIONAL: a revoked slot stays consumed.
- unique (compra_pase, persona) — UNCONDITIONAL: a person is never reused
  inside the same batch.
- partial unique (evento, persona) WHERE estado=ACTIVA — at most one active
  pass per person per event, across all purchases.

No backfill: the table starts empty.
"""
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eventos", "0001_initial"),
        ("salesianos_fest", "0014_crear_compra_pase"),
        ("usuarios", "0003_remove_historicalpersona_acepto_aptitud_fisica_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="PaseBeneficiario",
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
                    "slot",
                    models.PositiveIntegerField(verbose_name="Slot"),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("ACTIVA", "Activa"),
                            ("REVOCADA", "Revocada"),
                        ],
                        default="ACTIVA",
                        max_length=15,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "asignado_en",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Fecha de asignación"
                    ),
                ),
                (
                    "revocado_en",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Fecha de revocación",
                    ),
                ),
                (
                    "motivo_revocacion",
                    models.TextField(
                        blank=True, null=True, verbose_name="Motivo de revocación"
                    ),
                ),
                (
                    "asignado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pases_asignados",
                        to="usuarios.usuario",
                        verbose_name="Asignado por",
                    ),
                ),
                (
                    "compra_pase",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="beneficiarios",
                        to="salesianos_fest.comprapase",
                        verbose_name="Compra de pases",
                    ),
                ),
                (
                    "evento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="beneficiarios_pase",
                        to="eventos.evento",
                        verbose_name="Evento",
                    ),
                ),
                (
                    "persona",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pases_beneficiario",
                        to="usuarios.persona",
                        verbose_name="Beneficiario",
                    ),
                ),
                (
                    "revocado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pases_revocados",
                        to="usuarios.usuario",
                        verbose_name="Revocado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Beneficiario de pase",
                "verbose_name_plural": "Beneficiarios de pase",
                "db_table": "pases_beneficiarios",
                "ordering": ["compra_pase", "slot"],
                "indexes": [
                    models.Index(
                        fields=["persona", "estado"],
                        name="idx_pase_ben_persona_estado",
                    ),
                    models.Index(
                        fields=["compra_pase", "estado"],
                        name="idx_pase_ben_compra_estado",
                    ),
                ],
            },
        ),
        # El slot es INMUTABLE: un slot revocado queda consumido para siempre
        # y no puede volver a entregarse a otra persona.
        migrations.AddConstraint(
            model_name="pasebeneficiario",
            constraint=models.UniqueConstraint(
                fields=("compra_pase", "slot"),
                name="unique_pase_beneficiario_slot",
            ),
        ),
        # La misma persona no puede reutilizarse dentro del mismo lote, ni
        # siquiera después de una revocación (un pase pagado no se transfiere).
        migrations.AddConstraint(
            model_name="pasebeneficiario",
            constraint=models.UniqueConstraint(
                fields=("compra_pase", "persona"),
                name="unique_pase_beneficiario_persona",
            ),
        ),
        # Como máximo un pase ACTIVO por persona y evento, entre todas las
        # compras.
        migrations.AddConstraint(
            model_name="pasebeneficiario",
            constraint=models.UniqueConstraint(
                condition=models.Q(("estado", "ACTIVA")),
                fields=("evento", "persona"),
                name="unique_activa_pase_beneficiario_evento",
            ),
        ),
    ]
