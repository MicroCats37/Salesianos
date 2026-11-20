"""Payloads de prueba del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §4 · §10.5

`factories.py` NO es un archivo de fixtures: contiene funciones PURAS que
devuelven `dict`. No hay base de datos, no hay pytest, no hay `factory_boy` y
no hay `unittest.mock.patch`.

Los payloads de los tests se IMPORTAN, nunca se escriben en línea.
"""

#: URL de un video reproducible: el cliente la clasifica como ARCHIVO.
URL_ARCHIVO = "https://media.salesianosfest.org/videos/presentacion.mp4"

#: URL de un embed de un proveedor permitido.
URL_EMBED = "https://www.youtube.com/embed/dQw4w9WgXcQ"


def make_video_payload(
    titulo: str = "Presentación del festival",
    descripcion: str = "El saludo de apertura.",
    url: str = URL_ARCHIVO,
) -> dict:
    """El payload del alta y de la edición de un video."""
    return {
        "titulo": titulo,
        "descripcion": descripcion,
        "url": url,
    }


def make_video_update_payload(
    titulo: str | None = None,
    descripcion: str | None = None,
    url: str | None = None,
) -> dict:
    """El payload de una edición PARCIAL: sólo lo que se quiere cambiar."""
    payload: dict = {}

    if titulo is not None:
        payload["titulo"] = titulo
    if descripcion is not None:
        payload["descripcion"] = descripcion
    if url is not None:
        payload["url"] = url

    return payload


__all__ = [
    "URL_ARCHIVO",
    "URL_EMBED",
    "make_video_payload",
    "make_video_update_payload",
]
