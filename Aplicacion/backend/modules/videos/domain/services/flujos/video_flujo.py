"""`VideoFlujo` — casos de uso completos del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.4 (flujos)

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`.
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.videos.domain.results.videos_results import VideoResult
from modules.videos.domain.schemas.videos_schemas import (
    VideoActualizarData,
    VideoCrearData,
)
from modules.videos.domain.services.core.video_service import VideoService


class VideoFlujo:
    """Casos de uso de escritura sobre los videos."""

    @inject
    def __init__(self, core_service: VideoService):
        self.core_service = core_service

    # ── Alta ────────────────────────────────────────────────────────────────

    async def crear_video(self, data: VideoCrearData) -> VideoResult:
        """Crea un video de forma atómica."""
        return await sync_to_async(self._crear_video_sync)(data)

    @transaction.atomic
    def _crear_video_sync(self, data: VideoCrearData) -> VideoResult:
        """Alta atómica del video."""
        video = self.core_service.crear(data)
        return self.core_service.result_de(video)

    # ── Actualización ───────────────────────────────────────────────────────

    async def actualizar_video(
        self,
        video_id,
        data: VideoActualizarData,
    ) -> VideoResult:
        """Actualiza un video de forma atómica.

        Un video inexistente responde 404 (`VIDEO_NO_ENCONTRADO`).
        """
        return await sync_to_async(self._actualizar_video_sync)(video_id, data)

    @transaction.atomic
    def _actualizar_video_sync(self, video_id, data: VideoActualizarData):
        """Actualización atómica del video."""
        video = self.core_service.obtener(video_id)
        video = self.core_service.actualizar(video, data)
        return self.core_service.result_de(video)

    # ── Borrado ─────────────────────────────────────────────────────────────

    async def eliminar_video(self, video_id) -> bool:
        """Borra un video de forma atómica.

        Un video inexistente responde 404 (`VIDEO_NO_ENCONTRADO`): el borrado
        no es idempotente a propósito, para que el operador sepa si la fila
        estaba.
        """
        return await sync_to_async(self._eliminar_video_sync)(video_id)

    @transaction.atomic
    def _eliminar_video_sync(self, video_id) -> bool:
        """Borrado atómico del video."""
        video = self.core_service.obtener(video_id)
        video.delete()
        return True


__all__ = ["VideoFlujo"]
