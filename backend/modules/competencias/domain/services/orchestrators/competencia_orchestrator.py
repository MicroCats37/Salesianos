"""CompetenciaOrchestrator — thin async facade of the competition commands."""
from injector import inject

from ...results.competencias_results import CompetenciaResult
from ...schemas.competencias_schemas import (
    CompetenciaCreateData,
    CompetenciaUpdateData,
)
from ..core.competencia_service import CompetenciaCoreService
from ..flujos.competencia_flujo import CompetenciaFlujo


class CompetenciaOrchestrator:
    """Thin orchestrator — it only delegates to the flow (contracts §4.5)."""

    @inject
    def __init__(self, competencia_core: CompetenciaCoreService):
        self._core = competencia_core
        self._flujo = CompetenciaFlujo(competencia_core)

    async def crear_competencia_proceso(
        self,
        data: CompetenciaCreateData,
        actor=None,
    ) -> CompetenciaResult:
        """Create a competition."""
        return await self._flujo.crear(data, actor)

    async def actualizar_competencia_proceso(
        self,
        competencia_id,
        data: CompetenciaUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaResult:
        """Update the editable fields of a competition."""
        return await self._flujo.actualizar(
            competencia_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def cambiar_estado_competencia_proceso(
        self,
        competencia_id,
        nuevo_estado,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaResult:
        """Move a competition through its lifecycle."""
        return await self._flujo.cambiar_estado(
            competencia_id,
            nuevo_estado,
            actor,
            motivo,
            expected_version,
        )

    async def eliminar_competencia_proceso(self, competencia_id, actor=None) -> None:
        """Delete a competition that was never used."""
        return await self._flujo.eliminar(competencia_id, actor)
