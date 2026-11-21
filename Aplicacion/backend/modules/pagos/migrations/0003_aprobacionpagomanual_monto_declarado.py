# Generated manually for the audited DECLARED amount of a manual payment.
#
# `monto_declarado` es INFORMATIVO y AUDITADO: NO toca el total canónico de
# la orden (`OrdenPago.monto`), ni el estado del pago, ni el de la compra.
# La columna es NULLABLE con default NULL para que las aprobaciones
# anteriores (las del Marketplace y las del flujo público) conserven su
# verdad: "no declarado".

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pagos", "0002_aprobacion_pago_manual"),
    ]

    operations = [
        migrations.AddField(
            model_name="aprobacionpagomanual",
            name="monto_declarado",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    "Importe DECLARADO por el administrador. Es INFORMATIVO y "
                    "AUDITADO: no altera el total canónico de la orden ni el "
                    "estado del pago. Vacío significa 'no declarado'."
                ),
                max_digits=12,
                null=True,
                verbose_name="Monto declarado",
            ),
        ),
    ]
