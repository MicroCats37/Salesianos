"""RondaOrchestrator — thin async facade of the rounds of the bracket."""
from injector import inject

from ...results.competencias_results import RondaResult
from ...schemas.competencias_schemas import RondaCreateData, RondaUpdateData
from ..core.competencia_service import CompetenciaCoreService
from ..core.ronda_service import RondaCoreService
from ..flujos.ronda_flujo import RondaFlujo


class RondaOrchestrator:
    """Thin orchestrator — it only delegates to the flow (contracts §4.5)."""

    @inject
    def __init__(
        self,
        ronda_core: RondaCoreService,
        competencia_core: CompetenciaCoreService,
    ):
        self._core = ronda_core
        self._flujo = RondaFlujo(ronda_core, competencia_core)

    async def crear_ronda_proceso(
        self,
        competencia_id,
        data: RondaCreateData,
        actor=None,
    ) -> RondaResult:
        """Create a round of the bracket."""
        return await self._flujo.crear(competencia_id, data, actor)

    async def actualizar_ronda_proceso(
        self,
        ronda_id,
        data: RondaUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> RondaResult:
        """Update the label or the order of a round."""
        return await self._flujo.actualizar(
            ronda_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def invalidar_ronda_proceso(
        self,
        ronda_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> RondaResult:
        """Invalidate a round (it is never deleted)."""
        return await self._flujo.invalidar(
            ronda_id,
            actor,
            motivo,
            expected_version,
        )

    async def eliminar_ronda_proceso(self, ronda_id, actor=None) -> None:
        """Delete a round that was never used."""
        return await self._flujo.eliminar(ronda_id, actor)
