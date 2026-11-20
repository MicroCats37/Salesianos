"""Esquemas HTTP del módulo `patrocinadores`.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0`
Contract: `contract/SCHEMA_DRY_INTENTION.md` (composición) ·
          `contract/api-wrapper-presenter-contract.md` §2, §7

Composición de los TRES bloques (SCHEMA_DRY_INTENTION):

| Bloque | Contenido | Clase |
|---|---|---|
| Identidad | ids + marcas de tiempo | `PatrocinadorIdentidadOut` |
| General | lo compartido por casi todas las salidas | `PatrocinadorGeneralOut` |
| Específico | lo que varía por caso de uso | `PatrocinadorEspecificaOut` |

`PatrocinadorOut` se COMONE de esos bloques; no es un schema monolítico
duplicado.

El ledger (FR-07 §3.3) congela para este módulo:

| Ruta | Presenter | Wrapper de salida | Schema de entrada |
|---|---|---|---|
| `RT-MD-02` | `PatrocinadorPresenter` | `PatrocinadorOut` | `CrearPatrocinadorIn` |

Todos heredan de `core.types.BaseSchema` (`contract/PLAN_REFACTORIZACION.md`
§C). El espejo Zod 1:1 del frontend es responsabilidad de A7 (FR-07 §1.1);
este lado NO declara `z.any()` ni campos genéricos.

SIN FINANZAS: ningún schema de este módulo declara aportaciones, comisiones,
montos, facturas ni datos de pago. ADM-21 lo prohíbe mientras no sea
requisito, y el plan lo confirma (`funcional/01` §`patrocinadores`).
"""

from datetime import datetime
from uuid import UUID

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from pydantic import Field, field_validator

from core.types import BaseSchema


class PatrocinadorIdentidadOut(BaseSchema):
    """Bloque de identidad: identificadores y marcas de tiempo."""

    id: UUID = Field(..., description="Identificador del patrocinador.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class PatrocinadorGeneralOut(BaseSchema):
    """Bloque general: el alcance de edición."""

    edicion_id: UUID = Field(..., description="Edición de alcance del patrocinador.")
    edicion_nombre: str = Field("", description="Nombre de la edición.")


class PatrocinadorEspecificaOut(BaseSchema):
    """Bloque específico: la ficha del patrocinador y su visibilidad."""

    nombre: str = Field(..., description="Nombre del patrocinador.")
    slug: str = Field(..., description="Identificador del patrocinador en la edición.")
    descripcion: str = Field("", description="Descripción de la ficha.")
    sitio_web: str = Field("", description="Sitio web del patrocinador.")
    visible: bool = Field(True, description="Visibilidad pública del patrocinador.")
    orden: int = Field(0, description="Posición persistida del banner público.")


class PatrocinadorLogoOut(BaseSchema):
    """El logo de identidad del patrocinador."""

    url: str | None = Field(None, description="URL pública del archivo.")
    disponible: bool = Field(True, description="Si el archivo existe en el volumen.")


class PatrocinadorImagenOut(BaseSchema):
    """Una imagen de la galería, en su orden canónico."""

    id: UUID = Field(..., description="Identificador de la imagen.")
    orden: int = Field(..., description="Orden canónico dentro de la galería.")
    url: str | None = Field(None, description="URL pública del archivo.")
    texto_alternativo: str = Field("", description="Texto alternativo (alt).")
    disponible: bool = Field(True, description="Si el archivo existe en el volumen.")
    created_at: datetime = Field(..., description="Momento de creación.")


class PatrocinadorOut(PatrocinadorIdentidadOut, PatrocinadorGeneralOut, PatrocinadorEspecificaOut):
    """Salida de un patrocinador. Composición de los tres bloques."""

    logo: PatrocinadorLogoOut | None = Field(
        None,
        description="Logo de identidad; `null` si el patrocinador no tiene logo.",
    )
    imagenes: list[PatrocinadorImagenOut] = Field(
        default_factory=list,
        description="Galería ordenada del patrocinador.",
    )


class ImagenPatrocinadorIn(BaseSchema):
    """Una imagen declarada en el payload de alta.

    `token` es el token del protocolo multipart (`file_<uuid>`). El token
    aparece EXACTAMENTE UNA VEZ en el payload: por eso el texto alternativo
    viaja aquí y no en un campo aparte (duplicar el token sería un token
    duplicado).
    """

    token: str = Field(..., min_length=1, description="Token del archivo.")
    texto_alternativo: str = Field("", max_length=200, description="Texto alternativo.")


class CrearPatrocinadorIn(BaseSchema):
    """Alta de un patrocinador (RT-MD-02).

    `imagenes` es la GALERÍA ORDENADA: el orden del array ES el orden canónico
    (`orden`) de las imágenes (FR-06 §2.4).

    `logo` es el token del logo de identidad. Es OPCIONAL: un patrocinador
    puede existir sin logo, y el logo se reemplaza por su propio camino.

    El `slug` usa kebab-case (`^[a-z0-9]+(?:-[a-z0-9]+)*$`). La razón NO es
    estética: el protocolo multipart escanea el payload crudo en busca de
    tokens (`file_<uuid>`) y un identificador con guion bajo podría colisionar
    con ese patrón. El kebab-case hace la colisión IMPOSIBLE (documentado como
    `D-DOM08-04` en la evidencia de DOM-08).
    """

    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre del patrocinador.")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=200,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Identificador del patrocinador en la edición.",
    )
    descripcion: str = Field("", max_length=5000, description="Descripción de la ficha.")
    sitio_web: str = Field("", max_length=300, description="Sitio web del patrocinador.")
    visible: bool = Field(True, description="Visibilidad pública del patrocinador.")
    logo: str | None = Field(
        None,
        description="Token del logo de identidad (opcional).",
    )
    imagenes: list[ImagenPatrocinadorIn] = Field(
        default_factory=list,
        description="Galería ordenada del patrocinador.",
    )

    @field_validator("descripcion", "sitio_web", mode="before")
    @classmethod
    def _texto_opcional_a_cadena(cls, valor):
        """Una cadena vacía es un VALOR, no un `null`.

        `core.types.BaseSchema.sanitize_strings` convierte la cadena vacía en
        `None` antes de validar. Para un campo cuyo valor por defecto es la
        cadena vacía, eso convertiría un `""` legítimo en un error de tipo
        ("Input should be a valid string"). Este validador de borde devuelve
        la cadena vacía a su forma declarada, de modo que el contrato del
        wire (un `str`, nunca un `null`) y el valor por defecto coincidan.

        El arreglo es LOCAL a este módulo: `core/types.py` es de A0 y esta
        entrada lo pide (A0-10) para que los módulos hermanos converjan.
        """
        if valor is None:
            return ""
        return valor


