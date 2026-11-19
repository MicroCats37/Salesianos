"""Re-export puro de los modelos del módulo `commerce`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta desde `domain/models/`.
"""

from modules.commerce.domain.models import ActivacionCompra, Compra

__all__ = ["ActivacionCompra", "Compra"]
