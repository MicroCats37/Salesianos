"""`AdminAccionSensibleFlujo` — el caso de uso de una acción SENSIBLE.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

## La regla del Dueño

Este flujo **no implementa ninguna regla del dominio**: la EJECUCIÓN la hace
el módulo DUEÑO (`salesianos_fest`), a través de su flujo público
(`PoolFlujo.retirar_participante`). Aquí sólo se orchestran tres cosas:

1. el **motivo**, que se exige antes de tocar nada (422 `MOTIVO_REQUERIDO`);
2. la **versión**, que se comprueba antes de tocar nada (409
   `RESOURCE_CHANGED`);
3. el **acta**, que se escribe después de la acción y la nombra.

## Por qué el motivo vive en el acta y no en la participación

La participación tiene su campo `motivo`, pero es el motivo TÉCNICO del
dueño y "no sale al cliente" (`PoolCoreService.retirar_participacion`). El
motivo que escribe el operador es un hecho ADMINISTRATIVO: su sitio es el
ACTA transversal, que es lo que nombra QUIÉN, CUÁNDO, QUÉ y POR QUÉ.

## La transacción

El dueño abre su propia transacción atómica (su flujo es el que la abre).
El acta se escribe justo después, en su propia escritura. La ventana entre
las dos es la que A0 tiene que decidir (`A0-XCT02-13`): si el ACTA debe
compartir la transacción del dueño, hace falta que el dueño exponga un
punto de extensión transaccional.
"""

from asgiref.sync import sync_to_async
from injector import inject

from core.exceptions import NotFoundError
from modules.administracion.domain.constants import (
    CodigoAccionAdmin,
    EntidadAuditada,
)
from modules.administracion.domain.services.core.admin_accion_sensible_service import (
    AdminAccionSensibleService,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo
from modules.salesianos_fest.domain.models import Participacion


class AdminAccionSensibleFlujo:
    """El caso de uso completo de una acción sensible del panel."""

    @inject
    def __init__(
        self,
        servicio: AdminAccionSensibleService,
        pool_flujo: PoolFlujo,
    ):
        self.servicio = servicio
        self.pool_flujo = pool_flujo

    async def retirar_participante(
        self,
        actor,
        inscripcion_id,
        participacion_id,
        motivo: str,
        version: str | None = None,
    ):
        """Retira un participante de una inscripción y deja el ACTA.

        El efecto lo aplica el DUEÑO: la retirada libera el cupo de ESA
        inscripción y no toca la compra, ni la orden de pago, ni el
        historial comercial (`RN-I04` · `DEC-06`).

        Returns:
            El `PoolResult` del dueño, ya con la retirada aplicada.
        """
        texto_motivo = self.servicio.validar_motivo(motivo)

        participacion = await sync_to_async(self._obtener_participacion)(
            inscripcion_id, participacion_id
        )
        self.servicio.validar_version(participacion, version)

        pool = await self.pool_flujo.retirar_participante(
            inscripcion_id, participacion_id
        )

        await sync_to_async(self.servicio.registrar_acta)(
            actor=actor,
            accion=CodigoAccionAdmin.RETIRAR_PARTICIPANTE,
            entidad=EntidadAuditada.PARTICIPACION,
            motivo=texto_motivo,
            edicion_id=str(participacion.edicion_id),
            entidad_id=str(participacion.id),
            datos={
                "inscripcion_id": str(inscripcion_id),
                "rol": participacion.rol,
                "equipo_id": str(participacion.equipo_id),
            },
        )

        return pool

    # ── Internos sync ────────────────────────────────────────────────────────

    @staticmethod
    def _obtener_participacion(inscripcion_id, participacion_id):
        """La participación, si pertenece a la inscripción.

        Una participación de otra inscripción NO EXISTE para este comando:
        el mismo 404 responde a los dos casos (`FR-03` §2.1).
        """
        participacion = (
            Participacion.objects.filter(
                id=participacion_id,
                inscripcion_id=inscripcion_id,
            )
            .select_related("edicion", "equipo")
            .first()
        )

        if participacion is None:
            raise NotFoundError(
                resource="Participación",
                code="RESOURCE_NOT_FOUND",
            )

        return participacion


__all__ = ["AdminAccionSensibleFlujo"]
