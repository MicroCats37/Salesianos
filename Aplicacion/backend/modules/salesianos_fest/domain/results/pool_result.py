"""Results del POOL de una inscripción y de la COMPRA de cupos extra.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros que el PRESENTER proyecta a schemas HTTP.

La aritmética del pool la calcula el SERVIDOR: `cupos_disponibles` es la
diferencia entre `cupos_pagados` y `cupos_asignados` (`RN-I03`). El cliente
nunca resta (`SH-05` §1.3).
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ParticipacionResult(BaseModel):
    """Una participación del pool."""

    id: str = Field(..., description="Identificador de la participación.")
    persona_id: str = Field(..., description="Persona que participa.")
    persona_nombres: str = Field(..., description="Nombres de la persona.")
    persona_apellidos: str = Field(..., description="Apellidos de la persona.")
    equipo_id: str = Field(..., description="Equipo de la participación.")
    equipo_nombre: str = Field(..., description="Nombre del equipo.")
    disciplina_id: str = Field(..., description="Disciplina del equipo.")
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


class ImpedimentoResult(BaseModel):
    """Un impedimento concreto del pool.

    Es la CAUSA que el servidor publica para que el operador entienda por
    qué una operación no puede ejecutarse (`FL-05` paso 5: "el administrador
    ve causas concretas de equipo incompleto/no elegible").
    """

    codigo: str = Field(..., description="Código de máquina del impedimento.")
    mensaje: str = Field(..., description="Mensaje público del impedimento.")
    equipo_id: str | None = Field(
        default=None,
        description="Equipo implicado, si el impedimento es de un equipo.",
    )


class PoolResult(BaseModel):
    """El estado del pool de una inscripción.

    `cupos_disponibles` lo calcula el servidor (`RN-I03`): nunca es
    negativo.
    """

    inscripcion_id: str = Field(..., description="Inscripción consultada.")
    responsable_id: str = Field(
        ...,
        description=(
            "Persona responsable de la inscripción. La comprobación de "
            "titularidad la usa el orquestador (`FR-03` §2.1)."
        ),
    )
    cupos_pagados: int = Field(..., ge=0, description="Cupos pagados y activados.")
    cupos_asignados: int = Field(..., ge=0, description="Cupos ocupados por participantes.")
    cupos_disponibles: int = Field(..., ge=0, description="Cupos pagados sin asignar.")
    participaciones: list[ParticipacionResult] = Field(
        default_factory=list,
        description="Participaciones del pool, incluidas las retiradas.",
    )
    impedimentos: list[ImpedimentoResult] = Field(
        default_factory=list,
        description="Causas concretas que impiden ampliar la plantilla.",
    )
    causa_operativa: str = Field(
        ...,
        description="Causa operativa de la respuesta.",
    )


class CompraCuposResult(BaseModel):
    """El resultado de comprar cupos extra para una inscripción.

    La compra es un hecho de `commerce`: su vida es de `commerce` y `pagos`.
    Este módulo sólo proyecta lo que necesita el comprador.
    """

    inscripcion_id: str = Field(..., description="Inscripción ampliada.")
    compra_id: str = Field(..., description="Identificador de la compra.")
    orden_pago_id: str = Field(..., description="Identificador de la orden de pago.")
    estado: str = Field(..., description="Estado comercial de la compra.")
    total: Decimal = Field(..., ge=0, description="Total congelado de la compra.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    cupos_solicitados: int = Field(..., gt=0, description="Cupos extra comprados.")
    cupos_pagados: int = Field(
        ...,
        ge=0,
        description=(
            "Capacidad pagada de la inscripción. NO cambia hasta que el pago "
            "se active (`RN-I02`)."
        ),
    )
    cupos_asignados: int = Field(..., ge=0, description="Cupos ocupados por participantes.")
    cupos_disponibles: int = Field(..., ge=0, description="Cupos pagados sin asignar.")
    reutilizada: bool = Field(
        default=False,
        description="Si la compra pendiente ya existía y se reutilizó.",
    )
    causa_operativa: str = Field(
        ...,
        description="Causa operativa de la respuesta.",
    )


__all__ = [
    "CompraCuposResult",
    "ImpedimentoResult",
    "ParticipacionResult",
    "PoolResult",
]
