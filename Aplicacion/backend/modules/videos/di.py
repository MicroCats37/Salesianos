"""Wiring de dependencias (DI) del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.15

El módulo se registra en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Este archivo sólo declara las ligas del módulo.

El módulo `videos` es una HOJA del grafo de dependencias: no consume ningún
otro dominio, así que su wiring no puede entrar en un ciclo.
"""

from injector import Binder, Module, singleton

from modules.videos.domain.selectors.video_selector import VideoSelector
from modules.videos.domain.services.core.video_service import VideoService
from modules.videos.domain.services.flujos.video_flujo import VideoFlujo
from modules.videos.domain.services.orchestrators.video_orchestrator import (
    VideoOrchestrator,
)


class VideosModule(Module):
    """Bindings de dependencias del módulo `videos`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(VideoSelector, to=VideoSelector, scope=singleton)
        binder.bind(VideoService, to=VideoService, scope=singleton)
        binder.bind(VideoFlujo, to=VideoFlujo, scope=singleton)
        binder.bind(VideoOrchestrator, to=VideoOrchestrator, scope=singleton)


__all__ = ["VideosModule"]
