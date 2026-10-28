"""
Pase — pase de fiesta independiente (catálogo paralelo a Paquete).
"""
from django.db import models

from core.models import BaseModel
from modules.eventos.domain.models import Evento

from ..constants import CANTIDAD_MAXIMA_SIN_LIMITE


class Pase(BaseModel):
    """
    Pase de fiesta: acceso nominativo a la fiesta, sin inscripción deportiva.

    NO es un `Paquete`. El pase no tiene disciplinas, equipos, beneficios de
    paquete ni mínimos de compra deportiva: el catálogo de paquetes y su
    contrato público quedan intactos.

    Attributes:
        evento: Evento al que pertenece el pase.
        nombre: Nombre comercial del pase (ej: "Pase de Fiesta").
        descripcion: Descripción pública del pase.
        cantidad_maxima: Inventario máximo; 0 = sin límite.
        activo: Indica si el pase se publica en el catálogo público.
    """

    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="pases",
        verbose_name="Evento",
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del pase",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
    )
    cantidad_maxima = models.PositiveIntegerField(
        default=CANTIDAD_MAXIMA_SIN_LIMITE,
        verbose_name="Cantidad máxima",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="¿Está activo?",
    )

    class Meta:
        db_table = "pases"
        verbose_name = "Pase"
        verbose_name_plural = "Pases"
        ordering = ["evento", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "nombre"],
                name="unique_pase_evento_nombre",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.evento.nombre} - {self.nombre}"
