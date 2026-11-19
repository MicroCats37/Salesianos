"""DTOs internos del módulo `marketplace`.

Freeze: `FREEZE-MD-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.6 (DTOs internos)

Estos DTOs son Pydantic `BaseModel` (NO schemas HTTP): describen lo que la
capa de servicios necesita, no lo que el cliente envía.

`ImagenProductoUploadData` es LA REPRESENTACIÓN ÚNICA de un archivo: viaja
desde el borde HTTP (controller) hasta el flujo sin cambiar de forma y sin
argumentos paralelos duplicados. El controller la construye UNA vez (tras
validar el archivo con `core.media`) y el flujo la consume tal cual.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.core.files.uploadedfile import UploadedFile
from pydantic import BaseModel, Field

from modules.marketplace.domain.constants import EstadoProducto


class ImagenProductoUploadData(BaseModel):
    """Un archivo de imagen validado, listo para persistirse.

    `archivo` conserva el `UploadedFile` original; el resto son los datos que
    `core.media.validar_archivo_media` YA calculó (MIME detectado, extensión
    normalizada y tamaño). La validación ocurre en el borde HTTP, antes de
    tocar el disco (FR-06 §2.3).
    """

    model_config = {"arbitrary_types_allowed": True}

    token: str = Field(..., description="Token del protocolo multipart.")
    archivo: UploadedFile = Field(..., description="Archivo ya validado.")
    mime_detectado: str = Field(..., description="MIME detectado por la firma.")
    extension: str = Field(..., description="Extensión storage normalizada.")
    tamano: int = Field(..., description="Tamaño del archivo en bytes.")
    nombre_original: str = Field("", description="Nombre declarado por el cliente.")


class ImagenProductoData(BaseModel):
    """Una imagen declarada en el payload, resuelta a su archivo."""

    model_config = {"arbitrary_types_allowed": True}

    token: str = Field(..., description="Token del protocolo multipart.")
    es_principal: bool = Field(False, description="Imagen principal explícita.")
    texto_alternativo: str = Field("", description="Texto alternativo (alt).")
    upload: ImagenProductoUploadData | None = Field(
        None,
        description="Archivo resuelto; `None` sólo en el modo JSON sin archivos.",
    )


class ProductoCreateData(BaseModel):
    """Alta de un producto con su galería."""

    model_config = {"arbitrary_types_allowed": True}

    edicion_id: UUID = Field(..., description="Edición de alcance.")
    nombre: str = Field(..., description="Nombre del producto.")
    slug: str = Field(..., description="Identificador del producto en la edición.")
    descripcion: str = Field("", description="Descripción del producto.")
    categoria_id: UUID | None = Field(None, description="Categoría del producto.")
    precio: Decimal = Field(..., description="Precio normal.")
    precio_oferta: Decimal | None = Field(None, description="Precio de oferta.")
    oferta_inicia: datetime | None = Field(None, description="Inicio de la oferta.")
    oferta_termina: datetime | None = Field(None, description="Fin de la oferta.")
    estado: str = Field(EstadoProducto.ACTIVO, description="Estado comercial.")
    imagenes: list[ImagenProductoData] = Field(
        default_factory=list,
        description="Galería ordenada del producto.",
    )


class ProductoUpdateData(BaseModel):
    """Actualización parcial de un producto. NO toca la galería."""

    nombre: str | None = Field(None, description="Nombre del producto.")
    descripcion: str | None = Field(None, description="Descripción del producto.")
    categoria_id: UUID | None = Field(None, description="Categoría del producto.")
    precio: Decimal | None = Field(None, description="Precio normal.")
    precio_oferta: Decimal | None = Field(None, description="Precio de oferta.")
    oferta_inicia: datetime | None = Field(None, description="Inicio de la oferta.")
    oferta_termina: datetime | None = Field(None, description="Fin de la oferta.")
    estado: str | None = Field(None, description="Estado comercial.")


class CategoriaProductoCreateData(BaseModel):
    """Alta de una categoría de producto."""

    edicion_id: UUID = Field(..., description="Edición de alcance.")
    nombre: str = Field(..., description="Nombre de la categoría.")
    slug: str = Field(..., description="Identificador de la categoría.")
    orden: int = Field(0, description="Orden de la categoría.")


__all__ = [
    "CategoriaProductoCreateData",
    "ImagenProductoData",
    "ImagenProductoUploadData",
    "ProductoCreateData",
    "ProductoUpdateData",
]
