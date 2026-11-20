"""Re-export puro de los modelos del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta `domain/models/`.
"""

from modules.patrocinadores.domain.models import (
    Patrocinador,
    PatrocinadorImagen,
)

__all__ = [
    "Patrocinador",
    "PatrocinadorImagen",
]
