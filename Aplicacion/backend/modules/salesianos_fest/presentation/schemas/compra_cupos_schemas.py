"""Contrato HTTP de la COMPRA de cupos extra.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §5 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición de bloques)

Ledger: `RT-CM-01` (POST `/inscripciones/{inscripcion_id}/compras/cupos`) ·
preserver `CompraCuposPresenter` · wrapper `CompraCreadaOut` · entrada
`ComprarCuposIn` · códigos `COMPRA_NO_AUTORIZADA` (403),
`PAQUETE_NO_VIGENTE` (409), `CUPO_INVALIDO` (422).

El payload NO admite importe: el precio lo resuelve el servidor contra el
catálogo vigente (`RN-C02`). La cantidad NO lleva rango en el schema: el
límite de dominio lo declara y lo hace cumplir el módulo, que responde con
el código estable `CUPO_INVALIDO` (422) del ledger.
"""

from uuid import UUID

from pydantic import Field

from core.types import BaseSchema
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    CompraOut,
)


class ComprarCuposIn(BaseSchema):
    """El payload de la compra de cupos extra."""

    cantidad: int = Field(
        ...,
        description=(
            "Cantidad de cupos extra a comprar. El límite lo declara y lo "
            "hace cumplir el servidor (`CUPO_INVALIDO`, 422)."
        ),
    )

class CompraCreadaIdentidadOut(BaseSchema):
    """Bloque de identidad de la compra de cupos."""

    inscripcion_id: UUID = Field(..., description="Inscripción ampliada.")
    compra: CompraOut = Field(..., description="La compra pendiente.")


class CompraCreadaGeneralOut(BaseSchema):
    """Bloque general: la capacidad de la inscripción.

    Los cupos comprados NO están pagados todavía: la capacidad sólo cambia
    cuando el pago se activa (`RN-I02`).
    """

    cupos_solicitados: int = Field(..., gt=0, description="Cupos extra comprados.")
    cupos_pagados: int = Field(
        ...,
        ge=0,
        description="Capacidad pagada de la inscripción.",
    )
    cupos_asignados: int = Field(..., ge=0, description="Cupos ocupados por participantes.")
    cupos_disponibles: int = Field(..., ge=0, description="Cupos pagados sin asignar.")


class CompraCreadaOut(
    CompraCreadaIdentidadOut,
    CompraCreadaGeneralOut,
):
    """Salida de la compra de cupos extra.

    El importe, la moneda y la marca de reutilización viajan DENTRO de
    `compra`: es la proyección de la compra de `commerce` y no se duplica.
    """

    causa_operativa: str = Field(
        ...,
        description="Causa operativa de la respuesta. La declara el dominio.",
    )


__all__ = [
    "CompraCreadaGeneralOut",
    "CompraCreadaIdentidadOut",
    "CompraCreadaOut",
    "ComprarCuposIn",
]
