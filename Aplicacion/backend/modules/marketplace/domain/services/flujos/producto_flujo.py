"""`ProductoFlujo` — casos de uso completos del catálogo de productos.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.4 (flujos)

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`.

Regla de limpieza (FR-06 §2.5): los archivos escritos durante la transacción
se BORRAN si la transacción falla. La base de datos se revierte sola; el
volumen de media es estado durable y NO se revierte: hay que limpiarlo a
mano, y ese es el trabajo de este flujo.

El flujo es el dueño del ALCANCE: resuelve la edición (nivel 1 explícito o
nivel 3, la edición publicada única) y exige que el módulo lógico
`marketplace` esté habilitado en ella (RN-E02).
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.marketplace.domain.exceptions import (
    CategoriaProductoSlugDuplicadoError,
    ProductoImagenNoEncontradaError,
    ProductoNoEncontradoError,
    ProductoSlugDuplicadoError,
)
from modules.marketplace.domain.schemas.producto_schemas import ProductoCreateData
from modules.marketplace.domain.services.core.producto_core_service import (
    ProductoCoreService,
)
from modules.marketplace.domain.services.core.producto_media_service import (
    ProductoMediaService,
)


class ProductoFlujo:
    """Casos de uso de escritura sobre el catálogo de productos."""

    @inject
    def __init__(
        self,
        core_service: ProductoCoreService,
        media_service: ProductoMediaService,
    ):
        self.core_service = core_service
        self.media_service = media_service

    # ── Alta de producto ────────────────────────────────────────────────────

    async def crear_producto(self, data: ProductoCreateData):
        """Crea un producto con su galería, de forma atómica.

        Si la escritura falla (base de datos o disco), los archivos escritos
        durante la operación se BORRAN: el volumen de media es estado durable
        y no admite archivos huérfanos (FR-06 §2.5).
        """
        rutas: list[str] = []
        try:
            return await sync_to_async(self._crear_producto_sync)(data, rutas)
        except IntegrityError as exc:
            await sync_to_async(self.media_service.limpiar)(rutas)
            raise ProductoSlugDuplicadoError() from exc
        except Exception:
            await sync_to_async(self.media_service.limpiar)(rutas)
            raise

    @transaction.atomic()
    def _crear_producto_sync(self, data: ProductoCreateData, rutas: list[str]):
        """Alta atómica del producto y de su galería."""
        producto = self.core_service.crear(data)
        for indice, imagen in enumerate(data.imagenes or []):
            self.media_service.escribir(producto, imagen, indice, rutas)
        return self.core_service.result_de(producto)

    # ── Alta de categoría ───────────────────────────────────────────────────

    async def crear_categoria(self, data):
        """Crea una categoría de producto dentro de una edición."""
        try:
            return await sync_to_async(self._crear_categoria_sync)(data)
        except IntegrityError as exc:
            raise CategoriaProductoSlugDuplicadoError() from exc

    @transaction.atomic()
    def _crear_categoria_sync(self, data):
        """Alta atómica de la categoría."""
        return self.core_service.crear_categoria(data)

    # ── Reemplazo de imagen ─────────────────────────────────────────────────

    async def reemplazar_imagen(self, producto_id, imagen_id, upload):
        """Reemplaza el archivo de una imagen existente.

        FR-06 §2.5: el archivo anterior se borra DESPUÉS de que el nuevo
        quedó persistido. Si algo falla, el anterior sigue en su sitio y el
        nuevo se limpia.
        """
        rutas: list[str] = []
        try:
            return await sync_to_async(self._reemplazar_imagen_sync)(
                producto_id, imagen_id, upload, rutas
            )
        except Exception:
            await sync_to_async(self.media_service.limpiar)(rutas)
            raise

    @transaction.atomic()
    def _reemplazar_imagen_sync(self, producto_id, imagen_id, upload, rutas: list[str]):
        """Reemplazo atómico del archivo de una imagen."""
        producto = self.core_service.producto_selector.obtener_por_id(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError()
        imagenes = self.core_service.producto_selector.listar_imagenes(producto.id)
        previa = next((imagen for imagen in imagenes if str(imagen.id) == str(imagen_id)), None)
        if previa is None:
            raise ProductoImagenNoEncontradaError()
        self.media_service.reemplazar(producto, previa, upload, rutas)
        return self.core_service.result_de(producto)

    # ── Borrado de imagen ───────────────────────────────────────────────────

    async def eliminar_imagen(self, producto_id, imagen_id):
        """Elimina una imagen de la galería y borra su archivo."""
        return await sync_to_async(self._eliminar_imagen_sync)(producto_id, imagen_id)

    @transaction.atomic()
    def _eliminar_imagen_sync(self, producto_id, imagen_id):
        """Borrado atómico de la imagen y limpieza de su archivo."""
        producto = self.core_service.producto_selector.obtener_por_id(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError()
        imagenes = self.core_service.producto_selector.listar_imagenes(producto.id)
        objetivo = next((imagen for imagen in imagenes if str(imagen.id) == str(imagen_id)), None)
        if objetivo is None:
            raise ProductoImagenNoEncontradaError()
        ruta = objetivo.imagen.name if objetivo.imagen else ""
        objetivo.delete()
        self.media_service.limpiar([ruta] if ruta else [])
        return self.core_service.result_de(producto)

    # ── Borrado de producto ─────────────────────────────────────────────────

    async def eliminar_producto(self, producto_id):
        """Elimina un producto y borra los archivos de su galería.

        Los archivos se borran DESPUÉS de que la fila desapareció: el volumen
        de media no puede quedar con archivos que ya no tienen dueño
        (FR-06 §2.5).
        """
        return await sync_to_async(self._eliminar_producto_sync)(producto_id)

    @transaction.atomic()
    def _eliminar_producto_sync(self, producto_id):
        """Borrado atómico del producto y limpieza de sus archivos."""
        producto = self.core_service.producto_selector.obtener_por_id(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError()
        imagenes = self.core_service.producto_selector.listar_imagenes(producto.id)
        producto.delete()
        self.media_service.eliminar_archivos_de(imagenes)
        return True


__all__ = ["ProductoFlujo"]
