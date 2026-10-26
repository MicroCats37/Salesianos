"""
AdminEquipoSelector — read queries of the teams (A7).

The roster state (`COMPLETO` / `INCOMPLETO`) is DERIVED, never persisted: a
team is complete when its ACTIVE participations reach the `min_jugadores` of
its discipline (`modules.salesianos_fest.domain.models.Disciplina`). The
derivation happens HERE, in SQL, with a HAVING clause over the aggregate —
never in the frontend (`contract/api-wrapper-presenter-contract.md` §7).

Read-only by construction: no method in this selector writes.
"""
from django.db.models import Count, F, Q

from modules.administracion.domain.results.admin_inscripcion_results import (
    AdminEquipoListItemResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.salesianos_fest.domain.constants import EstadoParticipacionChoices
from modules.salesianos_fest.domain.models import Equipo

ROSTER_COMPLETO = "COMPLETO"
ROSTER_INCOMPLETO = "INCOMPLETO"


def _referencia_corta(identificador) -> str:
    """Return a short display reference of an id."""
    return str(identificador)[:8].upper()


class AdminEquipoSelector:
    """Read-only queries for the teams of an event."""

    def listar(
        self,
        evento_id: str,
        *,
        inscripcion_id: str | None = None,
        disciplina_id: str | None = None,
        estado: str | None = None,
        roster: str | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminEquipoListItemResult], int]:
        """Return the page of teams and the total of matching rows.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            inscripcion_id: filter by the registration that owns the team.
            disciplina_id: filter by the discipline.
            estado: filter by the team state (ACTIVE / CANCELLED).
            roster: filter by the DERIVED roster state (COMPLETE / INCOMPLETE).
            q: free text over the team name.
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = Equipo.objects.filter(inscripcion__evento_id=evento_id)

        if inscripcion_id:
            qs = qs.filter(inscripcion_id=inscripcion_id)

        if disciplina_id:
            qs = qs.filter(disciplina_id=disciplina_id)

        if estado:
            qs = qs.filter(estado=estado)

        if q:
            qs = qs.filter(nombre__icontains=q)

        if roster:
            qs = self._filtrar_roster(qs, roster)

        total = qs.count()

        filas = list(
            qs.select_related("inscripcion", "disciplina", "categoria")
            .order_by(params.ordering)[params.offset: params.offset + params.page_size]
        )

        roster_map = self._roster_por_equipo([fila.id for fila in filas])

        items: list[AdminEquipoListItemResult] = []
        for fila in filas:
            jugadores, minimo = roster_map.get(
                str(fila.id),
                (0, fila.disciplina.min_jugadores or 0),
            )
            items.append(
                AdminEquipoListItemResult(
                    id=str(fila.id),
                    nombre=fila.nombre,
                    disciplina_sigla=fila.disciplina.sigla,
                    disciplina_nombre=fila.disciplina.nombre,
                    categoria_nombre=fila.categoria.nombre if fila.categoria else None,
                    inscripcion_id=str(fila.inscripcion_id),
                    inscripcion_ref=_referencia_corta(fila.inscripcion_id),
                    estado=fila.estado,
                    jugadores_registrados=jugadores,
                    minimo_deportivo=minimo,
                    faltantes=max(0, minimo - jugadores),
                    estado_roster=(
                        ROSTER_COMPLETO if jugadores >= minimo else ROSTER_INCOMPLETO
                    ),
                    created_at=fila.created_at,
                )
            )

        return items, total

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _filtrar_roster(qs, roster: str):
        """Restrict a team queryset to the COMPLETE or INCOMPLETE teams.

        The comparison happens in SQL: the count of ACTIVE participations is
        compared with the `min_jugadores` of the discipline through a HAVING
        clause, so the filter is applied BEFORE the pagination.
        """
        anotado = qs.annotate(
            jugadores=Count(
                "participaciones",
                filter=Q(participaciones__estado=EstadoParticipacionChoices.ACTIVA),
            )
        )

        if roster == ROSTER_COMPLETO:
            return anotado.filter(jugadores__gte=F("disciplina__min_jugadores"))

        return anotado.filter(jugadores__lt=F("disciplina__min_jugadores"))

    @staticmethod
    def _roster_por_equipo(equipo_ids: list) -> dict[str, tuple[int, int]]:
        """Return `(jugadores, minimo)` of every team of the given ids."""
        if not equipo_ids:
            return {}

        filas = (
            Equipo.objects
            .filter(id__in=equipo_ids)
            .values("id", "disciplina__min_jugadores")
            .annotate(
                jugadores=Count(
                    "participaciones",
                    filter=Q(participaciones__estado=EstadoParticipacionChoices.ACTIVA),
                )
            )
        )

        return {
            str(fila["id"]): (
                fila["jugadores"] or 0,
                fila["disciplina__min_jugadores"] or 0,
            )
            for fila in filas
        }


__all__ = ["AdminEquipoSelector"]
