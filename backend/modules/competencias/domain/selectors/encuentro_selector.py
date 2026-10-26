"""
EncuentroSelector — read-only queries of the encounters of the bracket.

The selector loads the relations and returns DOMAIN RESULT DTOs (never HTTP
schemas): the presenter of the presentation layer maps them
(`contract/api-wrapper-presenter-contract.md` §3).

The authorized scope is applied by the server: `eventos_permitidos`
restricts the result to the events the reader is authorized for and `None`
means "no restriction" (the administrative surface).

Read-only by construction: no method in this selector writes.
"""
from datetime import date

from modules.competencias.domain.models import Encuentro
from modules.competencias.domain.results.competencias_results import (
    AgendaResult,
    EncuentroResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    EncuentroFiltrosData,
)


class EncuentroSelector:
    """Read-only queries of `Encuentro`."""

    def listar(
        self,
        filtros: EncuentroFiltrosData | None = None,
        eventos_permitidos: list[str] | None = None,
    ) -> list[EncuentroResult]:
        """Return the encounters of the scope.

        The filters combine with AND. The encounters WITHOUT a schedule are
        part of the result: an empty or partial bracket must be readable.
        """
        filtros = filtros or EncuentroFiltrosData()
        qs = (
            Encuentro.objects.select_related(
                "ronda__competencia",
                "participante_1__equipo",
                "participante_2__equipo",
            )
        )
        qs = self._aplicar_filtros(qs, filtros)
        qs = self._aplicar_alcance(qs, eventos_permitidos)
        qs = qs.order_by("ronda__orden", "orden")
        return [EncuentroResult.desde(encuentro) for encuentro in qs]

    def obtener_agenda(
        self,
        fecha: date,
        filtros: EncuentroFiltrosData | None = None,
        eventos_permitidos: list[str] | None = None,
    ) -> AgendaResult:
        """Return the agenda of ONE day.

        The agenda is TEMPORAL: it lists the encounters whose schedule starts
        that day. A day without encounters is a valid answer (an empty
        agenda), never an error.
        """
        filtros = filtros or EncuentroFiltrosData()
        filtros = filtros.model_copy(update={"fecha": fecha})
        encuentros = self.listar(filtros, eventos_permitidos)
        return AgendaResult(
            fecha=fecha,
            total=len(encuentros),
            encuentros=encuentros,
        )

    # ── internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _aplicar_alcance(qs, eventos_permitidos: list[str] | None):
        """Restrict the query to the events the reader is authorized for."""
        if eventos_permitidos is None:
            return qs
        return qs.filter(ronda__competencia__evento_id__in=eventos_permitidos)

    @staticmethod
    def _aplicar_filtros(qs, filtros: EncuentroFiltrosData):
        """Apply the filters of the read surface (they combine with AND)."""
        if filtros.evento_id:
            qs = qs.filter(ronda__competencia__evento_id=filtros.evento_id)
        if filtros.competencia_id:
            qs = qs.filter(ronda__competencia_id=filtros.competencia_id)
        if filtros.ronda_id:
            qs = qs.filter(ronda_id=filtros.ronda_id)
        if filtros.disciplina_id:
            qs = qs.filter(ronda__competencia__disciplina_id=filtros.disciplina_id)
        if filtros.categoria_id:
            qs = qs.filter(ronda__competencia__categoria_id=filtros.categoria_id)
        if filtros.estado:
            qs = qs.filter(estado=filtros.estado)
        if filtros.fecha:
            qs = qs.filter(inicio_programado__date=filtros.fecha)
        return qs


__all__ = ["EncuentroSelector"]
