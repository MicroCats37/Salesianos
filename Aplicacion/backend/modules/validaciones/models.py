"""Los modelos del módulo `validaciones` (re-export puro).

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

Este archivo NO contiene lógica: re-exporta desde `domain/models/`
(`contract/django-app-architecture-contract.md` §4.1).
"""

from modules.validaciones.domain.models import Ticket, ValidacionTicket

__all__ = [
    "Ticket",
    "ValidacionTicket",
]
