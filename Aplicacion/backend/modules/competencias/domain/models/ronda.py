"""`Ronda` — una ronda del cuadro.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Invariantes:

- Una ronda pertenece a UNA competencia.
- La etiqueta y el orden son ÚNICOS dentro de la competencia: el cuadro tiene
  una lectura única.
- Una ronda `INVALIDADA` se conserva: el cuadro que se trazó con ella sigue
  en la historia. Invalidar NO es borrar (`RN-K02`).
"""

from django.db import models

from modules.competencias.domain.constants import EstadoRonda
from modules.competencias.domain.models.base import CompetenciaBaseModel


class Ronda(CompetenciaBaseModel):
    """Una ronda del cuadro de una competencia."""

    competencia = models.ForeignKey(
        "competencias.Competencia",
        on_delete=models.PROTECT,
        related_name="rondas",
        verbose_name="Competencia",
    )
    etiqueta = models.CharField(
        max_length=80,
        verbose_name="Etiqueta",
        help_text="Nombre de la ronda: 'Cuartos de final', 'Final', ...",
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden",
        help_text="Orden de la ronda dentro del cuadro. Las rondas avanzan hacia él.",
    )
    estado = models.CharField(
        max_length=16,
        choices=EstadoRonda.choices,
        default=EstadoRonda.ACTIVA,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "competencia_rondas"
        verbose_name = "Ronda"
        verbose_name_plural = "Rondas"
        ordering = ["competencia_id", "orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["competencia", "etiqueta"],
                name="competencia_ronda_etiqueta_unica",
            ),
            models.UniqueConstraint(
                fields=["competencia", "orden"],
                name="competencia_ronda_orden_unico",
            ),
        ]
        indexes = [
            models.Index(
                fields=["competencia", "estado", "orden"],
                name="ix_cmp_ron_cmp_est_ord",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.etiqueta} ({self.estado})"


__all__ = ["Ronda"]
