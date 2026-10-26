"""
PropietarioOrdenPagoAdapter — resolves the owner of a payment order.

`commerce` owns `Compra`, the aggregate that funds an `OrdenPago`. This
adapter answers the `pagos` port so the payment module never imports the
commerce module (the dependency direction stays `commerce -> pagos`).
"""
import logging

from django.core.exceptions import ValidationError as DjangoValidationError

from modules.commerce.domain.models import Compra
from modules.pagos.domain.ports import IPropietarioOrdenPagoService

logger = logging.getLogger(__name__)


class PropietarioOrdenPagoAdapter(IPropietarioOrdenPagoService):
    """
    Ownership of a payment order, resolved through the purchase that funds it.

    The owner of the order is the responsible of the purchase. An order
    without a purchase, or a purchase without a responsible, has no owner:
    nobody can relay its payment through the browser — only the provider
    notification channel can settle it.
    """

    def es_propietario(self, orden_pago_id: str, persona_id: str) -> bool:
        """Return True when the person is the owner of the payment order."""
        if not orden_pago_id or not persona_id:
            return False

        try:
            return Compra.objects.filter(
                orden_pago_id=orden_pago_id,
                responsable_id=persona_id,
            ).exists()
        except (ValueError, TypeError, DjangoValidationError):
            # A malformed identifier never grants access.
            logger.warning("Ownership check rejected a malformed order id")
            return False
