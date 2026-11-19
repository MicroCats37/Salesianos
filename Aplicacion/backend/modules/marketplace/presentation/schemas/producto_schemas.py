"""Esquemas HTTP del módulo `marketplace`.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0`
Contract: `contract/SCHEMA_DRY_INTENTION.md` (composición) ·
          `contract/api-wrapper-presenter-contract.md` §2, §7

Composición de los TRES bloques (SCHEMA_DRY_INTENTION):

| Bloque | Contenido | Clase |
|---|---|---|
| Identidad | ids + marcas de tiempo | `ProductoIdentidadOut` |
| General | lo compartido por casi todas las salidas | `ProductoGeneralOut` |
| Específico | lo que varía por caso de uso | `ProductoEspecificaOut` |

`ProductoOut` y `ProductoDetalleOut` se COMONEN de esos bloques; no son
schemas monolíticos duplicados.

Fechas TIPADAS en el borde HTTP: `oferta_inicia` y `oferta_termina` son
`datetime`, nunca cadenas que el controller tenga que parsear.

Todos heredan de `core.types.BaseSchema` (`contract/PLAN_REFACTORIZACION.md`
§C). El espejo Zod 1:1 del frontend es responsabilidad de A7 (FR-07 §1.1);
este lado NO declara `z.any()` ni campos genéricos.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


class ProductoIdentidadOut(BaseSchema):
    """Bloque de identidad: identificadores y marcas de tiempo."""

    id: UUID = Field(..., description="Identificador del producto.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class ProductoGeneralOut(BaseSchema):
    """Bloque general: el alcance de edición y la categoría."""

    edicion_id: UUID = Field(..., description="Edición de alcance del producto.")
    edicion_nombre: str = Field("", description="Nombre de la edición.")
    categoria_id: UUID | None = Field(None, description="Categoría del producto.")
    categoria_nombre: str | None = Field(None, description="Nombre de la categoría.")


class ProductoEspecificaOut(BaseSchema):
    """Bloque específico: identidad comercial, precio y oferta."""

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


class ProductoImagenOut(BaseSchema):
    """Una imagen de la galería, en su orden canónico."""

    id: UUID = Field(..., description="Identificador de la imagen.")
    orden: int = Field(..., description="Orden canónico dentro de la galería.")
    url: str | None = Field(None, description="URL pública del archivo.")
    es_principal: bool = Field(False, description="Si es la imagen principal.")
    texto_alternativo: str = Field("", description="Texto alternativo (alt).")
    disponible: bool = Field(True, description="Si el archivo existe en el volumen.")
    created_at: datetime = Field(..., description="Momento de creación.")


class ProductoOut(ProductoIdentidadOut, ProductoGeneralOut, ProductoEspecificaOut):
    """Salida de un producto. Composición de los tres bloques."""

    imagenes: list[ProductoImagenOut] = Field(
        default_factory=list,
        description="Galería ordenada del producto.",
    )
    imagen_principal_url: str | None = Field(
        None,
        description="URL de la imagen principal explícita, si la hay.",
    )


class ProductoDetalleOut(ProductoOut):
    """Salida del detalle de un producto: el producto con su galería."""


class ProductoListItemOut(BaseSchema):
    """Salida de un producto en la lista del catálogo."""

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


class CategoriaListaOut(BaseSchema):
    """Salida de una categoría del catálogo."""

    id: UUID = Field(..., description="Identificador de la categoría.")
    nombre: str = Field(..., description="Nombre de la categoría.")
    slug: str = Field(..., description="Identificador de la categoría.")
    orden: int = Field(0, description="Orden de la categoría.")


class ImagenProductoIn(BaseSchema):
    """Una imagen declarada en el payload de alta.

    `token` es el token del protocolo multipart (`file_<uuid>`). El token
    aparece EXACTAMENTE UNA VEZ en el payload: por eso la imagen principal
    y el texto alternativo viajan aquí y no en campos aparte (duplicar el
    token sería un token duplicado).
    """

    token: str = Field(..., min_length=1, description="Token del archivo.")
    es_principal: bool = Field(False, description="Si es la imagen principal.")
    texto_alternativo: str = Field("", max_length=200, description="Texto alternativo.")


class CrearProductoIn(BaseSchema):
    """Alta de un producto (RT-MD-01).

    `imagenes` es la GALERÍA ORDENADA: el orden del array ES el orden
    canónico (`orden`) de las imágenes (FR-06 §2.4).
    """

    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del producto.")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        pattern=r"^[-a-zA-Z0-9_]+$",
        description="Identificador del producto en la edición.",
    )
    descripcion: str = Field("", max_length=5000, description="Descripción del producto.")
    categoria_id: UUID | None = Field(None, description="Categoría del producto.")
    precio: Decimal = Field(..., ge=0, description="Precio normal.")
    precio_oferta: Decimal | None = Field(None, ge=0, description="Precio de oferta.")
    oferta_inicia: datetime | None = Field(None, description="Inicio de la oferta.")
    oferta_termina: datetime | None = Field(None, description="Fin de la oferta.")
    estado: str = Field(
        default="ACTIVO",
        pattern=r"^(ACTIVO|INACTIVO)$",
        description="Estado comercial del producto.",
    )
    imagenes: list[ImagenProductoIn] = Field(
        default_factory=list,
        description="Galería ordenada del producto.",
    )


__all__ = [
    "CategoriaListaOut",
    "CrearProductoIn",
    "ImagenProductoIn",
    "ProductoDetalleOut",
    "ProductoEspecificaOut",
    "ProductoGeneralOut",
    "ProductoIdentidadOut",
    "ProductoImagenOut",
    "ProductoListItemOut",
    "ProductoOut",
]
