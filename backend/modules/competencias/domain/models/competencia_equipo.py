"""
CompetenciaEquipo — the participation of a team inside a competition.

It is the bridge between the team of the enrollment domain (`Equipo`) and the
bracket (`Competencia`). It carries the manual seed/order and the state of the
participation (active or withdrawn).
"""
from django.db import models
from simple_history.models import HistoricalRecords

from modules.salesianos_fest.domain.models import Equipo
from .competencia import Competencia
from .base import CompetenciaBaseModel
from ..constants import EstadoCompetenciaEquipoChoices


class CompetenciaEquipo(CompetenciaBaseModel):
    """
    A team registered in the bracket of a competition.

    Attributes:
        competencia: Competition the team belongs to.
        equipo: Team of the enrollment domain (never duplicated here).
        orden: Manual seed/order of the team inside the bracket.
        estado: Participation state (ACTIVO / RETIRADO).
        version: Optimistic-locking counter.
    """

    history = HistoricalRecords(
        # The audit motive may be up to 500 characters (design: motivo
        # 5..500), so the default 100-char column of simple_history is
        # widened to a TextField.
        history_change_reason_field=models.TextField(null=True),
    )

    competencia = models.ForeignKey(
        Competencia,
        on_delete=models.PROTECT,
        related_name="competencia_equipos",
        verbose_name="Competencia",
    )
    equipo = models.ForeignKey(
        Equipo,
        on_delete=models.PROTECT,
        related_name="competencia_equipos",
        verbose_name="Equipo",
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoCompetenciaEquipoChoices.choices,
        default=EstadoCompetenciaEquipoChoices.ACTIVO,
        verbose_name="Estado",
    )
    class Meta:
        db_table = "competencia_equipos"
        verbose_name = "Equipo de competencia"
        verbose_name_plural = "Equipos de competencia"
        ordering = ["competencia", "orden"]
        constraints = [
            # A team enters a competition only once.
            models.UniqueConstraint(
                fields=["competencia", "equipo"],
                name="uq_competencia_equipo_competencia_equipo",
            ),
            # The order is unique among the ACTIVE entries only: a withdrawn
            # team frees its position for the next one.
            models.UniqueConstraint(
                fields=["competencia", "orden"],
                condition=models.Q(estado=EstadoCompetenciaEquipoChoices.ACTIVO),
                name="uq_competencia_equipo_competencia_orden_activo",
            ),
        ]
        indexes = [
            models.Index(
                fields=["competencia", "estado", "orden"],
                name="ix_comp_equipo_comp_est_orden",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.equipo_id} - {self.estado}"
