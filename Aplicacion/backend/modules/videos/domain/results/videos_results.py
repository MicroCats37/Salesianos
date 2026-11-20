"""Result objects del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.6 · §4.9

Los result objects son el contrato entre el DOMINIO y la capa HTTP: el
orquestador devuelve result objects y el presenter los convierte en wrappers.
Son Pydantic (`BaseModel`) y NO conocen el envelope HTTP.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class VideoResult(BaseModel):
    """Un video del dominio, proyectado a result object."""

    id: UUID = Field(..., description="Identificador del video.")
    titulo: str = Field(..., description="Título del video.")
    descripcion: str = Field("", description="Descripción del video.")
    url: str = Field(..., description="Dirección pública del video.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class VideoListadoResult(BaseModel):
    """Una página del listado administrativo de videos."""

    items: list[VideoResult] = Field(default_factory=list, description="Videos de la página.")
    total: int = Field(0, description="Total de videos que cumplen el filtro.")
    page: int = Field(1, description="Página, 1-based.")
    page_size: int = Field(25, description="Tamaño de la página.")
    total_pages: int = Field(0, description="Número de páginas del listado.")


__all__ = [
    "VideoListadoResult",
    "VideoResult",
]
