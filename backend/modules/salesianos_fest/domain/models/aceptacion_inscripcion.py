"""
AceptacionInscripcion — registro de aceptacion de documento legal por persona en una inscripcion.

Cada vez que una persona es agregada a una inscripcion, se registran las aceptaciones
de los documentos legales requeridos (bases, aptitud fisica, imagen).

Attributes:
    inscripcion_persona: FK(InscripcionPersona) - vinculo al cual pertenece la aceptacion.
    tipo_aceptacion: BASES, APTITUD_FISICA, IMAGEN.
    documento_version: Version del documento aceptado (e.g. "BASES-SF26-2026-09-06").
    aceptado_en: Fecha y hora en que se declaro la aceptacion.
    actor_id: ID de la persona que declaro la aceptacion (el beneficiario mismo).
    medio: WEB, MOBILE, PAPER.
    ip_address: Direccion IP desde donde se declaro (nullable).
"""
from django.db import models

from core.models import BaseModel
from .inscripcion_persona import InscripcionPersona
from ..constants import TipoAceptacionChoices, MedioAceptacionChoices


class AceptacionInscripcion(BaseModel):
    """
    Registro de aceptacion de documento legal por persona en una inscripcion.
    """

    inscripcion_persona = models.ForeignKey(
        InscripcionPersona,
        on_delete=models.CASCADE,
        related_name="aceptaciones",
        verbose_name="Inscripcion Persona",
    )
    tipo_aceptacion = models.CharField(
        max_length=20,
        choices=TipoAceptacionChoices.choices,
        verbose_name="Tipo de aceptacion",
    )
    documento_version = models.CharField(
        max_length=50,
        verbose_name="Version del documento",
    )
    aceptado_en = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y hora de aceptacion",
    )
    actor_id = models.CharField(
        max_length=36,
        verbose_name="ID del actor que acepto",
    )
    medio = models.CharField(
        max_length=10,
        choices=MedioAceptacionChoices.choices,
        default=MedioAceptacionChoices.WEB,
        verbose_name="Medio de aceptacion",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Direccion IP",
    )

    class Meta:
        db_table = "aceptaciones_inscripcion"
        verbose_name = "Aceptacion de Inscripcion"
        verbose_name_plural = "Aceptaciones de Inscripcion"
        ordering = ["inscripcion_persona", "aceptado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscripcion_persona", "tipo_aceptacion"],
                name="unique_aceptacion_inscripcion_persona_tipo",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.tipo_aceptacion} - {self.inscripcion_persona} ({self.aceptado_en})"
