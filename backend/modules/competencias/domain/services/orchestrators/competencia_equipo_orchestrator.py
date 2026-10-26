"""CompetenciaEquipoOrchestrator — thin async facade of the teams of the bracket."""
from injector import inject

from ...results.competencias_results import CompetenciaEquipoResult
from ...schemas.competencias_schemas import CompetenciaEquipoUpdateData
from ..core.competencia_equipo_service import CompetenciaEquipoCoreService
from ..core.competencia_service import CompetenciaCoreService
from ..flujos.competencia_equipo_flujo import CompetenciaEquipoFlujo


class CompetenciaEquipoOrchestrator:
    """Thin orchestrator — it only delegates to the flow (contracts §4.5)."""

    @inject
    def __init__(
        self,
        competencia_equipo_core: CompetenciaEquipoCoreService,
        competencia_core: CompetenciaCoreService,
    ):
        self._core = competencia_equipo_core
        self._flujo = CompetenciaEquipoFlujo(competencia_equipo_core, competencia_core)

    async def incorporar_equipo_proceso(
        self,
        competencia_id,
        equipo_id,
        orden,
        actor=None,
    ) -> CompetenciaEquipoResult:
        """Register a team in the bracket with its manual order."""
        return await self._flujo.incorporar(competencia_id, equipo_id, orden, actor)

    async def actualizar_equipo_proceso(
        self,
        competencia_equipo_id,
        data: CompetenciaEquipoUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Update the manual order or the state of the participation."""
        return await self._flujo.actualizar(
            competencia_equipo_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def retirar_equipo_proceso(
        self,
        competencia_equipo_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Withdraw a team from the bracket."""
        return await self._flujo.retirar(
            competencia_equipo_id,
            actor,
            motivo,
            expected_version,
        )

    async def reactivar_equipo_proceso(
        self,
        competencia_equipo_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Bring a withdrawn team back into the bracket."""
        return await self._flujo.reactivar(
            competencia_equipo_id,
            actor,
            motivo,
            expected_version,
        )
