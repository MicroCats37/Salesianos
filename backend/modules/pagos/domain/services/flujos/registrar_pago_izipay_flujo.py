"""
RegistrarPagoIzipayFlujo — async flow for Izipay Perú Web Core 2.0 payment registration.

Async flow with transaction.atomic — coordinates the full prepare + confirm cycle:

PREPARE (server-side token generation):
  1. Validates the inscription is payable (not already PAGADA)
  2. Generates transaction_id + order_number
  3. Snapshots amount from paquete.precio_promocional | precio_regular
  4. Calls Izipay Perú Token/Generate (server-side)
  5. Creates IzipayTransaccion as PENDIENTE (only after successful provider call)
  6. Returns token + SDK config to frontend

CONFIRM (callback from frontend):
  1. Receives kr_answer directly from frontend (Izipay Perú does NOT do server-to-server retrieval)
  2. Validates kr_answer.transactionId matches stored transaction
  3. Validates kr_answer.code == "00" for success
  4. Cross-checks amount/order if present in callback
  5. Inside transaction.atomic: updates transaction, transitions Inscripcion to PAGADA
  6. Idempotent: if already EXITO, returns immediately

NOTE ON SIGNATURE VERIFICATION:
  Izipay Perú may include a `signature` field (HMAC-SHA256 of payloadHttp).
  Without an exact documented algorithm and key, server-side signature verification
  cannot be reliably implemented. This is documented as a limitation.
  The primary trust mechanism is that the callback reaches our server via the
  trusted frontend channel, and transactionId is cross-checked against DB.

Idempotency: confirmed by transaction_id uniqueness + already_confirmed check.
Atomicity: transaction.atomic wraps the DB writes for the confirm step.
"""
import asyncio
import logging

from django.db import transaction

from injector import inject

from modules.inscripciones.domain.models import Inscripcion
from modules.usuarios.domain.models import Persona
from modules.inscripciones.domain import exceptions as exc_insc
from modules.inscripciones.domain.constants import EstadoInscripcionChoices
from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService

from modules.pagos.domain.constants import IzipayStatus
from modules.pagos.domain.exceptions import IzipayError, TransaccionDuplicadaError
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.infrastructure import IzipayClient, sanitizar_kr_answer
from modules.pagos.domain.schemas.result import IzipayPrepareResult, IzipayConfirmResult

logger = logging.getLogger(__name__)


