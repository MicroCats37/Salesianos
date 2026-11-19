"""`PoolOrchestrator` — fachada async del pool de una inscripción.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS.

Este orquestador hace DOS cosas y ninguna más:

1. Comprueba la TITULARIDAD sobre el recurso del módulo ANTES de tocarlo
   (`FR-03` §2.1 regla 1). El grupo `Administrador` NO sustituye la
   titularidad de una inscripción ajena.
2. Delega en `PoolFlujo`.

El resto de las reglas vive en `PoolFlujo`.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.exceptions import InscripcionNoAutorizadaError
from modules.salesianos_fest.domain.ports import ITitularidadService
from modules.salesianos_fest.domain.results.pool_result import PoolResult
from modules.salesianos_fest.domain.schemas.pool_schemas import (
    ParticipanteAsignarData,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo


class PoolOrchestrator:
    """Fachada del pool de una inscripción."""

    @inject
    def __init__(self, flujo: PoolFlujo, titularidad: ITitularidadService):
        self.flujo = flujo
        self.titularidad = titularidad

    async def obtener_pool(self, actor, inscripcion_id) -> PoolResult:
        """El pool de una inscripción, si el actor es su responsable."""
        pool = await self.flujo.obtener_pool(inscripcion_id)
        await self._verificar_responsable(actor, pool.responsable_id)
        return pool

    async def agregar_participante(
        self,
        actor,
        inscripcion_id,
        data: ParticipanteAsignarData,
    ) -> PoolResult:
        """Agrega (o mueve) un participante, si el actor es el responsable."""
        pool = await self.flujo.obtener_pool(inscripcion_id)
        await self._verificar_responsable(actor, pool.responsable_id)
        intencion = data.model_copy(update={"inscripcion_id": inscripcion_id})
        return await self.flujo.agregar_participante(intencion)

    async def retirar_participante(
        self,
        actor,
        inscripcion_id,
        participacion_id,
    ) -> PoolResult:
        """Retira un participante, si el actor es el responsable."""
        pool = await self.flujo.obtener_pool(inscripcion_id)
        await self._verificar_responsable(actor, pool.responsable_id)
        return await self.flujo.retirar_participante(inscripcion_id, participacion_id)

    # ── Internos ────────────────────────────────────────────────────────────

    async def _verificar_responsable(self, actor, responsable_id: str) -> None:
        """La titularidad la decide el MÓDULO DUEÑO del recurso."""
        persona_id = await sync_to_async(self.titularidad.persona_id_del_actor)(actor)
        if not self.titularidad.es_responsable(persona_id, responsable_id):
            raise InscripcionNoAutorizadaError()


__all__ = ["PoolOrchestrator"]
