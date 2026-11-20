"""Selectores del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)
"""

from modules.patrocinadores.domain.selectors.patrocinador_selector import (
    PatrocinadorSelector,
)

__all__ = [
    "PatrocinadorSelector",
]
