"""Contrato HTTP de la cotización de un paquete.

Change: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/api-wrapper-presenter-contract.md` §2, §5 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición de bloques) ·
          `contract/PLAN_REFACTORIZACION.md` §1.C (todo schema hereda
          `BaseSchema`).

La cotización es un cálculo de LECTURA: el cliente pregunta por un paquete
y una cantidad y el servidor responde con el precio UNITARIO vigente, el
total que deriva y el TOKEN DE CONCURRENCIA del precio (`RN-C02`).

El cliente NUNCA devuelve un importe: devuelve la CANTIDAD (su decisión) y,
cuando cotizó antes, el `version` de la cotización, que el alta devuelve
para que el servidor detecte que el catálogo se movió.
"""

from uuid import UUID

from pydantic import Field

from core.types import BaseSchema
from modules.salesianos_fest.domain.constants import MIN_CANTIDAD_POR_INSCRIPCION


class CotizacionIn(BaseSchema):
    """El payload de la cotización.

    No lleva precio ni total: el servidor los resuelve contra el catálogo
    vigente (`RN-C02`).
    """

    paquete_id: UUID = Field(..., description="Paquete a cotizar.")
    cantidad: int = Field(
        ...,
        ge=MIN_CANTIDAD_POR_INSCRIPCION,
        description="Número de participantes por los que se cotiza.",
    )


__all__ = ["CotizacionIn"]
