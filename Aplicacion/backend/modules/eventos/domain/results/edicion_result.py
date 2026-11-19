"""Result objects del módulo `eventos`.

Freeze: `FREEZE-ED-1.0.0`
Contract: `contract/PLAN_REFACTORIZACION.md` §3.C ·
          `contract/django-app-architecture-contract.md` §4.6

`domain/results/` son DTOs INTERNOS: los que el orquestador devuelve al
controller y que el presenter convierte en el schema HTTP. Heredan de
`BaseModel` puro de Pydantic (no de `BaseSchema`), porque no son contrato de
transporte.

`EdicionResult` NO contiene el modelo Django: son sólo datos primitivos. Eso
obliga al presenter a no poder consultar la base de datos ni depender del ORM
(`contract/api-wrapper-presenter-contract.md` §3).
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from modules.eventos.domain.constants import ModuloLogico


class EdicionResult(BaseModel):
    """Resultado de dominio que describe una edición."""

    id: UUID = Field(..., description="Identificador de la edición.")
    evento_id: UUID = Field(..., description="Identificador del evento propietario.")
    evento_nombre: str = Field(..., description="Nombre del evento propietario.")
    evento_slug: str = Field(..., description="Slug del evento propietario.")
    nombre: str = Field(..., description="Nombre de la edición.")
    slug: str = Field(..., description="Slug de la edición dentro del evento.")
    anio: int = Field(..., description="Año de la edición.")
    estado: str = Field(..., description="Estado de la edición.")
    modulos_habilitados: list[str] = Field(
        default_factory=list,
        description="Claves de módulos opcionales habilitados.",
    )
    fecha_inicio: date | None = Field(default=None, description="Fecha de inicio.")
    fecha_fin: date | None = Field(default=None, description="Fecha de fin.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")

    @classmethod
    def desde_edicion(cls, edicion) -> "EdicionResult":
        """Proyecta el modelo de dominio al resultado.

        La proyección es explícita campo por campo: el result no arrastra el
        modelo Django y por tanto el presenter no puede tocar el ORM.
        """
        return cls(
            id=edicion.id,
            evento_id=edicion.evento_id,
            evento_nombre=edicion.evento.nombre,
            evento_slug=edicion.evento.slug,
            nombre=edicion.nombre,
            slug=edicion.slug,
            anio=edicion.anio,
            estado=edicion.estado,
            modulos_habilitados=list(edicion.modulos_habilitados or []),
            fecha_inicio=edicion.fecha_inicio,
            fecha_fin=edicion.fecha_fin,
            created_at=edicion.created_at,
            updated_at=edicion.updated_at,
        )


class ModuloResult(BaseModel):
    """Estado de habilitación de un módulo lógico de la edición."""

    clave: str = Field(..., description="Clave del módulo lógico.")
    nombre: str = Field(..., description="Nombre legible del módulo.")
    habilitado: bool = Field(..., description="Si el módulo está habilitado en la edición.")


class EdicionActualResult(BaseModel):
    """Resultado de la edición resuelta + el estado de sus módulos."""

    edicion: EdicionResult = Field(..., description="Edición resuelta.")
    modulos: list[ModuloResult] = Field(
        default_factory=list,
        description="Estado de cada módulo lógico de la edición.",
    )

    @classmethod
    def desde_edicion(cls, edicion) -> "EdicionActualResult":
        """Construye el resultado a partir de la edición.

        El listado de módulos incluye SIEMPRE las cinco claves lógicas,
        habilitadas o no: el valor por defecto es deshabilitado y el cliente
        tiene que poder VER que un módulo está apagado (RN-E02).
        """
        efectivos = list(edicion.modulos_habilitados or [])
        return cls(
            edicion=EdicionResult.desde_edicion(edicion),
            modulos=[
                ModuloResult(
                    clave=modulo.value,
                    nombre=str(modulo.label),
                    habilitado=modulo.value in efectivos,
                )
                for modulo in ModuloLogico
            ],
        )


__all__ = [
    "EdicionActualResult",
    "EdicionResult",
    "ModuloResult",
]
