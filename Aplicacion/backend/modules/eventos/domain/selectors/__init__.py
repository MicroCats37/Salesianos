"""Selectores del módulo `eventos` (superficie de consulta)."""

from modules.eventos.domain.selectors.edicion_selector import EdicionSelector
from modules.eventos.domain.selectors.evento_selector import EventoSelector

__all__ = [
    "EdicionSelector",
    "EventoSelector",
]
