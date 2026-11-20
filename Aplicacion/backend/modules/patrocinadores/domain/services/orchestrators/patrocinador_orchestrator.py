"""`PatrocinadorOrchestrator` — fachada async del módulo `patrocinadores`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.5 (orchestrators)

Fachada MUY DELGADA: un método público por caso de uso y nada más. No contiene
lógica de negocio; delega en el flujo (escrituras) o en el core service
(lecturas). Devuelve result objects, nunca schemas HTTP.

El alcance de edición se resuelve por el PUERTO `IAlcanceEdicion`: el módulo
no conoce el módulo que provee el dato (FR-02 §2.2). Toda operación exige que
el módulo lógico `patrocinadores` esté habilitado en la edición (RN-E02): un
módulo deshabilitado no expone catálogo ni rutas de escritura.

El cliente NUNCA elige la edición: el orquestador sustituye el `edicion_id`
del payload por la edición vigente resuelta según el orden congelado.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.patrocinadores.domain.constants import MODULO_LOGICO
from modules.patrocinadores.domain.exceptions import ModuloNoHabilitadoError
from modules.patrocinadores.domain.ports.alcance_edicion import IAlcanceEdicion
from modules.patrocinadores.domain.schemas.patrocinadores_schemas import (
    PatrocinadorCreateData,
)
from modules.patrocinadores.domain.services.core.patrocinador_core_service import (
    PatrocinadorCoreService,
)
from modules.patrocinadores.domain.services.flujos.patrocinador_flujo import (
    PatrocinadorFlujo,
)


class PatrocinadorOrchestrator:
    """Fachada async de los patrocinadores."""

    @inject
    def __init__(
        self,
        core_service: PatrocinadorCoreService,
        flujo: PatrocinadorFlujo,
        alcance: IAlcanceEdicion,
    ):
        self.core_service = core_service
        self.flujo = flujo
        self.alcance = alcance
        self._resolver_actual = sync_to_async(self._resolver_actual_sync)
        self._listar_por_edicion = sync_to_async(self._listar_por_edicion_sync)
        self._obtener_por_slug = sync_to_async(self._obtener_por_slug_sync)

    # ── Alcance ─────────────────────────────────────────────────────────────

    def _resolver_actual_sync(self):
        """Resuelve la edición vigente según el orden congelado de FR-02 §2.2."""
        edicion = self.alcance.resolver_actual()
        if not edicion.modulo_habilitado(MODULO_LOGICO):
            raise ModuloNoHabilitadoError()
        return edicion

    async def _edicion_actual(self):
        """La edición vigente con el módulo `patrocinadores` habilitado."""
        return await self._resolver_actual()

    # ── Lecturas ────────────────────────────────────────────────────────────

    def _listar_por_edicion_sync(self, edicion_id, visible=None):
        patrocinadores = self.core_service.patrocinador_selector.listar_por_edicion(
            edicion_id, visible=visible
        )
        return [self.core_service.result_de(patrocinador) for patrocinador in patrocinadores]

    def _obtener_por_slug_sync(self, edicion_id, slug):
        from modules.patrocinadores.domain.exceptions import PatrocinadorNoEncontradoError

        patrocinador = self.core_service.patrocinador_selector.obtener_por_slug(
            edicion_id, slug
        )
        if patrocinador is None:
            raise PatrocinadorNoEncontradoError()
        return self.core_service.result_de(patrocinador)

    async def listar_por_edicion(self, visible=None):
        """Los patrocinadores de la edición vigente, en orden canónico."""
        edicion = await self._edicion_actual()
        return await self._listar_por_edicion(edicion.id, visible)

    async def obtener_por_slug(self, slug):
        """Un patrocinador de la edición vigente, por slug."""
        edicion = await self._edicion_actual()
        return await self._obtener_por_slug(edicion.id, slug)

    # ── Escrituras ──────────────────────────────────────────────────────────

    async def crear_patrocinador(self, data: PatrocinadorCreateData):
        """Crea un patrocinador con su logo y su galería (delegado en el flujo).

        El alcance lo resuelve el SERVIDOR: el `edicion_id` del payload del
        cliente se descarta y se sustituye por la edición vigente resuelta
        según el orden congelado (FR-02 §2.2). Un cliente nunca elige la
        edición a la que escribe.
        """
        edicion = await self._edicion_actual()
        data = data.model_copy(update={"edicion_id": edicion.id})
        return await self.flujo.crear_patrocinador(data)

    async def actualizar_patrocinador(self, patrocinador_id, data):
        """Actualiza la ficha y la visibilidad (delegado en el flujo)."""
        return await self.flujo.actualizar_patrocinador(patrocinador_id, data)

    async def reordenar_galeria(self, patrocinador_id, ordenes):
        """Fija el orden de la galería (delegado en el flujo)."""
        return await self.flujo.reordenar_galeria(patrocinador_id, ordenes)

    async def reemplazar_logo(self, patrocinador_id, upload):
        """Reemplaza el archivo del logo (delegado en el flujo)."""
        return await self.flujo.reemplazar_logo(patrocinador_id, upload)

    async def reemplazar_imagen(self, patrocinador_id, imagen_id, upload):
        """Reemplaza el archivo de una imagen de la galería (delegado en el flujo)."""
        return await self.flujo.reemplazar_imagen(patrocinador_id, imagen_id, upload)

    async def eliminar_imagen(self, patrocinador_id, imagen_id):
        """Elimina una imagen de la galería (delegado en el flujo)."""
        return await self.flujo.eliminar_imagen(patrocinador_id, imagen_id)

    async def eliminar_patrocinador(self, patrocinador_id):
        """Elimina un patrocinador y sus archivos (delegado en el flujo)."""
        return await self.flujo.eliminar_patrocinador(patrocinador_id)


__all__ = ["PatrocinadorOrchestrator"]
