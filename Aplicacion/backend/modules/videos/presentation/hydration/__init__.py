"""Hidración de la capa HTTP del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.8
"""

from modules.videos.presentation.hydration.videos_hydrator import VideoHydrator

__all__ = ["VideoHydrator"]
