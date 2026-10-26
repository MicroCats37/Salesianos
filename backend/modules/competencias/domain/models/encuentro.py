"""
Encuentro — a single match of the bracket.

An encounter belongs to a round and holds two participant slots (nullable:
the bracket may be empty or partial), an optional schedule, the optional
scores and the propagation link to the next encounter of the bracket.

Everything nullable here is nullable ON PURPOSE: an empty or partial bracket
must be readable and editable without inventing participants or advances.
"""
from django.db import models
from django.db.models import F, Q
from simple_history.models import HistoricalRecords

from .competencia_equipo import CompetenciaEquipo
from .ronda import Ronda
from .base import CompetenciaBaseModel
from ..constants import (
    EstadoEncuentroChoices,
    EstadoPreSuspensionChoices,
    SlotDestinoChoices,
)


class Encuentro(CompetenciaBaseModel):
    """
    A match of the bracket.

    Attributes:
        ronda: Round the encounter belongs to.
        orden: Order of the encounter inside the round.
        participante_1: First slot (null while the bracket is incomplete).
        participante_2: Second slot (null while the bracket is incomplete).
        inicio_programado: Scheduled start (null when not scheduled).
        fin_programado: Scheduled end (null when not scheduled).
        estado: Lifecycle state of the encounter.
        estado_pre_suspension: State to resume after a suspension (null when
            the encounter was never suspended).
        iniciado_en: Timestamp of the real start (null until it starts).
        finalizado_en: Timestamp of the real end (null until it finishes).
        es_bye: Marks a manually assigned bye (never chosen automatically).
        puntaje_1: Optional score of the first slot.
        puntaje_2: Optional score of the second slot.
        marcador_detalle: Optional free text (sets, partial scores, notes).
        ganador: Authoritative winner — it must occupy one of the slots.
        siguiente_encuentro: Next encounter of the bracket (link).
        slot_destino: Slot of `siguiente_encuentro` that receives the winner.
        ganador_propagado: Winner that was propagated into this encounter.
        version: Optimistic-locking counter.
    """

    history = HistoricalRecords(
        # The audit motive may be up to 500 characters (design: motivo
        # 5..500), so the default 100-char column of simple_history is
        # widened to a TextField.
        history_change_reason_field=models.TextField(null=True),
    )

    ronda = models.ForeignKey(
        Ronda,
        on_delete=models.PROTECT,
        related_name="encuentros",
        verbose_name="Ronda",
    )
    orden = models.PositiveIntegerField(
        verbose_name="Orden",
    )
    participante_1 = models.ForeignKey(
        CompetenciaEquipo,
        on_delete=models.PROTECT,
        related_name="encuentros_como_participante_1",
        null=True,
        blank=True,
        verbose_name="Participante 1",
    )
    participante_2 = models.ForeignKey(
        CompetenciaEquipo,
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
        choices=EstadoEncuentroChoices.choices,
        default=EstadoEncuentroChoices.BORRADOR,
        verbose_name="Estado",
    )
    estado_pre_suspension = models.CharField(
        max_length=20,
        choices=EstadoPreSuspensionChoices.choices,
        null=True,
        blank=True,
        verbose_name="Estado previo a la suspensión",
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
    es_bye = models.BooleanField(
        default=False,
        verbose_name="¿Es pase libre (bye)?",
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
    )
    ganador = models.ForeignKey(
        CompetenciaEquipo,
        on_delete=models.PROTECT,
        related_name="encuentros_ganados",
        null=True,
        blank=True,
        verbose_name="Ganador",
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
        choices=SlotDestinoChoices.choices,
        null=True,
        blank=True,
        verbose_name="Slot de destino",
    )
    ganador_propagado = models.ForeignKey(
        CompetenciaEquipo,
        on_delete=models.PROTECT,
        related_name="encuentros_con_propagacion",
        null=True,
        blank=True,
        verbose_name="Ganador propagado",
    )
    class Meta:
        db_table = "encuentros"
        verbose_name = "Encuentro"
        verbose_name_plural = "Encuentros"
        ordering = ["ronda", "orden"]
        constraints = [
            # The order of an encounter is unique inside its round.
            models.UniqueConstraint(
                fields=["ronda", "orden"],
                name="uq_encuentro_ronda_orden",
            ),
            # A team never plays against itself.
            models.CheckConstraint(
                condition=(
                    Q(participante_1__isnull=True)
                    | Q(participante_2__isnull=True)
                    | ~Q(participante_1=F("participante_2"))
                ),
                name="ck_encuentro_participantes_distintos",
            ),
            # The schedule is either absent as a whole or a positive interval.
            models.CheckConstraint(
                condition=(
                    Q(inicio_programado__isnull=True, fin_programado__isnull=True)
                    | Q(
                        inicio_programado__isnull=False,
                        fin_programado__isnull=False,
                        fin_programado__gt=F("inicio_programado"),
                    )
                ),
                name="ck_encuentro_horario_intervalo",
            ),
            # The link to the next encounter and its destination slot travel
            # together: one without the other is meaningless.
            models.CheckConstraint(
                condition=(
                    Q(siguiente_encuentro__isnull=True, slot_destino__isnull=True)
                    | Q(siguiente_encuentro__isnull=False, slot_destino__isnull=False)
                ),
                name="ck_encuentro_enlace_slot",
            ),
            # The winner is authoritative and must occupy one of the slots.
            models.CheckConstraint(
                condition=(
                    Q(ganador__isnull=True)
                    | Q(ganador=F("participante_1"), participante_1__isnull=False)
                    | Q(ganador=F("participante_2"), participante_2__isnull=False)
                ),
                name="ck_encuentro_ganador_en_slot",
            ),
        ]
        indexes = [
            models.Index(
                fields=["estado", "inicio_programado", "fin_programado"],
                name="ix_enc_estr_ini_fin",
            ),
        ]

    def __str__(self) -> str:
        return f"Encuentro {self.orden} ({self.estado})"
