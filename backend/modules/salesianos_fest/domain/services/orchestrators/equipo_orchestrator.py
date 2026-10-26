"""EquipoOrchestrator — thin async facade for equipo operations."""
from asgiref.sync import sync_to_async
from injector import inject

from ..core.equipo_service import EquipoCoreService
from ..flujos.crear_equipo_flujo import CrearEquipoFlujo
from ...selectors.equipo_selector import EquipoSelector
from ...results.inscripcion_results import EquipoResult


class EquipoOrchestrator:
    """Thin async orchestrator — delegates to flujos, no business logic."""

    @inject
    def __init__(self, equipo_core: EquipoCoreService):
        self._equipo_core = equipo_core
        self._crear_flujo = CrearEquipoFlujo(equipo_core)

    async def crear_equipo_proceso(self, data) -> EquipoResult:
        """Create a new equipo."""
        return await self._crear_flujo.ejecutar(data)

    async def obtener_equipo_proceso(self, equipo_id: str) -> EquipoResult | None:
        """Get equipo by ID."""
        return await sync_to_async(EquipoSelector.get_by_id)(equipo_id)

    async def listar_por_inscripcion_proceso(self, inscripcion_id: str) -> list[EquipoResult]:
        """List equipos for an inscripcion."""
        return await sync_to_async(EquipoSelector.get_by_inscripcion)(inscripcion_id)
