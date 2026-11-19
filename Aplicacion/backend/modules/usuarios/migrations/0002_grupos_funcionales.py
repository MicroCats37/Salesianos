"""
Crea los DOS grupos funcionales de negocio.

Freeze: `FREEZE-ID-1.0.0` · `FR-03` §1.2 · `DEC-02` · `RN-U02`.

`Normal` y `Administrador` son los dos únicos grupos funcionales del
proyecto. Prohibido crear un tercer grupo por defecto (`FR-03` §1.2); la
política de los operadores de validación sigue abierta
(`GOV-01-OPEN-04`, owner A0 + producto).

Los grupos nacen SIN permisos de Django: son marcadores de rol. La
autorización por acción la resuelve cada módulo dueño sobre su recurso, y
el grupo NO sustituye la titularidad (`FR-03` §2.1 regla 3).
"""

from django.db import migrations

GRUPOS_FUNCIONALES = ("Normal", "Administrador")


def crear_grupos_funcionales(apps, schema_editor):
    """Crea los dos grupos funcionales si no existen."""
    grupo_model = apps.get_model("auth", "Group")
    for nombre in GRUPOS_FUNCIONALES:
        grupo_model.objects.get_or_create(name=nombre)


def eliminar_grupos_funcionales(apps, schema_editor):
    """Elimina los grupos funcionales creados por esta migración."""
    grupo_model = apps.get_model("auth", "Group")
    grupo_model.objects.filter(name__in=GRUPOS_FUNCIONALES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            crear_grupos_funcionales,
            eliminar_grupos_funcionales,
        ),
    ]
