"""Migración inicial del módulo `competencias`.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

**ESCRITA A MANO, NO GENERADA.** La verificación en runtime está diferida por
instrucción explícita del usuario (`makemigrations` no se puede ejecutar), así
que esta migración reproduce EXACTAMENTE lo que declaran los modelos del
módulo.

Reglas que esta migración respeta (aprendizaje `F-60`):

- las expresiones de una restricción se escriben con los MISMOS argumentos
  que usa el modelo, para que la comparación de restricciones del
  autodetector NO las lea como distintas;
- los `Q` con varios argumentos se escriben con ARGUMENTOS NOMBRADOS: un `Q`
  escrito con tuplas posicionales conserva el ORDEN de las tuplas, mientras
  que el `Q` del modelo ORDENA sus argumentos nombrados. Con dos o más
  argumentos, ambas formas NO son iguales y el drift no se estabiliza;
- el `Lower` se importa por su ruta COMPLETA (`django.db.models.functions.text`),
  que es la que serializa el autodetector.

Dependencias (grafo de migraciones del objetivo):

    eventos.0001            → `Edicion`
    salesianos_fest.0003    → `Disciplina`, `Equipo`
    usuarios.0002           → `Usuario` (actor de la auditoría)
"""

import django.db.models.deletion
import django.db.models.functions.text
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("eventos", "0001_initial"),
        ("salesianos_fest", "0003_pases_derechos"),
        ("usuarios", "0002_grupos_funcionales"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Competencia",
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
                (
                    "version",
                    models.PositiveIntegerField(
                        default=1,
                        help_text=(
                            "Contador de bloqueo optimista. El cliente envía la "
                            "versión que conoce y el servidor la compara antes "
                            "de escribir."
                        ),
                        verbose_name="Versión",
                    ),
                ),
                (
                    "edicion",
                    models.ForeignKey(
                        help_text="La edición es el alcance: una competencia no es global.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="competencias",
                        to="eventos.edicion",
                        verbose_name="Edición",
                    ),
                ),
                (
                    "disciplina",
                    models.ForeignKey(
                        help_text=(
                            "La disciplina del torneo. Es la que fija la "
                            "elegibilidad de los equipos (`RN-K01`)."
                        ),
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="competencias",
                        to="salesianos_fest.disciplina",
                        verbose_name="Disciplina",
                    ),
                ),
                (
                    "nombre",
                    models.CharField(max_length=200, verbose_name="Nombre"),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("PLANIFICADA", "Planificada"),
                            ("EN_CURSO", "En curso"),
                            ("FINALIZADA", "Finalizada"),
                            ("CANCELADA", "Cancelada"),
                        ],
                        default="PLANIFICADA",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "fecha",
                    models.DateField(
                        help_text=(
                            "Día de la competencia. El horario de los encuentros "
                            "vive dentro de este día."
                        ),
                        verbose_name="Fecha",
                    ),
                ),
            ],
            options={
                "db_table": "competencia_competencias",
                "verbose_name": "Competencia",
                "verbose_name_plural": "Competencias",
                "ordering": ["-fecha", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="Ronda",
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
                (
                    "version",
                    models.PositiveIntegerField(
                        default=1,
                        help_text=(
                            "Contador de bloqueo optimista. El cliente envía la "
                            "versión que conoce y el servidor la compara antes "
                            "de escribir."
                        ),
                        verbose_name="Versión",
                    ),
                ),
                (
                    "competencia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="rondas",
                        to="competencias.competencia",
                        verbose_name="Competencia",
                    ),
                ),
                (
                    "etiqueta",
                    models.CharField(
                        help_text=(
                            "Nombre de la ronda: 'Cuartos de final', 'Final', ..."
                        ),
                        max_length=80,
                        verbose_name="Etiqueta",
                    ),
                ),
                (
                    "orden",
                    models.PositiveIntegerField(
                        help_text=(
                            "Orden de la ronda dentro del cuadro. Las rondas "
                            "avanzan hacia él."
                        ),
                        verbose_name="Orden",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[("ACTIVA", "Activa"), ("INVALIDADA", "Invalidada")],
                        default="ACTIVA",
                        max_length=16,
                        verbose_name="Estado",
                    ),
                ),
            ],
            options={
                "db_table": "competencia_rondas",
                "verbose_name": "Ronda",
                "verbose_name_plural": "Rondas",
                "ordering": ["competencia_id", "orden"],
            },
        ),
        migrations.CreateModel(
            name="CompetenciaEquipo",
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
                (
                    "version",
                    models.PositiveIntegerField(
                        default=1,
                        help_text=(
                            "Contador de bloqueo optimista. El cliente envía la "
                            "versión que conoce y el servidor la compara antes "
                            "de escribir."
                        ),
                        verbose_name="Versión",
                    ),
                ),
                (
                    "competencia",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="equipos",
                        to="competencias.competencia",
                        verbose_name="Competencia",
                    ),
                ),
                (
                    "equipo",
                    models.ForeignKey(
                        help_text=(
                            "Equipo de inscripción. Su estado, su edición y su "
                            "disciplina los decide `modules.salesianos_fest`, no "
                            "este módulo."
                        ),
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="participaciones_en_competencias",
                        to="salesianos_fest.equipo",
                        verbose_name="Equipo",
                    ),
                ),
                (
                    "orden",
                    models.PositiveIntegerField(
                        help_text=(
                            "Semilla del cuadro. La elige el administrador: el "
                            "sistema nunca."
                        ),
                        verbose_name="Orden",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[("ACTIVO", "Activo"), ("RETIRADO", "Retirado")],
                        default="ACTIVO",
                        max_length=16,
                        verbose_name="Estado",
                    ),
                ),
            ],
            options={
                "db_table": "competencia_equipos",
                "verbose_name": "Equipo de competencia",
                "verbose_name_plural": "Equipos de competencia",
                "ordering": ["competencia_id", "orden"],
            },
        ),
        migrations.CreateModel(
            name="Encuentro",
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
                (
                    "version",
                    models.PositiveIntegerField(
                        default=1,
                        help_text=(
                            "Contador de bloqueo optimista. El cliente envía la "
                            "versión que conoce y el servidor la compara antes "
                            "de escribir."
                        ),
                        verbose_name="Versión",
                    ),
                ),
                (
                    "ronda",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="encuentros",
                        to="competencias.ronda",
                        verbose_name="Ronda",
                    ),
                ),
                (
                    "orden",
                    models.PositiveIntegerField(
                        help_text="Orden del encuentro dentro de su ronda.",
                        verbose_name="Orden",
                    ),
                ),
                (
                    "participante_1",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="encuentros_como_participante_1",
                        to="competencias.competenciaequipo",
                        verbose_name="Participante 1",
                    ),
                ),
                (
                    "participante_2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="encuentros_como_participante_2",
                        to="competencias.competenciaequipo",
                        verbose_name="Participante 2",
                    ),
                ),
                (
                    "inicio_programado",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Inicio programado",
                    ),
                ),
                (
                    "fin_programado",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Fin programado",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("BORRADOR", "Borrador"),
                            ("PROGRAMADO", "Programado"),
                            ("EN_CURSO", "En curso"),
                            ("FINALIZADO", "Finalizado"),
                            ("CANCELADO", "Cancelado"),
                        ],
                        default="BORRADOR",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "es_bye",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Bye MANUAL: lo decide el administrador y exige "
                            "exactamente un equipo. El sistema NUNCA inventa un bye."
                        ),
                        verbose_name="¿Es pase libre (bye)?",
                    ),
                ),
                (
                    "puntaje_1",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Puntaje participante 1",
                    ),
                ),
                (
                    "puntaje_2",
                    models.PositiveIntegerField(
                        blank=True,
                        null=True,
                        verbose_name="Puntaje participante 2",
                    ),
                ),
                (
                    "marcador_detalle",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text=(
                            "Marcador opcional e informativo: nunca decide el ganador."
                        ),
                        max_length=500,
                        verbose_name="Detalle del marcador",
                    ),
                ),
                (
                    "ganador",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "Ganador AUTORITATIVO: siempre ocupa uno de los dos slots."
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="encuentros_ganados",
                        to="competencias.competenciaequipo",
                        verbose_name="Ganador",
                    ),
                ),
                (
                    "siguiente_encuentro",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="encuentros_siguientes",
                        to="competencias.encuentro",
                        verbose_name="Siguiente encuentro",
                    ),
                ),
                (
                    "slot_destino",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PARTICIPANTE_1", "Participante 1"),
                            ("PARTICIPANTE_2", "Participante 2"),
                        ],
                        help_text=(
                            "Slot del siguiente encuentro que recibe al ganador propagado."
                        ),
                        max_length=20,
                        null=True,
                        verbose_name="Slot de destino",
                    ),
                ),
                (
                    "ganador_propagado",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "Ganador que el sistema propagó a este encuentro. "
                            "Distingue una colocación propagada de una manual: la "
                            "corrección nunca pisa la manual."
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="encuentros_con_propagacion",
                        to="competencias.competenciaequipo",
                        verbose_name="Ganador propagado",
                    ),
                ),
                (
                    "iniciado_en",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Iniciado en",
                    ),
                ),
                (
                    "finalizado_en",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Finalizado en",
                    ),
                ),
            ],
            options={
                "db_table": "competencia_encuentros",
                "verbose_name": "Encuentro",
                "verbose_name_plural": "Encuentros",
                "ordering": ["ronda_id", "orden"],
            },
        ),
        migrations.CreateModel(
            name="AuditoriaOperacion",
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
                (
                    "accion",
                    models.CharField(
                        choices=[
                            ("CREACION_COMPETENCIA", "Creación de competencia"),
                            ("INCORPORACION_EQUIPO", "Incorporación de equipo"),
                            ("EDICION_EQUIPO", "Edición de equipo"),
                            ("CREACION_RONDA", "Creación de ronda"),
                            ("CREACION_ENCUENTRO", "Creación de encuentro"),
                            ("PARTICIPANTES", "Cambio de participantes"),
                            ("ENLACE", "Cambio de enlace"),
                            ("PROGRAMACION", "Programación de horario"),
                            ("BYE", "Asignación de bye"),
                            ("ESTADO", "Cambio de estado del encuentro"),
                            ("CANCELACION", "Cancelación de encuentro"),
                            ("RESULTADO", "Registro de resultado"),
                            ("AVANCE", "Avance confirmado"),
                            ("CORRECCION", "Corrección de resultado"),
                        ],
                        max_length=40,
                        verbose_name="Acción",
                    ),
                ),
                (
                    "detalle",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Antes/después de la operación. Contexto TÉCNICO del "
                            "servidor: nunca se publica en una respuesta HTTP."
                        ),
                        verbose_name="Detalle",
                    ),
                ),
                (
                    "motivo",
                    models.TextField(
                        help_text="Motivo auditado de la operación (5..500 caracteres).",
                        verbose_name="Motivo",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        help_text=(
                            "Cuenta que ejecutó la operación. Vacío si no hubo actor "
                            "autenticado."
                        ),
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="auditorias_competencias",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Actor",
                    ),
                ),
                (
                    "competencia",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="auditorias",
                        to="competencias.competencia",
                        verbose_name="Competencia",
                    ),
                ),
                (
                    "encuentro",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="auditorias",
                        to="competencias.encuentro",
                        verbose_name="Encuentro",
                    ),
                ),
            ],
            options={
                "db_table": "competencia_auditoria",
                "verbose_name": "Auditoría de operación",
                "verbose_name_plural": "Auditorías de operaciones",
                "ordering": ["-created_at"],
            },
        ),
        # ── Restricciones ───────────────────────────────────────────────────
        migrations.AddConstraint(
            model_name="competencia",
            constraint=models.UniqueConstraint(
                models.F("edicion"),
                models.F("disciplina"),
                django.db.models.functions.text.Lower("nombre"),
                name="competencia_identidad_unica_por_edicion_disciplina",
            ),
        ),
        migrations.AddConstraint(
            model_name="ronda",
            constraint=models.UniqueConstraint(
                fields=("competencia", "etiqueta"),
                name="competencia_ronda_etiqueta_unica",
            ),
        ),
        migrations.AddConstraint(
            model_name="ronda",
            constraint=models.UniqueConstraint(
                fields=("competencia", "orden"),
                name="competencia_ronda_orden_unico",
            ),
        ),
        migrations.AddConstraint(
            model_name="competenciaequipo",
            constraint=models.UniqueConstraint(
                fields=("competencia", "equipo"),
                name="competencia_equipo_unico_por_competencia",
            ),
        ),
        migrations.AddConstraint(
            model_name="competenciaequipo",
            constraint=models.UniqueConstraint(
                condition=models.Q(estado="ACTIVO"),
                fields=("competencia", "orden"),
                name="competencia_equipo_orden_unico_entre_activos",
            ),
        ),
        migrations.AddConstraint(
            model_name="encuentro",
            constraint=models.UniqueConstraint(
                fields=("ronda", "orden"),
                name="competencia_encuentro_orden_unico_por_ronda",
            ),
        ),
        migrations.AddConstraint(
            model_name="encuentro",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(participante_1__isnull=True)
                    | models.Q(participante_2__isnull=True)
                    | ~models.Q(participante_1=models.F("participante_2"))
                ),
                name="competencia_encuentro_participantes_distintos",
            ),
        ),
        migrations.AddConstraint(
            model_name="encuentro",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(fin_programado__isnull=True, inicio_programado__isnull=True)
                    | models.Q(
                        fin_programado__gt=models.F("inicio_programado"),
                        fin_programado__isnull=False,
                        inicio_programado__isnull=False,
                    )
                ),
                name="competencia_encuentro_horario_intervalo",
            ),
        ),
        migrations.AddConstraint(
            model_name="encuentro",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(slot_destino__isnull=True, siguiente_encuentro__isnull=True)
                    | models.Q(
                        slot_destino__isnull=False,
                        siguiente_encuentro__isnull=False,
                    )
                ),
                name="competencia_encuentro_enlace_slot",
            ),
        ),
        migrations.AddConstraint(
            model_name="encuentro",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(ganador__isnull=True)
                    | models.Q(
                        ganador=models.F("participante_1"),
                        participante_1__isnull=False,
                    )
                    | models.Q(
                        ganador=models.F("participante_2"),
                        participante_2__isnull=False,
                    )
                ),
                name="competencia_encuentro_ganador_en_slot",
            ),
        ),
        # ── Índices ─────────────────────────────────────────────────────────
        migrations.AddIndex(
            model_name="competencia",
            index=models.Index(
                fields=["edicion", "disciplina", "estado", "fecha"],
                name="ix_cmp_edi_dis_est_fecha",
            ),
        ),
        migrations.AddIndex(
            model_name="ronda",
            index=models.Index(
                fields=["competencia", "estado", "orden"],
                name="ix_cmp_ron_cmp_est_ord",
            ),
        ),
        migrations.AddIndex(
            model_name="competenciaequipo",
            index=models.Index(
                fields=["competencia", "estado", "orden"],
                name="ix_cmp_equ_cmp_est_ord",
            ),
        ),
        migrations.AddIndex(
            model_name="encuentro",
            index=models.Index(
                fields=["estado", "inicio_programado", "fin_programado"],
                name="ix_comp_enc_estr_ini_fin",
            ),
        ),
        migrations.AddIndex(
            model_name="auditoriaoperacion",
            index=models.Index(
                fields=["encuentro", "-created_at"],
                name="ix_comp_aud_enc_created",
            ),
        ),
        migrations.AddIndex(
            model_name="auditoriaoperacion",
            index=models.Index(
                fields=["competencia", "-created_at"],
                name="ix_comp_aud_comp_created",
            ),
        ),
    ]
