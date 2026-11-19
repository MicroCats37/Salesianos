"""DTOs internos del módulo `eventos`.

Freeze: `FREEZE-ED-1.0.0`
Contract: `contract/django-app-architecture-contract.md` §4.6 ·
          `contract/PLAN_REFACTORIZACION.md` §3.C

`domain/schemas/` contiene los DTOs que viajan ENTRE capas (servicio ←
orquestador). NO son el contrato HTTP: el contrato HTTP vive en
`modules/eventos/presentation/schemas/` y lo compone el presenter.

Todos heredan de `core.types.BaseSchema`, que es el `BaseSchema` del proyecto
(`contract/PLAN_REFACTORIZACION.md` §C: "Todo esquema, ya sea de entrada
(`In`) o de respuesta (`Out`), debe heredar obligatoriamente de `BaseSchema`").
"""

from datetime import date
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


class EdicionCreateData(BaseSchema):
    """Datos de alta de una edición."""

    evento_id: UUID = Field(..., description="Identificador del evento propietario.")
    nombre: str = Field(..., min_length=1, max_length=200, description="Nombre de la edición.")
    slug: str = Field(..., min_length=1, max_length=100, description="Slug único dentro del evento.")
    anio: int = Field(..., ge=1, le=9999, description="Año de la edición.")
    modulos_habilitados: list[str] = Field(
        default_factory=list,
        description="Claves de módulos opcionales habilitados (por defecto, ninguno).",
    )
    fecha_inicio: date | None = Field(default=None, description="Fecha de inicio.")
    fecha_fin: date | None = Field(default=None, description="Fecha de fin.")


class EdicionUpdateData(BaseSchema):
    """Datos de actualización parcial de una edición.

    `estado` NO se actualiza aquí: publicar y cerrar son transiciones con
    regla propia (invariante de una única edición publicada por evento).
    """

    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    anio: int | None = Field(default=None, ge=1, le=9999)
    modulos_habilitados: list[str] | None = Field(default=None)
    fecha_inicio: date | None = Field(default=None)
    fecha_fin: date | None = Field(default=None)


class EdicionPublicarData(BaseSchema):
    """Datos de la transición a `PUBLICADA`."""

    edicion_id: UUID = Field(..., description="Identificador de la edición a publicar.")


__all__ = [
    "EdicionCreateData",
    "EdicionPublicarData",
    "EdicionUpdateData",
]
