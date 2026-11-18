"""
IzipayCoreService — sync core operations for Izipay transactions and payment orders.

Core service — no transaction.atomic own, no async.
Operations that touch the DB are here; atomicity is provided by the caller flujo.
"""
import hashlib
import secrets
import time
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from injector import inject

from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.constants import (
    CLAVE_TOKEN_SESION,
    IzipayStatus,
    OrdenPagoStatus,
    METADATA_ALLOWED_KEYS,
    METADATA_FORBIDDEN_KEYS,
)
from modules.pagos.domain.exceptions import TransaccionDuplicadaError
from modules.pagos.domain.schemas.result import OrdenConMultiplesIntentosVivos

# ── Identity format ───────────────────────────────────────────────────────────
#
# The provider identity of an attempt is built from three parts:
#
#   <scope>   a stable digest of the payment order → the identity of an
#             attempt is recognizable as the one of its order.
#   <ordinal> the position of the attempt inside its order → two attempts of
#             the same order can NEVER share an identity.
#   <nonce>   random digits → two DIFFERENT orders can practically never
#             collide.
#
# All of them are digits: the provider keeps receiving the same shape it has
# always received (14 digits for the transaction id, 10 for the order number).
DIGITOS_ALCANCE = 6
DIGITOS_ORDINAL = 4
DIGITOS_NONCE = 4


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

    def generar_transaction_id(
        self,
        orden_pago_id: str | None = None,
        ordinal: int | None = None,
    ) -> str:
        """
        Generate the provider transaction id of an attempt.

        The identity is scoped to the payment order and collision-safe: the
        scope is a stable digest of the order, the ordinal is the position of
        the attempt inside that order and the nonce is random. Two attempts of
        the same order can never share an id; two different orders collide
        only by chance.

        Format: <scope 6><ordinal 4><nonce 4> = 14 digits.
        This is the idempotency key sent to Izipay.
        """
        return (
            self._alcance(orden_pago_id)
            + self._ordinal(ordinal)
            + self._nonce(DIGITOS_NONCE)
        )

    def generar_order_number(
        self,
        orden_pago_id: str | None = None,
        ordinal: int | None = None,
    ) -> str:
        """
        Generate the provider order reference of an attempt.

        It is deterministic: the same order and the same attempt always
        produce the same reference, so the reconciliation with the provider is
        possible without storing anything else.

        Format: <scope 6><ordinal 4> = 10 digits.
        Separate from transaction_id — used for Izipay's order tracking.
        """
        return self._alcance(orden_pago_id) + self._ordinal(ordinal)

    def generar_numero_orden(self) -> str:
        """
        Generate a human-readable order number for OrdenPago.

        Format: ORD + 6-digit millisecond + 6 random digits.
        The random part keeps two orders created in the same millisecond
        apart — the number is unique.
        """
        marca = f"{int(time.time() * 1000) % 1_000_000:06d}"
        return f"ORD{marca}{self._nonce(6)}"

    def _alcance(self, orden_pago_id: str | None) -> str:
        """
        Return the order scope of an identity.

        It is a stable digest of the order id (the same digest in every
        process), so an attempt identity is recognizable as the one of its
        order. Without an order the scope is random: the identity still has
        to be unique.
        """
        if not orden_pago_id:
            return self._nonce(DIGITOS_ALCANCE)
        digest = hashlib.sha256(str(orden_pago_id).encode("utf-8")).hexdigest()
        return f"{int(digest[:12], 16) % (10 ** DIGITOS_ALCANCE):0{DIGITOS_ALCANCE}d}"

    def _ordinal(self, ordinal: int | None) -> str:
        """
        Return the position of the attempt inside its order.

        Without an order the current millisecond is used: the identity still
        changes over time.
        """
        if ordinal is None:
            ordinal = int(time.time() * 1000) % (10 ** DIGITOS_ORDINAL)
        return f"{ordinal % (10 ** DIGITOS_ORDINAL):0{DIGITOS_ORDINAL}d}"

    def _nonce(self, digitos: int) -> str:
        """Return random digits — the part that makes an identity unique."""
        return "".join(secrets.choice("0123456789") for _ in range(digitos))

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
        session was opened for the order. Every checkout opening creates its
        own attempt — the previous one is retired — and `metadata` carries
        the provider session of THIS attempt.

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

    def bloquear_orden_pago(self, orden_pago_id: str) -> OrdenPago | None:
        """
        Load the order and lock its row until the transaction commits.

        The lock serializes the preparation of an order: two preparations of
        the same order cannot create two live attempts at the same time.
        """
        return (
            OrdenPago.objects
            .filter(id=orden_pago_id)
            .select_for_update()
            .first()
        )

    def contar_intentos(self, orden_pago_id: str) -> int:
        """
        Count every attempt an order has.

        The attempts are never deleted — they are the audit trail — so the
        count is the position of the next attempt of that order.
        """
        return TransaccionPago.objects.filter(orden_pago_id=orden_pago_id).count()

    def guardar_token_sesion(self, transaction_id: str, token: str) -> bool:
        """
        Persist the provider session on a LIVE attempt.

        The row is locked while it is read and written, so an attempt that is
        retired meanwhile is never given a session.

        Returns False when the attempt is no longer live: it was superseded
        while its provider session was being opened, and that session must
        NOT be handed to the browser.
        """
        intento = (
            TransaccionPago.objects
            .select_for_update()
            .filter(
                transaction_id=transaction_id,
                status=IzipayStatus.PENDIENTE,
            )
            .first()
        )
        if intento is None:
            return False

        metadata = dict(intento.metadata or {})
        metadata[CLAVE_TOKEN_SESION] = token
        intento.metadata = metadata
        intento.save(update_fields=["metadata", "updated_at"])
        return True

    def marcar_intento_fallido(
        self,
        transaction_id: str,
        response_message: str | None = None,
    ) -> None:
        """
        Mark a live attempt as FALLIDO when its provider session never opened.

        The attempt is kept as history: it is not a charge and it must not
        stay as the live attempt of its order.
        """
        TransaccionPago.objects.filter(
            transaction_id=transaction_id,
            status=IzipayStatus.PENDIENTE,
        ).update(
            status=IzipayStatus.FALLIDO,
            response_message=response_message,
            updated_at=timezone.now(),
        )

    # ── Deployment preflight ───────────────────────────────────────────────────

    def resumen_intentos_vivos(self) -> dict[str, int]:
        """
        Return the live-attempt counters of the deployment preflight.

        A live attempt is a PENDIENTE TransaccionPago. The counters describe
        the data as it is — they never change it.
        """
        vivos = TransaccionPago.objects.filter(status=IzipayStatus.PENDIENTE)
        return {
            "intentos_vivos": vivos.count(),
            "ordenes_con_intento_vivo": vivos.values("orden_pago_id").distinct().count(),
            "ordenes_inseguras": self.contar_ordenes_con_multiples_intentos_vivos(),
        }

    def contar_ordenes_con_multiples_intentos_vivos(self) -> int:
        """
        Count the orders that carry MORE THAN ONE live attempt.

        These orders are exactly the ones that make the one-live-attempt
        guard uninstallable: the unique partial index on the order of the
        PENDIENTE attempts would fail on them.
        """
        return (
            TransaccionPago.objects
            .filter(status=IzipayStatus.PENDIENTE)
            .values("orden_pago_id")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .count()
        )

    def ordenes_con_multiples_intentos_vivos(self) -> list[OrdenConMultiplesIntentosVivos]:
        """
        Return the orders that carry MORE THAN ONE live attempt.

        The report is READ-ONLY: no attempt is retired, cancelled or deleted —
        a payment attempt is an audit record and it may be money in flight.
        The operator resolves the unsafe rows explicitly (see
        `backend/modules/pagos/docs/despliegue_intento_unico.md`).
        """
        conteo = list(
            TransaccionPago.objects
            .filter(status=IzipayStatus.PENDIENTE)
            .values("orden_pago_id")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )
        if not conteo:
            return []

        ordenes = {
            str(orden_id): numero
            for orden_id, numero in OrdenPago.objects.filter(
                id__in=[fila["orden_pago_id"] for fila in conteo]
            ).values_list("id", "numero")
        }

        vivos = TransaccionPago.objects.filter(
            status=IzipayStatus.PENDIENTE,
            orden_pago_id__in=[fila["orden_pago_id"] for fila in conteo],
        ).order_by("orden_pago_id", "created_at").values_list(
            "orden_pago_id", "transaction_id"
        )

        por_orden: dict[str, list[str]] = {}
        for orden_pago_id, transaction_id in vivos:
            por_orden.setdefault(str(orden_pago_id), []).append(transaction_id)

        return [
            OrdenConMultiplesIntentosVivos(
                orden_pago_id=str(fila["orden_pago_id"]),
                numero_orden=ordenes.get(str(fila["orden_pago_id"]), ""),
                intentos_vivos=fila["total"],
                transaction_ids=por_orden.get(str(fila["orden_pago_id"]), []),
            )
            for fila in sorted(conteo, key=lambda fila: str(fila["orden_pago_id"]))
        ]
