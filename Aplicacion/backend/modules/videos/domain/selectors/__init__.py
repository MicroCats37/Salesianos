"""Selectores del módulo `videos`.

Change: `public-video-streaming-crud`
"""

from modules.videos.domain.selectors.video_selector import (
    COLUMNAS_ORDEN,
    VideoSelector,
)

__all__ = [
    "COLUMNAS_ORDEN",
    "VideoSelector",
]
