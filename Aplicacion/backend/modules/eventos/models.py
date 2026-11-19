"""Re-export puro de los modelos del módulo `eventos`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta `domain/models/`.
"""

from modules.eventos.domain.models import Edicion, Evento

__all__ = [
    "Edicion",
    "Evento",
]
