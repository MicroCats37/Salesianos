"""`VideoOrchestrator` — fachada async del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.5 (orchestrators)

Fachada MUY DELGADA: un método público por endpoint y nada más. No contiene
lógica de negocio; delega en el flujo (escrituras) o en el core service
(lecturas). Devuelve result objects, nunca schemas HTTP.
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.videos.domain.results.videos_results import (
    VideoListadoResult,
    VideoResult,
)
from modules.videos.domain.schemas.videos_schemas import (
    VideoActualizarData,
    VideoCrearData,
)
from modules.videos.domain.services.core.video_service import VideoService
from modules.videos.domain.services.flujos.video_flujo import VideoFlujo


class VideoOrchestrator:
    """Fachada async de la sala de proyección."""

    @inject
    def __init__(
        self,
        core_service: VideoService,
        flujo: VideoFlujo,
    ):
        self.core_service = core_service
        self.flujo = flujo
        self._listar_videos = sync_to_async(self._listar_videos_sync)
        self._listar_videos_admin = sync_to_async(self._listar_videos_admin_sync)
        self._obtener_video = sync_to_async(self._obtener_video_sync)

    # ── Lecturas ────────────────────────────────────────────────────────────

    def _listar_videos_sync(self) -> list[VideoResult]:
        videos = self.core_service.selector.listar()
        return [self.core_service.result_de(video) for video in videos]

    def _listar_videos_admin_sync(
        self,
        q: str | None,
        ordering: str | None,
        page: int,
        page_size: int,
    ) -> VideoListadoResult:
        videos, total = self.core_service.selector.listar_paginado(
            q=q,
            ordering=ordering,
            page=page,
            page_size=page_size,
        )
        return self.core_service.result_listado(videos, total, page, page_size)

    def _obtener_video_sync(self, video_id) -> VideoResult:
        video = self.core_service.obtener(video_id)
        return self.core_service.result_de(video)

    async def listar_videos(self) -> list[VideoResult]:
        """La galería pública de videos, en el orden canónico.

        El listado público NO se pagina: es una sala de proyección pequeña y
        el navegador recibe la lista completa.
        """
        return await self._listar_videos()

    async def obtener_video(self, video_id) -> VideoResult:
        """Un video por identificador.

        Un video inexistente lanza `VideoNoEncontradoError` (404).
        """
        return await self._obtener_video(video_id)

    async def listar_videos_admin(
        self,
        q: str | None = None,
        ordering: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> VideoListadoResult:
        """El listado administrativo de videos, con su paginación."""
        return await self._listar_videos_admin(q, ordering, page, page_size)

    # ── Escrituras ──────────────────────────────────────────────────────────

    async def crear_video(self, data: VideoCrearData) -> VideoResult:
        """Crea un video (delegado en el flujo)."""
        return await self.flujo.crear_video(data)

    async def actualizar_video(
        self,
        video_id,
        data: VideoActualizarData,
    ) -> VideoResult:
        """Actualiza un video (delegado en el flujo)."""
        return await self.flujo.actualizar_video(video_id, data)

    async def eliminar_video(self, video_id) -> bool:
        """Borra un video (delegado en el flujo)."""
        return await self.flujo.eliminar_video(video_id)


__all__ = ["VideoOrchestrator"]
