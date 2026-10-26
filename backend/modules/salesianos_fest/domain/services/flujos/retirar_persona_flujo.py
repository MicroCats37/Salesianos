"""RetirarPersonaFlujo — async flow for retiring a person from an inscripcion."""
from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from ...models import InscripcionPersona, Participacion, Inscripcion
from ...exceptions import InscripcionNotFoundError, FechaLimiteExcedidaError
from ..core.acreditacion_service import AcreditacionCoreService
from ..core.asignacion_service import AsignacionCoreService


class RetirarPersonaFlujo:
    """Async flow for retiring a person from an inscripcion.

    Retires the InscripcionPersona AND all active Participaciones.
    The paid right (AsignacionCupo) is RELEASED (LIBERADA) — the purchase stays
    paid, so the freed slot can be reassigned or restored on re-entry.
    After retirement, recalculates AcreditacionEvento from all remaining
    active paid origins (R15 / F5).

    This respects R11: the person can re-enroll in another inscripcion later.
    """

    @inject
    def __init__(
        self,
        acreditacion_core: AcreditacionCoreService,
        asignacion_core: AsignacionCoreService = None,
    ):
        self.acreditacion_core = acreditacion_core
        self.asignacion_core = asignacion_core or AsignacionCoreService()

    def _verificar_fecha_limite(self, inscripcion_id: str) -> None:
        """Verify that modifications are still allowed for this evento."""
        inscripcion = Inscripcion.objects.select_related("evento").get(id=inscripcion_id)
        if not inscripcion.evento.puede_modificar():
            raise FechaLimiteExcedidaError()

    @sync_to_async
    def _retirar_atomico(self, inscripcion_id: str, persona_id: str) -> InscripcionPersona:
        """Retire persona from inscripcion in a transaction.

        After retiring, recalculates AcreditacionEvento from all remaining
        active paid origins so that fiesta access is correctly reflected.
        """
        with transaction.atomic():
            # Verify fecha_limite has not been exceeded
            self._verificar_fecha_limite(inscripcion_id)

            try:
                ip = InscripcionPersona.objects.select_related(
                    "persona", "inscripcion__evento"
                ).get(
                    inscripcion_id=inscripcion_id,
                    persona_id=persona_id,
                )
            except InscripcionPersona.DoesNotExist:
                raise InscripcionNotFoundError()

            # Retire all active participaciones for this inscripcion-persona
            Participacion.objects.filter(
                inscripcion_persona_id=str(ip.id),
                estado="A",
            ).update(estado="R")

            # F5: the person no longer plays in this inscripcion — release the
            # paid right. The cup becomes LIBERADA (not deleted): the purchase
            # stays paid and the slot can be reassigned or restored on re-entry.
            asignacion = self.asignacion_core.obtener_asignacion_activa_por_persona(
                inscripcion_id=inscripcion_id,
                persona_id=persona_id,
            )
            if asignacion is not None:
                self.asignacion_core.liberar_asignacion(
                    asignacion,
                    motivo="Retiro de la inscripción",
                )

            # Retire the inscripcion-persona itself
            ip.estado = "R"
            ip.save()

            # The freed paid slot returns to the available capacity and is
            # offered to the earliest participant still waiting in the pool.
            # The retired person is already RETIRADA, so the deterministic
            # allocator excludes it — the slot never comes back to them.
            reasignadas = self.asignacion_core.asignar_cupos_a_preregistrados(
                inscripcion_id=inscripcion_id,
            )
            for asignacion in reasignadas:
                self.acreditacion_core.sync_acreditacion_desde_compras(
                    evento_id=str(ip.inscripcion.evento_id),
                    persona_id=str(asignacion.inscripcion_persona.persona_id),
                )

            # R15 / F5: recalculate AcreditacionEvento from all remaining
            # active paid origins so fiesta access is correctly updated
            evento_id = str(ip.inscripcion.evento_id)
            self.acreditacion_core.sync_acreditacion_desde_compras(
                evento_id=evento_id,
                persona_id=persona_id,
            )

            return ip

    async def ejecutar(self, inscripcion_id: str, persona_id: str) -> InscripcionPersona:
        """Execute the retirar persona flow."""
        return await self._retirar_atomico(inscripcion_id, persona_id)
