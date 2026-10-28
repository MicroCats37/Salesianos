"""
EstadoCompraOrdenPagoAdapter — resolves the commercial state of the purchase
that funds a payment order.

`commerce` owns `Compra`, the aggregate that funds an `OrdenPago`. This
adapter answers the `pagos` port so the payment module never imports the
commerce module (the dependency direction stays `commerce -> pagos`).
"""
import logging

from django.core.exceptions import ValidationError as DjangoValidationError

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.pagos.domain.ports import IEstadoCompraOrdenPagoService
from modules.pagos.domain.schemas.aprobacion_pago_manual_schemas import (
    EstadoCompraOrdenPago,
)

logger = logging.getLogger(__name__)


class EstadoCompraOrdenPagoAdapter(IEstadoCompraOrdenPagoService):
    """
    Commercial state of the purchase that funds a payment order.

    An order with no purchase has no commercial state: the caller decides
    what that means for its own rule (for the manual approval it means
    "there is nothing to approve").
    """

    def obtener_estado_compra(self, orden_pago_id: str) -> EstadoCompraOrdenPago:
        """Return the commercial state of the purchase that funds the order."""
        if not orden_pago_id:
            return EstadoCompraOrdenPago(existe=False, estado=None)

        try:
            compra = Compra.objects.filter(orden_pago_id=orden_pago_id).first()
        except (ValueError, TypeError, DjangoValidationError):
            # A malformed identifier never grants access.
            logger.warning("Purchase state check rejected a malformed order id")
            return EstadoCompraOrdenPago(existe=False, estado=None)

        if compra is None:
            return EstadoCompraOrdenPago(existe=False, estado=None)

        return EstadoCompraOrdenPago(
            existe=True,
            estado=compra.estado,
            cancelada=compra.estado == EstadoCompraChoices.CANCELADA,
        )


__all__ = ["EstadoCompraOrdenPagoAdapter"]
