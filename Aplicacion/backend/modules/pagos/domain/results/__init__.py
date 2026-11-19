"""Re-export de los result objects del módulo `pagos`."""

from modules.pagos.domain.results.pago_result import (
    EstadoOperativoResult,
    IntentoPagoResult,
    OrdenPagoResult,
    PagoConfirmadoResult,
)

__all__ = [
    "EstadoOperativoResult",
    "IntentoPagoResult",
    "OrdenPagoResult",
    "PagoConfirmadoResult",
]
