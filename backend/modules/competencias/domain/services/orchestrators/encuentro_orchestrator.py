"""EncuentroOrchestrator — thin async facade of the commands of the encounters."""
from injector import inject

from ...results.competencias_results import EncuentroResult
from ...schemas.competencias_schemas import (
    EncuentroCreateData,
    EncuentroProgramacionData,
)
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService
from ..core.ronda_service import RondaCoreService
from ..flujos.encuentro_flujo import EncuentroFlujo


class EncuentroOrchestrator:
    """Thin orchestrator — it only delegates to the flow (contracts §4.5)."""

    @inject
    def __init__(
        self,
        encuentro_core: EncuentroCoreService,
        ronda_core: RondaCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = encuentro_core
        self._flujo = EncuentroFlujo(
            encuentro_core,
            ronda_core,
            programacion_core,
        )

    async def crear_encuentro_proceso(
        self,
        ronda_id,
        data: EncuentroCreateData,
        actor=None,
    ) -> EncuentroResult:
        """Create an encounter of a round."""
        return await self._flujo.crear(ronda_id, data, actor)

    async def asignar_participantes_proceso(
        self,
        encuentro_id,
        participante_1_id=None,
        participante_2_id=None,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Move the teams of the slots of an encounter."""
        return await self._flujo.asignar_participantes(
            encuentro_id,
            participante_1_id,
            participante_2_id,
            actor,
            motivo,
            expected_version,
        )

    async def configurar_bye_proceso(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Configure a manual bye."""
        return await self._flujo.configurar_bye(
            encuentro_id,
            actor,
            motivo,
            expected_version,
        )

    async def programar_encuentro_proceso(
        self,
        encuentro_id,
        data: EncuentroProgramacionData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Schedule an encounter."""
        return await self._flujo.programar(
            encuentro_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def cambiar_estado_encuentro_proceso(
        self,
        encuentro_id,
        nuevo_estado,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Move an encounter through its lifecycle."""
        return await self._flujo.cambiar_estado(
            encuentro_id,
            nuevo_estado,
            actor,
            motivo,
            expected_version,
        )

    async def eliminar_encuentro_proceso(self, encuentro_id, actor=None) -> None:
        """Delete a draft that was never used."""
        return await self._flujo.eliminar(encuentro_id, actor)

    async def enlazar_siguiente_encuentro_proceso(
        self,
        encuentro_id,
        siguiente_encuentro_id,
        slot_destino,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Link the encounter to the next encounter of the bracket."""
        return await self._flujo.enlazar_siguiente(
            encuentro_id,
            siguiente_encuentro_id,
            slot_destino,
            actor,
            motivo,
            expected_version,
        )

    async def desenlazar_siguiente_encuentro_proceso(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Remove the link of the encounter."""
        return await self._flujo.desenlazar_siguiente(
            encuentro_id,
            actor,
            motivo,
            expected_version,
        )
