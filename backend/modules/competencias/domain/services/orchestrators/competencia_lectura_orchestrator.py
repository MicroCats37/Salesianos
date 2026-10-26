"""
CompetenciaLecturaOrchestrator — the thin async facade of the READ surfaces.

One public method per endpoint of the read controllers, and nothing else: it
resolves the scope, delegates the query to the selector and returns a result
object (`contract/django-app-architecture-contract.md` §4.5).

The ORM calls are sync, so they are wrapped with `sync_to_async` — never
`asyncio.to_thread` (the project convention for Django ORM in async code).

There are TWO orchestrators:

- `CompetenciaLecturaOrchestrator` — the ADMINISTRATIVE surface: every
  edition is visible and the `evento_id` filter narrows it.
- `CompetenciaPublicaLecturaOrchestrator` — the PUBLIC surface: only the
  AUTHORIZED (active) editions are visible. The scope is resolved on the
  server; the client never chooses it.
"""
from datetime import date

from asgiref.sync import sync_to_async
from injector import inject

from modules.competencias.domain.exceptions import CompetenciaNotFoundError
from modules.competencias.domain.results.competencias_results import (
    AgendaResult,
    CompetenciaDetalleResult,
    CompetenciaEquipoResult,
    CompetenciaListadoResult,
    CuadroResult,
    EncuentroResult,
    RondaResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaFiltrosData,
    EncuentroFiltrosData,
)
from modules.competencias.domain.selectors import (
    AlcanceEventoSelector,
    CompetenciaSelector,
    EncuentroSelector,
)


class CompetenciaLecturaOrchestrator:
    """Async facade of the reads of the bracket (administrative scope)."""

    @inject
    def __init__(
        self,
        competencia_selector: CompetenciaSelector,
        encuentro_selector: EncuentroSelector,
        alcance_selector: AlcanceEventoSelector,
    ):
        self._competencia_selector = competencia_selector
        self._encuentro_selector = encuentro_selector
        self._alcance_selector = alcance_selector

        self._listar = sync_to_async(competencia_selector.listar)
        self._detalle = sync_to_async(competencia_selector.obtener_detalle)
        self._cuadro = sync_to_async(competencia_selector.obtener_cuadro)
        self._equipos = sync_to_async(competencia_selector.listar_equipos)
        self._rondas = sync_to_async(competencia_selector.listar_rondas)
        self._encuentros = sync_to_async(encuentro_selector.listar)
        self._agenda = sync_to_async(encuentro_selector.obtener_agenda)
        self._autorizados = sync_to_async(alcance_selector.eventos_autorizados)

    # ── scope ──────────────────────────────────────────────────────────────

    async def _eventos_permitidos(self) -> list[str] | None:
        """Return the events the reader may read.

        `None` means "every edition": the administrative surface may read all
        of them and narrow the scope with the `evento_id` filter.
        """
        return None

    # ── reads ──────────────────────────────────────────────────────────────

    async def listar_competencias(
        self,
        filtros: CompetenciaFiltrosData,
    ) -> list[CompetenciaListadoResult]:
        """Return the competitions of the scope with their counters."""
        eventos = await self._eventos_permitidos()
        return await self._listar(filtros, eventos)

    async def obtener_competencia(
        self,
        competencia_id,
    ) -> CompetenciaDetalleResult:
        """Return the detail of one competition.

        Raises:
            CompetenciaNotFoundError: when the competition does not exist OR
                when it is outside of the authorized scope (the surface never
                confirms the existence of a resource the reader cannot see).
        """
        eventos = await self._eventos_permitidos()
        resultado = await self._detalle(competencia_id, eventos)
        if resultado is None:
            raise CompetenciaNotFoundError()
        return resultado

    async def obtener_cuadro(self, competencia_id) -> CuadroResult:
        """Return the bracket of one competition (it may be empty or partial).

        Raises:
            CompetenciaNotFoundError: when the competition does not exist OR
                when it is outside of the authorized scope.
        """
        eventos = await self._eventos_permitidos()
        resultado = await self._cuadro(competencia_id, eventos)
        if resultado is None:
            raise CompetenciaNotFoundError()
        return resultado

    async def listar_equipos(
        self,
        competencia_id,
    ) -> list[CompetenciaEquipoResult]:
        """Return the teams registered in the bracket."""
        return await self._equipos(competencia_id)

    async def listar_rondas(self, competencia_id) -> list[RondaResult]:
        """Return the rounds of the bracket."""
        return await self._rondas(competencia_id)

    async def listar_encuentros(
        self,
        filtros: EncuentroFiltrosData,
    ) -> list[EncuentroResult]:
        """Return the encounters of the scope."""
        eventos = await self._eventos_permitidos()
        return await self._encuentros(filtros, eventos)

    async def obtener_agenda(
        self,
        fecha: date | None,
        filtros: EncuentroFiltrosData,
    ) -> AgendaResult:
        """Return the agenda of ONE day (today when the client does not say)."""
        eventos = await self._eventos_permitidos()
        dia = fecha if fecha is not None else date.today()
        return await self._agenda(dia, filtros, eventos)


class CompetenciaPublicaLecturaOrchestrator(CompetenciaLecturaOrchestrator):
    """Async facade of the PUBLIC reads — the scope is the authorized events.

    The public surface is READ-ONLY and it never sees a competition of an
    edition the reader is not authorized for.
    """

    async def _eventos_permitidos(self) -> list[str]:
        """Return the AUTHORIZED (active) editions of the public surface."""
        return await self._autorizados()


__all__ = [
    "CompetenciaLecturaOrchestrator",
    "CompetenciaPublicaLecturaOrchestrator",
]
