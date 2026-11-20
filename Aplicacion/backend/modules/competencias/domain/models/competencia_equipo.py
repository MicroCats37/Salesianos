"""`CompetenciaEquipo` — la participación de un equipo en el cuadro.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Invariantes:

- El `equipo` es un equipo de `modules.salesianos_fest`: este módulo NO
  duplica el equipo, lo REFERENCIA. La elegibilidad la resuelve el dueño del
  equipo por PUERTO (`RN-K01`).
- Un equipo entra UNA vez en una competencia.
- **El orden (la semilla) es MANUAL**: el sistema nunca lo elige. La
  restricción de unicidad del orden sólo aplica a las entradas `ACTIVO`: un
  equipo retirado libera su posición para el siguiente.
- Retirar NO es borrar: el equipo conserva su historia y el cuadro conserva
  su posición en la historia (`RN-K02`).
"""

from django.db import models

from modules.competencias.domain.constants import EstadoCompetenciaEquipo
from modules.competencias.domain.models.base import CompetenciaBaseModel


class CompetenciaEquipo(CompetenciaBaseModel):
    """Un equipo dentro del cuadro de una competencia."""

    competencia = models.ForeignKey(
        "competencias.Competencia",
        on_delete=models.PROTECT,
        related_name="equipos",
        verbose_name="Competencia",
    )
    equipo = models.ForeignKey(
        "salesianos_fest.Equipo",
        on_delete=models.PROTECT,
        related_name="participaciones_en_competencias",
        verbose_name="Equipo",
        help_text=(
            "Equipo de inscripción. Su estado, su edición y su disciplina los "
            "decide `modules.salesianos_fest`, no este módulo."
        ),
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden",
        help_text="Semilla del cuadro. La elige el administrador: el sistema nunca.",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoCompetenciaEquipo.choices,
        default=EstadoCompetenciaEquipo.ACTIVO,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "competencia_equipos"
        verbose_name = "Equipo de competencia"
        verbose_name_plural = "Equipos de competencia"
        ordering = ["competencia_id", "orden"]
        constraints = [
            # Un equipo entra UNA vez en una competencia.
            models.UniqueConstraint(
                fields=["competencia", "equipo"],
                name="competencia_equipo_unico_por_competencia",
            ),
            # El orden es único entre las entradas ACTIVAS: un equipo retirado
            # libera su posición.
            models.UniqueConstraint(
                fields=["competencia", "orden"],
                condition=models.Q(estado=EstadoCompetenciaEquipo.ACTIVO),
                name="competencia_equipo_orden_unico_entre_activos",
            ),
        ]
        indexes = [
            models.Index(
                fields=["competencia", "estado", "orden"],
                name="ix_cmp_equ_cmp_est_ord",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.equipo_id} ({self.estado})"


__all__ = ["CompetenciaEquipo"]
