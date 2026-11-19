"""`CompraCuposPresenter` — result de la compra de cupos → wrapper HTTP.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)
Ledger: `FR-07` §3.3 · `RT-CM-01`

El presenter es un TRANSFORMADOR PURO. Es el dueño de la CAUSA OPERATIVA de
la compra: publica por qué la operación devolvió lo que devolvió —"la
compra se creó" o "la compra pendiente ya existía y se reutilizó"—
(`RN-C07`, `RN-A02`).

El precio, el estado y la marca de reutilización son una PROYECCIÓN de la
compra de `commerce`: este módulo no publica su modelo entero.
"""

from uuid import UUID

from modules.salesianos_fest.domain.results.pool_result import CompraCuposResult
from modules.salesianos_fest.presentation.schemas.compra_cupos_schemas import (
    CompraCreadaOut,
)
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    CompraOut,
)


class CompraCuposPresenter:
    """Transformador de la compra de cupos extra."""

    @staticmethod
    def present_compra(result: CompraCuposResult) -> CompraCreadaOut:
        """Proyecta la compra de cupos al wrapper HTTP."""
        return CompraCreadaOut(
            inscripcion_id=UUID(result.inscripcion_id),
            compra=CompraOut(
                compra_id=UUID(result.compra_id),
                orden_pago_id=UUID(result.orden_pago_id),
                estado=result.estado,
                total=result.total,
                moneda=result.moneda,
                reutilizada=result.reutilizada,
            ),
            cupos_solicitados=result.cupos_solicitados,
            cupos_pagados=result.cupos_pagados,
            cupos_asignados=result.cupos_asignados,
            cupos_disponibles=result.cupos_disponibles,
            causa_operativa=result.causa_operativa,
        )


__all__ = ["CompraCuposPresenter"]
