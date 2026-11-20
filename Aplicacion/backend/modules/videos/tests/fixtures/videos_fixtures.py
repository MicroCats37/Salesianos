"""Fixtures del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3

Las fixtures viven aquí; `modules/videos/tests/conftest.py` sólo las importa y
registra.

El módulo `videos` NO comparte fixtures con ningún otro módulo: su entidad
es editorial y no depende de la edición, del evento ni de la persona. Sus
únicas cuentas son las dos que necesita la frontera de permisos: una
administradora (`is_staff`) y una normal.
"""

import pytest

from modules.videos.domain.models import Video


#: URL de un video reproducible: el cliente la clasifica como ARCHIVO.
URL_ARCHIVO = "https://media.salesianosfest.org/videos/presentacion.mp4"

#: URL de un embed de un proveedor permitido.
URL_EMBED = "https://www.youtube.com/embed/dQw4w9WgXcQ"

#: URL de un host que NO está en la lista blanca de embeds.
URL_EXTERNA = "https://ejemplo.org/videos/presentacion.mp4"


@pytest.fixture
def video(db):
    """Un video publicado."""
    return Video.objects.create(
        titulo="Presentación del festival",
        descripcion="El saludo de apertura.",
        url=URL_ARCHIVO,
    )


@pytest.fixture
def video_2(db):
    """Un segundo video publicado, para las pruebas de listado."""
    return Video.objects.create(
        titulo="Charla deinners",
        descripcion="La charla inaugural.",
        url=URL_EMBED,
    )


@pytest.fixture
def usuario_admin_videos(db):
    """Cuenta con `is_staff`: la puerta `RequireAdmin` la admite."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="admin.videos",
        password="Prueba-12345",
        email="admin.videos@example.com",
        is_staff=True,
    )


@pytest.fixture
def usuario_no_admin_videos(db):
    """Cuenta normal: autenticada, pero sin `is_staff`."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="normal.videos",
        password="Prueba-12345",
        email="normal.videos@example.com",
    )


@pytest.fixture
def token_admin_videos(usuario_admin_videos):
    """Token JWT de la cuenta administradora."""
    from ninja_jwt.tokens import AccessToken

    return AccessToken.for_user(usuario_admin_videos)


@pytest.fixture
def token_no_admin_videos(usuario_no_admin_videos):
    """Token JWT de la cuenta normal."""
    from ninja_jwt.tokens import AccessToken

    return AccessToken.for_user(usuario_no_admin_videos)
