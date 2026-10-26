"""
Test doubles for the commercial settlement port.

Pure Python classes — no pytest, no DB. They record the calls they receive so
the tests can assert that the backend (and never the browser) drives the
commercial settlement of a paid order.
"""
from modules.pagos.domain.ports import IConfirmadorOrdenPagoService
from modules.pagos.domain.schemas.result import SettlementResult


class ConfirmadorOrdenPagoFake(IConfirmadorOrdenPagoService):
    """
    In-memory double for IConfirmadorOrdenPagoService.

    Args:
        settled: what the port reports when it succeeds.
        already_settled: what the port reports as "it was already settled".
        error: when set, the port raises it instead of returning a result.
    """

    def __init__(
        self,
        settled: bool = True,
        already_settled: bool = False,
        error: Exception | None = None,
    ):
        self.settled = settled
        self.already_settled = already_settled
        self.error = error
        self.llamadas: list[str] = []

    async def confirmar_orden_pagada(self, orden_pago_id: str) -> SettlementResult:
        """Record the call and return (or raise) the configured outcome."""
        self.llamadas.append(orden_pago_id)
        if self.error is not None:
            raise self.error
        return SettlementResult(
            settled=self.settled,
            already_settled=self.already_settled,
        )

    @property
    def llamada_actual(self) -> str | None:
        """The last orden_pago_id received, or None when never called."""
        return self.llamadas[-1] if self.llamadas else None


__all__ = ["ConfirmadorOrdenPagoFake"]
