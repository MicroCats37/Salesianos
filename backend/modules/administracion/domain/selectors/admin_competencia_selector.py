"""
AdminCompetenciaSelector — the KPI/alert aggregation of the bracket.

The administration area keeps ZERO tables: it only AGGREGATES what the
owning module (`modules.competencias`) owns. The selector reads the models
of the owning module through their `domain/models` re-exports and never
re-implements a business rule of the bracket
(`contract/api-wrapper-presenter-contract.md` §1 — "cross-module data access
goes through selectors").

What this aggregation adds to the operational overview:

- the counters of the competitions, the teams of the bracket and the
  encounters,
- the ALERTS of the bracket: the situations the administrator has to
  resolve (an empty bracket, a match without a team, a winner that was
  never propagated).

Read-only by construction: no method in this selector writes.
"""
from django.db.models import Count, Q

from modules.competencias.domain.constants import (
    EstadoCompetenciaEquipoChoices,
    EstadoEncuentroChoices,
)
from modules.competencias.domain.models import Competencia, CompetenciaEquipo
from modules.competencias.domain.models import Encuentro, Ronda

#: States of an encounter that need a team in BOTH slots to be played.
ESTADOS_EN_JUEGO = {
    EstadoEncuentroChoices.PROGRAMADO,
    EstadoEncuentroChoices.EN_CURSO,
}


class AdminCompetenciaSelector:
    """Read-only KPI/alert aggregation of the bracket of an event."""

    # ── KPIs ───────────────────────────────────────────────────────────────

    def contar_competencias(self, evento_id: str) -> dict:
        """Return the counters of the competitions of the event.

        Returns:
            `{"total", "por_estado", "con_rondas", "con_equipos"}`.
        """
        qs = Competencia.objects.filter(evento_id=evento_id)

        por_estado = {
            fila["estado"]: fila["cantidad"]
            for fila in qs.values("estado").annotate(cantidad=Count("id"))
        }

        con_rondas = qs.filter(rondas__isnull=False).distinct().count()
        con_equipos = qs.filter(
            competencia_equipos__estado=EstadoCompetenciaEquipoChoices.ACTIVO
        ).distinct().count()

        return {
            "total": sum(por_estado.values()),
            "por_estado": por_estado,
            "con_rondas": con_rondas,
            "con_equipos": con_equipos,
        }

    def contar_equipos(self, evento_id: str) -> dict:
        """Return the counters of the teams registered in the brackets.

        Only the ACTIVE entries are counted: a withdrawn team is not part of
        the operation.
        """
        base = CompetenciaEquipo.objects.filter(
            competencia__evento_id=evento_id,
        )
        por_estado = {
            fila["estado"]: fila["cantidad"]
            for fila in base.values("estado").annotate(cantidad=Count("id"))
        }
        return {
            "total": sum(por_estado.values()),
            "activos": por_estado.get(EstadoCompetenciaEquipoChoices.ACTIVO, 0),
            "retirados": por_estado.get(EstadoCompetenciaEquipoChoices.RETIRADO, 0),
        }

    def contar_encuentros(self, evento_id: str) -> dict:
        """Return the counters of the encounters of the event.

        `sin_horario` counts the encounters that were never scheduled and
        `byes` the MANUAL byes of the bracket (the system never chooses one).
        """
        base = Encuentro.objects.filter(ronda__competencia__evento_id=evento_id)

        por_estado = {
            fila["estado"]: fila["cantidad"]
            for fila in base.values("estado").annotate(cantidad=Count("id"))
        }

        sin_horario = base.filter(
            inicio_programado__isnull=True,
            fin_programado__isnull=True,
        ).count()

        return {
            "total": sum(por_estado.values()),
            "por_estado": por_estado,
            "sin_horario": sin_horario,
            "finalizados": por_estado.get(EstadoEncuentroChoices.FINALIZADO, 0),
            "byes": base.filter(es_bye=True).count(),
            "rondas": Ronda.objects.filter(
                competencia__evento_id=evento_id
            ).count(),
        }

    # ── alertas ────────────────────────────────────────────────────────────

    def listar_alertas(self, evento_id: str) -> list[dict]:
        """Return the alerts of the bracket of the event.

        Every alert carries a STABLE code, the number of cases and a fixed
        message (never an identifier, never a raw exception).

        The three alerts are:

        - `CUADRO_SIN_EQUIPOS`: a competition with rounds but without teams —
          the bracket cannot be played yet,
        - `ENCUENTRO_SIN_PARTICIPANTE`: an encounter that is scheduled (or in
          course) with an empty slot,
        - `GANADOR_NO_PROPAGADO`: a finished encounter whose winner was never
          placed in the linked slot of the next encounter.
        """
        alertas = []

        alertas.append(
            self._alerta(
                "CUADRO_SIN_EQUIPOS",
                self._competencias_sin_equipos(evento_id),
                "Hay competencias con rondas pero sin equipos registrados.",
            )
        )
        alertas.append(
            self._alerta(
                "ENCUENTRO_SIN_PARTICIPANTE",
                self._encuentros_sin_participante(evento_id),
                "Hay encuentros programados o en curso con un participante vacío.",
            )
        )
        alertas.append(
            self._alerta(
                "GANADOR_NO_PROPAGADO",
                self._ganadores_no_propagados(evento_id),
                "Hay encuentros finalizados cuyo ganador no se propagó al "
                "encuentro siguiente.",
            )
        )

        return [alerta for alerta in alertas if alerta["cantidad"] > 0]

    # ── internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _alerta(codigo: str, cantidad: int, mensaje: str) -> dict:
        """Build one alert of the aggregation."""
        return {"codigo": codigo, "cantidad": cantidad, "mensaje": mensaje}

    @staticmethod
    def _competencias_sin_equipos(evento_id: str) -> int:
        """Count the competitions that have rounds but no active team."""
        return (
            Competencia.objects.filter(evento_id=evento_id, rondas__isnull=False)
            .exclude(
                competencia_equipos__estado=EstadoCompetenciaEquipoChoices.ACTIVO
            )
            .distinct()
            .count()
        )

    @staticmethod
    def _encuentros_sin_participante(evento_id: str) -> int:
        """Count the encounters that are scheduled with an empty slot."""
        return (
            Encuentro.objects.filter(
                ronda__competencia__evento_id=evento_id,
                estado__in=ESTADOS_EN_JUEGO,
            )
            .filter(Q(participante_1__isnull=True) | Q(participante_2__isnull=True))
            .distinct()
            .count()
        )

    @staticmethod
    def _ganadores_no_propagados(evento_id: str) -> int:
        """Count the finished encounters whose winner never reached the link.

        The check walks the FINISHED encounters that have a link: the winner
        must occupy the slot of the destination. The set is bounded by the
        bracket of ONE event and it is read with ONE query.
        """
        encuentros = list(
            Encuentro.objects.filter(
                ronda__competencia__evento_id=evento_id,
                estado=EstadoEncuentroChoices.FINALIZADO,
                siguiente_encuentro__isnull=False,
            ).select_related("siguiente_encuentro")
        )

        pendientes = 0
        for encuentro in encuentros:
            destino = encuentro.siguiente_encuentro
            campo = (
                "participante_1"
                if encuentro.slot_destino == "PARTICIPANTE_1"
                else "participante_2"
            )
            ocupante = getattr(destino, campo, None)
            if ocupante is None or ocupante.id != encuentro.ganador_id:
                pendientes += 1
        return pendientes


__all__ = ["AdminCompetenciaSelector"]
