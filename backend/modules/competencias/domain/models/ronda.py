"""
Ronda — one round (column) of the bracket of a competition.

A round groups the encounters that are played in the same stage of the
elimination tournament. Rounds are ordered and can be invalidated (never
deleted) so the history of the bracket is preserved.
"""
from django.db import models
from simple_history.models import HistoricalRecords

from .competencia import Competencia
from .base import CompetenciaBaseModel
from ..constants import EstadoRondaChoices


class Ronda(CompetenciaBaseModel):
    """
    A round of the bracket.

    Attributes:
        competencia: Competition the round belongs to.
        etiqueta: Label of the round (standard or custom, e.g. "Semifinal").
        orden: Order of the round inside the competition.
        estado: Round state (ACTIVA / INVALIDADA).
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
        related_name="rondas",
        verbose_name="Competencia",
    )
    etiqueta = models.CharField(
        max_length=100,
        verbose_name="Etiqueta",
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoRondaChoices.choices,
        default=EstadoRondaChoices.ACTIVA,
        verbose_name="Estado",
    )
    class Meta:
        db_table = "rondas"
        verbose_name = "Ronda"
        verbose_name_plural = "Rondas"
        ordering = ["competencia", "orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["competencia", "etiqueta"],
                name="uq_ronda_competencia_etiqueta",
            ),
            models.UniqueConstraint(
                fields=["competencia", "orden"],
                name="uq_ronda_competencia_orden",
            ),
        ]
        indexes = [
            models.Index(
                fields=["competencia", "estado", "orden"],
                name="ix_ronda_comp_est_orden",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.etiqueta} ({self.estado})"
