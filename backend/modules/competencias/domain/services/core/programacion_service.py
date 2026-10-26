"""
Core sync service of the scheduling of the encounters.

Scheduling is the only operation of the bracket that touches more than one
table at once, so it is also the only one that needs locks:

- the competition (the aggregate root),
- the encounters affected by the change,
- the UNDERLYING teams of the slots (`Equipo`), locked in ascending UUID
  order so two concurrent schedulers can never deadlock.

The overlap check is PORTABLE: it looks at every encounter of every
competition in which one of the teams plays, because a physical team cannot
play two matches at the same time even in two different brackets.
"""
from django.db.models import Q

from modules.salesianos_fest.domain.models import Equipo

from ...constants import EstadoEncuentroChoices
from ...exceptions import InvalidScheduleError
from ...models import Competencia, Encuentro


class ProgramacionCoreService:
    """Locks, interval validation and overlap detection of the schedule."""

    # ── locks ──────────────────────────────────────────────────────────────

    @staticmethod
    def bloquear_competencia(competencia_id) -> Competencia:
        """Lock the competition row of the bracket."""
        return Competencia.objects.select_for_update().get(id=competencia_id)

    @staticmethod
    def bloquear_encuentros(encuentro_ids) -> list[Encuentro]:
        """Lock the affected encounters in ascending UUID order."""
        return list(
            Encuentro.objects.select_for_update()
            .filter(id__in=encuentro_ids)
            .select_related("ronda__competencia")
            .order_by("id")
        )

    @staticmethod
    def bloquear_equipos(equipo_ids) -> list[Equipo]:
        """Lock the underlying teams in ascending UUID order.

        The order is deterministic on purpose: two schedulers that lock the
        same teams in a different order would deadlock.
        """
        if not equipo_ids:
            return []
        return list(
            Equipo.objects.select_for_update()
            .filter(id__in=equipo_ids)
            .order_by("id")
        )

    # ── reads ──────────────────────────────────────────────────────────────

    @staticmethod
    def equipos_de_encuentro(encuentro: Encuentro) -> list[str]:
        """UUIDs of the underlying teams that play in the encounter."""
        equipos = []
        for participante in (encuentro.participante_1, encuentro.participante_2):
            if participante is not None:
                equipos.append(str(participante.equipo_id))
        return equipos

    @staticmethod
    def detectar_solape(
        equipo_ids,
        inicio,
        fin,
        excluir_encuentro_id=None,
    ) -> list[Encuentro]:
        """Return the encounters of the teams that overlap the interval.

        The intervals are SEMI-OPEN (`[inicio, fin)`): two encounters that
        only touch (the end of one is the beginning of the other) do NOT
        overlap. Cancelled encounters never reserve the slot of a team.
        """
        if not equipo_ids or inicio is None or fin is None:
            return []
        # The join to the participants is resolved first: mixing it with the
        # filters of the encounter would make the join multi-valued and the
        # database would refuse the combination.
        encuentros_de_los_equipos = Encuentro.objects.filter(
            Q(participante_1__equipo_id__in=equipo_ids)
            | Q(participante_2__equipo_id__in=equipo_ids)
        ).values("id")
        consultas = Encuentro.objects.filter(
            id__in=encuentros_de_los_equipos,
            inicio_programado__isnull=False,
            fin_programado__isnull=False,
            inicio_programado__lt=fin,
            fin_programado__gt=inicio,
        ).exclude(estado=EstadoEncuentroChoices.CANCELADO)
        if excluir_encuentro_id is not None:
            consultas = consultas.exclude(id=excluir_encuentro_id)
        return list(consultas)

    # ── validations ───────────────────────────────────────────────────────

    @staticmethod
    def validar_horario(competencia: Competencia, inicio, fin) -> None:
        """The schedule must be a positive interval of the day of the bracket.

        The start and the end MUST share the date of the competition: a
        competition happens on a single day.
        """
        if inicio is None or fin is None:
            raise InvalidScheduleError()
        if fin <= inicio:
            raise InvalidScheduleError()
        if inicio.date() != competencia.fecha or fin.date() != competencia.fecha:
            raise InvalidScheduleError()
