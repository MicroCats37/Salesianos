"""`EstadoCompraOrdenPagoAdapter` — el estado comercial de la compra.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

`commerce` es dueño de `Compra`, el agregado que financia una `OrdenPago`.
Este adaptador responde al puerto de `pagos` para que el módulo de pago nunca
importe el de commerce: la dirección de dependencias se queda
`commerce -> pagos`.

Expone **banderas**, no el vocabulario crudo del estado: `pagos` no necesita
conocer los valores de `EstadoCompra` y el acoplamiento queda cerrado también
en los datos.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError

from modules.commerce.domain.constants import EstadoCompra
from modules.commerce.domain.models import Compra
from modules.pagos.domain.schemas.pago_schemas import (
    EstadoCompraOrdenPago,
    MarcaCompraPagadaResult,
)

logger = logging.getLogger(__name__)


class EstadoCompraOrdenPagoAdapter:
    """Estado comercial de la compra que financia una orden de pago."""

    def obtener_estado_compra(self, orden_pago_id: str) -> EstadoCompraOrdenPago:
        """Devuelve el estado comercial de la compra que financia la orden.

        Args:
            orden_pago_id: UUID de la `OrdenPago`.

        Returns:
            `EstadoCompraOrdenPago` con `existe=False` cuando ninguna compra
            financia la orden.
        """
        compra = self._buscar(orden_pago_id)
        if compra is None:
            return EstadoCompraOrdenPago(existe=False, pagada=False, cancelada=False)

        return EstadoCompraOrdenPago(
            existe=True,
            pagada=compra.estado == EstadoCompra.PAGADA,
            cancelada=compra.estado == EstadoCompra.CANCELADA,
        )

    def marcar_compra_pagada(self, orden_pago_id: str) -> MarcaCompraPagadaResult:
        """Marca la compra de la orden como pagada. Idempotente.

        Una compra `CANCELADA` **no** se resucita: el pago de una compra
        cancelada es una incidencia visible (RN-C08), no un derecho devuelto.

        No habilita ningún derecho: eso es un hecho posterior y separado
        (FR-04 §4).
        """
        compra = self._buscar(orden_pago_id)
        if compra is None:
            return MarcaCompraPagadaResult(existe=False, pagada=False, ya_pagada=False)

        if compra.estado == EstadoCompra.PAGADA:
            return MarcaCompraPagadaResult(existe=True, pagada=True, ya_pagada=True)

        if compra.estado == EstadoCompra.CANCELADA:
            return MarcaCompraPagadaResult(existe=True, pagada=False, ya_pagada=False)

        compra.estado = EstadoCompra.PAGADA
        compra.save(update_fields=["estado", "updated_at"])
        return MarcaCompraPagadaResult(existe=True, pagada=True, ya_pagada=False)

    # ── Internos ─────────────────────────────────────────────────────────────

    def _buscar(self, orden_pago_id: str) -> Compra | None:
        """La compra que financia la orden, si existe.

        Un identificador mal formado nunca concede acceso: se registra y se
        devuelve `None`.
        """
        if not orden_pago_id:
            return None
        try:
            return Compra.objects.filter(orden_pago_id=orden_pago_id).first()
        except (ValueError, TypeError, DjangoValidationError):
            logger.warning(
                "La consulta del estado de la compra rechazó un identificador "
                "de orden mal formado."
            )
            return None


__all__ = ["EstadoCompraOrdenPagoAdapter"]
