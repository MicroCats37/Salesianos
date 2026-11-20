"""Modelos del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.2
"""

from modules.patrocinadores.domain.models.patrocinador import Patrocinador
from modules.patrocinadores.domain.models.patrocinador_imagen import (
    PatrocinadorImagen,
)

__all__ = [
    "Patrocinador",
    "PatrocinadorImagen",
]
