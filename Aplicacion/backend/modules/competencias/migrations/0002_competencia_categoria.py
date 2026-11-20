"""Migración ESCENIFICADA: la CATEGORÍA de la competencia.

Change: `restore-registration-promotion-catalog-flow` · Slice: `backend-competencias`

**ESCRITA A MANO, NO GENERADA.** `makemigrations` no se puede ejecutar en este
cambio, así que esta migración reproduce EXACTAMENTE lo que declara el
modelo `Competencia` (`domain/models/competencia.py`), con los MISMOS
argumentos que usa el modelo, para que el autodetector NO lea la diferencia
como drift (aprendizaje `F-60`).

**Es una migración en DOS ETAPAS a propósito:**

1. Esta etapa (`0002`) DECLARA la columna `categoria` NULA y hace el
   backfill DERIVADO de la evidencia que ya existe: los equipos que ya están
   en el cuadro. NUNCA inventa una categoría.
2. La etapa siguiente (`0003`) la vuelve OBLIGATORIA, y se niega a pasar si
   alguna competencia se quedó sin categoría.

**El backfill NO adivina.** La categoría de una competencia se deriva de los
equipos que ya la integran: si TODOS coinciden en la MISMA categoría, esa es
la categoría de la competencia. Si no hay equipos, si sus categorías NO
coinciden o si alguno no tiene categoría asignada, la competencia se queda
SIN categoría y la migración lo REPORTA: decidirlo es una decisión de
producto, no del backfill.

Dependencias:

    competencias.0001_initial              → `Competencia`, `CompetenciaEquipo`
    salesianos_fest.0004_promocion_categoria_precio_por_persona
                                           → `Categoria` (el dueño)

**La dependencia con `salesianos_fest` es OBLIGATORIA y es un contrato entre
las dos ramas paralelas**: el dueño introduce `salesianos_fest.Categoria` en
`0004_promocion_categoria_precio_por_persona` (que también crea
`fest_promocion` y deja `Equipo.categoria` obligatoria y derivada). Si el
dueño renombra su migración, esta dependencia se ajusta en una línea.
"""

import logging

import django.db.models.deletion
import django.db.models.functions.text
from django.db import migrations, models

#: Logger del backfill: los BLOQUEOS se reportan aquí, nunca en una respuesta
#: HTTP (una migración no es una frontera pública).
LOGGER = logging.getLogger("migraciones.competencias")


def _asignar_categoria_por_equipos(apps, schema_editor):
    """Deriva la categoría de cada competencia de los equipos de su cuadro.

    La evidencia es la ÚNICA admitida: los equipos ya incorporados. Una
    competencia sin equipos, con equipos de categorías distintas o con
    equipos sin categoría NO recibe ninguna: se reporta como BLOQUEO.
    """
    Competencia = apps.get_model("competencias", "Competencia")
    CompetenciaEquipo = apps.get_model("competencias", "CompetenciaEquipo")
    Equipo = apps.get_model("salesianos_fest", "Equipo")

    bloqueos = []
    resueltas = 0

    for competencia in Competencia.objects.filter(categoria__isnull=True).iterator():
        equipo_ids = list(
            CompetenciaEquipo.objects.filter(competencia_id=competencia.id).values_list(
                "equipo_id",
                flat=True,
            )
        )
        categorias = set(
            Equipo.objects.filter(id__in=equipo_ids)
            .exclude(categoria__isnull=True)
            .values_list("categoria_id", flat=True)
        )

        if len(categorias) == 1:
            competencia.categoria_id = categorias.pop()
            competencia.save(update_fields=["categoria"])
            resueltas += 1
            continue

        if not equipo_ids:
            motivo = "sin equipos en el cuadro"
        elif not categorias:
            motivo = "equipos sin categoría asignada"
        else:
            motivo = f"{len(categorias)} categorías distintas en el cuadro"
        bloqueos.append((str(competencia.id), motivo))

    if bloqueos:
        # El backfill NO decide: deja la columna nula y lo dice. La etapa
        # `0003` es la que se niega a dejar la categoría sin asignar.
        LOGGER.warning(
            "Backfill de `Competencia.categoria`: %s competencia(s) derivadas y "
            "%s competencia(s) SIN categoría asignada. Es una decisión de "
            "producto: complétalas antes de aplicar "
            "`0003_competencia_categoria_obligatoria`.",
            resueltas,
            len(bloqueos),
        )
        for identificador, motivo in bloqueos:
            LOGGER.warning("  - %s: %s", identificador, motivo)
    else:
        LOGGER.info(
            "Backfill de `Competencia.categoria`: %s competencia(s) derivadas.",
            resueltas,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("competencias", "0001_initial"),
        ("salesianos_fest", "0004_promocion_categoria_precio_por_persona"),
    ]

    operations = [
        # ── Etapa 1: la columna nace NULA ────────────────────────────────────
        migrations.AddField(
            model_name="competencia",
            name="categoria",
            field=models.ForeignKey(
                help_text=(
                    "La categoría (franja etaria) del torneo. Junto con la "
                    "disciplina, es la que fija la elegibilidad de los equipos "
                    "(`RN-K01`)."
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="competencias",
                to="salesianos_fest.categoria",
                verbose_name="Categoría",
            ),
        ),
        migrations.RunPython(
            _asignar_categoria_por_equipos,
            reverse_code=migrations.RunPython.noop,
        ),
        # ── La identidad pasa de tres partes a cuatro ───────────────────────
        migrations.RemoveConstraint(
            model_name="competencia",
            name="competencia_identidad_unica_por_edicion_disciplina",
        ),
        migrations.AddConstraint(
            model_name="competencia",
            constraint=models.UniqueConstraint(
                models.F("edicion"),
                models.F("disciplina"),
                models.F("categoria"),
                django.db.models.functions.text.Lower("nombre"),
                name="competencia_identidad_unica_por_edicion_disciplina_categoria",
            ),
        ),
        # ── El índice que acompaña al filtro por categoría ──────────────────
        migrations.AddIndex(
            model_name="competencia",
            index=models.Index(
                fields=["edicion", "categoria", "estado", "fecha"],
                name="ix_cmp_edi_cat_est_fecha",
            ),
        ),
    ]
