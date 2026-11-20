"""Promociones, categorías y precio POR PERSONA del paquete.

Change: `restore-registration-promotion-catalog-flow` (2026-11-20)

Esta migración RESTITUYE los conceptos que el rebuild había omitido
(`Promocion`, `Categoria`) y devuelve al paquete su semántica COMERCIAL del
legacy: el precio es UNITARIO y el comprador declara la cantidad de
participantes, con un mínimo declarado por el paquete.

Qué hace, en orden:

1. Crea `fest_promocion` (GLOBAL: una cohorte de nacimiento es una
   propiedad de la persona, no de un evento) y `fest_categoria` (por
   EDICIÓN: es la banda competitiva con la que compite un equipo).
2. Añade a `Paquete` los conceptos `tipo`, `modo_disciplinas`,
   `cantidad_disciplinas` y `minimo_compra_inicial`. `cupos_incluidos`
   SOBREVIVE como hecho DECLARADO de la oferta y DEPRECADO: ya no gobierna
   la compra (la cantidad la declara el comprador), pero lo publica el
   espejo del frontend ya aplicado. Es la transición documentada.
3. Añade `Inscripcion.promocion` (obligatoria), `Inscripcion.fusion_promocion`
   (opcional y descriptiva) y `Equipo.categoria` (obligatoria y derivada).

ENFOQUE POR ETAPAS (columna nullable → backfill → constraint)

Los campos nuevos se crean NULLABLE, se rellenan y sólo después se
declaran NOT NULL. Es el orden que hace segura la migración sobre datos
existentes.

QUÉ SE RELLENA Y CÓMO

- `Paquete.minimo_compra_inicial` ← `Paquete.cupos_incluidos`. La cantidad
  fija que el rebuild compraba pasa a ser el MÍNIMO COMERCIAL: es la misma
  verdad de negocio con otro nombre, no una invención. `cupos_incluidos`
  conserva su valor como hecho declarado de la oferta (DEPRECADO).
- `Paquete.cantidad_disciplinas` ← el número de vínculos
  `PaqueteDisciplina` del paquete. Reproduce exactamente el comportamiento
  anterior del rebuild (se podían declarar hasta todas las disciplinas
  vinculadas al paquete).
- `Equipo.categoria` ← la categoría de la EDICIÓN cuyo rango
  `[promocion_desde, promocion_hasta]` contiene el año de la promoción de
  la inscripción. Es una DERIVACIÓN determinista.

BLOQUEOS DE DATOS (y por qué NO se inventan)

1. **Inscripciones sin promoción.** El año de cohorte de una inscripción
   existente NO se puede deducir de nada: no está en la fila ni se puede
   derivar de la disciplina. Inventar una cohorte sería fabricar el hecho
   que decide la categoría con la que compite el equipo. Si hay inscripciones
   sin promoción, la migración SE DETIENE con un mensaje explícito: el
   operador debe asignar la promoción antes de continuar.
2. **Precios de paquete que eran TOTALES.** Bajo la semántica del rebuild,
   `PaquetePrecio.monto` era el precio del PAQUETE COMPLETO (por ejemplo,
   S/ 350.00 por un paquete de 10 cupos). Bajo la semántica restaurada, el
   monto es el precio de UNA persona. La migración NO reescribe los
   precios: no puede saber si un monto guardado era un total o ya era
   unitario, y dividirlo a ciegas sería alterar un hecho comercial. Los
   precios los reconcilia el operador (el seed tampoco pisa un precio ya
   configurado).

Ninguna de las dos decisiones es un defecto de la migración: son hechos que
el backend no puede deducir. Se dejan_CONSTANTES y se documentan.
"""

import django.db.models.deletion
import uuid
from django.db import migrations, models


# ── Backfill ────────────────────────────────────────────────────────────────


