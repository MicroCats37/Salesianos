"""Contrato HTTP del módulo `eventos`.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/SCHEMA_DRY_INTENTION.md` (composición) ·
          `contract/api-wrapper-presenter-contract.md` §2, §7 ·
          `contract/PLAN_REFACTORIZACION.md` §C

Composición de los TRES bloques (SCHEMA_DRY_INTENTION):

| Bloque | Contenido | Clase |
|---|---|---|
| Identidad | ids + marcas de tiempo | `EdicionIdentidadOut` |
| General | lo compartido por casi todas las salidas | `EdicionGeneralOut` |
| Específico | lo que varía por caso de uso | `EdicionEspecificaOut` |

`EdicionOut` y `EdicionActualOut` se COMONEN de esos bloques; no son schemas
monolíticos duplicados.

Todos heredan de `core.types.BaseSchema` (`contract/PLAN_REFACTORIZACION.md`
§C). El espejo Zod 1:1 del frontend es responsabilidad de A7 (FR-07 §1.1);
este lado NO declara `z.any()` ni campos genéricos.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


class EdicionIdentidadOut(BaseSchema):
    """Bloque de identidad: identificadores y marcas de tiempo."""

    id: UUID = Field(..., description="Identificador de la edición.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class EdicionGeneralOut(BaseSchema):
    """Bloque general: la familia de evento a la que pertenece la edición."""

    evento_id: UUID = Field(..., description="Identificador del evento propietario.")
    evento_nombre: str = Field(..., description="Nombre del evento propietario.")
    evento_slug: str = Field(..., description="Identificador del evento propietario.")


class EdicionEspecificaOut(BaseSchema):
    """Bloque específico: los datos propios de la edición."""

    nombre: str = Field(..., description="Nombre de la edición.")
    slug: str = Field(..., description="Identificador de la edición dentro del evento.")
    anio: int = Field(..., description="Año de la edición.")
    estado: str = Field(..., description="Estado de la edición (BORRADOR, PUBLICADA o CERRADA).")
    modulos_habilitados: list[str] = Field(
        default_factory=list,
        description="Claves de módulos opcionales habilitados en esta edición.",
    )
    fecha_inicio: date | None = Field(default=None, description="Fecha de inicio.")
    fecha_fin: date | None = Field(default=None, description="Fecha de fin.")


class ModuloHabilitadoOut(BaseSchema):
    """Estado de habilitación de un módulo lógico de la edición (RN-E02)."""

    clave: str = Field(..., description="Clave del módulo lógico.")
    nombre: str = Field(..., description="Nombre legible del módulo.")
    habilitado: bool = Field(..., description="Si el módulo está habilitado en la edición.")


class EdicionOut(EdicionIdentidadOut, EdicionGeneralOut, EdicionEspecificaOut):
    """Salida de una edición. Composición de los tres bloques."""


class EdicionActualOut(EdicionOut):
    """Salida de la edición vigente: la edición + el estado de sus módulos.

    `FL-01` paso 1: el sistema indica la edición publicada y los módulos
    habilitados. El listado de módulos incluye SIEMPRE las cinco claves
    lógicas, habilitadas o no, porque el valor por defecto es deshabilitado.
    """

    modulos: list[ModuloHabilitadoOut] = Field(
        default_factory=list,
        description="Estado de cada módulo lógico de la edición.",
    )


__all__ = [
    "EdicionActualOut",
    "EdicionEspecificaOut",
    "EdicionGeneralOut",
    "EdicionIdentidadOut",
    "EdicionOut",
    "ModuloHabilitadoOut",
]
