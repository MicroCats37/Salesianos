"""
IzipayCoreService — sync core operations for Izipay transactions and payment orders.

Core service — no transaction.atomic own, no async.
Operations that touch the DB are here; atomicity is provided by the caller flujo.
"""
import time
from datetime import timedelta

from django.utils import timezone
from injector import inject

from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.constants import (
    IzipayStatus,
    OrdenPagoStatus,
    METADATA_ALLOWED_KEYS,
    METADATA_FORBIDDEN_KEYS,
)
from modules.pagos.domain.exceptions import TransaccionDuplicadaError


def sanitize_metadata(metadata: dict | None) -> dict:
    """
    Sanitize metadata dict to enforce the OrdenPago metadata contract.

    - Strips any key NOT in METADATA_ALLOWED_KEYS.
    - Strips any key in METADATA_FORBIDDEN_KEYS (defense in depth).
    - Returns a safe clean dict suitable for storing in JSONField.

    This is audit/display context only — it NEVER drives authorization
    or replaces real FK relationships.
    """
    if metadata is None:
        return {}
    allowed = METADATA_ALLOWED_KEYS
    forbidden = METADATA_FORBIDDEN_KEYS
    return {
        k: v
        for k, v in metadata.items()
        if k in allowed and k not in forbidden
    }