class ActualizarPatrocinadorIn(BaseSchema):
    """Edición parcial de la ficha, sin alterar piezas de media."""

    nombre: str | None = Field(None, min_length=1, max_length=200)
    descripcion: str | None = Field(None, max_length=5000)
    sitio_web: str | None = Field(None, max_length=300)
    visible: bool | None = None

    _texto_opcional_a_cadena = field_validator("descripcion", "sitio_web", mode="before")(
        CrearPatrocinadorIn._texto_opcional_a_cadena
    )
    @field_validator("sitio_web")
    @classmethod
    def _sitio_web_valido(cls, valor: str | None) -> str | None:
        if not valor:
            return valor
        try:
            URLValidator()(valor)
        except DjangoValidationError:
            raise ValueError("El sitio web indicado no es una URL válida.") from None
        return valor


class ReordenarImagenesPatrocinadorIn(BaseSchema):
    """La secuencia ordenada de identificadores de piezas de la galería."""

    imagen_ids: list[UUID] = Field(default_factory=list)


class ReordenarPatrocinadoresIn(BaseSchema):
    patrocinador_ids: list[UUID] = Field(default_factory=list)


class ReemplazarArchivoPatrocinadorIn(BaseSchema):
    """Token multipart de una pieza que se reemplaza."""

    archivo: str = Field(..., min_length=1)


__all__ = [
    "CrearPatrocinadorIn",
    "ActualizarPatrocinadorIn",
    "ImagenPatrocinadorIn",
    "PatrocinadorEspecificaOut",
    "PatrocinadorGeneralOut",
    "PatrocinadorIdentidadOut",
    "PatrocinadorImagenOut",
    "PatrocinadorLogoOut",
    "PatrocinadorOut",
    "ReemplazarArchivoPatrocinadorIn",
    "ReordenarImagenesPatrocinadorIn",
    "ReordenarPatrocinadoresIn",
]
