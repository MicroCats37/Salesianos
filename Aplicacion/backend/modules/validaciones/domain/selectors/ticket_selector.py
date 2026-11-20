"""Consultas de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

El selector CARGA datos y devuelve objetos de dominio. NO transforma a
schemas HTTP ni conoce la capa de presentación
(`contract/api-wrapper-presenter-contract.md` §3).
"""

from modules.validaciones.domain.models import Ticket, ValidacionTicket


def referencia_de(ticket: Ticket) -> str:
    """El identificador del DERECHO al que apunta la credencial.

    El ticket NO duplica el derecho: sólo lo REFERENCIA. La referencia es
    una clave ajena al módulo dueño (`PaseBeneficiario` o `Pedido`).
    """
    if ticket.pase_beneficiario_id:
        return str(ticket.pase_beneficiario_id)
    return str(ticket.pedido_id)


class TicketSelector:
    """Las consultas de la credencial y de su acta."""

    @staticmethod
    def obtener_por_codigo(codigo: str, bloquear: bool = False) -> Ticket | None:
        """La credencial de un código, o `None`.

        `bloquear=True` toma el bloqueo de fila (`select_for_update`): lo usa
        la confirmación para que dos operadores simultáneos se serialicen
        sobre la MISMA credencial (`QA-V02`).
        """
        consulta = Ticket.objects.select_related(
            "edicion",
            "pase_beneficiario",
            "pedido",
        )
        if bloquear:
            consulta = consulta.select_for_update()
        return consulta.filter(codigo=codigo).first()

    @staticmethod
    def obtener_acta_por_idempotencia(
        idempotency_key: str,
        bloquear: bool = False,
    ) -> ValidacionTicket | None:
        """El acta de una clave de idempotencia, o `None`."""
        consulta = ValidacionTicket.objects.select_related("ticket", "actor_usuario")
        if bloquear:
            consulta = consulta.select_for_update()
        return consulta.filter(idempotency_key=idempotency_key).first()


__all__ = ["TicketSelector", "referencia_de"]
