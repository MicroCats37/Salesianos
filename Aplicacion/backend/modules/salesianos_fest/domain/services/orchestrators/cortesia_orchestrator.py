"""`CortesiaOrchestrator` — fachada async del otorgamiento de cortesías.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS.

Este orquestador hace DOS cosas y ninguna más:

1. Exige que la operación la ejecute una CUENTA autenticada: una cortesía
   es un acto administrativo y siempre tiene ACTOR (`RN-P05`, `FL-07` paso 2).
2. Delega en `CortesiaFlujo`.

El resto de las reglas vive en el flujo.
"""

from injector import inject

from modules.salesianos_fest.domain.exceptions import ActorRequeridoError
from modules.salesianos_fest.domain.results.pase_result import (
    AdminCortesiaListaResult,
    CortesiaPaseResult,
)
from modules.salesianos_fest.domain.schemas.pase_schemas import OtorgarCortesiaData
from modules.salesianos_fest.domain.services.flujos.cortesia_flujo import CortesiaFlujo


class CortesiaOrchestrator:
    """Fachada del otorgamiento de cortesías."""

    @inject
    def __init__(self, flujo: CortesiaFlujo):
        self.flujo = flujo

    async def otorgar_cortesia(
        self,
        actor,
        data: OtorgarCortesiaData,
    ) -> CortesiaPaseResult:
        """Registra una cortesía con actor y motivo.

        Sin cuenta no hay cortesía: el ACTOR es la auditoría, y la auditoría
        exige una cuenta (`RN-P05`).
        """
        if actor is None or not getattr(actor, "is_authenticated", False):
            raise ActorRequeridoError()
        return await self.flujo.otorgar_cortesia(data, actor)

    async def listar_cortesias(
        self,
        edicion_id=None,
        estado: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> AdminCortesiaListaResult:
        """El listado administrativo de actas de cortesía.

        La autorización de ADMINISTRADOR la aplica la ruta (la puerta
        compartida `RequireAdmin`); este orquestador no la repite.
        """
        return await self.flujo.listar_cortesias(
            edicion_id,
            estado,
            page,
            page_size,
        )


__all__ = ["CortesiaOrchestrator"]
