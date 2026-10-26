"""
Disciplina — deporte o actividad competitiva en el evento.
"""
from django.db import models
from django.core.validators import MinValueValidator

from core.models import BaseModel
from ..constants import ModalidadChoices


class Disciplina(BaseModel):
    """
    Representa un deporte o actividad competitiva.

    Attributes:
        nombre: Nombre completo de la disciplina.
        sigla: Código único (ej: F7M, VOL, BAS).
        modalidad: Masculino (M), Femenino (F) o Mixto (X).
        min_jugadores: Número mínimo de jugadores por equipo.
        max_jugadores: Número máximo de jugadores por equipo.
        esta_activa: Indica si la disciplina está disponible.
    """

    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre de la disciplina",
    )
    sigla = models.CharField(
        max_length=10,
        verbose_name="Sigla",
        unique=True,
    )
    modalidad = models.CharField(
        max_length=1,
        choices=ModalidadChoices.choices,
        verbose_name="Modalidad",
    )
    min_jugadores = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Mínimo de jugadores por equipo",
    )
    max_jugadores = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Máximo de jugadores por equipo",
    )
    esta_activa = models.BooleanField(
        default=True,
        verbose_name="¿Está activa?",
    )

    class Meta:
        db_table = "disciplinas"
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["sigla"],
                name="unique_disciplina_sigla",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.sigla})"
