"""`OrdenPagoCoreService` — operaciones sync sobre la orden de pago.

Contract: `contract/django-app-architecture-contract.md` §4.3

- Es **sync**.
- Opera directamente sobre el ORM.
- **NO** abre `transaction.atomic()`: la atomicidad la aporta el flujo
  (`domain/services/flujos/`).

Reglas que este servicio respeta:

- El `monto` y la `moneda` son un **snapshot congelado**: ninguna operación de
  este servicio los reescribe. Un cambio de precio posterior es una compra
  nueva, no una edición de la orden (FR-04 §1.2).
- `marcar_confirmada` es **idempotente**: una orden ya confirmada conserva su
  `pagada_en` original. Reabrir el checkout o repetir la notificación nunca
  reescribe la evidencia de un pago (FR-04 I-1).
"""

from datetime import datetime, timedelta

from django.utils import timezone

from modules.pagos.domain.constants import (
    METADATA_ALLOWED_KEYS,
    METADATA_FORBIDDEN_KEYS,
    ORDEN_VIGENCIA_HORAS,
    EstadoOrdenPago,
)
from modules.pagos.domain.models import OrdenPago


def sanitizar_metadata(metadata: dict | None) -> dict:
    """Sanea el contexto de auditoría de una orden.

    - Sólo sobreviven las claves de `METADATA_ALLOWED_KEYS`.
    - Las claves de `METADATA_FORBIDDEN_KEYS` se descartan por defensa en
      profundidad (aunque ninguna clave permitida esté en esa lista).
    - El resultado es contexto **no autoritativo**: nunca sustituye a una FK
      real ni dirige una autorización.
    """
    if not isinstance(metadata, dict):
        return {}
    permitidas = METADATA_ALLOWED_KEYS
    prohibidas = METADATA_FORBIDDEN_KEYS
    return {
        clave: valor
        for clave, valor in metadata.items()
        if clave in permitidas and clave not in prohibidas
    }


class OrdenPagoCoreService:
    """Operaciones de bajo nivel sobre `OrdenPago`."""

    def crear(
        self,
        *,
        referencia: str,
        monto,
        moneda: str = "PEN",
        metadata: dict | None = None,
        vence_en: datetime | None = None,
    ) -> OrdenPago:
        """Crea una orden `PENDIENTE` con su monto congelado.

        Args:
            referencia: referencia **visible** del proveedor. Es única.
            monto: el monto congelado. `Decimal`, nunca `float`.
            moneda: código ISO-4217.
            metadata: contexto de auditoría; se sanea antes de guardarse.
            vence_en: instante de vencimiento. Por defecto, dos horas.

        Returns:
            La orden creada.
        """
        if vence_en is None:
            vence_en = timezone.now() + timedelta(hours=ORDEN_VIGENCIA_HORAS)
        return OrdenPago.objects.create(
            referencia=referencia,
            estado=EstadoOrdenPago.PENDIENTE,
            monto=monto,
            moneda=moneda,
            pagada_en=None,
            vence_en=vence_en,
            metadata=sanitizar_metadata(metadata),
        )

    def obtener_por_id(self, orden_pago_id) -> OrdenPago | None:
        """La orden por su identificador."""
        return OrdenPago.objects.filter(id=orden_pago_id).first()

    def obtener_por_referencia(self, referencia: str) -> OrdenPago | None:
        """La orden por su referencia visible."""
        if not referencia:
            return None
        return OrdenPago.objects.filter(referencia=referencia).first()

    def bloquear(self, orden_pago_id) -> OrdenPago | None:
        """Carga la orden y bloquea su fila hasta el commit.

        El bloqueo serializa la confirmación: dos confirmaciones simultáneas de
        la misma orden no pueden confirmar dos veces.
        """
        return (
            OrdenPago.objects.filter(id=orden_pago_id).select_for_update().first()
        )

    def marcar_confirmada(self, orden: OrdenPago) -> OrdenPago:
        """Marca la orden como `CONFIRMADA` y fecha el pago.

        Idempotente: si ya estaba confirmada conserva su `pagada_en` original.
        """
        if orden.estado != EstadoOrdenPago.CONFIRMADA:
            orden.estado = EstadoOrdenPago.CONFIRMADA
            orden.pagada_en = timezone.now()
            orden.save(update_fields=["estado", "pagada_en", "updated_at"])
        return orden

    def marcar_en_verificacion(self, orden: OrdenPago) -> OrdenPago:
        """Marca la orden como `EN_VERIFICACION`.

        Es el estado de "estamos verificando tu pago" (RN-C07): la
        notificación llegó pero todavía no se pudo confirmar. Idempotente.
        """
        if orden.estado not in (
            EstadoOrdenPago.CONFIRMADA,
            EstadoOrdenPago.FALLIDA,
            EstadoOrdenPago.VENCIDA,
        ):
            orden.estado = EstadoOrdenPago.EN_VERIFICACION
            orden.save(update_fields=["estado", "updated_at"])
        return orden

    def marcar_fallida(self, orden: OrdenPago) -> OrdenPago:
        """Marca la orden como `FALLIDA`. Idempotente.

        Un fallo NO cancela la orden: el comprador puede reintentar con un
        intento nuevo sobre la MISMA orden (RN-C03, RN-C04).
        """
        if orden.estado not in (EstadoOrdenPago.CONFIRMADA, EstadoOrdenPago.VENCIDA):
            orden.estado = EstadoOrdenPago.FALLIDA
            orden.save(update_fields=["estado", "updated_at"])
        return orden

    def marcar_vencida(self, orden: OrdenPago) -> OrdenPago:
        """Marca la orden como `VENCIDA`. Idempotente."""
        if orden.estado != EstadoOrdenPago.CONFIRMADA:
            orden.estado = EstadoOrdenPago.VENCIDA
            orden.save(update_fields=["estado", "updated_at"])
        return orden


__all__ = ["OrdenPagoCoreService", "sanitizar_metadata"]
