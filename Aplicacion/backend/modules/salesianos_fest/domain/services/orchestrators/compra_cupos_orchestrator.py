"""`CompraCuposOrchestrator` — fachada async de la compra de cupos extra.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS.

La COMPRA de cupos extra la puede pedir únicamente el RESPONSABLE de la
inscripción: el código de denegación es `COMPRA_NO_AUTORIZADA` (403), el
CONGELADO por el ledger `FR-07` §3.3 para `RT-CM-01`.

La titularidad la decide el MÓDULO DUEÑO del recurso (`FR-03` §2.1 regla 1):
ser `Administrador` NO sustituye la titularidad de una inscripción ajena.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.exceptions import CompraNoAutorizadaError
from modules.salesianos_fest.domain.ports import ITitularidadService
from modules.salesianos_fest.domain.results.pool_result import CompraCuposResult
from modules.salesianos_fest.domain.schemas.pool_schemas import CompraCuposData
from modules.salesianos_fest.domain.services.flujos.compra_cupos_flujo import (
    CompraCuposFlujo,
)


class CompraCuposOrchestrator:
    """Fachada de la compra de cupos extra."""

    @inject
    def __init__(
        self,
        flujo: CompraCuposFlujo,
        titularidad: ITitularidadService,
    ):
        self.flujo = flujo
        self.titularidad = titularidad

    async def comprar_cupos(
        self,
        actor,
        inscripcion_id,
        data: CompraCuposData,
    ) -> CompraCuposResult:
        """Compra cupos extra para la inscripción del actor."""
        responsable_id = await self.flujo.obtener_responsable(inscripcion_id)
        await self._verificar_responsable(actor, responsable_id)
        intencion = data.model_copy(update={"inscripcion_id": inscripcion_id})
        return await self.flujo.comprar_cupos(intencion)

    # ── Internos ────────────────────────────────────────────────────────────

    async def _verificar_responsable(self, actor, responsable_id: str) -> None:
        """La titularidad la decide el MÓDULO DUEÑO del recurso."""
        persona_id = await sync_to_async(self.titularidad.persona_id_del_actor)(actor)
        if not self.titularidad.es_responsable(persona_id, responsable_id):
            raise CompraNoAutorizadaError()


__all__ = ["CompraCuposOrchestrator"]
