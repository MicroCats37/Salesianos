# Generated manually for the audited manual-payment evidence model.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pagos", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AprobacionPagoManual",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Última actualización")),
                ("canal", models.CharField(max_length=32)),
                ("referencia", models.CharField(max_length=100)),
                ("monto", models.DecimalField(decimal_places=2, max_digits=12)),
                ("moneda", models.CharField(max_length=3)),
                ("motivo", models.TextField(max_length=1000)),
                ("estado", models.CharField(choices=[("APROBADA", "Aprobada")], default="APROBADA", max_length=20)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aprobaciones_manuales_pago", to=settings.AUTH_USER_MODEL)),
                ("orden_pago", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="aprobaciones_manuales", to="pagos.ordenpago")),
            ],
            options={"db_table": "pagos_aprobacionpagomanual", "ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="aprobacionpagomanual",
            constraint=models.UniqueConstraint(condition=models.Q(("estado", "APROBADA")), fields=("orden_pago",), name="aprobacion_manual_activa_unica_por_orden"),
        ),
        migrations.AddIndex(
            model_name="aprobacionpagomanual",
            index=models.Index(fields=["orden_pago", "estado"], name="ix_aprobmanual_orden_estado"),
        ),
        migrations.AddIndex(
            model_name="aprobacionpagomanual",
            index=models.Index(fields=["actor", "created_at"], name="ix_aprobmanual_actor_fecha"),
        ),
    ]
