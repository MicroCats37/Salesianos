"""DTOs internos de la inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros, NO schemas HTTP.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class EquipoCreateData(BaseModel):
    """Un equipo declarado por el responsable en el alta."""

    disciplina_id: UUID = Field(..., description="Disciplina del equipo.")
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=160,
        description="Nombre del equipo.",
    )


class InscripcionInicialData(BaseModel):
    """La intención de alta de una inscripción inicial.

    `responsable_id` lo resuelve el ORQUESTADOR a partir de la cuenta
    autenticada: el cliente NO declara quién es el responsable (`RN-U04`).
    Aquí es opcional porque lo rellena quien conoce al actor.
    """

    responsable_id: UUID | None = Field(
        default=None,
        description="Persona responsable. Lo resuelve el orquestador.",
    )
    edicion_id: UUID = Field(..., description="Edición del alcance.")
    paquete_id: UUID = Field(..., description="Paquete de inscripción.")
    equipos: list[EquipoCreateData] = Field(
        default_factory=list,
        description="Equipos declarados en el alta.",
    )


__all__ = ["EquipoCreateData", "InscripcionInicialData"]
