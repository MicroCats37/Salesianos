"""`InventarioOrchestrator` — fachada async del inventario de marketplace.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.5

Fachada MUY DELGADA: un método público por endpoint y nada más. No contiene
lógica de negocio; delega en el flujo (escrituras) o en los core services
(lecturas). Devuelve result objects, nunca schemas HTTP.

El alcance de edición se resuelve por el PUERTO `IAlcanceEdicion` y exige
que el módulo lógico `marketplace` esté habilitado (`RN-E02`).
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.marketplace.domain.constants import MODULO_LOGICO
from modules.marketplace.domain.exceptions import ModuloNoHabilitadoError
from modules.marketplace.domain.ports.alcance_edicion import IAlcanceEdicion
from modules.marketplace.domain.schemas.inventario_schemas import (
    RegistrarMovimientoInventarioData,
    RevertirMovimientoInventarioData,
)
from modules.marketplace.domain.services.core.inventario_core_service import (
    InventarioCoreService,
)
from modules.marketplace.domain.services.core.pedido_core_service import (
    PedidoCoreService,
)
from modules.marketplace.domain.services.flujos.inventario_flujo import InventarioFlujo


class InventarioOrchestrator:
    """Fachada async del inventario y de las entregas de marketplace."""

    @inject
    def __init__(
        self,
        core_service: InventarioCoreService,
        pedido_core_service: PedidoCoreService,
        flujo: InventarioFlujo,
        alcance: IAlcanceEdicion,
    ):
        self.core_service = core_service
        self.pedido_core_service = pedido_core_service
        self.flujo = flujo
        self.alcance = alcance
        self._resolver_actual = sync_to_async(self._resolver_actual_sync)
        self._listar_inventario = sync_to_async(self._listar_inventario_sync)
        self._listar_entregas = sync_to_async(self._listar_entregas_sync)

    # ── Alcance ─────────────────────────────────────────────────────────────

    def _resolver_actual_sync(self):
        """Resuelve la edición vigente según el orden congelado de FR-02 §2.2."""
        edicion = self.alcance.resolver_actual()
        if not edicion.modulo_habilitado(MODULO_LOGICO):
            raise ModuloNoHabilitadoError()
        return edicion

    async def _edicion_actual(self):
        """La edición vigente con el módulo `marketplace` habilitado."""
        return await self._resolver_actual()

    # ── Lecturas ─────────────────────────────────────────────────────────────

    def _listar_inventario_sync(self, edicion_id):
        return self.core_service.listar_inventario(edicion_id)

    def _listar_entregas_sync(self, edicion_id):
        return self.pedido_core_service.listar_entregas(edicion_id)

    async def listar_inventario(self):
        """El inventario de la edición vigente: físico, reservado y
        disponible, con la bitácora de cada producto."""
        edicion = await self._edicion_actual()
        return await self._listar_inventario(edicion.id)

    async def listar_entregas(self):
        """Las recogidas pendientes y entregadas de la edición vigente."""
        edicion = await self._edicion_actual()
        return await self._listar_entregas(edicion.id)

    # ── Escrituras ───────────────────────────────────────────────────────────

    async def registrar_movimiento(self, usuario, data: RegistrarMovimientoInventarioData):
        """Registra un movimiento manual de inventario (delegado en el flujo)."""
        edicion = await self._edicion_actual()
        return await self.flujo.registrar_movimiento(edicion.id, data, usuario)

    async def revertir_movimiento(self, usuario, data: RevertirMovimientoInventarioData):
        """Compensa un movimiento ya registrado (delegado en el flujo)."""
        edicion = await self._edicion_actual()
        return await self.flujo.revertir_movimiento(edicion.id, data, usuario)


__all__ = ["InventarioOrchestrator"]
