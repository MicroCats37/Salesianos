"""`PoolPresenter` — results del pool → wrapper HTTP.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §3 (presenter)

El presenter es un TRANSFORMADOR PURO: no consulta la base de datos, no
llama a selectores y no construye mensajes públicos de error.

Es el dueño de la CAUSA OPERATIVA del pool: proyecta la causa que declara el
dominio para que el comprador entienda por qué la operación devolvió lo que
devolvió (`RN-A02`).
"""

from uuid import UUID

from modules.salesianos_fest.domain.results.pool_result import (
    ImpedimentoResult,
    ParticipacionResult,
    PoolResult,
)
from modules.salesianos_fest.presentation.schemas.pool_schemas import (
    ImpedimentoOut,
    ParticipacionOut,
    PoolOut,
)


class PoolPresenter:
    """Transformador del pool de una inscripción."""

    @staticmethod
    def present_pool(result: PoolResult) -> PoolOut:
        """Proyecta el pool al wrapper HTTP."""
        return PoolOut(
            inscripcion_id=UUID(result.inscripcion_id),
            cupos_pagados=result.cupos_pagados,
            cupos_asignados=result.cupos_asignados,
            cupos_disponibles=result.cupos_disponibles,
            participaciones=[
                PoolPresenter._present_participacion(participacion)
                for participacion in result.participaciones
            ],
            impedimentos=[
                PoolPresenter._present_impedimento(impedimento)
                for impedimento in result.impedimentos
            ],
            causa_operativa=result.causa_operativa,
        )

    # ── Internos ────────────────────────────────────────────────────────────

    @staticmethod
    def _present_participacion(participacion: ParticipacionResult) -> ParticipacionOut:
        """Proyecta una participación."""
        return ParticipacionOut(
            id=UUID(participacion.id),
            persona_id=UUID(participacion.persona_id),
            equipo_id=UUID(participacion.equipo_id),
            equipo_nombre=participacion.equipo_nombre,
            disciplina_id=UUID(participacion.disciplina_id),
            disciplina_nombre=participacion.disciplina_nombre,
            rol=participacion.rol,
            estado=participacion.estado,
            ocupa_cupo=participacion.ocupa_cupo,
            retirada_en=participacion.retirada_en,
        )

    @staticmethod
    def _present_impedimento(impedimento: ImpedimentoResult) -> ImpedimentoOut:
        """Proyecta un impedimento."""
        return ImpedimentoOut(
            codigo=impedimento.codigo,
            mensaje=impedimento.mensaje,
            equipo_id=UUID(impedimento.equipo_id) if impedimento.equipo_id else None,
        )


__all__ = ["PoolPresenter"]
