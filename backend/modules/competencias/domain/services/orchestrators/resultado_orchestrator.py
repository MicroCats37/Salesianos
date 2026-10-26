"""ResultadoOrchestrator — thin async facade of the result of an encounter."""
from injector import inject

from ...results.competencias_results import EncuentroResult
from ...schemas.competencias_schemas import ResultadoEncuentroData
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService
from ..core.resultado_service import ResultadoCoreService
from ..flujos.resultado_flujo import ResultadoFlujo


class ResultadoOrchestrator:
    """Thin orchestrator — it only delegates to the flow (contracts §4.5)."""

    @inject
    def __init__(
        self,
        resultado_core: ResultadoCoreService,
        encuentro_core: EncuentroCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = resultado_core
        self._flujo = ResultadoFlujo(
            resultado_core,
            encuentro_core,
            programacion_core,
        )

    async def registrar_resultado_proceso(
        self,
        encuentro_id,
        data: ResultadoEncuentroData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Register the authoritative winner of an encounter."""
        return await self._flujo.registrar_resultado(
            encuentro_id,
            data,
            actor,
            motivo,
            expected_version,
        )
