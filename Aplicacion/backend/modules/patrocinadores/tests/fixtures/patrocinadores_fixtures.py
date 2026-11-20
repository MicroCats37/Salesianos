"""Fixtures compartidas del módulo `patrocinadores`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §3

Las fixtures viven aquí; `modules/patrocinadores/tests/conftest.py` sólo las
importa y registra.
"""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image


def _bytes_de_imagen(formato: str) -> bytes:
    """Una imagen real y mínima en el formato pedido.

    Se genera con Pillow (dependencia declarada del proyecto) para que la
    firma de contenido sea auténtica: el validador de `core.media` compara
    los bytes mágicos con el MIME declarado.
    """
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 120, 200)).save(buffer, format=formato)
    return buffer.getvalue()


#: Bytes de un PNG válido.
PNG_MINIMO = _bytes_de_imagen("PNG")

#: Bytes de un JPEG válido.
JPEG_MINIMO = _bytes_de_imagen("JPEG")


def archivo_png(nombre: str = "logo.png") -> SimpleUploadedFile:
    """Un PNG válido con el MIME correcto."""
    return SimpleUploadedFile(nombre, PNG_MINIMO, content_type="image/png")


def archivo_jpeg(nombre: str = "logo.jpg") -> SimpleUploadedFile:
    """Un JPEG válido con el MIME correcto."""
    return SimpleUploadedFile(nombre, JPEG_MINIMO, content_type="image/jpeg")


def archivo_mentiroso(nombre: str = "mentiroso.png") -> SimpleUploadedFile:
    """Un archivo que DECLARA `image/png` pero NO tiene firma de imagen."""
    return SimpleUploadedFile(nombre, b"esto no es una imagen" * 10, content_type="image/png")


def archivo_grande(nombre: str = "grande.png") -> SimpleUploadedFile:
    """Un PNG válido que excede el tope de tamaño configurado."""
    return SimpleUploadedFile(nombre, PNG_MINIMO * 4096, content_type="image/png")


# ── Datos del dominio ───────────────────────────────────────────────────────


@pytest.fixture
def evento(db):
    """Evento propietario de la edición de los tests."""
    from modules.eventos.domain.models import Evento

    return Evento.objects.create(nombre="Salesianos FEST", slug="salesianos-fest")


@pytest.fixture
def edicion_publicada(db, evento):
    """Edición `PUBLICADA` con el módulo `patrocinadores` habilitado."""
    from modules.eventos.domain.constants import EstadoEdicion
    from modules.eventos.domain.models import Edicion

    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2026",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=["patrocinadores"],
    )


@pytest.fixture
def edicion_sin_patrocinadores(db, evento):
    """Edición `PUBLICADA` con el módulo `patrocinadores` DESHABILITADO."""
    from modules.eventos.domain.constants import EstadoEdicion
    from modules.eventos.domain.models import Edicion

    return Edicion.objects.create(
        evento=evento,
        nombre="Salesianos FEST 2024",
        slug="2024",
        anio=2024,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=["pases"],
    )


@pytest.fixture
def edicion_otra(db):
    """Otra edición publicada de OTRO evento.

    La base de datos admite como máximo una edición `PUBLICADA` por evento,
    así que la segunda edición vive en otro evento: sirve para comprobar la
    coherencia de edición sin romper el invariante de FND-02.
    """
    from modules.eventos.domain.constants import EstadoEdicion
    from modules.eventos.domain.models import Edicion, Evento

    otro_evento = Evento.objects.create(nombre="Otro FEST", slug="otro-fest")
    return Edicion.objects.create(
        evento=otro_evento,
        nombre="Otro FEST 2026",
        slug="2026",
        anio=2026,
        estado=EstadoEdicion.PUBLICADA,
        modulos_habilitados=["patrocinadores"],
    )


@pytest.fixture
def patrocinador(db, edicion_publicada):
    """Patrocinador de ejemplo, visible y sin archivos."""
    from modules.patrocinadores.domain.models import Patrocinador

    return Patrocinador.objects.create(
        edicion=edicion_publicada,
        nombre="Colegio San Juan Bosco",
        slug="colegio-san-juan-bosco",
        descripcion="Patrocinador de la edición 2026.",
        visible=True,
    )


@pytest.fixture
def usuario_admin(db):
    """Cuenta con `is_staff`: el permiso `Administrador` del ledger."""
    from modules.usuarios.domain.models import Usuario

    return Usuario.objects.create_user(
        username="admin.patrocinadores",
        password="Prueba-12345",
        email="admin.patrocinadores@example.com",
        is_staff=True,
    )


@pytest.fixture
def token_admin(usuario_admin):
    """Token JWT de la cuenta administradora."""
    from ninja_jwt.tokens import AccessToken

    return AccessToken.for_user(usuario_admin)


@pytest.fixture
def media_root(tmp_path, settings):
    """Apunta `MEDIA_ROOT` a un directorio temporal de test.

    El volumen de media del proyecto es ESTADO DURABLE: los tests NUNCA
    escriben en él. Al terminar, pytest borra el directorio temporal.

    `settings.MEDIA_ROOT` dispara la señal `setting_changed`, que limpia las
    propiedades cacheadas de `FileSystemStorage`: el `default_storage` sigue
    apuntando al directorio temporal durante todo el test.
    """
    destino = tmp_path / "media"
    destino.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(destino)
    return destino
