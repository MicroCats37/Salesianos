"""
AsignacionOrchestrator — async thin facade for AsignacionCupo operations.

Orchestrator — async thin facade that delegates to flujos.
No business logic here — only delegation.
"""
from injector import inject

from asgiref.sync import sync_to_async

from modules.salesianos_fest.domain.schemas.asignacion_schemas import SaldoInscripcionResult
from modules.salesianos_fest.domain.results.asignacion_results import (
    AsignacionCupoCreatedResult,
    AsignacionCupoLiberadaResult,
)
from modules.salesianos_fest.domain.services.flujos.asignar_persona_flujo import AsignarPersonaFlujo
from modules.salesianos_fest.domain.services.flujos.liberar_cupo_flujo import LiberarCupoFlujo
from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService


class AsignacionOrchestrator:
    """
    Thin async facade for AsignacionCupo operations.
    """

    @inject
    def __init__(
        self,
        asignar_flujo: AsignarPersonaFlujo,
        liberar_flujo: LiberarCupoFlujo,
        asignacion_core: AsignacionCoreService,
    ):
        self.asignar_flujo = asignar_flujo
        self.liberar_flujo = liberar_flujo
        self.asignacion_core = asignacion_core

    async def asignar_persona(
        self,
        inscripcion_id: str,
        persona_id: str,
    ) -> AsignacionCupoCreatedResult:
        """
        Assign a person to an inscripcion if saldo disponible > 0.

        See AsignarPersonaFlujo._asignar_persona for full docs.
        """
        result = await self.asignar_flujo._asignar_persona(inscripcion_id, persona_id)
        return AsignacionCupoCreatedResult(
            asignacion_id=result["asignacion_id"],
            inscripcion_id=result["inscripcion_id"],
            persona_id=result["persona_id"],
            estado=result["estado"],
            compra_origen_id=result.get("compra_origen_id"),
        )

    async def liberar_cupo(
        self,
        inscripcion_id: str,
        persona_id: str,
        motivo: str | None = None,
        disciplina_id: str | None = None,
    ) -> AsignacionCupoLiberadaResult:
        """
        Liberate a player's cupo from an inscripcion.

        `disciplina_id` scopes the release to ONE discipline: the paid cup
        survives while the person keeps an active participation in another
        discipline of the same inscripcion.

        See LiberarCupoFlujo._liberar_cupo for full docs.
        """
        result = await self.liberar_flujo._liberar_cupo(
            inscripcion_id, persona_id, motivo, disciplina_id
        )
        return AsignacionCupoLiberadaResult(
            asignacion_id=result.get("asignacion_id") or "",
            inscripcion_id=result["inscripcion_id"],
            persona_id=result["persona_id"],
            estado="LIBERADA" if result["cupo_liberado"] else "N/A",
        )

    async def obtener_saldo(
        self,
        inscripcion_id: str,
    ) -> SaldoInscripcionResult:
        """
        Get saldo for an inscripcion.

        Returns: contratados/pagados/asignados_pagados/disponibles_pagados

        `calcular_saldo_inscripcion` is a SYNC core service (ORM access), so it
        MUST be wrapped in `sync_to_async`. Calling it directly from this async
        facade raised `SynchronousOnlyOperation` inside the running event loop
        and turned `GET /api/inscripciones/{id}/saldo` into a HTTP 500 — which
        silently killed the pool capacity chips and the Pagar/Ampliar CTA of
        the participant pool. Same pattern as
        `InscripcionOrchestrator.obtener_inscripcion_detalle_proceso`.
        """
        return await sync_to_async(
            self.asignacion_core.calcular_saldo_inscripcion
        )(inscripcion_id)
