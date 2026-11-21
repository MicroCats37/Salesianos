"""`ValidacionOrchestrator` — la fachada async de la consola de validación.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0`

Es DELGADA: un método público por endpoint y NADA de lógica de negocio
(`contract/django-app-architecture-contract.md` §4.5).

Las dos operaciones comparten INFRAESTRUCTURA, nunca decisión de negocio ni
pantalla: el INGRESO y la ENTREGA se resuelven en su módulo dueño
(`FR-05` §5).
"""

from injector import inject

from modules.validaciones.domain.results.validacion_results import (
    TicketConfirmadoResult,
    TicketEmitidoResult,
    TicketPreviewResult,
)
from modules.validaciones.domain.schemas.validacion_schemas import (
    ConfirmarTicketData,
    EmitirTicketData,
    PreviewTicketData,
)
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)
from modules.validaciones.domain.services.flujos.emitir_ticket_flujo import (
    EmitirTicketFlujo,
)
from modules.validaciones.domain.services.flujos.preview_ticket_flujo import (
    PreviewTicketFlujo,
)


class ValidacionOrchestrator:
    """La fachada de las operaciones de la consola."""

    @inject
    def __init__(
        self,
        preview_flujo: PreviewTicketFlujo,
        confirmar_flujo: ConfirmarTicketFlujo,
        emitir_flujo: EmitirTicketFlujo,
    ):
        self.preview_flujo = preview_flujo
        self.confirmar_flujo = confirmar_flujo
        self.emitir_flujo = emitir_flujo

    async def preview(self, data: PreviewTicketData) -> TicketPreviewResult:
        """La vista previa de una credencial. NO consume."""
        return await self.preview_flujo._preview(data)

    async def confirmar(
        self,
        actor,
        data: ConfirmarTicketData,
    ) -> TicketConfirmadoResult:
        """El canje confirmado de una credencial."""
        return await self.confirmar_flujo._confirmar(
            _usuario_id(actor),
            _persona_id(actor),
            data,
        )

    async def emitir_ticket(self, data: EmitirTicketData) -> TicketEmitidoResult:
        """La emisión de una credencial de puerta.

        El CÓDIGO es un secreto: se devuelve UNA vez, en esta respuesta. No se
        publica en ningún listado, no se registra en la auditoría y no se
        escribe en ningún log.
        """
        return await self.emitir_flujo._emitir(data)


def _usuario_id(actor) -> str | None:
    """La cuenta que opera."""
    if actor is None:
        return None
    identificador = getattr(actor, "id", None)
    return str(identificador) if identificador else None


def _persona_id(actor) -> str | None:
    """La persona del actor, si la cuenta tiene una."""
    if actor is None:
        return None
    identificador = getattr(actor, "persona_fk_id", None)
    return str(identificador) if identificador else None


__all__ = ["ValidacionOrchestrator"]
