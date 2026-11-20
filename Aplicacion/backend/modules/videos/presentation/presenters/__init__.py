"""Presenters del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/api-wrapper-presenter-contract.md` §3
"""

from modules.videos.presentation.presenters.videos_presenter import (
    VideoListaPresenter,
    VideoPresenter,
)

__all__ = [
    "VideoListaPresenter",
    "VideoPresenter",
]
