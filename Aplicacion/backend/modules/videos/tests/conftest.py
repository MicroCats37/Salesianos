"""Registro de fixtures del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3.3

Este `conftest.py` sólo importa y registra los módulos de fixtures; las
fixtures reales viven en `fixtures/`.
"""

import pytest

from modules.videos.tests.fixtures.videos_fixtures import (  # noqa: F401
    URL_ARCHIVO,
    URL_EMBED,
    URL_EXTERNA,
    token_admin_videos,
    token_no_admin_videos,
    usuario_admin_videos,
    usuario_no_admin_videos,
    video,
    video_2,
)


@pytest.fixture(scope="session")
def injector():
    """El inyector de dependencias del módulo `videos`.

    El módulo es una HOJA del grafo: no liga ningún módulo de dominio, así
    que su wiring se registra solo.
    """
    from injector import Injector

    from modules.videos.di import VideosModule

    return Injector([VideosModule])
