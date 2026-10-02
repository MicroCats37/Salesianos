"""
Inscripcion and InscripcionDelegado models for Salesianos FEST.

Inscripcion: main inscription record linking responsible, event, and package.
InscripcionDelegado: delegate assigned to an inscription (one per inscription initially).
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import EstadoInscripcionChoices


class Inscripcion(BaseModel):
    """
    Main inscription record for a team/responsible.

    Links the responsible person with an event and package.
    Does NOT have:
    - codigo field (R6)
    - cantidad_participantes (R7 - computed via queryset)
    """

    history = HistoricalRecords()

    evento = models.ForeignKey(
        "inscripciones.Evento",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Evento"
    )
    responsable = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="inscripciones_responsable",
        verbose_name="Responsable"
    )
    paquete = models.ForeignKey(
        "inscripciones.Paquete",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Paquete"
    )
    promocion = models.ForeignKey(
        "inscripciones.Promocion",
        on_delete=models.PROTECT,
        related_name="inscripciones",
        verbose_name="Promoción",
        help_text="Año de promoción del equipo/responsable"
    )
    fusion_promocion = models.ForeignKey(
        "inscripciones.Promocion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inscripciones_fusion",
        verbose_name="Promoción de fusión",
        help_text="Promoción de fusión (opcional, para equipos combinados)"
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoInscripcionChoices.choices,
        default=EstadoInscripcionChoices.RECIBIDA,
        verbose_name="Estado"
    )
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observación",
        help_text="Observación del Comité"
    )
    comprobante_pago = models.FileField(
        upload_to="inscripciones/comprobantes/",
        blank=True,
        null=True,
        verbose_name="Comprobante de pago",
        help_text="Comprobante de pago manual (depósito bancario u otro método)"
    )

    class Meta:
        verbose_name = "Inscripción"
        verbose_name_plural = "Inscripciones"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Inscripción {self.id} - {self.promocion.anio} ({self.evento.nombre})"


class InscripcionDelegado(BaseModel):
    """
    Delegate assigned to an inscription.

    The delegate can be the responsible or a participant in any team of that inscription.
    Initially one delegate per inscription (UniqueConstraint on inscripcion).
    """

    history = HistoricalRecords()

    inscripcion = models.ForeignKey(
        Inscripcion,
        on_delete=models.CASCADE,
        related_name="delegados",
        verbose_name="Inscripción"
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="delegaciones",
        verbose_name="Delegado"
    )

    class Meta:
        verbose_name = "Delegado de inscripción"
        verbose_name_plural = "Delegados de inscripción"
        constraints = [
            models.UniqueConstraint(
                fields=["inscripcion"],
                name="unique_delegado_por_inscripcion"
            )
        ]

    def __str__(self):
        return f"Delegado: {self.persona} → {self.inscripcion}"
