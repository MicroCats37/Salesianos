"""`ProductoOrchestrator` — fachada async del módulo `marketplace`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.5 (orchestrators)

Fachada MUY DELGADA: un método público por endpoint y nada más. No contiene
lógica de negocio; delega en el flujo (escrituras) o en el core service
(lecturas). Devuelve result objects, nunca schemas HTTP.

El alcance de edición se resuelve por el PUERTO `IAlcanceEdicion`: el
módulo no conoce el módulo que provee el dato (FR-02 §2.2). Toda operación
exige que el módulo lógico `marketplace` esté habilitado en la edición
(RN-E02): un módulo deshabilitado no expone catálogo ni rutas de escritura.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.marketplace.domain.constants import MODULO_LOGICO
from modules.marketplace.domain.exceptions import ModuloNoHabilitadoError
from modules.marketplace.domain.ports.alcance_edicion import IAlcanceEdicion
from modules.marketplace.domain.schemas.producto_schemas import ProductoCreateData
from modules.marketplace.domain.services.core.producto_core_service import (
    ProductoCoreService,
)
from modules.marketplace.domain.services.flujos.producto_flujo import ProductoFlujo


class ProductoOrchestrator:
    """Fachada async del catálogo de productos."""

    @inject
    def __init__(
        self,
        core_service: ProductoCoreService,
        flujo: ProductoFlujo,
        alcance: IAlcanceEdicion,
    ):
        self.core_service = core_service
        self.flujo = flujo
        self.alcance = alcance
        self._resolver_actual = sync_to_async(self._resolver_actual_sync)
        self._listar_categorias = sync_to_async(self._listar_categorias_sync)
        self._listar_productos = sync_to_async(self._listar_productos_sync)
        self._obtener_producto = sync_to_async(self._obtener_producto_sync)

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

    # ── Lecturas ────────────────────────────────────────────────────────────

    def _listar_categorias_sync(self, edicion_id):
        categorias = self.core_service.categoria_selector.listar_por_edicion(edicion_id)
        return [self.core_service.result_categoria(categoria) for categoria in categorias]

    def _listar_productos_sync(self, edicion_id, categoria_id=None, page=1, page_size=25):
        productos = self.core_service.producto_selector.listar_por_edicion(
            edicion_id, estado="ACTIVO"
        )
        if categoria_id is not None:
            productos = [
                producto
                for producto in productos
                if str(producto.categoria_id) == str(categoria_id)
            ]
        total = len(productos)
        inicio = max(0, (page - 1) * page_size)
        ventana = productos[inicio : inicio + page_size]
        return [self.core_service.result_item(producto) for producto in ventana], total

    def _obtener_producto_sync(self, edicion_id, slug):
        from modules.marketplace.domain.exceptions import ProductoNoEncontradoError

        producto = self.core_service.producto_selector.obtener_por_slug(edicion_id, slug)
        if producto is None or producto.estado != "ACTIVO":
            raise ProductoNoEncontradoError()
        return self.core_service.result_de(producto)

    async def listar_categorias(self):
        """Categorías del catálogo de la edición vigente, en orden."""
        edicion = await self._edicion_actual()
        return await self._listar_categorias(edicion.id)

    async def listar_productos(self, categoria_id=None, page=1, page_size=25):
        """Productos `ACTIVO` de la edición vigente, con su paginación.

        Devuelve `(items, total)`: el total es el número de productos que
        cumplen el filtro, no el de la página.
        """
        edicion = await self._edicion_actual()
        return await self._listar_productos(edicion.id, categoria_id, page, page_size)

    async def obtener_producto(self, slug):
        """Un producto `ACTIVO` de la edición vigente, por slug."""
        edicion = await self._edicion_actual()
        return await self._obtener_producto(edicion.id, slug)

    # ── Escrituras ──────────────────────────────────────────────────────────

    async def crear_producto(self, data: ProductoCreateData):
        """Crea un producto con su galería (delegado en el flujo).

        El alcance lo resuelve el SERVIDOR: el `edicion_id` del payload del
        cliente se descarta y se sustituye por la edición vigente resuelta
        según el orden congelado (FR-02 §2.2). Un cliente nunca elige la
        edición a la que escribe.
        """
        edicion = await self._edicion_actual()
        data = data.model_copy(update={"edicion_id": edicion.id})
        return await self.flujo.crear_producto(data)

    async def crear_categoria(self, data):
        """Crea una categoría de producto (delegado en el flujo)."""
        edicion = await self._edicion_actual()
        data = data.model_copy(update={"edicion_id": edicion.id})
        return await self.flujo.crear_categoria(data)


__all__ = ["ProductoOrchestrator"]
