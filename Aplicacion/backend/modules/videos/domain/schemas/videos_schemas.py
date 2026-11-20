"""DTOs internos del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.6 (DTOs internos)

Estos DTOs son Pydantic `BaseModel` (NO schemas HTTP): describen lo que la
capa de servicios necesita, no lo que el cliente envía.

`VideoActualizarData` es PARCIAL: sólo se aplican los campos presentes en el
payload (`exclude_unset`), de modo que un `PATCH` que no menciona la
descripción no la toca.
"""

from pydantic import BaseModel, Field


class VideoCrearData(BaseModel):
    """Alta de un video."""

    titulo: str = Field(..., min_length=1, max_length=200, description="Título del video.")
    descripcion: str = Field(
        "",
        max_length=5000,
        description="Descripción del video.",
    )
    url: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Dirección pública del video (http o https).",
    )


class VideoActualizarData(BaseModel):
    """Actualización parcial de un video."""

    titulo: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Título del video.",
    )
    descripcion: str | None = Field(
        None,
        max_length=5000,
        description="Descripción del video.",
    )
    url: str | None = Field(
        None,
        min_length=1,
        max_length=500,
        description="Dirección pública del video (http o https).",
    )


__all__ = [
    "VideoActualizarData",
    "VideoCrearData",
]
