"""`VideoController` — la superficie PÚBLICA de la sala de proyección.

Change: `public-video-streaming-crud`

| Ruta | Método | Wrapper |
|---|---|---|
| `GET /api/videos` | GET | `list[VideoListOut]` |
| `GET /api/videos/{video_id}` | GET | `VideoOut` |

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A). Sólo parsea, delega al
orquestador y devuelve el éxito formateado por el presenter. Los errores los
traduce el catálogo global de `core/exceptions.py`; este archivo no construye
respuestas de error.

La superficie pública NO expone escrituras: un video se publica desde el
panel de administración (`AdminVideosController`).

La ruta es ANÓNIMA: `auth=None` + `permissions=[AllowAny]`. El video es un
contenido público por definición — el modelo no tiene `es_publico`.
"""

from uuid import UUID

from injector import inject
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny

from core.responses import ApiResponse, success_response
from modules.videos.domain.services.orchestrators.video_orchestrator import (
    VideoOrchestrator,
)
from modules.videos.presentation.presenters.videos_presenter import (
    VideoListaPresenter,
    VideoPresenter,
)
from modules.videos.presentation.schemas.videos_schemas import (
    VideoListOut,
    VideoOut,
)


@api_controller("/videos", tags=["Videos"])
class VideoController:
    """La galería pública de videos."""

    @inject
    def __init__(self, orchestrator: VideoOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "",
        response={200: ApiResponse[list[VideoListOut]]},
        auth=None,
        permissions=[AllowAny],
        summary="La galería pública de videos.",
    )
    async def listar_videos(self, request):
        """Route: GET /api/videos

        El listado público NO se pagina: devuelve la galería completa, del
        video más reciente al más antiguo.
        """
        items = await self.orchestrator.listar_videos()
        return success_response(VideoListaPresenter.present_lista(items))

    @route.get(
        "/{video_id}",
        response={200: ApiResponse[VideoOut]},
        auth=None,
        permissions=[AllowAny],
        summary="El detalle de un video.",
    )
    async def obtener_video(self, request, video_id: UUID):
        """Route: GET /api/videos/{video_id}

        Un video inexistente responde 404 con `error.code = VIDEO_NO_ENCONTRADO`.
        """
        result = await self.orchestrator.obtener_video(video_id)
        return success_response(VideoPresenter.present(result))


__all__ = ["VideoController"]
