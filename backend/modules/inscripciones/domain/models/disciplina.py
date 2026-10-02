"""
Disciplina and Categoria models for Salesianos FEST.

Disciplina: sport/discipline with team size constraints.
Categoria: age category within a discipline.
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import ModalidadChoices


class Disciplina(BaseModel):
    """
    Sport or discipline available for inscription.

    Examples: Football (Futsal), Basketball, Volleyball, etc.
    """

    history = HistoricalRecords()

    nombre = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nombre de disciplina"
    )
    sigla = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Sigla"
    )
    modalidad = models.CharField(
        max_length=1,
        choices=ModalidadChoices.choices,
        verbose_name="Modalidad"
    )
    min_jugadores = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Mínimo de jugadores",
        help_text="Null = sin límite inferior"
    )
    max_jugadores = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Máximo de jugadores",
        help_text="Null = sin límite superior"
    )
    esta_activa = models.BooleanField(
        default=True,
        verbose_name="¿Está activa?"
    )

    class Meta:
        verbose_name = "Disciplina"
        verbose_name_plural = "Disciplinas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.sigla})"


class Categoria(BaseModel):
    """
    Age category within a discipline.

    Examples: Junior (born 2006-2008), Senior (born 2003-2005), Master (born 2002 and earlier).
    """

    history = HistoricalRecords()

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.PROTECT,
        related_name="categorias",
        verbose_name="Disciplina"
    )
    nombre = models.CharField(
        max_length=50,
        verbose_name="Nombre de categoría"
    )
    anio_minimo = models.PositiveIntegerField(
        verbose_name="Año mínimo de nacimiento"
    )
    anio_maximo = models.PositiveIntegerField(
        verbose_name="Año máximo de nacimiento"
    )
    esta_activa = models.BooleanField(
        default=True,
        verbose_name="¿Está activa?"
    )

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["disciplina", "anio_minimo"]
        constraints = [
            models.UniqueConstraint(
                fields=["disciplina", "nombre"],
                name="unique_disciplina_categoria_nombre"
            )
        ]

    def __str__(self):
        return f"{self.nombre} ({self.disciplina.sigla})"
