"""
Paquete — oferta comercial (pack o disciplina individual).
"""
from django.db import models

from core.models import BaseModel
from modules.eventos.domain.models import Evento
from ..constants import TipoPaqueteChoices, ModoDisciplinasChoices


class Paquete(BaseModel):
    """
    Representa una oferta comercial en el evento.

    Attributes:
        evento: Evento al que pertenece el paquete.
        nombre: Nombre de la oferta (ej: Reencuentro + Fiesta).
        descripcion: Descripción detallada.
        tipo: PACK (con beneficios) o DISCIPLINA (individual).
        modo_disciplinas: FIJO (disciplinas predefinidas) o ELEGIBLE (elige el participante).
        cantidad_disciplinas: Cantidad de disciplinas según tipo (1, 2 o 3).
        minimo_compra_inicial: Monto mínimo de compra inicial.
        activo: Indica si el paquete está disponible.
    """

    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="paquetes",
        verbose_name="Evento",
    )
    nombre = models.CharField(
        max_length=200,
        verbose_name="Nombre del paquete",
    )
    descripcion = models.TextField(
        blank=True,
        default="",
        verbose_name="Descripción",
    )
    tipo = models.CharField(
        max_length=10,
        choices=TipoPaqueteChoices.choices,
        verbose_name="Tipo de paquete",
    )
    modo_disciplinas = models.CharField(
        max_length=10,
        choices=ModoDisciplinasChoices.choices,
        verbose_name="Modo de disciplinas",
    )
    cantidad_disciplinas = models.PositiveIntegerField(
        verbose_name="Cantidad de disciplinas",
    )
    minimo_compra_inicial = models.PositiveIntegerField(
        default=0,
        verbose_name="Mínimo de compra inicial",
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="¿Está activo?",
    )

    class Meta:
        db_table = "paquetes"
        verbose_name = "Paquete"
        verbose_name_plural = "Paquetes"
        ordering = ["evento", "nombre"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "nombre"],
                name="unique_paquete_evento_nombre",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.evento.nombre} - {self.nombre}"
