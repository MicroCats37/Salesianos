"""
Rename the AsignacionCupo index (inscripcion, estado).

The index name created in migration 0010 exceeded the 30 character limit of
Django (models.E034), which made every management command fail:

    salesianos_fest.AsignacionCupo: (models.E034) The index name
    'idx_asign_cupo_inscripcion_estado' cannot be longer than 30 characters.

The index keeps the same columns; only its name changes.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("salesianos_fest", "0010_asignacioncupo_constraint_compra_and_indexes"),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="asignacioncupo",
            name="idx_asign_cupo_inscripcion_estado",
        ),
        migrations.AddIndex(
            model_name="asignacioncupo",
            index=models.Index(
                fields=["inscripcion", "estado"],
                name="idx_asign_cupo_insc_estado",
            ),
        ),
    ]
