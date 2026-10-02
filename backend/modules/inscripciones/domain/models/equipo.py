"""
EquipoInscrito, ParticipacionDisciplina, and ParticipanteInscripcion models.

EquipoInscrito: team registered under an inscription for a specific discipline.
ParticipacionDisciplina: records that a person participates in a discipline+event (R11 protected).
ParticipanteInscripcion: links a participation to a team with role and shirt size.
"""

from django.db import models
from simple_history.models import HistoricalRecords

from core.models import BaseModel
from ..constants import RolParticipanteChoices, TalleCamisetaChoices


class EquipoInscrito(BaseModel):
    """
    Team registered under an inscription for a specific discipline.

    Constraint: one team per inscription+discipline (D7 confirmed).
    Category is a descriptive attribute, not an identity factor.
    """

    history = HistoricalRecords()

    inscripcion = models.ForeignKey(
        "inscripciones.Inscripcion",
        on_delete=models.CASCADE,
        related_name="equipos",
        verbose_name="Inscripción"
    )
    disciplina = models.ForeignKey(
        "inscripciones.Disciplina",
        on_delete=models.PROTECT,
        related_name="equipos_inscritos",
        verbose_name="Disciplina"
    )
    categoria = models.ForeignKey(
        "inscripciones.Categoria",
        on_delete=models.PROTECT,
        related_name="equipos_inscritos",
        null=True,
        blank=True,
        verbose_name="Categoría"
    )
    nombre = models.CharField(
        max_length=120,
        verbose_name="Nombre del equipo"
    )

    class Meta:
        verbose_name = "Equipo inscrito"
        verbose_name_plural = "Equipos inscritos"
        ordering = ["inscripcion", "disciplina"]

    def __str__(self):
        return f"{self.nombre} ({self.disciplina.sigla})"


class ParticipacionDisciplina(BaseModel):
    """
    Records that a persona participates in a discipline within an event.

    This model materializes the R11 uniqueness constraint at database level:
    unique(evento, disciplina, persona).

    The fields evento and disciplina are direct (not derived from equipo) to allow
    the UniqueConstraint without complex cross-table queries.
    """

    history = HistoricalRecords()

    evento = models.ForeignKey(
        "inscripciones.Evento",
        on_delete=models.CASCADE,
        related_name="participaciones",
        verbose_name="Evento"
    )
    disciplina = models.ForeignKey(
        "inscripciones.Disciplina",
        on_delete=models.CASCADE,
        related_name="participaciones",
        verbose_name="Disciplina"
    )
    persona = models.ForeignKey(
        "usuarios.Persona",
        on_delete=models.CASCADE,
        related_name="participaciones",
        verbose_name="Persona"
    )
    equipo = models.ForeignKey(
        EquipoInscrito,
        on_delete=models.PROTECT,
        related_name="participaciones",
        verbose_name="Equipo"
    )

    class Meta:
        verbose_name = "Participación en disciplina"
        verbose_name_plural = "Participaciones en disciplinas"
        ordering = ["evento", "disciplina", "persona"]
        constraints = [
            models.UniqueConstraint(
                fields=["evento", "disciplina", "persona"],
                name="unique_persona_disciplina_evento"
            )
        ]

    def __str__(self):
        return f"{self.persona} - {self.disciplina.nombre} ({self.evento.nombre})"


class ParticipanteInscripcion(BaseModel):
    """
    Links a participation to a team with role and shirt size.

    Represents a person enrolled in a specific team with a specific role.
    """

    history = HistoricalRecords()

    participacion = models.ForeignKey(
        ParticipacionDisciplina,
        on_delete=models.CASCADE,
        related_name="participantes",
        verbose_name="Participación"
    )
    equipo = models.ForeignKey(
        EquipoInscrito,
        on_delete=models.CASCADE,
        related_name="participantes_inscripcion",
        verbose_name="Equipo"
    )
    rol = models.CharField(
        max_length=20,
        choices=RolParticipanteChoices.choices,
        default=RolParticipanteChoices.JUGADOR,
        verbose_name="Rol"
    )
    talle_camiseta = models.CharField(
        max_length=5,
        choices=TalleCamisetaChoices.choices,
        blank=True,
        null=True,
        verbose_name="Talle de camiseta"
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Notas internas del responsable sobre el participante (alergias, observaciones, etc.)"
    )

    class Meta:
        verbose_name = "Participante de inscripción"
        verbose_name_plural = "Participantes de inscripción"
        ordering = ["participacion", "equipo"]

    def __str__(self):
        return f"{self.participacion.persona} as {self.rol} in {self.equipo.nombre}"
