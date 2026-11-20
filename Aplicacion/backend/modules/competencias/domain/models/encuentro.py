"""`Encuentro` — un encuentro del cuadro.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Invariantes:

- **Todo lo que puede faltar, falta a propósito**: el cuadro puede estar
  vacío o parcial (`frontend/05` §1.3). Un encuentro sin participantes y sin
  horario es un `BORRADOR` LEGÍTIMO.
- **Los participantes son `CompetenciaEquipo`, no `Equipo`**: el cuadro
  referencia la PARTICIPACIÓN en la competencia, no al equipo de inscripción.
  Así una retirada de equipo no reescribe la historia del cuadro.
- **El horario es un intervalo POSITIVO** dentro del día de la competencia.
- **El enlace y su slot viajan juntos**: uno sin el otro no significa nada.
- **El ganador es autoritativo y ocupa uno de los slots**: si no lo ocupara,
  el resultado sería una invención.
- **El winner propagado se registra aparte** (`ganador_propagado`): una
  corrección posterior puede distinguir un participante propagado de uno
  colocado a mano, y así NUNCA toca una colocación manual.

Los modelos son planos y anémicos
(`contract/django-app-architecture-contract.md` §6).
"""

from django.db import models
from django.db.models import F, Q

from modules.competencias.domain.constants import (
    EstadoEncuentro,
    SlotDestino,
)
from modules.competencias.domain.models.base import CompetenciaBaseModel


class Encuentro(CompetenciaBaseModel):
    """Un encuentro del cuadro."""

    ronda = models.ForeignKey(
        "competencias.Ronda",
        on_delete=models.PROTECT,
        related_name="encuentros",
        verbose_name="Ronda",
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden",
        help_text="Orden del encuentro dentro de su ronda.",
    )
    participante_1 = models.ForeignKey(
        "competencias.CompetenciaEquipo",
        on_delete=models.PROTECT,
        related_name="encuentros_como_participante_1",
        null=True,
        blank=True,
        verbose_name="Participante 1",
    )
    participante_2 = models.ForeignKey(
        "competencias.CompetenciaEquipo",
        on_delete=models.PROTECT,
        related_name="encuentros_como_participante_2",
        null=True,
        blank=True,
        verbose_name="Participante 2",
    )
    inicio_programado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Inicio programado",
    )
    fin_programado = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fin programado",
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoEncuentro.choices,
        default=EstadoEncuentro.BORRADOR,
        verbose_name="Estado",
    )
    es_bye = models.BooleanField(
        default=False,
        verbose_name="¿Es pase libre (bye)?",
        help_text=(
            "Bye MANUAL: lo decide el administrador y exige exactamente un "
            "equipo. El sistema NUNCA inventa un bye."
        ),
    )
    puntaje_1 = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Puntaje participante 1",
    )
    puntaje_2 = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Puntaje participante 2",
    )
    marcador_detalle = models.CharField(
        max_length=500,
        default="",
        blank=True,
        verbose_name="Detalle del marcador",
        help_text="Marcador opcional e informativo: nunca decide el ganador.",
    )
    ganador = models.ForeignKey(
        "competencias.CompetenciaEquipo",
        on_delete=models.PROTECT,
        related_name="encuentros_ganados",
        null=True,
        blank=True,
        verbose_name="Ganador",
        help_text="Ganador AUTORITATIVO: siempre ocupa uno de los dos slots.",
    )
    siguiente_encuentro = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="encuentros_siguientes",
        null=True,
        blank=True,
        verbose_name="Siguiente encuentro",
    )
    slot_destino = models.CharField(
        max_length=20,
        choices=SlotDestino.choices,
        null=True,
        blank=True,
        verbose_name="Slot de destino",
        help_text="Slot del siguiente encuentro que recibe al ganador propagado.",
    )
    ganador_propagado = models.ForeignKey(
        "competencias.CompetenciaEquipo",
        on_delete=models.PROTECT,
        related_name="encuentros_con_propagacion",
        null=True,
        blank=True,
        verbose_name="Ganador propagado",
        help_text=(
            "Ganador que el sistema propagó a este encuentro. Distingue una "
            "colocación propagada de una manual: la corrección nunca pisa la "
            "manual."
        ),
    )
    iniciado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Iniciado en",
    )
    finalizado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Finalizado en",
    )

    class Meta:
        db_table = "competencia_encuentros"
        verbose_name = "Encuentro"
        verbose_name_plural = "Encuentros"
        ordering = ["ronda_id", "orden"]
        constraints = [
            # El orden de un encuentro es único dentro de su ronda.
            models.UniqueConstraint(
                fields=["ronda", "orden"],
                name="competencia_encuentro_orden_unico_por_ronda",
            ),
            # Un equipo nunca juega contra sí mismo.
            models.CheckConstraint(
                condition=(
                    Q(participante_1__isnull=True)
                    | Q(participante_2__isnull=True)
                    | ~Q(participante_1=F("participante_2"))
                ),
                name="competencia_encuentro_participantes_distintos",
            ),
            # El horario es ausente por completo o un intervalo positivo.
            models.CheckConstraint(
                condition=(
                    Q(inicio_programado__isnull=True, fin_programado__isnull=True)
                    | Q(
                        inicio_programado__isnull=False,
                        fin_programado__isnull=False,
                        fin_programado__gt=F("inicio_programado"),
                    )
                ),
                name="competencia_encuentro_horario_intervalo",
            ),
            # El enlace y su slot viajan juntos.
            models.CheckConstraint(
                condition=(
                    Q(siguiente_encuentro__isnull=True, slot_destino__isnull=True)
                    | Q(siguiente_encuentro__isnull=False, slot_destino__isnull=False)
                ),
                name="competencia_encuentro_enlace_slot",
            ),
            # El ganador es autoritativo y ocupa uno de los slots.
            models.CheckConstraint(
                condition=(
                    Q(ganador__isnull=True)
                    | Q(ganador=F("participante_1"), participante_1__isnull=False)
                    | Q(ganador=F("participante_2"), participante_2__isnull=False)
                ),
                name="competencia_encuentro_ganador_en_slot",
            ),
        ]
        indexes = [
            models.Index(
                fields=["estado", "inicio_programado", "fin_programado"],
                name="ix_comp_enc_estr_ini_fin",
            ),
        ]

    def __str__(self) -> str:
        return f"Encuentro {self.orden} ({self.estado})"


__all__ = ["Encuentro"]
