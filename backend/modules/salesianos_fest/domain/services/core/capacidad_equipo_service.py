"""
CapacidadEquipoService — the SINGLE owner of the capacity state of a team.

The administrative teams table used to publish the minimum of the discipline
(`minimo_deportivo`) and let the reader render it as a fraction next to the
registered players. That fraction answered the wrong question — "10/7" reads
as "10 of 7 slots" — and the HARD cap of the discipline (`max_jugadores`),
which the domain enforces on every write, was published nowhere: a team at the
cap was indistinguishable from a comfortable team.

This service publishes the capacity state instead: the answer to "does this
team still have room?".

The state is DERIVED, never typed: it is a pure function of the two facts the
domain already owns — the count of ACTIVE participations of the team and the
`max_jugadores` of its discipline.

The rules are evaluated IN THIS ORDER (the first match wins):

1. `CON_CUPOS` — the discipline declares NO cap (`max_jugadores <= 0`), so the
   team can never be full.
2. `AL_LIMITE` — the registered players REACHED the cap of the discipline.
3. `CON_CUPOS` — the team still has room.

The threshold is the SAME one the write path respects: `ParticipacionCoreService`
rejects a new participation when the team already holds `max_jugadores` active
players (`RosterCompletoError`), so `AL_LIMITE` is exactly the state in which
the next participant cannot be added.

The service owns the PRECEDENCE, never the data: it receives the facts of one
team and returns its verdict. It never queries the database and never writes.
"""
from modules.salesianos_fest.domain.constants import EstadoCapacidadEquipoChoices


class CapacidadEquipoService:
    """The capacity state of a team against the cap of its discipline."""

    @staticmethod
    def estado_capacidad(*, jugadores: int, maximo: int) -> str:
        """
        Return the capacity state of one team.

        Args:
            jugadores: the count of ACTIVE participations of the team.
            maximo: the hard cap of the discipline (`max_jugadores`).

        Returns:
            One code of `EstadoCapacidadEquipoChoices`.
        """
        if maximo <= 0:
            return EstadoCapacidadEquipoChoices.CON_CUPOS

        if jugadores >= maximo:
            return EstadoCapacidadEquipoChoices.AL_LIMITE

        return EstadoCapacidadEquipoChoices.CON_CUPOS


__all__ = ["CapacidadEquipoService"]
