"""
Evento model for Salesianos FEST.

Evento: groups inscriptions and defines the scope for uniqueness constraint R11.
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel


class Evento(BaseModel):
    """
    Sports event that groups inscriptions.

    Example: "Salesianos FEST 2026"
    """

    history = HistoricalRecords()

    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del evento"
    )
    fecha_inicio = models.DateField(
        verbose_name="Fecha de inicio"
    )
    fecha_fin = models.DateField(
        verbose_name="Fecha de fin"
    )
    esta_activo = models.BooleanField(
        default=True,
        verbose_name="¿Está activo?"
    )

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return self.nombre
