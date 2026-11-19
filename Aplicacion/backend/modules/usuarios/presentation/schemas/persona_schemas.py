"""
Esquemas HTTP del módulo `usuarios`.

Todos heredan de `core.types.BaseSchema`
(`contract/PLAN_REFACTORIZACION.md` §1.C): los strings vacíos se
normalizan a `None` antes de validar, así que un texto opcional se declara
como `str | None = None`.

La composición sigue los tres bloques de
`contract/SCHEMA_DRY_INTENTION.md`:

- `PersonaDatosOut` — bloque GENERAL (datos de la identidad civil).
- `PersonaIdentidadOut` — bloque IDENTIDAD (ids, marcas de tiempo,
  procedencia de los datos).
- Los wrappers finales — bloque GENERAL + IDENTIDAD + el bloque ESPECÍFICO
  del caso de uso.
"""

from datetime import datetime
from uuid import UUID

from core.types import BaseSchema
from ninja import Field


class PersonaDatosOut(BaseSchema):
    """Bloque GENERAL: datos de la identidad civil de una persona."""

    tipo_documento: str = Field(
        ...,
        description="Tipo de documento: DNI, CE o PAS.",
    )
    numero_documento: str = Field(
        ...,
        description="Número de documento normalizado.",
    )
    nombres: str = Field(..., description="Nombres de la persona.")
    apellidos: str | None = Field(
        None,
        description="Apellidos de la persona. Puede ir vacío si la fuente "
        "externa no permite separarlos de forma fiable.",
    )


class PersonaIdentidadOut(BaseSchema):
    """Bloque IDENTIDAD: identificadores, marcas de tiempo y procedencia."""

    id: UUID = Field(..., description="Identificador interno de la persona.")
    origen_datos: str = Field(
        ...,
        description="Procedencia de los datos: LOCAL o EXTERNO.",
    )
    datos_obtenidos_en: datetime | None = Field(
        None,
        description="Instante en que la fuente externa entregó los datos.",
    )
    creado_en: datetime = Field(..., description="Momento de creación.")
    actualizado_en: datetime = Field(..., description="Momento de la última actualización.")


class PersonaOut(PersonaDatosOut, PersonaIdentidadOut):
    """Wrapper de una `Persona` persistida (bloque GENERAL + IDENTIDAD)."""

    genero: str | None = Field(None, description="Género de la persona.")


class PersonaResueltaOut(PersonaDatosOut):
    """Wrapper del resultado del resolver (`RT-ID-02`).

    `persona_id` es `None` cuando el origen es `EXTERNO`: la identidad
    existe en la fuente pero TODAVÍA NO está persistida
    (`FR-03` §3.1 — el origen externo no habilita escritura por sí solo).
    """

    origen: str = Field(
        ...,
        description="Origen del resultado: LOCAL o EXTERNO.",
    )
    persona_id: UUID | None = Field(
        None,
        description="Identificador de la persona persistida. Nulo si el "
        "origen es EXTERNO.",
    )
    persistida: bool = Field(
        ...,
        description="Si la identidad ya está registrada en la base local.",
    )


class DocumentoConsultaOut(BaseSchema):
    """Wrapper de la consulta externa de documentos (`RT-ID-01`)."""

    tipo_documento: str = Field(
        ...,
        description="Tipo de documento reconocido por la fuente.",
    )
    numero_documento: str = Field(
        ...,
        description="Número de documento normalizado.",
    )
    nombre_completo: str = Field(
        ...,
        description="Nombre completo tal como lo entrega la fuente externa.",
    )


class PersonaResolverIn(BaseSchema):
    """Entrada del resolver (`RT-ID-02`)."""

    tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento: DNI, CE o PAS.",
    )
    numero_documento: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Número de documento de la persona.",
    )


class PersonaConfirmarIn(BaseSchema):
    """Entrada de la confirmación de una identidad (`RT-ID-03`).

    La confirmación es la operación real que PERSISTE la persona. No crea
    una cuenta: el nacimiento de cuenta es explícito y aparte
    (`FR-03` §1.2).
    """

    tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento: DNI, CE o PAS.",
    )
    numero_documento: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Número de documento de la persona.",
    )
    nombres: str = Field(..., max_length=255, description="Nombres de la persona.")
    apellidos: str | None = Field(
        None,
        max_length=255,
        description="Apellidos de la persona.",
    )
    genero: str | None = Field(
        None,
        max_length=1,
        description="Género de la persona: M o F.",
    )


__all__ = [
    "DocumentoConsultaOut",
    "PersonaConfirmarIn",
    "PersonaDatosOut",
    "PersonaIdentidadOut",
    "PersonaOut",
    "PersonaResueltaOut",
    "PersonaResolverIn",
]
