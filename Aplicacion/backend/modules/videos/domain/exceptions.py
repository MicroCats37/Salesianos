"""Excepciones de dominio del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §10 (Exceptions) ·
         `contract/api-wrapper-presenter-contract.md` §8

Cada excepción declara un `code` ESTABLE y machine-readable. El mensaje
público lo decide el catálogo de `core/exceptions.py` a partir de ese código:
esta clase NUNCA construye prosa para el usuario ni interpola UUIDs,
identificadores internos ni texto crudo.

Los dos códigos de este módulo:

- `VIDEO_NO_ENCONTRADO` (404) — el video solicitado no existe.
- `VIDEO_URL_INVALIDA` (422) — la URL no es una dirección `http`/`https`
  válida. Es un invariante ESTRUCTURAL del dato: una URL con otro esquema
  (`javascript:`, `data:`, `ftp:`) no es una URL de video.
"""

from core.exceptions import NotFoundError, UnprocessableEntityError


class VideoNoEncontradoError(NotFoundError):
    """El video solicitado no existe."""

    code = "VIDEO_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Video", code=self.code)


class VideoUrlInvalidaError(UnprocessableEntityError):
    """La URL del video no es una dirección `http`/`https` válida."""

    code = "VIDEO_URL_INVALIDA"

    def __init__(self):
        super().__init__(
            message="La URL del video no es válida.",
            code=self.code,
        )


__all__ = [
    "VideoNoEncontradoError",
    "VideoUrlInvalidaError",
]
