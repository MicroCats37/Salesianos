"""`PropietarioOrdenPagoAdapter` — la titularidad de una orden de pago.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

`pagos` necesita saber quién puede operar sobre una orden **antes** de
aceptar un reenvío desde el navegador. Como la compra es el agregado que
tiene al comprador, `commerce` responde por el puerto
`IPropietarioOrdenPagoService`.

El documento de identidad NO es una credencial (RN-U04): la titularidad se
comprueba contra la **persona compradora** de la compra que financia la
orden. Una cuenta técnica sin persona no es titular de ninguna orden.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError

from modules.commerce.domain.models import Compra

logger = logging.getLogger(__name__)


class PropietarioOrdenPagoAdapter:
    """Titularidad de una orden de pago."""

    def es_propietario(self, orden_pago_id: str, persona_id: str) -> bool:
        """Devuelve `True` si la persona es la compradora de la orden.

        Args:
            orden_pago_id: UUID de la `OrdenPago`.
            persona_id: UUID de la persona autenticada.

        Returns:
            `True` cuando la persona es la compradora de la orden.
        """
        if not orden_pago_id or not persona_id:
            return False
        try:
            compra = Compra.objects.filter(orden_pago_id=orden_pago_id).first()
        except (ValueError, TypeError, DjangoValidationError):
            logger.warning(
                "La comprobación de titularidad rechazó un identificador "
                "mal formado."
            )
            return False

        if compra is None:
            return False

        return str(compra.persona_id) == str(persona_id)


__all__ = ["PropietarioOrdenPagoAdapter"]
