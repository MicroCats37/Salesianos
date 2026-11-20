"""`AdminVideosController` — la superficie de ADMINISTRACIÓN de los videos.

Change: `public-video-streaming-crud`

| Ruta | Método | Wrapper |
|---|---|---|
| `GET /api/administracion/videos` | GET | `PaginatedData[VideoListOut]` |
| `GET /api/administracion/videos/{video_id}` | GET | `VideoOut` |
| `POST /api/administracion/videos` | POST | `VideoOut` (201) |
| `PATCH /api/administracion/videos/{video_id}` | PATCH | `VideoOut` |
| `DELETE /api/administracion/videos/{video_id}` | DELETE | 204 sin cuerpo |

**401 ANTES QUE 403**: `auth=JWTAuth()` + la puerta `RequireAdmin`
(`is_staff` OR `is_superuser`). Un anónimo recibe 401 y nunca llega a la
comprobación de autorización (`core/permissions.py`).

El `DELETE` responde **204 SIN CUERPO**: un 204 nunca se parsea
(`FREEZE-ENV-1.0.0` §4.4).

El controller es "SAGRADO": cero lógica
(`contract/PLAN_REFACTORIZACION.md` §1.A).
"""

from uuid import UUID

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from core.pagination import PaginatedData
from core.permissions import RequireAdmin
from core.responses import ApiResponse, paginated_response, success_response
from modules.videos.domain.schemas.videos_schemas import (
    VideoActualizarData,
    VideoCrearData,
)
from modules.videos.domain.services.orchestrators.video_orchestrator import (
    VideoOrchestrator,
)
from modules.videos.presentation.hydration.videos_hydrator import VideoHydrator
from modules.videos.presentation.presenters.videos_presenter import (
    VideoListaPresenter,
    VideoPresenter,
)
from modules.videos.presentation.schemas.videos_schemas import (
    VideoListOut,
    VideoOut,
)


@api_controller("/administracion/videos", tags=["Administración de videos"])
class AdminVideosController:
    """La gestión de los videos de la sala de proyección."""

    @inject
    def __init__(self, orchestrator: VideoOrchestrator):
        self.orchestrator = orchestrator

    @route.get(
        "",
        response={200: ApiResponse[PaginatedData[VideoListOut]]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="El listado administrativo de videos.",
    )
    async def listar_videos(
        self,
        request,
        q: str | None = Query(
            None,
            description="Búsqueda por título o descripción.",
        ),
        ordering: str | None = Query(
            None,
            description="Orden (lista blanca): created_at, updated_at, titulo.",
        ),
        page: int = Query(1, ge=1, description="Página (1-based)."),
        page_size: int = Query(25, ge=1, le=100, description="Tamaño de página."),
    ):
        """Route: GET /api/administracion/videos

        El listado administrativo SÍ se pagina: el total y los metadatos
        viajan DENTRO de `data`.
        """
        resultado = await self.orchestrator.listar_videos_admin(
            q=q,
            ordering=ordering,
            page=page,
            page_size=page_size,
        )
        return paginated_response(
            VideoListaPresenter.present_lista(resultado.items),
            total=resultado.total,
            page=resultado.page,
            page_size=resultado.page_size,
        )

    @route.get(
        "/{video_id}",
        response={200: ApiResponse[VideoOut]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="El detalle administrativo de un video.",
    )
    async def obtener_video(self, request, video_id: UUID):
        """Route: GET /api/administracion/videos/{video_id}

        Un video inexistente responde 404 con `error.code = VIDEO_NO_ENCONTRADO`.
        """
        result = await self.orchestrator.obtener_video(video_id)
        return success_response(VideoPresenter.present(result))

    @route.post(
        "",
        response={201: ApiResponse[VideoOut]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="Publica un video nuevo.",
    )
    async def crear_video(self, request):
        """Route: POST /api/administracion/videos

        La URL se valida en el borde HTTP y en el dominio: sólo `http` y
        `https` con host. Un esquema distinto responde 422 y NO se persiste.
        """
        payload = VideoHydrator.hydrate_crear(request)

        result = await self.orchestrator.crear_video(
            VideoCrearData(
                titulo=payload.titulo,
                descripcion=payload.descripcion or "",
                url=payload.url,
            )
        )
        return success_response(
            VideoPresenter.present(result),
            message="El video se registró correctamente.",
        )

    @route.patch(
        "/{video_id}",
        response={200: ApiResponse[VideoOut]},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="Edita un video.",
    )
    async def actualizar_video(
        self,
        request,
        video_id: UUID,
    ):
        """Route: PATCH /api/administracion/videos/{video_id}

        El `PATCH` es PARCIAL: sólo cambian los campos presentes en el
        payload.
        """
        payload = VideoHydrator.hydrate_actualizar(request)

        result = await self.orchestrator.actualizar_video(
            video_id,
            VideoActualizarData(
                **payload.model_dump(exclude_unset=True),
            ),
        )
        return success_response(
            VideoPresenter.present(result),
            message="El video se actualizó correctamente.",
        )

    @route.delete(
        "/{video_id}",
        response={204: None},
        auth=JWTAuth(),
        permissions=[RequireAdmin],
        summary="Elimina un video.",
    )
    async def eliminar_video(self, request, video_id: UUID):
        """Route: DELETE /api/administracion/videos/{video_id}

        Responde **204 SIN CUERPO**: un 204 nunca se parsea
        (`FREEZE-ENV-1.0.0` §4.4). Un video inexistente responde 404.
        """
        await self.orchestrator.eliminar_video(video_id)
        return None


__all__ = ["AdminVideosController"]
