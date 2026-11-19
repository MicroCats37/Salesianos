"""`CompraCoreService` — operaciones sync sobre la compra.

Contract: `contract/django-app-architecture-contract.md` §4.3

- Es **sync**.
- Opera directamente sobre el ORM.
- **NO** abre `transaction.atomic()`: la atomicidad la aporta el flujo.

Reglas que este servicio respeta:

- El `total` y las `lineas_snapshot` se escriben **una vez**, al crear la
  compra. Ninguna operación posterior los reescribe (FR-04 §1.1).
- `marcar_pagada` es **idempotente** y **no resucita** una compra cancelada:
  el pago de una compra cancelada es una incidencia, no un derecho devuelto.
"""

from django.utils import timezone

from modules.commerce.domain.constants import EstadoCompra
from modules.commerce.domain.models import Compra


class CompraCoreService:
    """Operaciones de bajo nivel sobre `Compra`."""

    def crear(
        self,
        *,
        persona_id,
        origen: str,
        total,
        moneda: str,
        lineas_snapshot: list,
        referencia: str,
    ) -> Compra:
        """Crea la compra en estado `PENDIENTE`, con su total congelado.

        Args:
            persona_id: UUID de la persona compradora.
            origen: dominio de origen de la compra.
            total: total **derivado** por el servidor de las líneas.
            moneda: código ISO-4217.
            lineas_snapshot: snapshot inmutable de lo comprado.
            referencia: referencia de la intención de compra.

        Returns:
            La compra creada.
        """
        return Compra.objects.create(
            persona_id=persona_id,
            origen=origen,
            estado=EstadoCompra.PENDIENTE,
            total=total,
            moneda=moneda,
            lineas_snapshot=list(lineas_snapshot or []),
            referencia=referencia,
        )

    def vincular_orden_pago(self, compra: Compra, orden_pago) -> Compra:
        """Enlaza la compra con su orden de pago.

        El enlace se escribe una sola vez: la orden de una compra no cambia.
        """
        if compra.orden_pago_id != orden_pago.id:
            compra.orden_pago = orden_pago
            compra.save(update_fields=["orden_pago", "updated_at"])
        return compra

    def marcar_pagada(self, compra: Compra) -> Compra:
        """Marca la compra como `PAGADA`. Idempotente.

        Una compra `CANCELADA` **no** se resucita: se deja como estaba y el
        veredicto operativo seguirá diciendo que el pago no está reflejado en
        la compra (la incidencia es recuperable, RN-C08).
        """
        if compra.estado == EstadoCompra.CANCELADA:
            return compra
        if compra.estado != EstadoCompra.PAGADA:
            compra.estado = EstadoCompra.PAGADA
            compra.save(update_fields=["estado", "updated_at"])
        return compra

    def marcar_cancelada(self, compra: Compra) -> Compra:
        """Marca la compra como `CANCELADA`. Idempotente.

        Cancelar **no** reembolsa por sí sola (`FR-04` §5): la política de
        cancelación/reembolso sigue ABIERTA (`PD-06`, `GOV-01-OPEN-06`).
        """
        if compra.estado != EstadoCompra.PAGADA:
            compra.estado = EstadoCompra.CANCELADA
            compra.save(update_fields=["estado", "updated_at"])
        return compra

    def esta_pendiente(self, compra: Compra) -> bool:
        """Si la compra sigue pendiente de pago."""
        return compra.estado == EstadoCompra.PENDIENTE

    def ahora(self):
        """El instante actual del servidor (usado para marcas de tiempo)."""
        return timezone.now()


__all__ = ["CompraCoreService"]
