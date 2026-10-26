"""
Promocion — rango etario para categorización de participantes.
"""
from django.db import models

from core.models import BaseModel


class Promocion(BaseModel):
    """
    Representa un rango etario (categoría por edad).

    Attributes:
        anio: Año base de la promoción (ej: 2012 para Junior).
        nombre: Nombre descriptivo (ej: Junior, Senior, Master).
        activa: Indica si la promoción está vigente.
    """

    anio = models.PositiveIntegerField(
        unique=True,
        verbose_name="Año base",
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre de la promoción",
    )
    activa = models.BooleanField(
        default=True,
        verbose_name="¿Está activa?",
    )

    class Meta:
        db_table = "promociones"
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        ordering = ["-anio"]
        constraints = [
            models.UniqueConstraint(
                fields=["anio"],
                name="unique_promocion_anio",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.anio})"
