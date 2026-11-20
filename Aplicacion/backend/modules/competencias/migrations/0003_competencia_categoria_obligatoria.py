"""Migración ESCENIFICADA: la CATEGORÍA de la competencia pasa a OBLIGATORIA.

Change: `restore-registration-promotion-catalog-flow` · Slice: `backend-competencias`

**ESCRITA A MANO, NO GENERADA.** `makemigrations` no se puede ejecutar en este
cambio, así que esta migración reproduce EXACTAMENTE lo que declara el
modelo `Competencia` (`domain/models/competencia.py`), con los MISMOS
argumentos que usa el modelo, para que el autodetector NO lea la diferencia
como drift (aprendizaje `F-60`).

**Esta es la ETAPA 2 de las dos** (la etapa 1 es
`0002_competencia_categoria`): la columna `categoria` nació nula para poder
derivar su valor de la evidencia existente, y aquí se vuelve OBLIGATORIA.

**Se NIEGA a pasar si alguna competencia se quedó sin categoría.** No es
rigidez: es la garantía de que NINGUNA competencia del festival compite en
una categoría inventada. La decisión de qué categoría le corresponde a una
competencia heredada es de producto, y su evidencia es el cuadro: la etapa
`0002` la dejó documentada.

Dependencias:

    competencias.0002_competencia_categoria → la columna y el backfill
"""

import django.db.models.deletion
from django.db import migrations, models


def _verificar_categoria_asignada(apps, schema_editor):
    """Falla si alguna competencia se quedó SIN categoría.

    El mensaje es técnico y va al log del servidor: no es una respuesta
    HTTP.
    """
    Competencia = apps.get_model("competencias", "Competencia")

    sin_categoria = list(
        Competencia.objects.filter(categoria__isnull=True).values_list("id", flat=True)
    )
    if sin_categoria:
        raise RuntimeError(
            "No se puede hacer OBLIGATORIA `Competencia.categoria`: "
            f"{len(sin_categoria)} competencia(s) siguen sin categoría "
            "asignada. El backfill NO inventa una categoría: asígnasela a cada "
            "una (el cuadro y sus equipos son la evidencia) y vuelve a "
            "aplicar esta migración. Identificadores: "
            + ", ".join(str(identificador) for identificador in sin_categoria)
        )


class Migration(migrations.Migration):

    dependencies = [
        ("competencias", "0002_competencia_categoria"),
    ]

    operations = [
        # La puerta antes de la puerta: primero se comprueba, después se
        # aplica.
        migrations.RunPython(
            _verificar_categoria_asignada,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="competencia",
            name="categoria",
            field=models.ForeignKey(
                help_text=(
                    "La categoría (franja etaria) del torneo. Junto con la "
                    "disciplina, es la que fija la elegibilidad de los equipos "
                    "(`RN-K01`)."
                ),
                on_delete=django.db.models.deletion.PROTECT,
                related_name="competencias",
                to="salesianos_fest.categoria",
                verbose_name="Categoría",
            ),
        ),
    ]
