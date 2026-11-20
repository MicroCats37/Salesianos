"""Los modelos de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

`Ticket` es la CREDENCIAL que referencia un derecho existente;
`ValidacionTicket` es el ACTA de cada intento de validación.
"""

from modules.validaciones.domain.models.ticket import Ticket, ValidacionTicket

__all__ = [
    "Ticket",
    "ValidacionTicket",
]
