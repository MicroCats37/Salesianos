"""
InscripcionPersona — vínculo entre una inscripción y una persona participante.
"""
from django.db import models

from core.models import BaseModel
from ..constants import EstadoInscripcionPersonaChoices


class InscripcionPersona(BaseModel):
    """
    Registra que una Persona participa en una Inscripción.

    Una misma persona puede estar en múltiples inscripciones (distintos
    eventos o paquetes). El estado permite retirar a alguien sin borrar
    el registro histórico.

    Attributes:
        inscripcion: Inscripción a la que pertenece.
        persona: Persona registrada.
        estado: A=Activo, R=Retirado.
    """

    inscripcion = models.ForeignKey(
        "Inscripcion",
        on_delete=models.PROTECT,
        related_name="inscripcion_personas",
        verbose_name="Inscripción",
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.PROTECT,
        related_name="inscripciones_persona",
        verbose_name="Persona",
    )
    estado = models.CharField(
        max_length=1,
        choices=EstadoInscripcionPersonaChoices.choices,
        default=EstadoInscripcionPersonaChoices.ACTIVO,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "inscripciones_personas"
        verbose_name = "Inscripción Persona"
        verbose_name_plural = "Inscripciones Personas"
        ordering = ["inscripcion", "persona"]
        constraints = [
            models.UniqueConstraint(
                fields=["inscripcion", "persona"],
                name="unique_inscripcion_persona",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.persona} en {self.inscripcion} ({self.estado})"
