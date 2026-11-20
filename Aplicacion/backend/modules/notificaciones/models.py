"""Modelos del módulo `notificaciones`.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

Un único modelo: `NotificacionEnvio`, la **trazabilidad** del intento de
notificar al comprador de una compra pagada.

Por qué NO lleva FK a `pagos` ni a `commerce`:

- El módulo `notificaciones` es una **hoja** del grafo: no depende de ningún
  módulo de dominio y ninguno depende de él (el puerto lo declara `pagos` y
  `notificaciones` lo implementa, como `commerce` con `pagos`).
- La fila registra el **hecho** del intento,indexado por el identificador de
  negocio. Una FK convertiría al auditor en un participante del ciclo de vida
  del cobro (`ON DELETE PROTECT` bloquearía el borrado de un pago, y el
  borrado de un pago está prohibido).

El modelo es plano y anémico (`contract/django-app-architecture-contract.md`
§4.2): campos, `Meta` y `__str__`. La lógica vive en los servicios.
"""

from django.db import models

from core.models import BaseModel
from modules.notificaciones.domain.constants import (
    EstadoNotificacion,
    TipoNotificacion,
)


class NotificacionEnvio(BaseModel):
    """La trazabilidad de un intento de notificación al comprador.

    Invariantes:

    - `orden_pago_id` + `tipo` son **únicos**: una compra pagada genera como
      máximo un registro de notificación por tipo. Un webhook duplicado NO
      crea un segundo registro (FR-04 I-1 aplicado a la notificación).
    - `estado` es el estado del **intento**, no el del pago: una notificación
      fallida NO revierte el cobro (RN-C08).
    - `incidencia` sólo admite las claves de una lista cerrada
      (`codigo`, `intento`, `fecha`). Nunca el texto de una excepción, ni un
      payload de proveedor, ni un secreto.
    - `codigo` es un código de máquina (`[A-Z0-9_]`), no un mensaje.

    La fila **es** la traza: no usa `simple_history` porque acumula los
    intentos en sus propios campos (`intentos`, `estado`, `incidencia`), y el
    histórico de modelos es opcional en este proyecto
    (`contract/django-app-architecture-contract.md` §…: «historic models *si el
    proyecto lo requiere*»).
    """

    orden_pago_id = models.UUIDField(
        db_index=True,
        verbose_name="Orden de pago",
        help_text=(
            "Identificador de la orden pagada. No es una FK: la trazabilidad "
            "de la notificación no debe participar del ciclo de vida del cobro."
        ),
    )
    persona_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Persona compradora",
        help_text="Identificador de la persona compradora, si la hay.",
    )
    tipo = models.CharField(
        max_length=40,
        choices=TipoNotificacion.choices,
        default=TipoNotificacion.COMPRA_CONFIRMADA,
        verbose_name="Tipo",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoNotificacion.choices,
        default=EstadoNotificacion.OMITIDA,
        verbose_name="Estado",
    )
    codigo = models.CharField(
        max_length=64,
        blank=True,
        default="",
        verbose_name="Código",
        help_text="Código de máquina del resultado. Nunca un texto libre.",
    )
    intentos = models.PositiveIntegerField(
        default=0,
        verbose_name="Intentos",
        help_text="Número de intentos de notificación consumidos.",
    )
    incidencia = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Incidencia",
        help_text=(
            "Datos seguros del último fallo (codigo, intento, fecha). Nunca el "
            "texto de una excepción ni un payload de proveedor."
        ),
    )
    enviada_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de envío",
        help_text="Instante en que el proveedor aceptó el envío. Nulo = no se envió.",
    )

    class Meta:
        db_table = "notificaciones_envio"
        verbose_name = "Envío de notificación"
        verbose_name_plural = "Envíos de notificación"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["orden_pago_id", "tipo"],
                name="notificacion_unica_por_orden_y_tipo",
            ),
        ]
        indexes = [
            models.Index(fields=["estado"], name="ix_notificacionenvio_estado"),
        ]

    def __str__(self) -> str:
        return f"NotificacionEnvio {self.tipo} - {self.estado}"


__all__ = ["NotificacionEnvio"]
