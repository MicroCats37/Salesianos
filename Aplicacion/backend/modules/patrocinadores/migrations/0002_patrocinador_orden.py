from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("patrocinadores", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="patrocinador",
            name="orden",
            field=models.PositiveIntegerField(default=0, verbose_name="Orden del banner"),
        ),
    ]
