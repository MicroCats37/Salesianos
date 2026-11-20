"""DTOs internos del módulo `videos`.

Change: `public-video-streaming-crud`
"""

from modules.videos.domain.schemas.videos_schemas import (
    VideoActualizarData,
    VideoCrearData,
)

__all__ = [
    "VideoActualizarData",
    "VideoCrearData",
]
