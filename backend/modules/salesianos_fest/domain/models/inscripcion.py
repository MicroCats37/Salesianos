"""
Inscripcion — registro de una inscripción deportiva a un evento.
"""
from django.db import models

from core.models import BaseModel
from modules.eventos.domain.models import Evento
from modules.usuarios.domain.models.persona import Persona
from ..constants import EstadoInscripcionChoices


class Inscripcion(BaseModel):
    """
    Representa una inscripción deportiva a un evento.

    El estado es exclusivamente deportivo/administrativo — NO incluye PAGADA
    ni ningún estado comercial. El pago es gestionado por un módulo
    externo (compras/pagos) en Fase 4+.

    Attributes:
        evento: Evento al que se inscribe.
        responsable: Persona que crea y gestiona la inscripción.
        paquete: Paquete comercial seleccionado.
        promocion: Promoción principal del equipo (calcula categoría).
        fusion_promocion: Promoción secundaria opcional para fusión
            (política de fusión pendiente — campo nullable sin validación).
        delegado: Persona responsable/delgado del equipo (opcional).
        estado: Estado deportivo de la inscripción.
        observacion: Notas administrativas (opcional).
    """

    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Evento",
    )
    responsable = models.ForeignKey(
        Persona,
        on_delete=models.PROTECT,
        related_name="inscripciones_responsable",
        verbose_name="Responsable",
    )
    paquete = models.ForeignKey(
        "Paquete",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Paquete",
    )
    promocion = models.ForeignKey(
        "Promocion",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Promoción principal",
    )
    fusion_promocion = models.ForeignKey(
        "Promocion",
        on_delete=models.PROTECT,
        related_name="inscripciones_fusion",
        null=True,
        blank=True,
        verbose_name="Promoción de fusión (opcional)",
    )
    delegado = models.ForeignKey(
        Persona,
        on_delete=models.PROTECT,
        related_name="inscripciones_delegado",
        null=True,
        blank=True,
        verbose_name="Delegado/Responsable",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoInscripcionChoices.choices,
        default=EstadoInscripcionChoices.BORRADOR,
        verbose_name="Estado",
    )
    observacion = models.TextField(
        blank=True,
        default="",
        verbose_name="Observación",
    )

    class Meta:
        db_table = "inscripciones"
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "responsable", "paquete"],
                name="unique_inscripcion_evento_responsable_paquete",
            ),
        ]

    def __str__(self) -> str:
        return f"Inscripción {self.evento.nombre} - {self.responsable} ({self.estado})"
