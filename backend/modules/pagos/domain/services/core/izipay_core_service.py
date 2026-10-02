"""
IzipayCoreService — sync core operations for Izipay transactions.

Core service — no transaction.atomic own, no async.
Operations that touch the DB are here; atomicity is provided by the caller flujo.
"""
import time

from injector import inject

from modules.pagos.domain.models import IzipayTransaccion
from modules.pagos.domain.constants import IzipayStatus
from modules.pagos.domain.exceptions import TransaccionDuplicadaError


class IzipayCoreService:
    """
    Core sync service for Izipay transaction operations.

    Handles:
    - transaction_id / order_number generation
    - IzipayTransaccion CRUD
    - Idempotency checks
    """

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
        return str(int(time.time() * 1000000))[:10]

    # ── Transaction operations ───────────────────────────────────────────────────

    def crear_transaccion(
        self,
        inscripcion_id: str,
        transaction_id: str,
        order_number: str,
        amount: str | float | int,
        currency: str = "PEN",
    ) -> IzipayTransaccion:
        """
        Create a new PENDIENTE IzipayTransaccion record.

        Raises:
            TransaccionDuplicadaError: if transaction_id already exists.
        """
        if IzipayTransaccion.objects.filter(transaction_id=transaction_id).exists():
            raise TransaccionDuplicadaError(
                f"Transaction {transaction_id} already exists."
            )

        return IzipayTransaccion.objects.create(
            inscripcion_id=inscripcion_id,
            transaction_id=transaction_id,
            order_number=order_number,
            amount=amount,
            currency=currency,
            status=IzipayStatus.PENDIENTE,
        )

    def obtener_por_transaction_id(
        self, transaction_id: str
    ) -> IzipayTransaccion | None:
        """Get a transaction by its transaction_id."""
        return IzipayTransaccion.objects.filter(
            transaction_id=transaction_id
        ).select_related("inscripcion").first()

    def actualizar_estado(
        self,
        transaction_id: str,
        status: str,
        response_code: str | None = None,
        response_message: str | None = None,
        metodo_pago: str | None = None,
        metadata: dict | None = None,
    ) -> IzipayTransaccion | None:
        """
        Update the status and response fields of an existing transaction.

        Returns the updated instance or None if not found.
        """
        # Guard against metadata=None: JSONField with null=False cannot store None.
        # Use empty dict as safe fallback when metadata is omitted.
        safe_metadata: dict = metadata if metadata is not None else {}
        updated = IzipayTransaccion.objects.filter(
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
        return IzipayTransaccion.objects.filter(
            transaction_id=transaction_id
        ).exists()
