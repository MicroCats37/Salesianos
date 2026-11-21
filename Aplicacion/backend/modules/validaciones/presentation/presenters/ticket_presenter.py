"""Los presentadores de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §3

Un presenter RECIBE un resultado del dominio y DEVUELVE el wrapper HTTP. NO
consulta la base de datos, NO llama a un selector y NO elige el mensaje de
éxito (`contract/api-wrapper-presenter-contract.md` §3).
"""

from uuid import UUID

from modules.validaciones.domain.results.validacion_results import (
    TicketConfirmadoResult,
    TicketEmitidoResult,
    TicketPreviewResult,
)
from modules.validaciones.presentation.schemas.validacion_schemas import (
    TicketActorOut,
    TicketConfirmadoOut,
    TicketEmitidoOut,
    TicketPreviewOut,
    TicketTitularOut,
)


class TicketPreviewPresenter:
    """Transforma el resultado de la vista previa en su wrapper."""

    @staticmethod
    def present(result: TicketPreviewResult) -> TicketPreviewOut:
        """La forma congelada de `FR-05` §3.1."""
        return TicketPreviewOut(
            edicion_id=result.edicion_id,
            tipo_derecho=result.tipo_derecho,
            codigo=result.codigo,
            estado=result.estado,
            cantidad_total=result.cantidad_total,
            cantidad_disponible=result.cantidad_disponible,
            cantidad_consumida=result.cantidad_consumida,
            puede_canjear=result.puede_canjear,
            motivo_codigo=result.motivo_codigo,
            motivo_mensaje=result.motivo_mensaje,
            titular=TicketTitularOut(
                persona_id=result.titular.persona_id,
                nombre=result.titular.nombre,
            ),
        )


class TicketConfirmPresenter:
    """Transforma el resultado del canje en su wrapper."""

    @staticmethod
    def present(result: TicketConfirmadoResult) -> TicketConfirmadoOut:
        """La forma congelada de `FR-05` §3.2."""
        return TicketConfirmadoOut(
            validacion_id=result.validacion_id,
            tipo_derecho=result.tipo_derecho,
            cantidad_consumida=result.cantidad_consumida,
            cantidad_restante=result.cantidad_restante,
            estado=result.estado,
            consumido_en=result.consumido_en,
            actor=TicketActorOut(
                usuario_id=result.actor_usuario_id,
                persona_id=result.actor_persona_id,
            ),
            repetido=result.repetido,
        )


class TicketEmitidoPresenter:
    """Transforma el resultado de la emisión en su wrapper."""

    @staticmethod
    def present(result: TicketEmitidoResult) -> TicketEmitidoOut:
        """La credencial emitida.

        El `codigo` se publica AQUÍ y sólo aquí: es la entrega ÚNICA del
        secreto. Ningún otro wrapper lo devuelve.
        """
        return TicketEmitidoOut(
            ticket_id=UUID(result.ticket_id),
            codigo=result.codigo,
            tipo_derecho=result.tipo_derecho,
            operacion=result.operacion,
            edicion_id=UUID(result.edicion_id),
            emitido_en=result.emitido_en,
        )


__all__ = [
    "TicketConfirmPresenter",
    "TicketEmitidoPresenter",
    "TicketPreviewPresenter",
]
