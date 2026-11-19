"""Result objects del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.6 (DTOs de salida)

Los results son la frontera entre el dominio y la presentación: llevan el
hecho ya calculado (incluido `precio_efectivo` y `oferta_activa`, que decide
el DOMINIO) para que el presenter sea un transformador puro.

Sobre la degradación de media (FR-06 §2.7): si el archivo deja de existir en
disco, la imagen viaja con `disponible = False` y `url = None`. La galería
DEGRADA CON AVISO y no se lanza un error 500 ni se oculta el hueco.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ProductoImagenResult(BaseModel):
    """Una imagen de la galería, en su orden canónico."""

    id: UUID = Field(..., description="Identificador de la imagen.")
    orden: int = Field(..., description="Orden canónico dentro de la galería.")
    url: str | None = Field(None, description="URL pública del archivo.")
    es_principal: bool = Field(False, description="Si es la imagen principal explícita.")
    texto_alternativo: str = Field("", description="Texto alternativo (alt).")
    disponible: bool = Field(True, description="Si el archivo existe en el volumen.")
    created_at: datetime = Field(..., description="Momento de creación.")


class ProductoResult(BaseModel):
    """Un producto del catálogo, con su galería ordenada."""

    id: UUID = Field(..., description="Identificador del producto.")
    edicion_id: UUID = Field(..., description="Edición de alcance.")
    edicion_nombre: str = Field("", description="Nombre de la edición.")
    categoria_id: UUID | None = Field(None, description="Categoría del producto.")
    categoria_nombre: str | None = Field(None, description="Nombre de la categoría.")
    nombre: str = Field(..., description="Nombre del producto.")
    slug: str = Field(..., description="Identificador del producto en la edición.")
    descripcion: str = Field("", description="Descripción del producto.")
    precio: Decimal = Field(..., description="Precio normal.")
    precio_oferta: Decimal | None = Field(None, description="Precio de oferta.")
    precio_efectivo: Decimal = Field(..., description="Precio que rige ahora.")
    oferta_activa: bool = Field(False, description="Si la oferta está vigente.")
    oferta_inicia: datetime | None = Field(None, description="Inicio de la oferta.")
    oferta_termina: datetime | None = Field(None, description="Fin de la oferta.")
    estado: str = Field(..., description="Estado comercial del producto.")
    imagenes: list[ProductoImagenResult] = Field(
        default_factory=list,
        description="Galería ordenada del producto.",
    )
    imagen_principal_url: str | None = Field(
        None,
        description="URL de la imagen principal explícita, si la hay.",
    )
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class ProductoListItemResult(BaseModel):
    """Un producto en la lista del catálogo: lo mínimo para una tarjeta."""

    id: UUID = Field(..., description="Identificador del producto.")
    nombre: str = Field(..., description="Nombre del producto.")
    slug: str = Field(..., description="Identificador del producto en la edición.")
    categoria_id: UUID | None = Field(None, description="Categoría del producto.")
    categoria_nombre: str | None = Field(None, description="Nombre de la categoría.")
    precio: Decimal = Field(..., description="Precio normal.")
    precio_oferta: Decimal | None = Field(None, description="Precio de oferta.")
    precio_efectivo: Decimal = Field(..., description="Precio que rige ahora.")
    oferta_activa: bool = Field(False, description="Si la oferta está vigente.")
    estado: str = Field(..., description="Estado comercial del producto.")
    imagen_principal_url: str | None = Field(
        None,
        description="URL de la imagen principal explícita, si la hay.",
    )
    cantidad_imagenes: int = Field(0, description="Imágenes de la galería.")


class CategoriaProductoResult(BaseModel):
    """Una categoría del catálogo."""

    id: UUID = Field(..., description="Identificador de la categoría.")
    nombre: str = Field(..., description="Nombre de la categoría.")
    slug: str = Field(..., description="Identificador de la categoría.")
    orden: int = Field(0, description="Orden de la categoría.")


__all__ = [
    "CategoriaProductoResult",
    "ProductoImagenResult",
    "ProductoListItemResult",
    "ProductoResult",
]
