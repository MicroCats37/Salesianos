# Commerce-refactor-clean-rebuild Batch 1:
# Step 1: RenameField handles column + field name: orden_pago_fk -> orden_pago
# Step 2: AlterField handles related_name="+" (suppresses reverse ORM accessor)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("commerce", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="compra",
            old_name="orden_pago_fk",
            new_name="orden_pago",
        ),
        migrations.AlterField(
            model_name="compra",
            name="orden_pago",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="pagos.ordenpago",
                verbose_name="Orden de pago",
            ),
        ),
    ]
