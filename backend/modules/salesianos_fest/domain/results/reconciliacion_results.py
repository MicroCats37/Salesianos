"""
Result DTOs for the payment reconciliation (reparación de pagos).

They describe what happened to every reviewed payment order, so the
management command can report exactly what it touched.
"""
from dataclasses import dataclass, field


@dataclass
class ReconciliacionOrdenResult:
    """Outcome of reconciling a single payment order."""
    orden_pago_id: str
    numero_orden: str
    estado: str
    motivo: str | None = None
    transaction_id: str | None = None
    compra_id: str | None = None
    intentos_expirados: int = 0


@dataclass
class ReconciliacionPagosResult:
    """Summary of a reconciliation run."""
    dry_run: bool
    revisadas: int
    reconciliadas: int
    ya_liquidadas: int
    omitidas: int
    errores: int
    detalle: list[ReconciliacionOrdenResult] = field(default_factory=list)