def _rellenar_minimo_y_cantidad(apps, schema_editor):
    """Rellena el mínimo comercial y la cantidad de disciplinas del paquete.

    - `minimo_compra_inicial` ← `cupos_incluidos` (la verdad equivalente).
    - `cantidad_disciplinas` ← el número de vínculos del paquete (conserva
      el comportamiento anterior del rebuild).
    """
    Paquete = apps.get_model("salesianos_fest", "Paquete")
    PaqueteDisciplina = apps.get_model("salesianos_fest", "PaqueteDisciplina")

    for paquete in Paquete.objects.all():
        vinculos = PaqueteDisciplina.objects.filter(paquete=paquete).count()
        Paquete.objects.filter(pk=paquete.pk).update(
            minimo_compra_inicial=paquete.cupos_incluidos,
            cantidad_disciplinas=max(vinculos, 1),
        )


def _rellenar_categorias(apps, schema_editor):
    """Deriva la categoría de cada equipo desde la promoción de su inscripción.

    Si hay inscripciones SIN promoción, la migración se detiene: la cohorte
    de una inscripción existente no se puede deducir y el backend no puede
    inventar la banda competitiva con la que compite su equipo.
    """
    Inscripcion = apps.get_model("salesianos_fest", "Inscripcion")
    Equipo = apps.get_model("salesianos_fest", "Equipo")
    Categoria = apps.get_model("salesianos_fest", "Categoria")
    Promocion = apps.get_model("salesianos_fest", "Promocion")

    sin_promocion = Inscripcion.objects.filter(promocion_id__isnull=True)
    total_sin_promocion = sin_promocion.count()
    if total_sin_promocion:
        raise RuntimeError(
            "restore-registration-promotion-catalog-flow: hay "
            f"{total_sin_promocion} inscripción(es) sin promoción. La cohorte "
            "de una inscripción existente NO se puede deducir: hay que "
            "asignarle la promoción antes de migrar (y su categoría se "
            "deriva de ella). No se inventa ninguna categoría."
        )

    promociones = {
        promocion.id: promocion for promocion in Promocion.objects.all()
    }

    for equipo in Equipo.objects.select_related("inscripcion").all():
        inscripcion = equipo.inscripcion
        promocion = promociones.get(inscripcion.promocion_id)
        if promocion is None:
            continue
        categoria = (
            Categoria.objects.filter(
                edicion_id=inscripcion.edicion_id,
                estado="ACTIVA",
                promocion_desde__lte=promocion.anio,
                promocion_hasta__gte=promocion.anio,
            )
            .order_by("-promocion_hasta", "nombre")
            .first()
        )
        if categoria is None:
            raise RuntimeError(
                "restore-registration-promotion-catalog-flow: la promoción "
                f"{promocion.anio} de una inscripción no cae en ninguna "
                "categoría activa de su edición. Hay que sembrar el "
                "catálogo de promociones y categorías ANTES de migrar; no "
                "se inventa ninguna categoría."
            )
        Equipo.objects.filter(pk=equipo.pk).update(categoria_id=categoria.id)


# ── Migración ───────────────────────────────────────────────────────────────


