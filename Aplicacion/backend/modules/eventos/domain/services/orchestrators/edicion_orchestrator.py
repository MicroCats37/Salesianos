"""`EdicionOrchestrator` — fachada async del módulo `eventos`.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §4.5 (orchestrators)

Fachada MUY DELGADA: un método público por endpoint y nada más. No contiene
lógica de negocio; delega en el servicio de alcance (lecturas) o en el flujo
(escrituras). Devuelve result objects, nunca schemas HTTP.

La lectura del ORM es sync, así que se envuelve con `sync_to_async` — nunca
`asyncio.to_thread` (convención del proyecto).
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.eventos.domain.results.edicion_result import EdicionActualResult
from modules.eventos.domain.services.core.edicion_scope_service import EdicionScopeService
from modules.eventos.domain.services.flujos.edicion_flujo import EdicionFlujo


class EdicionOrchestrator:
    """Fachada async del módulo de ediciones."""

    @inject
    def __init__(
        self,
        scope_service: EdicionScopeService,
        flujo: EdicionFlujo,
    ):
        self.scope_service = scope_service
        self.flujo = flujo
        self._resolver_actual = sync_to_async(self._resolver_actual_sync)
        self._resolver_explicita = sync_to_async(self.scope_service.resolver_explicita)

    # ── Lecturas ────────────────────────────────────────────────────────────

    async def obtener_edicion_actual(self) -> EdicionActualResult:
        """Resuelve la edición vigente y el estado de sus módulos.

        Aplica el orden congelado de FR-02 §2.2 en su entirety: nunca elige
        "la primera", "la más reciente" ni "la que coincida con un nombre por
        defecto". Ante ambigüedad o ausencia, la excepción de dominio
        correspondiente se propaga y el error HTTP lo decide el catálogo.
        """
        edicion = await self._resolver_actual()
        return EdicionActualResult.desde_edicion(edicion)

    async def obtener_edicion_explicita(self, edicion_id) -> EdicionActualResult:
        """Resuelve la edición por `edicion_id` (nivel 1, sin fallback)."""
        edicion = await self._resolver_explicita(edicion_id)
        return EdicionActualResult.desde_edicion(edicion)

    def _resolver_actual_sync(self):
        """Parte sync de la resolución de la edición vigente.

        El nivel 2 (edición activa del actor) no tiene proveedor en este
        paquete: FR-02 §3 no congela ninguna relación actor↔edición, de modo
        que el módulo NO inventa un modelo. El proveedor real lo conecta el
        módulo que posea esa relación (evidence FND-02 §"Decisiones abiertas").
        """
        return self.scope_service.resolver_actual()

    # ── Escrituras ──────────────────────────────────────────────────────────

    async def crear_edicion(self, data):
        """Crea una edición (delegado en el flujo)."""
        return await self.flujo.crear_edicion(data)

    async def publicar_edicion(self, edicion_id):
        """Publica una edición por alcance explícito (delegado en el flujo)."""
        return await self.flujo.publicar_edicion(edicion_id)

    async def cerrar_edicion(self, edicion_id):
        """Cierra una edición por alcance explícito (delegado en el flujo)."""
        return await self.flujo.cerrar_edicion(edicion_id)


__all__ = ["EdicionOrchestrator"]
