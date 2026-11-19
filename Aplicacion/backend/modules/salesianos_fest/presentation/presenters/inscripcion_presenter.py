"""`InscripcionPresenter` — results de inscripción → wrappers HTTP.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0`
Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter) ·
          `contract/PLAN_REFACTORIZACION.md` §3.A

El presenter es un TRANSFORMADOR PURO. En particular, **es el dueño de la
CAUSA OPERATIVA**: proyecta la causa que declara el dominio para que el
comprador entienda por qué la operación devolvió lo que devolvió (`RN-A02`,
`RN-C07`). El controller no decide causas ni las explica.

No consulta la base de datos, no llama a selectores y no construye mensajes
públicos de error.
"""

from uuid import UUID

from modules.salesianos_fest.domain.results.inscripcion_result import (
    CompraInscripcionResult,
    EquipoResult,
    InscripcionDetalleResult,
    InscripcionInicialResult,
)
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    CompraOut,
    EquipoOut,
    EquiposInscripcionOut,
    InscripcionDetalleOut,
    InscripcionInicialOut,
)


class InscripcionPresenter:
    """Transformador de las inscripciones."""

    @staticmethod
    def present_detalle(result: InscripcionDetalleResult) -> InscripcionDetalleOut:
        """Proyecta el detalle de una inscripción al wrapper HTTP."""
        return InscripcionDetalleOut(
            id=UUID(result.id),
            created_at=result.created_at,
            updated_at=result.updated_at,
            edicion_id=UUID(result.edicion_id),
            edicion_nombre=result.edicion_nombre,
            responsable_id=UUID(result.responsable_id),
            paquete_id=UUID(result.paquete_id),
            paquete_nombre=result.paquete_nombre,
            estado=result.estado,
            referencia=result.referencia,
            cupos_solicitados=result.cupos_solicitados,
            cupos_pagados=result.cupos_pagados,
            cupos_asignados=result.cupos_asignados,
            cupos_disponibles=result.cupos_disponibles,
            equipos=[
                InscripcionPresenter._present_equipo(equipo)
                for equipo in result.equipos
            ],
        )

    @staticmethod
    def present_equipos(
        inscripcion_id,
        equipos: list[EquipoResult],
    ) -> EquiposInscripcionOut:
        """Proyecta los equipos de una inscripción."""
        return EquiposInscripcionOut(
            inscripcion_id=UUID(str(inscripcion_id)),
            equipos=[
                InscripcionPresenter._present_equipo(equipo) for equipo in equipos
            ],
        )

    @staticmethod
    def present_inicial(result: InscripcionInicialResult) -> InscripcionInicialOut:
        """Proyecta el alta de una inscripción inicial.

        La `causa_operativa` la declara el dominio y la publica el presenter:
        el controller no la decide.
        """
        return InscripcionInicialOut(
            inscripcion=InscripcionPresenter.present_detalle(result.inscripcion),
            compra=InscripcionPresenter._present_compra(result.compra),
            causa_operativa=result.causa_operativa,
        )

    # ── Internos ────────────────────────────────────────────────────────────

    @staticmethod
    def _present_equipo(equipo: EquipoResult) -> EquipoOut:
        """Proyecta un equipo."""
        return EquipoOut(
            id=UUID(equipo.id),
            created_at=equipo.created_at,
            updated_at=equipo.updated_at,
            disciplina_id=UUID(equipo.disciplina_id),
            disciplina_nombre=equipo.disciplina_nombre,
            nombre=equipo.nombre,
            estado=equipo.estado,
        )

    @staticmethod
    def _present_compra(compra: CompraInscripcionResult) -> CompraOut:
        """Proyecta la compra que financia la inscripción."""
        return CompraOut(
            compra_id=UUID(compra.compra_id),
            orden_pago_id=UUID(compra.orden_pago_id),
            estado=compra.estado,
            total=compra.total,
            moneda=compra.moneda,
            reutilizada=compra.reutilizada,
        )


__all__ = ["InscripcionPresenter"]
