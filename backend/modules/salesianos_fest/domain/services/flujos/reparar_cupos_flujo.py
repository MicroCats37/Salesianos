"""
RepararCuposFlujo — materializes the paid cups that were never assigned.

A paid cup is a standing entitlement of a person: it is materialized from the
paid capacity of its inscripcion, FIFO by preregistration order, at payment
settlement AND at preregistration time.

Some inscriptions never got that treatment: a purchase marked PAGADA outside
the settlement flow (seed, admin edit, legacy rows) leaves the paid capacity
without any right, so the participants wait in the pool forever while the
saldo says the capacity is free.

This flow closes that gap:
1. Selects the inscriptions that hold at least one PAGADA compra.
2. For each one, counts the participants still waiting for a paid cup and the
   paid capacity still free.
3. Materializes the pending cups with the SAME deterministic allocator used at
   settlement (`asignar_cupos_a_preregistrados`) — one writer, FIFO order.
4. Syncs `AcreditacionEvento` for every person that received a right.

Idempotent: running it again produces no change and never duplicates rights.

NOTE: it does NOT touch `Inscripcion.estado` — the administrative state of an
inscription is a separate concern from the commercial rights.
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.salesianos_fest.domain.constants import EstadoReparacionCupoChoices
from modules.salesianos_fest.domain.results.reparar_cupos_results import (
    RepararCuposInscripcionResult,
    RepararCuposResult,
)
from modules.salesianos_fest.domain.services.core.acreditacion_service import (
    AcreditacionCoreService,
)
from modules.salesianos_fest.domain.services.core.asignacion_service import (
    AsignacionCoreService,
)

logger = logging.getLogger(__name__)


class RepararCuposFlujo:
    """
    Async flow that materializes the pending paid cups of every inscripcion.

    It is the business owner of the repair; the management command is only a
    thin entry point that parses the arguments and prints the report.
    """

    @inject
    def __init__(
        self,
        asignacion_core: AsignacionCoreService,
        acreditacion_core: AcreditacionCoreService,
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core

    async def _reparar(
        self,
        inscripcion_id: str | None = None,
        dry_run: bool = False,
    ) -> RepararCuposResult:
        """
        Materialize the pending paid cups.

        Args:
            inscripcion_id: Restrict the run to a single inscripcion (UUID).
            dry_run: Report what would be materialized without changing anything.

        Returns:
            RepararCuposResult with the summary and the per-inscripcion detail.
        """
        candidatas = await sync_to_async(self._candidatas)(inscripcion_id)

        detalle: list[RepararCuposInscripcionResult] = []
        for inscripcion_id in candidatas:
            detalle.append(await self._reparar_inscripcion(inscripcion_id, dry_run))

        return RepararCuposResult(
            dry_run=dry_run,
            revisadas=len(detalle),
            reparadas=self._contar(detalle, EstadoReparacionCupoChoices.REPARADA),
            sin_pendientes=self._contar(
                detalle, EstadoReparacionCupoChoices.SIN_PENDIENTES
            ),
            errores=self._contar(detalle, EstadoReparacionCupoChoices.ERROR),
            asignaciones_creadas=sum(d.asignaciones_creadas for d in detalle),
            detalle=detalle,
        )

    def _contar(self, detalle: list[RepararCuposInscripcionResult], estado: str) -> int:
        """Count the reviewed inscriptions that ended in the given state."""
        return len([item for item in detalle if item.estado == estado])

    def _candidatas(self, inscripcion_id: str | None) -> list[str]:
        """Return the inscriptions that hold paid capacity to distribute."""
        if inscripcion_id:
            return [str(inscripcion_id)]
        return self.asignacion_core.listar_inscripciones_con_capacidad_pagada()

    async def _reparar_inscripcion(
        self,
        inscripcion_id: str,
        dry_run: bool,
    ) -> RepararCuposInscripcionResult:
        """Materialize the pending cups of a single inscripcion."""
        saldo = await sync_to_async(
            self.asignacion_core.calcular_saldo_inscripcion
        )(inscripcion_id)
        pendientes = await sync_to_async(
            self.asignacion_core.contar_pendientes_de_cupo
        )(inscripcion_id)

        base = RepararCuposInscripcionResult(
            inscripcion_id=inscripcion_id,
            pagados=saldo["pagados"],
            asignados_pagados=saldo["asignados_pagados"],
            disponibles_pagados=saldo["disponibles_pagados"],
            pendientes=pendientes,
            asignaciones_creadas=0,
        )

        if saldo["pagados"] == 0:
            base.estado = EstadoReparacionCupoChoices.OMITIDA
            base.motivo = "La inscripción no tiene capacidad pagada."
            return base

        if pendientes == 0:
            base.estado = EstadoReparacionCupoChoices.SIN_PENDIENTES
            return base

        # Dry run: report what would happen, change nothing.
        if dry_run:
            base.estado = EstadoReparacionCupoChoices.REPARADA
            base.asignaciones_creadas = min(pendientes, saldo["disponibles_pagados"])
            return base

        try:
            creadas = await sync_to_async(self._materializar)(inscripcion_id)
        except Exception:
            logger.exception(
                "Cup repair failed for inscripcion %s — the paid capacity stays "
                "unassigned and can be retried",
                inscripcion_id,
            )
            base.estado = EstadoReparacionCupoChoices.ERROR
            base.motivo = "La reparación falló; se puede reintentar."
            return base

        base.asignaciones_creadas = len(creadas)
        base.estado = (
            EstadoReparacionCupoChoices.REPARADA
            if creadas
            else EstadoReparacionCupoChoices.SIN_PENDIENTES
        )
        return base

    @transaction.atomic()
    def _materializar(self, inscripcion_id: str) -> list:
        """Create the pending assignments of an inscripcion and sync the access.

        Atomic: the assignments and the accreditation they grant are committed
        together, so a person never keeps a right without its access.
        """
        from modules.salesianos_fest.domain.models import Inscripcion

        asignaciones = self.asignacion_core.asignar_cupos_a_preregistrados(
            inscripcion_id=inscripcion_id,
        )
        if not asignaciones:
            return []

        evento_id = str(
            Inscripcion.objects.only("evento_id").get(id=inscripcion_id).evento_id
        )
        for asignacion in asignaciones:
            self.acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=evento_id,
                persona_id=str(asignacion.inscripcion_persona.persona_id),
            )

        return asignaciones
