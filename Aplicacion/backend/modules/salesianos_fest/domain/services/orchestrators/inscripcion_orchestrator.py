"""`InscripcionOrchestrator` — fachada async de las inscripciones.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS.

Este orquestador hace DOS cosas y ninguna más:

1. Resuelve el RESPONSABLE a partir de la cuenta autenticada. El cliente
   no declara quién es el responsable: el documento es un identificador, no
   una credencial (`RN-U04`).
2. Comprueba la TITULARIDAD sobre el recurso del módulo antes de devolverlo
   (`FR-03` §2.1 regla 1). El grupo `Administrador` NO sustituye la
   titularidad de una inscripción ajena.

El resto de las reglas vive en `InscripcionFlujo`.
"""

from uuid import UUID

from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.exceptions import (
    CompradorSinPersonaError,
    InscripcionNoAutorizadaError,
)
from modules.salesianos_fest.domain.ports import ITitularidadService
from modules.salesianos_fest.domain.results.inscripcion_result import (
    EquipoResult,
    InscripcionDetalleResult,
    InscripcionInicialResult,
)
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    InscripcionInicialData,
)
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)


class InscripcionOrchestrator:
    """Fachada de las inscripciones."""

    @inject
    def __init__(self, flujo: InscripcionFlujo, titularidad: ITitularidadService):
        self.flujo = flujo
        self.titularidad = titularidad

    async def crear_inscripcion_inicial(
        self,
        actor,
        data: InscripcionInicialData,
    ) -> InscripcionInicialResult:
        """Crea (o reutiliza) la inscripción inicial del actor autenticado."""
        persona_id = await sync_to_async(self.titularidad.persona_id_del_actor)(actor)
        if not persona_id:
            raise CompradorSinPersonaError()

        intencion = InscripcionInicialData(
            responsable_id=UUID(persona_id),
            edicion_id=data.edicion_id,
            paquete_id=data.paquete_id,
            equipos=data.equipos,
        )
        return await self.flujo.crear_inscripcion_inicial(intencion)

    async def obtener_inscripcion(
        self,
        actor,
        inscripcion_id,
    ) -> InscripcionDetalleResult:
        """El detalle de una inscripción, si el actor es su responsable."""
        detalle = await self.flujo.obtener_inscripcion(inscripcion_id)
        await self._verificar_responsable(actor, detalle.responsable_id)
        return detalle

    async def listar_equipos(
        self,
        actor,
        inscripcion_id,
    ) -> list[EquipoResult]:
        """Los equipos de una inscripción, si el actor es su responsable."""
        detalle = await self.flujo.obtener_inscripcion(inscripcion_id)
        await self._verificar_responsable(actor, detalle.responsable_id)
        return detalle.equipos

    # ── Internos ────────────────────────────────────────────────────────────

    async def _verificar_responsable(self, actor, responsable_id: str) -> None:
        """La titularidad la decide el módulo DUEÑO del recurso."""
        persona_id = await sync_to_async(self.titularidad.persona_id_del_actor)(actor)
        if not self.titularidad.es_responsable(persona_id, responsable_id):
            raise InscripcionNoAutorizadaError()

__all__ = ["InscripcionOrchestrator"]
