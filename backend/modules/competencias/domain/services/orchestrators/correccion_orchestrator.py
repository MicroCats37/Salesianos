"""CorreccionOrchestrator — thin async facade of the correction of the winner."""
from injector import inject

from ...results.competencias_results import (
    CorreccionPreviewResult,
    CorreccionResult,
)
from ...schemas.competencias_schemas import CorreccionGanadorData
from ..core.correccion_service import CorreccionCoreService
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService
from ..flujos.correccion_flujo import CorreccionFlujo


class CorreccionOrchestrator:
    """Thin orchestrator — it only delegates to the flow (contracts §4.5)."""

    @inject
    def __init__(
        self,
        correccion_core: CorreccionCoreService,
        encuentro_core: EncuentroCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = correccion_core
        self._flujo = CorreccionFlujo(
            correccion_core,
            encuentro_core,
            programacion_core,
        )

    async def previsualizar_correccion_proceso(
        self,
        encuentro_id,
        ganador_nuevo_id,
    ) -> CorreccionPreviewResult:
        """Return the impact of the correction before applying it."""
        return await self._flujo.previsualizar(encuentro_id, ganador_nuevo_id)

    async def corregir_ganador_proceso(
        self,
        encuentro_id,
        data: CorreccionGanadorData,
        actor=None,
        expected_version=None,
    ) -> CorreccionResult:
        """Correct the authoritative winner of an encounter."""
        return await self._flujo.corregir(
            encuentro_id,
            data,
            actor,
            expected_version,
        )
