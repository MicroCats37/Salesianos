"""
Categoria — categoría competitiva dentro de un evento.
"""
from django.db import models
from django.db.models import Q, F

from core.models import BaseModel
from modules.eventos.domain.models import Evento


class Categoria(BaseModel):
    """
    Representa una categoría competitiva (ej: Sub-14, Sub-16, Senior).

    Attributes:
        evento: Evento al que pertenece esta categoría.
        nombre: Nombre de la categoría (ej: Sub-14, Senior).
        promocion_desde: Año mínimo del rango etario.
        promocion_hasta: Año máximo del rango etario.
        esta_activa: Indica si la categoría está activa.
    """

    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="categorias",
        verbose_name="Evento",
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre de la categoría",
    )
    promocion_desde = models.PositiveIntegerField(
        verbose_name="Año mínimo del rango",
    )
    promocion_hasta = models.PositiveIntegerField(
        verbose_name="Año máximo del rango",
    )
    esta_activa = models.BooleanField(
        default=True,
        verbose_name="¿Está activa?",
    )

    class Meta:
        db_table = "categorias"
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["evento", "nombre"]
        constraints = [
            models.CheckConstraint(
                condition=Q(promocion_desde__lte=F("promocion_hasta")),
                name="check_categoria_rango",
            ),
            models.UniqueConstraint(
                fields=["evento", "nombre"],
                condition=Q(esta_activa=True),
                name="unique_categoria_evento_nombre_activa",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.evento.nombre} - {self.nombre}"
