"""DTOs internos de la inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros, NO schemas HTTP.
"""

from uuid import UUID

from pydantic import BaseModel, Field

from modules.salesianos_fest.domain.constants import MIN_CANTIDAD_POR_INSCRIPCION


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
    Aquí es opcional porque lo rellena quien conoce el actor.

    `promocion_id` es OBLIGATORIA: es la cohorte que compra y la que
    determina la categoría del equipo (`D-CAT-01`).

    `fusion_promocion_id` es OPCIONAL y DESCRIPTIVA (`D-CAT-02`): nombra la
    segunda cohorte de una promoción fusionada. No altera cupos, pago,
    categoría, elegibilidad ni cuadro competitivo.

    `cantidad` es el NÚMERO DE PARTICIPANTES que se inscriben. El precio NO
    se declara: lo resuelve el servidor contra el catálogo vigente
    (`RN-C02`) y el total lo deriva como `cantidad × precio_unitario`.
    """

    responsable_id: UUID | None = Field(
        default=None,
        description="Persona responsable. Lo resuelve el orquestador.",
    )
    edicion_id: UUID = Field(..., description="Edición del alcance.")
    paquete_id: UUID = Field(..., description="Paquete de inscripción.")
    promocion_id: UUID = Field(..., description="Promoción (cohorte) que compra.")
    fusion_promocion_id: UUID | None = Field(
        default=None,
        description=(
            "Promoción fusionada. Es metadato descriptivo: no altera cupos, "
            "pago, categoría, elegibilidad ni cuadro competitivo."
        ),
    )
    cantidad: int = Field(
        ...,
        ge=MIN_CANTIDAD_POR_INSCRIPCION,
        description="Número de participantes que se inscriben.",
    )
    cotizacion_version: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Token de concurrencia de la cotización. Viaja sólo si el "
            "comprador cotizó antes: el servidor comprueba que el catálogo "
            "sigue en esa versión y, si no, rechaza el alta."
        ),
    )
    equipos: list[EquipoCreateData] = Field(
        default_factory=list,
        description="Equipos declarados en el alta.",
    )


__all__ = ["EquipoCreateData", "InscripcionInicialData"]