class Migration(migrations.Migration):
    """Promociones, categorías y precio por persona del paquete.

    Change: `restore-registration-promotion-catalog-flow` (2026-11-20)
    """

    dependencies = [
        ("eventos", "0001_initial"),
        ("salesianos_fest", "0003_pases_derechos"),
    ]

    operations = [
        # ── Catálogo: PROMOCIÓN (GLOBAL) ─────────────────────────────────────
        migrations.CreateModel(
            name="Promocion",
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
                ("anio", models.PositiveIntegerField(verbose_name="Año")),
                ("nombre", models.CharField(max_length=100, verbose_name="Nombre")),
                (
                    "estado",
                    models.CharField(
                        choices=[("ACTIVA", "Activa"), ("INACTIVA", "Inactiva")],
                        default="ACTIVA",
                        max_length=16,
                        verbose_name="Estado",
                    ),
                ),
            ],
            options={
                "verbose_name": "Promoción",
                "verbose_name_plural": "Promociones",
                "db_table": "fest_promocion",
                "ordering": ["-anio"],
            },
        ),
        migrations.AddConstraint(
            model_name="promocion",
            constraint=models.UniqueConstraint(
                fields=("anio",),
                name="fest_promocion_anio_unico",
            ),
        ),
        # ── Catálogo: CATEGORÍA (por EDICIÓN) ───────────────────────────────
        migrations.CreateModel(
            name="Categoria",
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
                ("nombre", models.CharField(max_length=100, verbose_name="Nombre")),
                (
                    "promocion_desde",
                    models.PositiveIntegerField(
                        help_text="Año de cohorte más reciente que entra en esta categoría.",
                        verbose_name="Promoción desde",
                    ),
                ),
                (
                    "promocion_hasta",
                    models.PositiveIntegerField(
                        help_text="Año de cohorte más antiguo que entra en esta categoría.",
                        verbose_name="Promoción hasta",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[("ACTIVA", "Activa"), ("INACTIVA", "Inactiva")],
                        default="ACTIVA",
                        max_length=16,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "edicion",
                    models.ForeignKey(
                        help_text="La edición es el alcance: el catálogo no es global.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="categorias",
                        to="eventos.edicion",
                        verbose_name="Edición",
                    ),
                ),
            ],
            options={
                "verbose_name": "Categoría",
                "verbose_name_plural": "Categorías",
                "db_table": "fest_categoria",
                "ordering": ["-promocion_hasta", "nombre"],
            },
        ),
        migrations.AddConstraint(
            model_name="categoria",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("promocion_desde__lte", models.F("promocion_hasta"))
                ),
                name="fest_categoria_rango_valido",
            ),
        ),
        migrations.AddConstraint(
            model_name="categoria",
            constraint=models.UniqueConstraint(
                condition=models.Q(("estado", "ACTIVA")),
                fields=("edicion", "nombre"),
                name="fest_categoria_nombre_unico_por_edicion",
            ),
        ),
        # ── Paquete: los conceptos restaurados ──────────────────────────────
        migrations.AddField(
            model_name="paquete",
            name="tipo",
            field=models.CharField(
                choices=[
                    ("PACK", "Pack (con beneficios)"),
                    ("DISCIPLINA", "Disciplina individual"),
                ],
                default="PACK",
                help_text=(
                    "`PACK` es una oferta con beneficios; `DISCIPLINA` es la "
                    "oferta de un solo torneo."
                ),
                max_length=16,
                verbose_name="Tipo",
            ),
        ),
        migrations.AddField(
            model_name="paquete",
            name="modo_disciplinas",
            field=models.CharField(
                choices=[
                    ("FIJO", "Fijo"),
                    ("ELEGIBLE", "Elegible por el participante"),
                ],
                default="ELEGIBLE",
                help_text=(
                    "`FIJO` obliga a declarar EXACTAMENTE las disciplinas del "
                    "paquete; `ELEGIBLE` deja elegir entre ellas."
                ),
                max_length=16,
                verbose_name="Modo de disciplinas",
            ),
        ),
        migrations.AddField(
            model_name="paquete",
            name="cantidad_disciplinas",
            field=models.PositiveIntegerField(
                default=1,
                help_text="Cuántas disciplinas puede declarar la inscripción con este paquete.",
                verbose_name="Cantidad de disciplinas",
            ),
        ),
        migrations.AddField(
            model_name="paquete",
            name="minimo_compra_inicial",
            field=models.PositiveIntegerField(
                default=1,
                help_text=(
                    "Mínimo COMERCIAL de participantes en el alta. El cliente "
                    "declara la cantidad; el servidor la contrasta con este "
                    "mínimo."
                ),
                verbose_name="Mínimo de compra inicial",
            ),
        ),
        migrations.RunPython(
            _rellenar_minimo_y_cantidad,
            migrations.RunPython.noop,
            elidable=False,
        ),
        migrations.AlterField(
            model_name="paquete",
            name="cupos_incluidos",
            field=models.PositiveIntegerField(
                default=1,
                help_text=(
                    "Cupos que DECLARA la oferta del paquete. DEPRECADO: es "
                    "el hecho de catálogo que la oferta incluye, NO la "
                    "cantidad que el comprador compra. La cantidad la "
                    "declara el comprador y su suelo comercial es "
                    "`minimo_compra_inicial` (`D-CAT-01`)."
                ),
                verbose_name="Cupos incluidos",
            ),
        ),
        migrations.AddConstraint(
            model_name="paquete",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("cantidad_disciplinas__gt", 1),
                    ("tipo", "DISCIPLINA"),
                    _negated=True,
                ),
                name="fest_paquete_disciplina_unica_cantidad",
            ),
        ),
        migrations.AddConstraint(
            model_name="paquete",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("modo_disciplinas", "ELEGIBLE"),
                    ("tipo", "DISCIPLINA"),
                    _negated=True,
                ),
                name="fest_paquete_disciplina_modo_fijo",
            ),
        ),
        # ── Inscripción: PROMOCIÓN y FUSIÓN ─────────────────────────────────
        migrations.AddField(
            model_name="inscripcion",
            name="promocion",
            field=models.ForeignKey(
                help_text=(
                    "Cohorte que compra la inscripción. Es OBLIGATORIA y es "
                    "la que determina la categoría del equipo (`D-CAT-01`)."
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inscripciones",
                to="salesianos_fest.promocion",
                verbose_name="Promoción",
            ),
        ),
        migrations.AddField(
            model_name="inscripcion",
            name="fusion_promocion",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Segunda cohorte de una promoción FUSIONADA. Es "
                    "DESCRIPTIVA: no altera cupos, pago, categoría, "
                    "elegibilidad ni cuadro competitivo (`D-CAT-02`)."
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inscripciones_fusionadas",
                to="salesianos_fest.promocion",
                verbose_name="Promoción fusionada",
            ),
        ),
        # ── Equipo: CATEGORÍA (derivada) ────────────────────────────────────
        migrations.AddField(
            model_name="equipo",
            name="categoria",
            field=models.ForeignKey(
                help_text=(
                    "Banda competitiva del equipo. La DERIVA el servidor "
                    "desde la promoción de la inscripción: el cliente no la "
                    "declara (`D-CAT-05`)."
                ),
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="equipos",
                to="salesianos_fest.categoria",
                verbose_name="Categoría",
            ),
        ),
        migrations.RunPython(
            _rellenar_categorias,
            migrations.RunPython.noop,
            elidable=False,
        ),
        migrations.AlterField(
            model_name="inscripcion",
            name="promocion",
            field=models.ForeignKey(
                help_text=(
                    "Cohorte que compra la inscripción. Es OBLIGATORIA y es "
                    "la que determina la categoría del equipo (`D-CAT-01`)."
                ),
                on_delete=django.db.models.deletion.PROTECT,
                related_name="inscripciones",
                to="salesianos_fest.promocion",
                verbose_name="Promoción",
            ),
        ),
        migrations.AlterField(
            model_name="equipo",
            name="categoria",
            field=models.ForeignKey(
                help_text=(
                    "Banda competitiva del equipo. La DERIVA el servidor "
                    "desde la promoción de la inscripción: el cliente no la "
                    "declara (`D-CAT-05`)."
                ),
                on_delete=django.db.models.deletion.PROTECT,
                related_name="equipos",
                to="salesianos_fest.categoria",
                verbose_name="Categoría",
            ),
        ),
        # ── Historial de la inscripción (simple_history) ───────────────────
        migrations.AddField(
            model_name="historicalinscripcion",
            name="promocion",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                help_text=(
                    "Cohorte que compra la inscripción. Es OBLIGATORIA y es "
                    "la que determina la categoría del equipo (`D-CAT-01`)."
                ),
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="salesianos_fest.promocion",
                verbose_name="Promoción",
            ),
        ),
        migrations.AddField(
            model_name="historicalinscripcion",
            name="fusion_promocion",
            field=models.ForeignKey(
                blank=True,
                db_constraint=False,
                help_text=(
                    "Segunda cohorte de una promoción FUSIONADA. Es "
                    "DESCRIPTIVA: no altera cupos, pago, categoría, "
                    "elegibilidad ni cuadro competitivo (`D-CAT-02`)."
                ),
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="+",
                to="salesianos_fest.promocion",
                verbose_name="Promoción fusionada",
            ),
        ),
    ]
