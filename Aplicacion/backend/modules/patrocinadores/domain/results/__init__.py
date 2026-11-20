"""Result objects del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.6 (DTOs de salida)
"""

from modules.patrocinadores.domain.results.patrocinadores_result import (
    PatrocinadorImagenResult,
    PatrocinadorLogoResult,
    PatrocinadorResult,
)

__all__ = [
    "PatrocinadorImagenResult",
    "PatrocinadorLogoResult",
    "PatrocinadorResult",
]
