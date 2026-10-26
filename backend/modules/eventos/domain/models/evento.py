"""
Evento — única entidad del módulo eventos.

Representa una edición del evento Salesianos FEST.
Sin simple_history: no es dato financiero.
"""
from django.db import models
from django.core.exceptions import ValidationError

from core.models import BaseModel


class Evento(BaseModel):
    """
    Modelo base para una edición del evento.

    Attributes:
        nombre: Nombre de la edición del evento.
        fecha_inicio: Fecha de inicio del evento.
        fecha_fin: Fecha de fin del evento.
        esta_activo: Indica si el evento está activo para inscripciones.
        fecha_limite_modificacion: Fecha límite para modificaciones de roster,
            equipos, participaciones y operaciones de cupos.
    """

    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del evento",
    )
    fecha_inicio = models.DateField(
        verbose_name="Fecha de inicio",
    )
    fecha_fin = models.DateField(
        verbose_name="Fecha de fin",
    )
    esta_activo = models.BooleanField(
        default=True,
        verbose_name="¿Está activo?",
    )
    fecha_limite_modificacion = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha límite de modificaciones",
        help_text="Después de esta fecha no se permiten cambios de roster, equipos o participaciones.",
    )

    class Meta:
        db_table = "eventos"
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-fecha_inicio"]

    def __str__(self) -> str:
        return self.nombre

    def puede_modificar(self) -> bool:
        """Check if modifications are still allowed based on fecha_limite_modificacion."""
        from datetime import date
        if self.fecha_limite_modificacion is None:
            return True  # No limit set, always allowed
        return date.today() <= self.fecha_limite_modificacion

    def clean(self):
        super().clean()
        if (
            self.fecha_limite_modificacion
            and self.fecha_fin
            and self.fecha_limite_modificacion > self.fecha_fin
        ):
            raise ValidationError({
                "fecha_limite_modificacion": "La fecha límite no puede ser posterior a la fecha de fin del evento."
            })
