"""
Equipo — equipo deportivo registrado bajo una inscripción.
"""
from django.db import models
from django.db.models import Q

from core.models import BaseModel
from ..constants import EstadoEquipoChoices


class Equipo(BaseModel):
    """
    Representa un equipo deportivo dentro de una inscripción.

    El nombre es libre (ej: "Los Tigres", "Equipo Senior 2002").
    La categoría se calcula desde Inscripcion.promocion usando el rango
    de Categoria.promocion_desde/hasta — no desde disciplina.

    Attributes:
        inscripcion: Inscripción padre.
        disciplina: Disciplina en la que compite este equipo.
        categoria: Categoría calculada (opcional — reservada).
        promocion: Reserva — se hereda de inscripcion.promocion.
        nombre: Nombre libre del equipo.
        estado: Estado del equipo.
    """

    inscripcion = models.ForeignKey(
        "Inscripcion",
        on_delete=models.PROTECT,
        related_name="equipos",
        verbose_name="Inscripción",
    )
    disciplina = models.ForeignKey(
        "Disciplina",
        on_delete=models.PROTECT,
        related_name="equipos",
        verbose_name="Disciplina",
    )
    categoria = models.ForeignKey(
        "Categoria",
        on_delete=models.PROTECT,
        related_name="equipos",
        null=True,
        blank=True,
        verbose_name="Categoría (calculada)",
    )
    promocion = models.ForeignKey(
        "Promocion",
        on_delete=models.PROTECT,
        related_name="equipos",
        null=True,
        blank=True,
        verbose_name="Promoción (reservada — heredar de inscripción)",
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del equipo",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoEquipoChoices.choices,
        default=EstadoEquipoChoices.EQUIPO_ACTIVO,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "equipos"
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"
        ordering = ["inscripcion", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscripcion", "disciplina"],
                condition=Q(estado=EstadoEquipoChoices.EQUIPO_ACTIVO),
                name="unique_equipo_inscripcion_disciplina_activo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.disciplina.sigla})"