class IzipayCoreService:
    """
    Core sync service for Izipay transaction and payment order operations.

    Handles:
    - transaction_id / order_number generation
    - OrdenPago CRUD
    - TransaccionPago CRUD
    - Idempotency checks
    """

    # Default order validity: 2 hours
    ORDEN_VIGENCIA_Horas = 2

    @inject
    def __init__(self):
        pass

    # ── ID generation ───────────────────────────────────────────────────────────

    def generar_transaction_id(self) -> str:
        """
        Generate a 14-digit unique transaction ID based on current timestamp.

        Format: str(int(time.time() * 1000)).rjust(14, "0")[:14]
        This is the idempotency key sent to Izipay.
        """
        return str(int(time.time() * 1000)).rjust(14, "0")[:14]

    def generar_order_number(self) -> str:
        """
        Generate a 10-digit order number based on microtimestamp.

        Format: str(int(time.time() * 1000000))[:10]
        Separate from transaction_id — used for Izipay's order tracking.
        """
        return str(time.time_ns())[-10:]

    def generar_numero_orden(self) -> str:
        """
        Generate a human-readable order number for OrdenPago.

        Format: ORD + 10-digit microtimestamp.
        """
        return f"ORD{self.generar_order_number()}"

    # ── OrdenPago operations ─────────────────────────────────────────────────────

    def crear_orden_pago(
        self,
        numero: str,
        monto_total: str | float | int,
        moneda: str = "PEN",
        descripcion: str = "",
        referencia_externa: str | None = None,
        metadata: dict | None = None,
    ) -> OrdenPago:
        """
        Create a new PENDIENTE OrdenPago record.

        Args:
            numero: Unique order number.
            monto_total: Total amount.
            moneda: Currency code (default PEN).
            descripcion: Audit/display description snapshot.
            referencia_externa: Business reference snapshot.
            metadata: Audit/display context dict. Keys are sanitized against
                METADATA_ALLOWED_KEYS — unauthorized keys are stripped.
                Must NEVER be used for authorization or as a substitute for
                real FK relationships.

        Raises:
            Exception: if numero already exists (unique constraint).
        """
        safe_metadata = sanitize_metadata(metadata)
        return OrdenPago.objects.create(
            numero=numero,
            monto_total=monto_total,
            moneda=moneda,
            estado=OrdenPagoStatus.PENDIENTE,
            expires_at=timezone.now() + timedelta(hours=self.ORDEN_VIGENCIA_Horas),
            descripcion=descripcion,
            referencia_externa=referencia_externa,
            metadata=safe_metadata,
        )

    def obtener_orden_pago_por_numero(self, numero: str) -> OrdenPago | None:
        """Get an OrdenPago by its numero."""
        return OrdenPago.objects.filter(numero=numero).first()

    def obtener_orden_pago_por_id(self, orden_pago_id: str) -> OrdenPago | None:
        """Get an OrdenPago by its ID."""
        return OrdenPago.objects.filter(id=orden_pago_id).first()

    def marcar_orden_pagada(self, orden_pago: OrdenPago) -> OrdenPago:
        """Mark an OrdenPago as PAGADA and record pagada_en timestamp."""
        orden_pago.estado = OrdenPagoStatus.PAGADA
        orden_pago.pagada_en = timezone.now()
        orden_pago.save(update_fields=["estado", "pagada_en", "updated_at"])
        return orden_pago

    def cancelar_orden_pago(self, orden_pago: OrdenPago) -> OrdenPago:
        """Mark an OrdenPago as CANCELADA."""
        orden_pago.estado = OrdenPagoStatus.CANCELADA
        orden_pago.save(update_fields=["estado", "updated_at"])
        return orden_pago

    # ── TransaccionPago operations ───────────────────────────────────────────────

    def crear_transaccion(
        self,
        orden_pago_id: str,
        transaction_id: str,
        order_number: str,
        amount: str | float | int,
        currency: str = "PEN",
        metadata: dict | None = None,
    ) -> TransaccionPago:
        """
        Create a new PENDIENTE TransaccionPago record linked to an OrdenPago.

        The record is an ATTEMPT, not a charge: it exists because a provider
        session was opened for the order. `metadata` may carry the provider
        session token so the attempt can be reused instead of opening a
        second session for the same order.

        Raises:
            TransaccionDuplicadaError: if transaction_id already exists.
        """
        if TransaccionPago.objects.filter(transaction_id=transaction_id).exists():
            raise TransaccionDuplicadaError(
                f"Transaction {transaction_id} already exists."
            )

        return TransaccionPago.objects.create(
            orden_pago_id=orden_pago_id,
            transaction_id=transaction_id,
            order_number=order_number,
            amount=amount,
            currency=currency,
            status=IzipayStatus.PENDIENTE,
            metadata=metadata if metadata is not None else {},
        )

    def obtener_por_transaction_id(
        self, transaction_id: str
    ) -> TransaccionPago | None:
        """Get a transaction by its transaction_id."""
        return TransaccionPago.objects.filter(
            transaction_id=transaction_id
        ).select_related("orden_pago").first()

    def actualizar_estado(
        self,
        transaction_id: str,
        status: str,
        response_code: str | None = None,
        response_message: str | None = None,
        metodo_pago: str | None = None,
        metadata: dict | None = None,
    ) -> TransaccionPago | None:
        """
        Update the status and response fields of an existing transaction.

        Returns the updated instance or None if not found.
        """
        # Guard against metadata=None: JSONField with null=False cannot store None.
        # Use empty dict as safe fallback when metadata is omitted.
        safe_metadata: dict = metadata if metadata is not None else {}
        updated = TransaccionPago.objects.filter(
            transaction_id=transaction_id
        ).update(
            status=status,
            response_code=response_code,
            response_message=response_message,
            metodo_pago=metodo_pago,
            metadata=safe_metadata,
        )
        if updated == 0:
            return None
        return self.obtener_por_transaction_id(transaction_id)

    def es_duplicada(self, transaction_id: str) -> bool:
        """Check whether a transaction with this transaction_id already exists."""
        return TransaccionPago.objects.filter(
            transaction_id=transaction_id
        ).exists()

    # ── Payment attempt lifecycle ───────────────────────────────────────────────

    def obtener_intento_pendiente(self, orden_pago_id: str) -> TransaccionPago | None:
        """
        Return the active attempt of an order — its newest PENDIENTE transaction.

        A PENDIENTE transaction is an attempt, not a charge. There is at most
        one active attempt per order: the superseded ones are expired.
        """
        return (
            TransaccionPago.objects
            .filter(
                orden_pago_id=orden_pago_id,
                status=IzipayStatus.PENDIENTE,
            )
            .order_by("-created_at")
            .first()
        )

    def obtener_intento_exitoso(self, orden_pago_id: str) -> TransaccionPago | None:
        """
        Return the successful attempt of an order — the payment evidence.

        An order can carry several attempts (the user re-opened the
        checkout). Only the EXITO one proves that the money arrived, so it is
        the one a reconciliation must select; the older pending attempts are
        tolerated, not mistaken for the payment.
        """
        return (
            TransaccionPago.objects
            .filter(
                orden_pago_id=orden_pago_id,
                status=IzipayStatus.EXITO,
            )
            .order_by("-created_at")
            .first()
        )

    def expirar_intentos_pendientes(self, orden_pago_id: str) -> int:
        """
        Close every pending attempt of an order. Returns the number closed.

        Used to keep the attempt lifecycle bounded: an order never keeps
        more than one open attempt, and the superseded ones are explicitly
        closed instead of piling up as if they were charges.
        """
        return TransaccionPago.objects.filter(
            orden_pago_id=orden_pago_id,
            status=IzipayStatus.PENDIENTE,
        ).update(
            status=IzipayStatus.CANCELADO,
            updated_at=timezone.now(),
        )
