"""AvanceOrchestrator — thin async facade of the advance of the bracket."""
from injector import inject

from ...results.competencias_results import AvancePreviewResult, AvanceResult
from ..core.avance_service import AvanceCoreService
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService
from ..flujos.avance_flujo import AvanceFlujo


class AvanceOrchestrator:
    """Thin orchestrator — it only delegates to the flow (contracts §4.5)."""

    @inject
    def __init__(
        self,
        avance_core: AvanceCoreService,
        encuentro_core: EncuentroCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = avance_core
        self._flujo = AvanceFlujo(
            avance_core,
            encuentro_core,
            programacion_core,
        )

    async def previsualizar_avance_proceso(
        self,
        encuentro_id,
    ) -> AvancePreviewResult:
        """Propose the placement of the winner in the linked slot."""
        return await self._flujo.previsualizar(encuentro_id)

    async def confirmar_avance_proceso(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> AvanceResult:
        """Place the winner in the linked slot and record the propagation."""
        return await self._flujo.confirmar(
            encuentro_id,
            actor,
            motivo,
            expected_version,
        )
