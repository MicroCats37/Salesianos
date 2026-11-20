# Migración inicial del módulo `notificaciones`.
#
# Freeze: FREEZE-CM-1.0.0 (FR-04 §4)
# Evidence: Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md
#
# Escribe a mano y NO genera el esquema: el paquete `notificaciones` registra
# la trazabilidad del intento de notificación al comprador. No depende de
# ningún módulo de dominio (`notificaciones` es una hoja del grafo), así que
# esta migración no declara ninguna FK.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="NotificacionEnvio",
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
                    models.DateTimeField(auto_now=True, verbose_name="Última actualización"),
                ),
                (
                    "orden_pago_id",
                    models.UUIDField(
                        db_index=True,
                        help_text=(
                            "Identificador de la orden pagada. No es una FK: la "
                            "trazabilidad de la notificación no debe participar "
                            "del ciclo de vida del cobro."
                        ),
                        verbose_name="Orden de pago",
                    ),
                ),
                (
                    "persona_id",
                    models.UUIDField(
                        blank=True,
                        db_index=True,
                        help_text="Identificador de la persona compradora, si la hay.",
                        null=True,
                        verbose_name="Persona compradora",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[("COMPRA_CONFIRMADA", "Compra confirmada")],
                        default="COMPRA_CONFIRMADA",
                        max_length=40,
                        verbose_name="Tipo",
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("OMITIDA", "Omitida"),
                            ("PENDIENTE", "Pendiente"),
                            ("ENVIADA", "Enviada"),
                            ("FALLIDA", "Fallida"),
                        ],
                        default="OMITIDA",
                        max_length=20,
                        verbose_name="Estado",
                    ),
                ),
                (
                    "codigo",
                    models.CharField(
                        blank=True,
                        default="",
                        help_text="Código de máquina del resultado. Nunca un texto libre.",
                        max_length=64,
                        verbose_name="Código",
                    ),
                ),
                (
                    "intentos",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Número de intentos de notificación consumidos.",
                        verbose_name="Intentos",
                    ),
                ),
                (
                    "incidencia",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text=(
                            "Datos seguros del último fallo (codigo, intento, fecha). "
                            "Nunca el texto de una excepción ni un payload de "
                            "proveedor."
                        ),
                        verbose_name="Incidencia",
                    ),
                ),
                (
                    "enviada_en",
                    models.DateTimeField(
                        blank=True,
                        help_text=(
                            "Instante en que el proveedor aceptó el envío. "
                            "Nulo = no se envió."
                        ),
                        null=True,
                        verbose_name="Fecha de envío",
                    ),
                ),
            ],
            options={
                "verbose_name": "Envío de notificación",
                "verbose_name_plural": "Envíos de notificación",
                "db_table": "notificaciones_envio",
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["estado"], name="ix_notificacionenvio_estado"
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("orden_pago_id", "tipo"),
                        name="notificacion_unica_por_orden_y_tipo",
                    )
                ],
            },
        ),
    ]
