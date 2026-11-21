"""`EmitirTicketFlujo` — la EMISIÓN de una credencial de control de acceso.

Change: `administracion-pases-alta-directa` · Apply C

Contract: `contract/django-app-architecture-contract.md` §4.4 — flujos ASYNC,
ABREN `transaction.atomic()`.

Este flujo es el camino HTTP de emisión. Antes sólo existía el comando de
gestión `emitir_ticket`: el administrador tenía que entrar a la consola para
entregar una credencial. La DOMINIO no cambia: el derecho es del módulo dueño,
la credencial es de `validaciones` y el código es un secreto de una sola
entrega.

**EL NAVEGADOR NO DECIDE EL TIPO.** El flujo pide al dueño del derecho (a
través del puerto `IEmisorCredencialService`) su tipo y su operación. El
cliente sólo manda el identificador del derecho (`RN-U04`).

**LA EMISIÓN ES ONE-SHOT POR DERECHO.** Si ese derecho ya tiene una credencial
VIGENTE, no se emite una segunda: se lanza `ConflictError` (409).
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.validaciones.domain.ports.emisor_credencial import (
    IEmisorCredencialService,
)
from modules.validaciones.domain.results.validacion_results import (
    TicketEmitidoResult,
)
from modules.validaciones.domain.schemas.validacion_schemas import EmitirTicketData
from modules.validaciones.domain.services.core.emision_credencial_core_service import (
    EmisionCredencialCoreService,
)


class EmitirTicketFlujo:
    """El flujo async de la emisión de una credencial."""

    @inject
    def __init__(
        self,
        emisor: IEmisorCredencialService,
        core: EmisionCredencialCoreService,
    ):
        self.emisor = emisor
        self.core = core

    async def _emitir(self, data: EmitirTicketData) -> TicketEmitidoResult:
        """La credencial emitida para el derecho indicado.

        Raises:
            PaseBeneficiarioNoEncontradoError: el derecho no existe (404).
            ConflictError: el derecho ya tiene una credencial vigente (409).
        """
        referencia = await sync_to_async(self.emisor.resolver_referencia)(
            data.derecho_id
        )
        ticket = await sync_to_async(self._emitir_sync)(referencia)
        return self._resultado(ticket)

    @transaction.atomic()
    def _emitir_sync(self, referencia) -> object:
        """La escritura de la credencial, en una sola transacción."""
        return self.core.emitir(referencia)

    @staticmethod
    def _resultado(ticket) -> TicketEmitidoResult:
        """El DTO de salida de la emisión.

        El `codigo` viaja AQUÍ y sólo aquí: es la única respuesta que lo
        publica. No se registra ni se lista.
        """
        return TicketEmitidoResult(
            ticket_id=str(ticket.id),
            codigo=ticket.codigo,
            tipo_derecho=ticket.tipo_derecho,
            operacion=ticket.operacion,
            edicion_id=str(ticket.edicion_id),
            emitido_en=ticket.emitido_en,
        )


__all__ = ["EmitirTicketFlujo"]
