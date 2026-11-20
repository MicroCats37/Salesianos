"""Presenters del módulo `videos` — result de dominio → schema HTTP.

Change: `public-video-streaming-crud`
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)

Los presenters son TRANSFORMADORES PUROS: reciben un result object y
devuelven un schema HTTP. No consultan la base de datos, no llaman a
selectores y no construyen mensajes públicos de error.
"""

from modules.videos.domain.results.videos_results import VideoResult
from modules.videos.presentation.schemas.videos_schemas import (
    VideoListOut,
    VideoOut,
)


class VideoPresenter:
    """Presenter del detalle de un video."""

    @staticmethod
    def present(result: VideoResult) -> VideoOut:
        """Proyecta el result de un video al wrapper HTTP."""
        return VideoOut(
            id=result.id,
            titulo=result.titulo,
            descripcion=result.descripcion,
            url=result.url,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )


class VideoListaPresenter:
    """Presenter del listado de videos."""

    @staticmethod
    def present_lista(items: list[VideoResult]) -> list[VideoListOut]:
        """Proyecta la lista de videos al wrapper HTTP."""
        return [
            VideoListOut(
                id=item.id,
                titulo=item.titulo,
                descripcion=item.descripcion,
                url=item.url,
                created_at=item.created_at,
            )
            for item in items
        ]


__all__ = [
    "VideoListaPresenter",
    "VideoPresenter",
]
