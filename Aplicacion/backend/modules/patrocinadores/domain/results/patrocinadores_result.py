"""Result objects del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.6 (DTOs de salida)

Los results son la frontera entre el dominio y la presentación: llevan el
hecho ya calculado para que el presenter sea un transformador puro.

Sobre la degradación de media (FR-06 §2.7): si el archivo deja de existir en
disco, la imagen viaja con `disponible = False` y `url = None`. La galería
DEGRADA CON AVISO y no se lanza un error 500 ni se oculta el hueco.

Sobre la visibilidad (ADM-21): `visible` viaja como un hecho del
patrocinador. El filtro de quién puede ver qué es de la CAPA DE CONSUMO, no
del result: el dominio proyecta el patrocinador y su estado de visibilidad.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PatrocinadorLogoResult(BaseModel):
    """El logo de identidad del patrocinador."""

    url: str | None = Field(None, description="URL pública del archivo.")
    disponible: bool = Field(True, description="Si el archivo existe en el volumen.")


class PatrocinadorImagenResult(BaseModel):
    """Una imagen de la galería, en su orden canónico."""

    id: UUID = Field(..., description="Identificador de la imagen.")
    orden: int = Field(..., description="Orden canónico dentro de la galería.")
    url: str | None = Field(None, description="URL pública del archivo.")
    texto_alternativo: str = Field("", description="Texto alternativo (alt).")
    disponible: bool = Field(True, description="Si el archivo existe en el volumen.")
    created_at: datetime = Field(..., description="Momento de creación.")


class PatrocinadorResult(BaseModel):
    """Un patrocinador, con su logo y su galería ordenada."""

    id: UUID = Field(..., description="Identificador del patrocinador.")
    edicion_id: UUID = Field(..., description="Edición de alcance.")
    edicion_nombre: str = Field("", description="Nombre de la edición.")
    nombre: str = Field(..., description="Nombre del patrocinador.")
    slug: str = Field(..., description="Identificador del patrocinador en la edición.")
    descripcion: str = Field("", description="Descripción de la ficha.")
    sitio_web: str = Field("", description="Sitio web del patrocinador.")
    visible: bool = Field(True, description="Visibilidad pública (ADM-21).")
    orden: int = Field(0, description="Posición persistida del banner público.")
    logo: PatrocinadorLogoResult | None = Field(
        None,
        description="Logo de identidad; `None` si el patrocinador no tiene logo.",
    )
    imagenes: list[PatrocinadorImagenResult] = Field(
        default_factory=list,
        description="Galería ordenada del patrocinador.",
    )
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


__all__ = [
    "PatrocinadorImagenResult",
    "PatrocinadorLogoResult",
    "PatrocinadorResult",
]
