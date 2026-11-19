"""Re-export puro de los modelos del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.1

Este archivo NO contiene lógica: sólo re-exporta desde `domain/models/`.
"""

from modules.pagos.domain.models import (
    OrdenPago,
    RegistroIdempotencia,
    TransaccionPago,
)

__all__ = [
    "OrdenPago",
    "RegistroIdempotencia",
    "TransaccionPago",
]
