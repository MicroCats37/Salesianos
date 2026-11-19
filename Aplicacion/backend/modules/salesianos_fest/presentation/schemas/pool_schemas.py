"""Contrato HTTP del POOL de una inscripción.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §5 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición de bloques) ·
          `contract/PLAN_REFACTORIZACION.md` §1.C (todo schema hereda
          `BaseSchema`).

Ledger: `RT-IN-03` (GET pool), `RT-IN-05` (agregar participante),
`RT-IN-06` (retirar participante).

La aritmética del pool la calcula el SERVIDOR: el wrapper lleva los TRES
números (`pagados`, `asignados`, `disponibles`) y la lista de impedimentos.
El cliente NUNCA resta (`SH-05` §1.3).
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field, model_validator

from core.types import BaseSchema
from modules.salesianos_fest.domain.constants import RolParticipante


class ParticipacionIdentidadOut(BaseSchema):
    """Bloque de identidad de una participación."""

    id: UUID = Field(..., description="Identificador de la participación.")
    persona_id: UUID = Field(..., description="Persona que participa.")


class ParticipacionEspecificaOut(BaseSchema):
    """Bloque específico de una participación."""

    equipo_id: UUID = Field(..., description="Equipo de la participación.")
    equipo_nombre: str = Field(..., description="Nombre del equipo.")
    disciplina_id: UUID = Field(..., description="Disciplina del equipo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    rol: str = Field(..., description="Rol de la persona en el equipo.")
    estado: str = Field(..., description="Estado de la participación.")
    ocupa_cupo: bool = Field(
        ...,
        description="Si la participación ocupa un cupo de la inscripción.",
    )
    retirada_en: datetime | None = Field(
        default=None,
        description="Momento de la retirada, si la hubo.",
    )


class ParticipacionOut(ParticipacionIdentidadOut, ParticipacionEspecificaOut):
    """Salida de una participación del pool."""


class ImpedimentoOut(BaseSchema):
    """Salida de un impedimento del pool."""

    codigo: str = Field(..., description="Código de máquina del impedimento.")
    mensaje: str = Field(..., description="Mensaje público del impedimento.")
    equipo_id: UUID | None = Field(
        default=None,
        description="Equipo implicado, si el impedimento es de un equipo.",
    )


class PoolIdentidadOut(BaseSchema):
    """Bloque de identidad del pool."""

    inscripcion_id: UUID = Field(..., description="Inscripción consultada.")


class PoolGeneralOut(BaseSchema):
    """Bloque general del pool: la aritmética de cupos.

    Los TRES números los calcula el servidor (`RN-I03`): el cliente nunca
    resta.
    """

    cupos_pagados: int = Field(..., ge=0, description="Cupos pagados y activados.")
    cupos_asignados: int = Field(..., ge=0, description="Cupos ocupados por participantes.")
    cupos_disponibles: int = Field(..., ge=0, description="Cupos pagados sin asignar.")


class PoolEspecificoOut(BaseSchema):
    """Bloque específico del pool: participantes e impedimentos."""

    participaciones: list[ParticipacionOut] = Field(
        default_factory=list,
        description="Participaciones del pool, incluidas las retiradas.",
    )
    impedimentos: list[ImpedimentoOut] = Field(
        default_factory=list,
        description="Causas concretas que impiden ampliar la plantilla.",
    )
    causa_operativa: str = Field(
        ...,
        description="Causa operativa de la respuesta. La declara el dominio.",
    )


class PoolOut(PoolIdentidadOut, PoolGeneralOut, PoolEspecificoOut):
    """Salida del pool de una inscripción."""


# ── Entradas ────────────────────────────────────────────────────────────────


class ParticipanteAsignarIn(BaseSchema):
    """El payload de agregar (o mover) un participante al pool.

    La persona se identifica por `persona_id` **o** por documento, nunca por
    las dos cosas a la vez. La cantidad de cupos NO aparece: el cupo es
    UNITARIO y lo asigna el servidor (`RN-I03`).

    `reemplaza_participacion_id` es el MOVIMIENTO de `FL-05` paso 4: la
    persona nueva toma el cupo de la retirada, en la misma transacción.
    """

    persona_id: UUID | None = Field(
        default=None,
        description="Persona ya existente del padrón.",
    )
    tipo_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Tipo de documento para resolver la persona.",
    )
    numero_documento: str | None = Field(
        default=None,
        max_length=20,
        description="Número de documento para resolver la persona.",
    )
    equipo_id: UUID = Field(..., description="Equipo de destino dentro de la inscripción.")
    rol: str = Field(
        default=RolParticipante.JUGADOR,
        max_length=16,
        description="Rol de la persona en el equipo.",
    )
    reemplaza_participacion_id: UUID | None = Field(
        default=None,
        description="Participación que se retira para liberar su cupo.",
    )

    @model_validator(mode="after")
    def _identificacion_exclusiva(self) -> "ParticipanteAsignarIn":
        """La persona se identifica por identificador O por documento."""
        por_identificador = self.persona_id is not None
        por_documento = bool(self.tipo_documento and self.numero_documento)
        if por_identificador == por_documento:
            raise ValueError(
                "La persona se identifica por identificador o por documento, "
                "no por ambos ni por ninguno."
            )
        return self

    @model_validator(mode="after")
    def _rol_conocido(self) -> "ParticipanteAsignarIn":
        """El rol pertenece al vocabulario cerrado."""
        if self.rol not in RolParticipante.values:
            raise ValueError("El rol del participante no es válido.")
        return self


__all__ = [
    "ImpedimentoOut",
    "ParticipacionEspecificaOut",
    "ParticipacionIdentidadOut",
    "ParticipacionOut",
    "ParticipanteAsignarIn",
    "PoolEspecificoOut",
    "PoolGeneralOut",
    "PoolIdentidadOut",
    "PoolOut",
]
