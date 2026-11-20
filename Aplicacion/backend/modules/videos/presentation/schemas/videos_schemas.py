"""Esquemas HTTP del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/api-wrapper-presenter-contract.md` §2, §7 ·
         `contract/next-app-architecture-contract.md` (espejo Zod 1:1)

Los wrappers son TIPADOS y explícitos: `VideoOut` (detalle), `VideoListOut`
(lista) y las entradas `CrearVideoIn` / `ActualizarVideoIn`. No hay `z.any()`
en el espejo del frontend ni campos genéricos aquí.

Todos heredan de `core.types.BaseSchema`, que normaliza las cadenas vacías a
`None` ANTES de validar. Por eso `descripcion` es nullable en las ENTRADAS:
una descripción vacía es una descripción VACÍA, no un error de validación.

La URL se valida en el BORDE HTTP con la MISMA regla que el dominio
(`domain/urls.py`): sólo `http` y `https`, con host. Así `javascript:`,
`data:` y `ftp:` se rechazan con un 422 y el error viaja por
`error.field_errors.url`, que es el único canal de error por campo.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from core.types import BaseSchema
from modules.videos.domain.urls import es_url_http_valida


class VideoOut(BaseSchema):
    """Salida del detalle de un video."""

    id: UUID = Field(..., description="Identificador del video.")
    titulo: str = Field(..., description="Título del video.")
    descripcion: str = Field("", description="Descripción del video.")
    url: str = Field(..., description="Dirección pública del video.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class VideoListOut(BaseSchema):
    """Salida de un video en el listado."""

    id: UUID = Field(..., description="Identificador del video.")
    titulo: str = Field(..., description="Título del video.")
    descripcion: str = Field("", description="Descripción del video.")
    url: str = Field(..., description="Dirección pública del video.")
    created_at: datetime = Field(..., description="Momento de creación.")


class CrearVideoIn(BaseSchema):
    """Alta de un video."""

    titulo: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Título del video.",
    )
    descripcion: str | None = Field(
        None,
        max_length=5000,
        description="Descripción del video.",
    )
    url: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Dirección pública del video (http o https).",
    )

    @field_validator("url")
    @classmethod
    def _url_http_valida(cls, value: str) -> str:
        """Sólo `http` y `https`: nada de `javascript:`, `data:` ni `ftp:`."""
        if not es_url_http_valida(value):
            raise ValueError("La URL debe ser una dirección http o https válida.")
        return value.strip()


class ActualizarVideoIn(BaseSchema):
    """Actualización parcial de un video.

    El `PATCH` sólo toca los campos presentes en el payload: un campo ausente
    conserva su valor.
    """

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

    @field_validator("url")
    @classmethod
    def _url_http_valida(cls, value: str | None) -> str | None:
        """Sólo `http` y `https`: nada de `javascript:`, `data:` ni `ftp:`."""
        if value is None:
            return None
        if not es_url_http_valida(value):
            raise ValueError("La URL debe ser una dirección http o https válida.")
        return value.strip()

    @model_validator(mode="after")
    def _titulo_y_url_no_pueden_ser_nulos(self):
        """Un título o una URL enviados explícitamente no pueden ser nulos."""
        enviados = self.model_fields_set

        if "titulo" in enviados and self.titulo is None:
            raise ValueError("El título del video no puede ser nulo.")
        if "url" in enviados and self.url is None:
            raise ValueError("La URL del video no puede ser nula.")

        return self


__all__ = [
    "ActualizarVideoIn",
    "CrearVideoIn",
    "VideoListOut",
    "VideoOut",
]
