"""`VideoService` — escritura y proyección de los videos.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.3 (core services)

El core service es SYNC y **NO abre `transaction.atomic()`**: la atomicidad
compuesta la aporta el flujo.

Reglas que este servicio es el dueño de:

- **URL `http`/`https`**: un video con `javascript:`, `data:` o `ftp:` no es
  un video. La regla vive en `domain/urls.py` (dominio puro) y este servicio
  la aplica ANTES de escribir.
- **Actualización parcial**: un `PATCH` sólo toca los campos presentes en el
  payload (`exclude_unset`).
- **Proyección a results**: el service devuelve result objects; el presenter
  los convierte en wrappers HTTP.
"""

from modules.videos.domain.exceptions import (
    VideoNoEncontradoError,
    VideoUrlInvalidaError,
)
from modules.videos.domain.models import Video
from modules.videos.domain.results.videos_results import (
    VideoListadoResult,
    VideoResult,
)
from modules.videos.domain.schemas.videos_schemas import (
    VideoActualizarData,
    VideoCrearData,
)
from modules.videos.domain.selectors.video_selector import VideoSelector
from modules.videos.domain.urls import es_url_http_valida


class VideoService:
    """Operaciones de escritura y proyección sobre `Video`."""

    def __init__(self, selector: VideoSelector = None):
        self.selector = selector or VideoSelector()

    # ── Alta ────────────────────────────────────────────────────────────────

    def crear(self, data: VideoCrearData) -> Video:
        """Crea un video.

        La URL se valida ANTES de escribir: un esquema no permitido nunca
        llega a la base de datos.
        """
        self._exigir_url_valida(data.url)

        return Video.objects.create(
            titulo=data.titulo,
            descripcion=data.descripcion or "",
            url=data.url,
        )

    # ── Actualización ───────────────────────────────────────────────────────

    def actualizar(self, video: Video, data: VideoActualizarData) -> Video:
        """Actualización parcial: sólo cambian los campos presentes."""
        campos = data.model_dump(exclude_unset=True)

        if "url" in campos:
            self._exigir_url_valida(campos["url"] or "")
            campos["url"] = (campos["url"] or "").strip()

        if "descripcion" in campos:
            # Una descripción vacía o nula es una descripción VACÍA: el
            # campo es texto libre y no admite `null`.
            campos["descripcion"] = campos["descripcion"] or ""

        if "titulo" in campos:
            campos["titulo"] = (campos["titulo"] or "").strip()

        for campo, valor in campos.items():
            setattr(video, campo, valor)

        video.save()
        return video

    # ── Lectura ─────────────────────────────────────────────────────────────

    def obtener(self, video_id) -> Video:
        """Un video por identificador.

        Lanza `VideoNoEncontradoError` (404) cuando no existe.
        """
        video = self.selector.obtener_por_id(video_id)
        if video is None:
            raise VideoNoEncontradoError()
        return video

    # ── Proyección a results ────────────────────────────────────────────────

    @staticmethod
    def result_de(video: Video) -> VideoResult:
        """Proyecta un video al result object."""
        return VideoResult(
            id=video.id,
            titulo=video.titulo,
            descripcion=video.descripcion or "",
            url=video.url,
            created_at=video.created_at,
            updated_at=video.updated_at,
        )

    @staticmethod
    def result_listado(
        items: list[Video],
        total: int,
        page: int,
        page_size: int,
    ) -> VideoListadoResult:
        """Proyecta una página del listado al result object."""
        return VideoListadoResult(
            items=[VideoService.result_de(video) for video in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if total else 0,
        )

    # ── Invariantes ─────────────────────────────────────────────────────────

    @staticmethod
    def _exigir_url_valida(url: str) -> None:
        """Rechaza cualquier URL que no sea `http`/`https` con host."""
        if not es_url_http_valida(url):
            raise VideoUrlInvalidaError()


__all__ = ["VideoService"]
