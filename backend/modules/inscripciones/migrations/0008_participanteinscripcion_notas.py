"""Add notas field to ParticipanteInscripcion."""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inscripciones", "0007_historicalcategoria_historicaldisciplina_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="participanteinscripcion",
            name="notas",
            field=models.TextField(
                blank=True,
                help_text=(
                    "Notas internas del responsable sobre el participante "
                    "(alergias, observaciones, etc.)"
                ),
                null=True,
                verbose_name="Notas",
            ),
        ),
        migrations.AddField(
            model_name="historicalparticipanteinscripcion",
            name="notas",
            field=models.TextField(
                blank=True,
                help_text=(
                    "Notas internas del responsable sobre el participante "
                    "(alergias, observaciones, etc.)"
                ),
                null=True,
                verbose_name="Notas",
            ),
        ),
    ]