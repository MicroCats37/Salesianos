"""`PatrocinadorFlujo` — casos de uso completos de los patrocinadores.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.4 (flujos)

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`.

Regla de limpieza (FR-06 §2.5): los archivos escritos durante la transacción
se BORRAN si la transacción falla. La base de datos se revierte sola; el
volumen de media es estado durable y NO se revierte: hay que limpiarlo a
mano, y ese es el trabajo de este flujo.

El flujo NO decide el alcance: la edición la resuelve el orquestador por el
puerto `IAlcanceEdicion` y se la pasa ya resuelta (FR-02 §2.2).
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.patrocinadores.domain.exceptions import (
    PatrocinadorImagenNoEncontradaError,
    PatrocinadorNoEncontradoError,
    PatrocinadorSlugDuplicadoError,
)
from modules.patrocinadores.domain.schemas.patrocinadores_schemas import (
    PatrocinadorCreateData,
)
from modules.patrocinadores.domain.services.core.patrocinador_core_service import (
    PatrocinadorCoreService,
)
from modules.patrocinadores.domain.services.core.patrocinador_media_service import (
    PatrocinadorMediaService,
)


class PatrocinadorFlujo:
    """Casos de uso de escritura sobre los patrocinadores."""

    @inject
    def __init__(
        self,
        core_service: PatrocinadorCoreService,
        media_service: PatrocinadorMediaService,
    ):
        self.core_service = core_service
        self.media_service = media_service

    # ── Alta ────────────────────────────────────────────────────────────────

    async def crear_patrocinador(self, data: PatrocinadorCreateData):
        """Crea un patrocinador con su logo y su galería, de forma atómica.

        Si la escritura falla (base de datos o disco), los archivos escritos
        durante la operación se BORRAN: el volumen de media es estado durable
        y no admite archivos huérfanos (FR-06 §2.5).
        """
        rutas: list[str] = []
        try:
            return await sync_to_async(self._crear_patrocinador_sync)(data, rutas)
        except IntegrityError as exc:
            await sync_to_async(self.media_service.limpiar)(rutas)
            raise PatrocinadorSlugDuplicadoError() from exc
        except Exception:
            await sync_to_async(self.media_service.limpiar)(rutas)
            raise

    @transaction.atomic()
    def _crear_patrocinador_sync(self, data: PatrocinadorCreateData, rutas: list[str]):
        """Alta atómica del patrocinador, su logo y su galería."""
        patrocinador = self.core_service.crear(data)

        logo = getattr(data, "logo", None)
        if logo is not None and getattr(logo, "upload", None) is not None:
            self.media_service.escribir_logo(patrocinador, logo.upload, rutas)

        for indice, imagen in enumerate(data.imagenes or []):
            self.media_service.escribir_imagen(patrocinador, imagen, indice, rutas)

        return self.core_service.result_de(patrocinador)

    # ── Edición de la ficha ─────────────────────────────────────────────────

    async def actualizar_patrocinador(self, patrocinador_id, data):
        """Actualiza la ficha y la visibilidad del patrocinador.

        No toca los archivos: el logo y la galería tienen su propio camino.
        """
        return await sync_to_async(self._actualizar_patrocinador_sync)(patrocinador_id, data)

    @transaction.atomic()
    def _actualizar_patrocinador_sync(self, patrocinador_id, data):
        """Actualización atómica de la ficha."""
        patrocinador = self.core_service.patrocinador_selector.obtener_por_id(
            patrocinador_id
        )
        if patrocinador is None:
            raise PatrocinadorNoEncontradoError()
        self.core_service.actualizar(patrocinador, data)
        return self.core_service.result_de(patrocinador)

    # ── Orden de la galería ─────────────────────────────────────────────────

    async def reordenar_galeria(self, patrocinador_id, ordenes):
        """Fija el orden canónico de las imágenes de la galería."""
        return await sync_to_async(self._reordenar_galeria_sync)(patrocinador_id, ordenes)

    @transaction.atomic()
    def _reordenar_galeria_sync(self, patrocinador_id, ordenes):
        """Reordenamiento atómico de la galería."""
        patrocinador = self.core_service.patrocinador_selector.obtener_por_id(
            patrocinador_id
        )
        if patrocinador is None:
            raise PatrocinadorNoEncontradoError()
        self.core_service.reordenar_imagenes(patrocinador, ordenes)
        return self.core_service.result_de(patrocinador)

    # ── Reemplazo del logo ──────────────────────────────────────────────────

    async def reemplazar_logo(self, patrocinador_id, upload):
        """Reemplaza el archivo del logo.

        FR-06 §2.5: el archivo anterior se borra DESPUÉS de que el nuevo
        quedó persistido. Si algo falla, el anterior sigue en su sitio y el
        nuevo se limpia.
        """
        rutas: list[str] = []
        try:
            return await sync_to_async(self._reemplazar_logo_sync)(
                patrocinador_id, upload, rutas
            )
        except Exception:
            await sync_to_async(self.media_service.limpiar)(rutas)
            raise

    @transaction.atomic()
    def _reemplazar_logo_sync(self, patrocinador_id, upload, rutas: list[str]):
        """Reemplazo atómico del logo."""
        patrocinador = self.core_service.patrocinador_selector.obtener_por_id(
            patrocinador_id
        )
        if patrocinador is None:
            raise PatrocinadorNoEncontradoError()
        self.media_service.reemplazar_logo(patrocinador, upload, rutas)
        return self.core_service.result_de(patrocinador)

    # ── Reemplazo de una imagen de la galería ───────────────────────────────

    async def reemplazar_imagen(self, patrocinador_id, imagen_id, upload):
        """Reemplaza el archivo de una imagen existente de la galería."""
        rutas: list[str] = []
        try:
            return await sync_to_async(self._reemplazar_imagen_sync)(
                patrocinador_id, imagen_id, upload, rutas
            )
        except Exception:
            await sync_to_async(self.media_service.limpiar)(rutas)
            raise

    @transaction.atomic()
    def _reemplazar_imagen_sync(self, patrocinador_id, imagen_id, upload, rutas: list[str]):
        """Reemplazo atómico del archivo de una imagen de la galería."""
        patrocinador = self.core_service.patrocinador_selector.obtener_por_id(
            patrocinador_id
        )
        if patrocinador is None:
            raise PatrocinadorNoEncontradoError()
        imagenes = self.core_service.patrocinador_selector.listar_imagenes(patrocinador.id)
        previa = next((imagen for imagen in imagenes if str(imagen.id) == str(imagen_id)), None)
        if previa is None:
            raise PatrocinadorImagenNoEncontradaError()
        self.media_service.reemplazar_imagen(patrocinador, previa, upload, rutas)
        return self.core_service.result_de(patrocinador)

    # ── Borrado de una imagen de la galería ─────────────────────────────────

    async def eliminar_imagen(self, patrocinador_id, imagen_id):
        """Elimina una imagen de la galería y borra su archivo."""
        return await sync_to_async(self._eliminar_imagen_sync)(patrocinador_id, imagen_id)

    @transaction.atomic()
    def _eliminar_imagen_sync(self, patrocinador_id, imagen_id):
        """Borrado atómico de la imagen y limpieza de su archivo."""
        patrocinador = self.core_service.patrocinador_selector.obtener_por_id(
            patrocinador_id
        )
        if patrocinador is None:
            raise PatrocinadorNoEncontradoError()
        imagenes = self.core_service.patrocinador_selector.listar_imagenes(patrocinador.id)
        objetivo = next((imagen for imagen in imagenes if str(imagen.id) == str(imagen_id)), None)
        if objetivo is None:
            raise PatrocinadorImagenNoEncontradaError()
        ruta = objetivo.imagen.name if objetivo.imagen else ""
        objetivo.delete()
        self.media_service.limpiar([ruta] if ruta else [])
        return self.core_service.result_de(patrocinador)

    # ── Borrado del patrocinador ────────────────────────────────────────────

    async def eliminar_patrocinador(self, patrocinador_id):
        """Elimina un patrocinador y borra el logo y los archivos de su galería.

        Los archivos se borran DESPUÉS de que la fila desapareció: el volumen
        de media no puede quedar con archivos que ya no tienen dueño
        (FR-06 §2.5).
        """
        return await sync_to_async(self._eliminar_patrocinador_sync)(patrocinador_id)

    @transaction.atomic()
    def _eliminar_patrocinador_sync(self, patrocinador_id):
        """Borrado atómico del patrocinador y limpieza de sus archivos."""
        patrocinador = self.core_service.patrocinador_selector.obtener_por_id(
            patrocinador_id
        )
        if patrocinador is None:
            raise PatrocinadorNoEncontradoError()
        imagenes = self.core_service.patrocinador_selector.listar_imagenes(patrocinador.id)
        rutas = self.media_service.rutas_de(patrocinador, imagenes)
        patrocinador.delete()
        self.media_service.limpiar(rutas)
        return True


__all__ = ["PatrocinadorFlujo"]
