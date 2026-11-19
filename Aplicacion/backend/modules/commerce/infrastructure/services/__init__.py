"""Adaptadores de `commerce` para los puertos de `pagos`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

`pagos` declara los puertos y `commerce` los implementa. El módulo de pago
nunca importa este módulo: pregunta por el estado comercial de la compra y
por la titularidad de la orden a través de la interfaz, en vocabulario de
pago. Así la dirección de dependencias queda `commerce -> pagos` y el grafo
de módulos es acíclico.
"""

from modules.commerce.infrastructure.services.activacion_compra import (
    ActivacionCompraAdapter,
)
from modules.commerce.infrastructure.services.estado_compra_orden_pago import (
    EstadoCompraOrdenPagoAdapter,
)
from modules.commerce.infrastructure.services.propietario_orden_pago import (
    PropietarioOrdenPagoAdapter,
)

__all__ = [
    "ActivacionCompraAdapter",
    "EstadoCompraOrdenPagoAdapter",
    "PropietarioOrdenPagoAdapter",
]
