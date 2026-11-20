"""DTOs internos del módulo `patrocinadores`.

Freeze: `FREEZE-MD-1.0.0` · `FREEZE-PS-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.6 (DTOs internos)

Estos DTOs son Pydantic `BaseModel` (NO schemas HTTP): describen lo que la
capa de servicios necesita, no lo que el cliente envía.

`ArchivoPatrocinadorUploadData` es LA REPRESENTACIÓN ÚNICA de un archivo:
viaja desde el borde HTTP (controller) hasta el flujo sin cambiar de forma y
sin argumentos paralelos duplicados. El controller la construye UNA vez (tras
validar el archivo con `core.media`) y el flujo la consume tal cual. El logo y
las imágenes de la galería comparten ESA única representación: son el mismo
tipo de recurso (una imagen validada, lista para persistirse).
"""

from uuid import UUID

from django.core.files.uploadedfile import UploadedFile
from pydantic import BaseModel, Field


class ArchivoPatrocinadorUploadData(BaseModel):
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


class LogoPatrocinadorData(BaseModel):
    """El logo declarado en el payload, resuelto a su archivo."""

    model_config = {"arbitrary_types_allowed": True}

    token: str = Field(..., description="Token del protocolo multipart.")
    upload: ArchivoPatrocinadorUploadData | None = Field(
        None,
        description="Archivo resuelto; `None` cuando el patrocinador no lleva logo.",
    )


class ImagenPatrocinadorData(BaseModel):
    """Una imagen declarada en la galería, resuelta a su archivo."""

    model_config = {"arbitrary_types_allowed": True}

    token: str = Field(..., description="Token del protocolo multipart.")
    texto_alternativo: str = Field("", description="Texto alternativo (alt).")
    upload: ArchivoPatrocinadorUploadData | None = Field(
        None,
        description="Archivo resuelto; `None` sólo en el modo JSON sin archivos.",
    )


class PatrocinadorCreateData(BaseModel):
    """Alta de un patrocinador con su logo y su galería."""

    model_config = {"arbitrary_types_allowed": True}

    edicion_id: UUID = Field(..., description="Edición de alcance.")
    nombre: str = Field(..., description="Nombre del patrocinador.")
    slug: str = Field(..., description="Identificador del patrocinador en la edición.")
    descripcion: str = Field("", description="Descripción de la ficha.")
    sitio_web: str = Field("", description="Sitio web del patrocinador.")
    visible: bool = Field(True, description="Visibilidad pública (ADM-21).")
    logo: LogoPatrocinadorData | None = Field(
        None,
        description="Logo de identidad; opcional.",
    )
    imagenes: list[ImagenPatrocinadorData] = Field(
        default_factory=list,
        description="Galería ordenada del patrocinador.",
    )


class PatrocinadorUpdateData(BaseModel):
    """Actualización parcial de la ficha y de la visibilidad.

    NO toca el logo ni la galería: los archivos tienen su propio camino de
    escritura (reemplazo) y su propia política de limpieza (FR-06 §2.5).
    """

    nombre: str | None = Field(None, description="Nombre del patrocinador.")
    descripcion: str | None = Field(None, description="Descripción de la ficha.")
    sitio_web: str | None = Field(None, description="Sitio web del patrocinador.")
    visible: bool | None = Field(None, description="Visibilidad pública (ADM-21).")


class PatrocinadorOrdenImagenData(BaseModel):
    """El orden explícito de UNA imagen de la galería."""

    imagen_id: UUID = Field(..., description="Identificador de la imagen.")
    orden: int = Field(..., ge=0, description="Posición canónica en la galería.")


__all__ = [
    "ArchivoPatrocinadorUploadData",
    "ImagenPatrocinadorData",
    "LogoPatrocinadorData",
    "PatrocinadorCreateData",
    "PatrocinadorOrdenImagenData",
    "PatrocinadorUpdateData",
]