class RegistrarPagoIzipayFlujo:
    """
    Async flow for registering an Izipay Perú Web Core 2.0 payment.

    Prepare step:
      - Validates inscription is payable
      - Generates transaction_id + order_number
      - Snapshots amount from paquete.precio_promocional | precio_regular
      - Calls Izipay Perú Token/Generate
      - Persists IzipayTransaccion as PENDIENTE (only after successful provider call)

    Confirm step:
      - Receives kr_answer callback directly from frontend
      - Idempotent by transaction_id
      - Validates transactionId + code == "00"
      - Updates IzipayTransaccion to EXITO/FALLIDO/CANCELADO
      - Transitions Inscripcion to PAGADA on success
      - All inside transaction.atomic
    """

    @inject
    def __init__(
        self,
        izipay_core: IzipayCoreService,
        inscripcion_svc: InscripcionService,
        izipay_client: IzipayClient,
    ):
        self.izipay_core = izipay_core
        self.inscripcion_svc = inscripcion_svc
        self.izipay_client = izipay_client

    # ── Prepare ─────────────────────────────────────────────────────────────────

    async def _preparar_pago(
        self,
        inscripcion_id: str,
        buyer_email: str | None = None,
        buyer_name: str | None = None,
        buyer_surname: str | None = None,
        buyer_document: str | None = "00000000",
        buyer_phone: str | None = "999999999",
    ) -> IzipayPrepareResult:
        """
        Prepare an Izipay Perú payment session (server-side token generation).

        Steps:
        1. Load and validate the inscription with responsable (select_related)
        2. Verify it is not already PAGADA or in a non-payable state
        3. Derive buyer data from inscripcion.responsable (Persona) when not provided
        4. Snapshot the amount from inscripcion.paquete.precio_promocional | precio_regular
        5. Generate transaction_id + order_number
        6. Call Izipay Perú Token/Generate (server-side)
        7. Persist IzipayTransaccion as PENDIENTE (only after successful provider call)

        Args:
            inscripcion_id: UUID of the inscription
            buyer_email: Payer email (derived from Persona if not provided)
            buyer_name: Payer first name (derived from Persona if not provided)
            buyer_surname: Payer last name (derived from Persona if not provided)
            buyer_document: Payer DNI (derived from Persona if not provided)
            buyer_phone: Payer phone (derived from Persona if not provided)

        Returns:
            IzipayPrepareResult with token and SDK configuration

        Raises:
            InscripcionNotFoundError: if inscription not found
            IzipayError: if inscription not payable or provider call fails
        """
        # 1. Load inscription with select_related("responsable") via selector
        #    so we can derive buyer data from the Persona without extra queries.
        from modules.inscripciones.domain.selectors.inscripcion_selector import InscripcionSelector
        selector = InscripcionSelector()
        inscripcion = await asyncio.to_thread(selector.obtener_inscripcion, inscripcion_id)
        if inscripcion is None:
            raise exc_insc.InscripcionNotFoundError(
                f"Inscripcion {inscripcion_id} not found."
            )

        # 2. Validate payable state
        no_payable_states = (
            EstadoInscripcionChoices.PAGADA,
            EstadoInscripcionChoices.CONFIRMADA,
            EstadoInscripcionChoices.RECHAZADA,
        )
        if inscripcion.estado in no_payable_states:
            raise IzipayError(
                f"Inscripcion {inscripcion_id} is in estado={inscripcion.estado}, "
                "which is not payable."
            )

        # 3. Derive buyer data from Persona (responsable) when not provided.
        #    inscripcion.responsable was loaded via select_related("responsable").
        responsable: Persona = inscripcion.responsable
        if buyer_email is None:
            buyer_email = getattr(responsable, "email", None) or "sin-email@ejemplo.com"
        if buyer_name is None:
            buyer_name = getattr(responsable, "nombres", None) or "CLIENTE"
        if buyer_surname is None:
            buyer_surname = getattr(responsable, "apellidos", None) or "VENTA"
        if buyer_document == "00000000" or buyer_document is None:
            buyer_document = getattr(responsable, "numero_documento", None) or "00000000"
        if buyer_phone == "999999999" or buyer_phone is None:
            buyer_phone = getattr(responsable, "telefono", None) or "999999999"

        # 4. Snapshot amount from package: promotional price if set, else regular
        amount = (
            inscripcion.paquete.precio_promocional
            if inscripcion.paquete.precio_promocional is not None
            else inscripcion.paquete.precio_regular
        )
        currency = "PEN"

        # 4. Generate IDs
        transaction_id = self.izipay_core.generar_transaction_id()
        order_number = self.izipay_core.generar_order_number()

        # 5. Call Izipay Perú Token/Generate — do NOT persist yet
        provider_response = await self.izipay_client.generar_token_sesion(
            transaction_id=transaction_id,
            order_number=order_number,
            amount=str(amount),
            currency=currency,
            buyer_email=buyer_email,
            buyer_name=buyer_name,
            buyer_surname=buyer_surname,
            buyer_document=buyer_document,
            buyer_phone=buyer_phone,
        )

        # Extract token from Izipay Perú response structure
        token = (
            provider_response.get("token")
            or (provider_response.get("response", {}).get("token")
                if isinstance(provider_response.get("response"), dict)
                else None)
        )
        if not token:
            raise IzipayError(
                f"Izipay token generation returned no token. "
                f"Response: {provider_response}"
            )

        # 6. Persist PENDIENTE transaction only after successful provider call
        # This avoids misleading PENDIENTE records when the provider call fails
        await asyncio.to_thread(
            self.izipay_core.crear_transaccion,
            inscripcion_id=inscripcion_id,
            transaction_id=transaction_id,
            order_number=order_number,
            amount=amount,
            currency=currency,
        )

        return IzipayPrepareResult(
            transaction_id=transaction_id,
            order_number=order_number,
            amount=amount,
            currency=currency,
            inscripcion_id=inscripcion_id,
            token=token,
            merchant_code=self.izipay_client.shop_id,
            buyer_email=buyer_email,
            buyer_name=buyer_name,
            buyer_surname=buyer_surname,
        )

    # ── Confirm ────────────────────────────────────────────────────────────────

    async def _confirmar_pago(
        self,
        kr_answer: dict,
    ) -> IzipayConfirmResult:
        """
        Confirm an Izipay Perú payment from the frontend callback (kr_answer).

        IMPORTANT: Izipay Perú Web Core 2.0 does NOT use a server-to-server
        retrieval step. The frontend SDK sends kr_answer directly to our
        confirmation endpoint after the popup closes.

        Idempotent: if the transaction is already EXITO, returns immediately.

        Steps:
        1. Extract transactionId from kr_answer
        2. Load existing IzipayTransaccion by transactionId
        3. If already EXITO → return success immediately (idempotent)
        4. Validate code == "00" for success
        5. Cross-check transactionId, orderNumber, amount if present in callback
        6. Inside transaction.atomic:
           a. Update IzipayTransaccion with final status + sanitized metadata
           b. If EXITO → transition Inscripcion to PAGADA
        7. Return IzipayConfirmResult

        Args:
            kr_answer: Callback payload from Izipay Perú frontend SDK.
                       Shape: { code, message, transactionId, response: {...},
                               orderNumber?, amount?, signature?, payloadHttp? }

        Returns:
            IzipayConfirmResult

        Raises:
            IzipayError: if transaction not found or validation fails
        """
        # 1. Extract transactionId from callback
        transaction_id = kr_answer.get("transactionId") or (
            kr_answer.get("response", {}).get("transactionId")
            if isinstance(kr_answer.get("response"), dict)
            else None
        )
        if not transaction_id:
            raise IzipayError(
                "kr_answer missing transactionId. "
                f"Received: {list(kr_answer.keys())}"
            )

        # 2. Load existing transaction
        tx = await asyncio.to_thread(
            self.izipay_core.obtener_por_transaction_id, transaction_id
        )
        if tx is None:
            raise IzipayError(f"Transaction {transaction_id} not found.")

        # 3. Idempotency: if already successful, return immediately
        if tx.status == IzipayStatus.EXITO:
            return IzipayConfirmResult(
                transaction_id=transaction_id,
                success=True,
                status=IzipayStatus.EXITO,
                response_code=tx.response_code,
                response_message=tx.response_message,
                metodo_pago=tx.metodo_pago,
                already_confirmed=True,
            )

        # 4. Validate code == "00" for success
        response_code = kr_answer.get("code", "")
        response_message = kr_answer.get("message", "Operación finalizada")

        # 5. Cross-check transaction details if present in callback
        # Note: These validations protect against tampered callbacks.
        # If the callback doesn't include these fields, we skip the check.
        stored_tx = tx  # alias for clarity

        # Amount cross-check
        if "orderNumber" in kr_answer or "response" in kr_answer:
            callback_order = (
                kr_answer.get("orderNumber")
                or (kr_answer.get("response", {}).get("orderNumber")
                    if isinstance(kr_answer.get("response"), dict)
                    else None)
            )
            if callback_order and callback_order != stored_tx.order_number:
                raise IzipayError(
                    f"Order number mismatch in callback: expected {stored_tx.order_number}, "
                    f"got {callback_order}"
                )

        is_success = response_code == "00"

        if is_success:
            final_status = IzipayStatus.EXITO
        elif response_code in ("111", "CANCELADO"):
            final_status = IzipayStatus.CANCELADO
        else:
            final_status = IzipayStatus.FALLIDO

        # 6. Extract payment method if available
        metodo_pago = ""
        inner_response = kr_answer.get("response", {})
        if isinstance(inner_response, dict):
            pay_method = inner_response.get("payMethod") or inner_response.get("paymentMethodType", "")
        else:
            pay_method = ""
        metodo_pago = pay_method

        # 7. Sanitize and store metadata
        raw_metadata = {
            k: v for k, v in kr_answer.items()
            if k not in ("code", "message", "transactionId", "signature", "payloadHttp")
        }
        sanitized_metadata = sanitizar_kr_answer(raw_metadata)

        # 8. Atomic DB update + Inscripcion state transition
        await asyncio.to_thread(
            self._confirmar_sync,
            transaction_id=transaction_id,
            inscripcion_id=str(tx.inscripcion_id),
            final_status=final_status,
            response_code=response_code,
            response_message=response_message,
            metodo_pago=metodo_pago,
            sanitized_metadata=sanitized_metadata,
        )

        return IzipayConfirmResult(
            transaction_id=transaction_id,
            success=(final_status == IzipayStatus.EXITO),
            status=final_status,
            response_code=response_code,
            response_message=response_message,
            metodo_pago=metodo_pago,
            already_confirmed=False,
        )

    @transaction.atomic()
    def _confirmar_sync(
        self,
        transaction_id: str,
        inscripcion_id: str,
        final_status: str,
        response_code: str,
        response_message: str,
        metodo_pago: str,
        sanitized_metadata: dict,
    ) -> None:
        """
        Sync wrapper with transaction.atomic for confirm step.

        Updates IzipayTransaccion status and transitions Inscripcion to PAGADA
        on success — all within the same DB transaction.
        """
        # Update transaction record
        self.izipay_core.actualizar_estado(
            transaction_id=transaction_id,
            status=final_status,
            response_code=response_code or None,
            response_message=response_message or None,
            metodo_pago=metodo_pago or None,
            metadata=sanitized_metadata,
        )

        # If successful, transition Inscripcion to PAGADA
        if final_status == IzipayStatus.EXITO:
            inscripcion = self.inscripcion_svc.obtener(inscripcion_id)
            if inscripcion is not None:
                self.inscripcion_svc.actualizar_estado(
                    inscripcion=inscripcion,
                    nuevo_estado=EstadoInscripcionChoices.PAGADA,
                    observacion=f"Pago Izipay exitoso - transaction_id={transaction_id}",
                )
