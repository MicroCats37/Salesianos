"""Modelos de dominio del módulo `eventos`.

Re-export puro: `modules/eventos/models.py` es el que Django lee.
"""

from modules.eventos.domain.models.edicion import Edicion
from modules.eventos.domain.models.evento import Evento

__all__ = [
    "Edicion",
    "Evento",
]
