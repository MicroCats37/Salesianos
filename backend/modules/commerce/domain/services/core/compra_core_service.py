"""
CompraCoreService — sync core operations for generic Compra.

Core service — no transaction.atomic own, no async.
Operations that touch the DB are here; atomicity is provided by the caller flujo.
"""
from decimal import Decimal

from django.utils import timezone
from injector import inject

from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices


class CompraCoreService:
    """
    Core sync service for generic Compra operations.

    Handles:
    - Compra creation with price snapshot
    - Compra state transitions (PENDIENTE -> PAGADA/CANCELADA)
    - Compra retrieval
    """

    @inject
    def __init__(self):
        pass

    def crear_compra(
        self,
        total: Decimal,
        responsable_id: str | None = None,
        descripcion: str = "",
        referencia_externa: str | None = None,
    ) -> Compra:
        """
        Create a new generic Compra with frozen total snapshot.

        The price is already calculated by the caller (flujo).
        orden_pago is assigned separately via the flujo.
        """
        return Compra.objects.create(
            responsable_id=responsable_id,
            descripcion=descripcion,
            referencia_externa=referencia_externa,
            total=total,
            estado=EstadoCompraChoices.PENDIENTE,
        )

    def obtener_compra(self, compra_id: str) -> Compra | None:
        """Get a Compra by its ID with select_related."""
        return (
            Compra.objects
            .select_related("responsable", "orden_pago")
            .filter(id=compra_id)
            .first()
        )

    def obtener_compra_por_orden_pago(self, orden_pago_id: str) -> Compra | None:
        """Get a Compra by its associated OrdenPago ID."""
        return (
            Compra.objects
            .select_related("responsable", "orden_pago")
            .filter(orden_pago_id=orden_pago_id)
            .first()
        )

    def marcar_pagada(self, compra: Compra) -> Compra:
        """Mark a Compra as PAGADA."""
        if compra.estado != EstadoCompraChoices.PENDIENTE:
            from core.exceptions import BusinessError
            raise BusinessError(
                "La compra no esta en estado pendiente.",
                code="COMPRA_NO_PENDIENTE",
            )
        compra.estado = EstadoCompraChoices.PAGADA
        compra.save(update_fields=["estado", "updated_at"])
        return compra

    def marcar_cancelada(self, compra: Compra) -> Compra:
        """Mark a Compra as CANCELADA."""
        compra.estado = EstadoCompraChoices.CANCELADA
        compra.save(update_fields=["estado", "updated_at"])
        return compra

    def asignar_orden_pago(self, compra: Compra, orden_pago) -> Compra:
        """Assign an OrdenPago to a Compra (OneToOne)."""
        compra.orden_pago = orden_pago
        compra.save(update_fields=["orden_pago", "updated_at"])
        return compra
