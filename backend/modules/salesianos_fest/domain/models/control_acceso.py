"""
ControlAcceso — registro de intentos de acceso via QR.

Attributes:
    acreditacion: FK(AcreditacionEvento) - que acreditacion se uso.
    fecha_hora: Timestamp del intento.
    resultado: PERMITIDO o DENEGADO.
    punto_acceso: Ubicacion del scanner (nullable).
    operador: Usuario que autorizo manualmente (nullable, para DENEGADO con override).

QR uniqueness: QR code grants access - single-use at entry time per event day.
Concurrent scans handled atomically via transaction.atomic.
"""
from django.db import models
from django.contrib.auth import get_user_model

from core.models import BaseModel
from .acreditacion_evento import AcreditacionEvento
from ..constants import ResultadoAccesoChoices


class ControlAcceso(BaseModel):
    """
    Registro de intentos de acceso via QR.
    """

    acreditacion = models.ForeignKey(
        AcreditacionEvento,
        on_delete=models.PROTECT,
        related_name="controles",
        verbose_name="Acreditacion",
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora del intento",
    )
    resultado = models.CharField(
        max_length=10,
        choices=ResultadoAccesoChoices.choices,
        verbose_name="Resultado",
    )
    punto_acceso = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Punto de acceso",
    )
    operador = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name="Operador que autorizo",
    )

    class Meta:
        db_table = "controles_acceso"
        verbose_name = "Control de Acceso"
        verbose_name_plural = "Controles de Acceso"
        ordering = ["-fecha_hora"]
        constraints = [
            # Partial unique constraint: only one PERMITIDO per acreditacion.
            # Combined with select_for_update in flujo, this prevents duplicate
            # PERMITIDO entries (TOCTOU defense-in-depth).
            models.UniqueConstraint(
                fields=["acreditacion"],
                condition=models.Q(resultado="PERMITIDO"),
                name="unique_permitido_acreditacion",
            ),
        ]

    def __str__(self) -> str:
        return f"ControlAcceso {self.acreditacion} - {self.resultado} ({self.fecha_hora})"
