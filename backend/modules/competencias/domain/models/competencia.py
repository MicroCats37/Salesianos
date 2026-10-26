"""
Competencia — the competition scope of a single elimination bracket.

A competition groups one `Evento + Disciplina + Categoria` combination and
owns the teams, the rounds and the encounters of its bracket. It is the
aggregate root of the `modules.competencias` domain.

The model is deliberately anemic: it holds fields, constraints and indexes
only. Every business rule (eligibility, scheduling, propagation, corrections)
lives in the service layer (see `domain/services/`).
"""
from django.db import models
from django.db.models.functions import Lower
from simple_history.models import HistoricalRecords

from modules.eventos.domain.models import Evento
from modules.salesianos_fest.domain.models import Categoria, Disciplina
from .base import CompetenciaBaseModel
from ..constants import EstadoCompetenciaChoices


class Competencia(CompetenciaBaseModel):
    """
    One elimination competition of the event.

    Attributes:
        evento: Event the competition belongs to.
        disciplina: Discipline of the competition (it already carries the
            modality/gender of the competition).
        categoria: Category of the competition.
        nombre: Name of the competition inside its event/discipline/category.
        fecha: Single day the competition takes place (inside the event).
        estado: Lifecycle state (PLANIFICADA → EN_CURSO → FINALIZADA, or
            CANCELADA before finishing).
        version: Optimistic-locking counter used by the commands
            (`expected_version`) to detect concurrent edits.
    """

    history = HistoricalRecords(
        # The audit motive may be up to 500 characters (design: motivo
        # 5..500), so the default 100-char column of simple_history is
        # widened to a TextField.
        history_change_reason_field=models.TextField(null=True),
    )

    evento = models.ForeignKey(
        Evento,
        on_delete=models.PROTECT,
        related_name="competencias",
        verbose_name="Evento",
    )
    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.PROTECT,
        related_name="competencias",
        verbose_name="Disciplina",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="competencias",
        verbose_name="Categoría",
    )
    nombre = models.CharField(
        max_length=150,
        verbose_name="Nombre",
    )
    fecha = models.DateField(
        verbose_name="Fecha",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoCompetenciaChoices.choices,
        default=EstadoCompetenciaChoices.PLANIFICADA,
        verbose_name="Estado",
    )
    class Meta:
        db_table = "competencias"
        verbose_name = "Competencia"
        verbose_name_plural = "Competencias"
        ordering = ["evento", "disciplina", "categoria", "nombre"]
        constraints = [
            # The identity of a competition is Evento + Disciplina + Categoria +
            # nombre, compared case-insensitively so "Final" and "final" are
            # the same competition.
            models.UniqueConstraint(
                "evento",
                "disciplina",
                "categoria",
                Lower("nombre"),
                name="uq_competencia_evento_disciplina_categoria_nombre",
            ),
        ]
        indexes = [
            models.Index(
                fields=["evento", "disciplina", "categoria", "estado", "fecha"],
                name="ix_comp_evt_disc_cat_est_fecha",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nombre} ({self.estado})"
