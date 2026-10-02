"""
Promocion model — catalog of promotion years for Salesianos FEST.

Represents a graduation year/class of a school (promocion).
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import ColegioChoices


class Promocion(BaseModel):
    """
    Catalog of promotion years.

    Represents a graduation year/class (e.g., "Promocion 2002").
    Used as FK in Inscripcion to identify the promotion of the team/responsible.
    """

    history = HistoricalRecords()

    anio = models.PositiveIntegerField(
        unique=True,
        verbose_name="Año de promoción",
        help_text="Año de graduación (e.g., 2002)"
    )
    colegio = models.CharField(
        max_length=3,
        choices=ColegioChoices.choices,
        default=ColegioChoices.MA,
        verbose_name="Colegio",
        help_text="SJB (San José) o MA (María Auxiliadora)"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre",
        help_text="e.g., 'Promoción 2002'",
        blank=True,
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="Activa",
        help_text="Si está activa para nuevas inscripciones"
    )

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        ordering = ["-anio"]

    def __str__(self):
        return self.nombre or f"Promoción {self.anio}"

    def save(self, *args, **kwargs):
        if not self.nombre:
            self.nombre = f"Promoción {self.anio}"
        super().save(*args, **kwargs)
