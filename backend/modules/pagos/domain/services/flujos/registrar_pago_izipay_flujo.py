"""
RegistrarPagoIzipayFlujo — async flow for Izipay Perú Web Core 2.0 payment registration.

Async flow with transaction.atomic — coordinates the full prepare + confirm cycle:

PREPARE (server-side token generation):
  1. Validates the orden_pago is PENDIENTE
  2. Applies the attempt lifecycle: the active pending attempt of the order
     is reused while it is still usable; otherwise the superseded attempts
     are expired before a new one is created
  3. Generates transaction_id + order_number for a new attempt
  4. Calls Izipay Perú Token/Generate (server-side)
  5. Creates TransaccionPago as PENDIENTE (only after successful provider call)
  6. Returns token + SDK config to frontend

CONFIRM (provider confirmation, from either channel):
  1. Extracts the transactionId from the provider payload
  2. Loads the stored TransaccionPago
  3. Verifies the CHANNEL (signature and/or ownership) — nothing is mutated
     before this passes
  4. Cross-checks amount/order against the persisted transaction
  5. Inside transaction.atomic: updates transaction, transitions OrdenPago to PAGADA
  6. Idempotent: if already EXITO, the commercial settlement is re-driven
  7. After the payment is durably recorded, the commercial settlement of the
     linked purchase is driven from the backend (no second browser request)

TRUST MODEL (two channels, two rules):
  - NOTIFICACION (server to server): the merchant `keyHash` MUST be configured
    and the provider signature MUST verify. There is no fallback — an
    unverifiable notification is refused.
  - BROWSER (the frontend SDK relays the payload): the caller MUST be
    authenticated and MUST own the order. The provider signature is verified
    whenever the merchant key is configured; an invalid signature is always
    refused, and a successful payment without a verifiable signature is
    refused as well while the key is configured.

  While `IZIPAY_KEY_HASH` is NOT configured the provider cannot be
  authenticated at all: the browser relay is accepted (authenticated +
  owned + correlated) but it is NOT provider-verified, and the release must
  stay blocked until the merchant key is delivered. That residual gap is
  logged as a warning on every confirmation.

Idempotency: confirmed by transaction_id uniqueness + already_confirmed check.
Atomicity: transaction.atomic wraps the DB writes for the confirm step.

MONEY SAFETY: the payment rows are committed BEFORE the commercial settlement
runs, in a separate transaction. A settlement failure must never roll back the
record of a real charge — it is logged and reported as a pending activation,
and the idempotent settlement converges on a later confirmation.

IMPORTANT: This flow does NOT transition Inscripcion or create AsignacionCupo.
The commercial settlement is delegated to `salesianos_fest` through the
`IConfirmadorOrdenPagoService` port.
"""
import json
import logging
from datetime import timedelta

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from injector import inject

from modules.pagos.domain.constants import (
    CLAVE_TOKEN_SESION,
    CanalConfirmacionPago,
    EstadoVerificacionPago,
    INTENTO_REUTILIZABLE_MINUTOS,
    IzipayStatus,
    OrdenPagoStatus,
    SettlementStatus,
)
from modules.pagos.domain.exceptions import (
    IzipayError,
    OrdenPagoNoEncontradaError,
    PagoDatosInconsistentesError,
    PagoFirmaInvalidaError,
    PagoNoAutorizadoError,
    PagoNotificacionNoVerificableError,
    TransaccionPagoNoEncontradaError,
)
from modules.pagos.domain.ports import (
    IConfirmadorOrdenPagoService,
    IPropietarioOrdenPagoService,
)
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.infrastructure import (
    IzipayClient,
    VerificadorFirmaIzipay,
    sanitizar_kr_answer,
)
from modules.pagos.domain.schemas.result import IzipayPrepareResult, IzipayConfirmResult

logger = logging.getLogger(__name__)

# Provider code that is delivered without a signature (communication error).
CODIGO_COMUNICACION_ERROR = "021"


class RegistrarPagoIzipayFlujo:
    """
    Async flow for registering an Izipay Perú Web Core 2.0 payment.

    Prepare step:
      - Validates orden_pago is PENDIENTE
      - Generates transaction_id + order_number
      - Calls Izipay Perú Token/Generate
      - Persists TransaccionPago as PENDIENTE (only after successful provider call)

    Confirm step:
      - Receives kr_answer callback directly from frontend
      - Idempotent by transaction_id
      - Validates transactionId + code == "00"
      - Updates TransaccionPago to EXITO/FALLIDO/CANCELADO
      - Transitions OrdenPago to PAGADA on success
      - All inside transaction.atomic
      - Then drives the commercial settlement of the linked purchase from the
        backend, so the browser never confirms the purchase
    """

    @inject
    def __init__(
        self,
        izipay_core: IzipayCoreService,
        izipay_client: IzipayClient,
        confirmador_orden_pago: IConfirmadorOrdenPagoService,
        propietario_orden_pago: IPropietarioOrdenPagoService,
        verificador_firma: VerificadorFirmaIzipay,
        verificacion_pago: VerificacionPagoService,
    ):
        self.izipay_core = izipay_core
        self.izipay_client = izipay_client
        self.confirmador_orden_pago = confirmador_orden_pago
        self.propietario_orden_pago = propietario_orden_pago
        self.verificador_firma = verificador_firma
        self.verificacion_pago = verificacion_pago

    # ── Prepare ─────────────────────────────────────────────────────────────────

    async def _preparar_pago(
        self,
        orden_pago_id: str,
        buyer_email: str,
        buyer_name: str,
        buyer_surname: str,
        buyer_document: str = "00000000",
        buyer_phone: str = "999999999",
    ) -> IzipayPrepareResult:
        """
        Prepare an Izipay Perú payment session (server-side token generation).

        Steps:
        1. Load and validate the OrdenPago with estado=PENDIENTE
        2. Apply the attempt lifecycle: reuse the active pending attempt of
           the order when it is still usable, otherwise expire the
           superseded attempts
        3. Generate transaction_id + order_number for a new attempt
        4. Call Izipay Perú Token/Generate (server-side)
        5. Persist TransaccionPago as PENDIENTE (only after successful
           provider call)
        6. Return token + SDK config to frontend

        Args:
            orden_pago_id: UUID of the OrdenPago
            buyer_email: Payer email
            buyer_name: Payer first name
            buyer_surname: Payer last name
            buyer_document: Payer DNI
            buyer_phone: Payer phone

        Returns:
            IzipayPrepareResult with token and SDK configuration

        Raises:
            IzipayError: if orden_pago not found, not payable, or provider call fails
        """
        # 1. Load OrdenPago and validate it's PENDIENTE
        orden_pago = await sync_to_async(
            self.izipay_core.obtener_orden_pago_por_id
        )(orden_pago_id)
        if orden_pago is None:
            raise IzipayError(f"OrdenPago {orden_pago_id} not found.")

        if orden_pago.estado != OrdenPagoStatus.PENDIENTE:
            raise IzipayError(
                f"OrdenPago {orden_pago_id} is in estado={orden_pago.estado}, "
                "which is not payable."
            )

        # 2. Attempt lifecycle. A pending transaction is an ATTEMPT, not a
        #    charge: re-opening the checkout must not pile up attempts.
        intento = await sync_to_async(
            self.izipay_core.obtener_intento_pendiente
        )(orden_pago_id)

        if intento is not None and self._intento_es_reutilizable(intento, orden_pago):
            # The active attempt is reused: the SAME provider session — and
            # therefore the same transaction id — is handed back. No new
            # attempt is created and no second charge opportunity is opened.
            return self._resultado_intento_reutilizado(
                intento,
                orden_pago,
                buyer_email=buyer_email,
                buyer_name=buyer_name,
                buyer_surname=buyer_surname,
            )

        # 3. Generate IDs for a new attempt
        transaction_id = self.izipay_core.generar_transaction_id()
        order_number = self.izipay_core.generar_order_number()

        # 4. Call Izipay Perú Token/Generate — do NOT persist yet
        provider_response = await self.izipay_client.generar_token_sesion(
            transaction_id=transaction_id,
            order_number=order_number,
            amount=str(orden_pago.monto_total),
            currency=orden_pago.moneda,
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

        # 5. Close the superseded attempts BEFORE the new one is persisted,
        #    then persist the new attempt with its provider session token so
        #    it can be reused instead of opening a second session.
        await sync_to_async(
            self.izipay_core.expirar_intentos_pendientes
        )(orden_pago_id)
        await sync_to_async(
            self.izipay_core.crear_transaccion
        )(
            orden_pago_id=orden_pago_id,
            transaction_id=transaction_id,
            order_number=order_number,
            amount=orden_pago.monto_total,
            currency=orden_pago.moneda,
            metadata={CLAVE_TOKEN_SESION: token},
        )

        return IzipayPrepareResult(
            transaction_id=transaction_id,
            order_number=order_number,
            amount=orden_pago.monto_total,
            currency=orden_pago.moneda,
            orden_pago_id=orden_pago_id,
            token=token,
            merchant_code=self.izipay_client.shop_id,
            buyer_email=buyer_email,
            buyer_name=buyer_name,
            buyer_surname=buyer_surname,
        )

    def _intento_es_reutilizable(self, intento, orden_pago) -> bool:
        """
        Resolve whether an active attempt can be reused for this order.

        An attempt is reusable when it still matches the order (amount and
        currency) and its provider session is still fresh. A stale or
        mismatched attempt is superseded: it is expired and a new attempt is
        created instead.
        """
        if intento.amount != orden_pago.monto_total:
            return False
        if intento.currency != orden_pago.moneda:
            return False
        if not (intento.metadata or {}).get(CLAVE_TOKEN_SESION):
            return False

        ventana = timezone.now() - timedelta(
            minutes=INTENTO_REUTILIZABLE_MINUTOS
        )
        return intento.created_at >= ventana

    def _resultado_intento_reutilizado(
        self,
        intento,
        orden_pago,
        buyer_email: str,
        buyer_name: str,
        buyer_surname: str,
    ) -> IzipayPrepareResult:
        """
        Build the prepare result of a reused attempt.

        The provider session — and therefore the transaction id — is the one
        of the active attempt: the browser continues the SAME checkout
        instead of opening a second charge opportunity for the same order.
        """
        return IzipayPrepareResult(
            transaction_id=intento.transaction_id,
            order_number=intento.order_number,
            amount=orden_pago.monto_total,
            currency=orden_pago.moneda,
            orden_pago_id=str(orden_pago.id),
            token=intento.metadata[CLAVE_TOKEN_SESION],
            merchant_code=self.izipay_client.shop_id,
            buyer_email=buyer_email,
            buyer_name=buyer_name,
            buyer_surname=buyer_surname,
        )

    # ── Confirm ────────────────────────────────────────────────────────────────

    async def _confirmar_pago(
        self,
        kr_answer: dict,
        persona_id: str | None = None,
        es_admin: bool = False,
        canal: str = CanalConfirmacionPago.BROWSER,
        payload_http: str | None = None,
        signature: str | None = None,
    ) -> IzipayConfirmResult:
        """
        Confirm an Izipay Perú payment from a provider confirmation.

        The confirmation may arrive through two channels: the browser relay
        (the frontend SDK payload) or the server-to-server notification. Both
        go through the same persistence and the same settlement; only the
        trust rule differs (see `_verificar_canal`).

        Idempotent: if the transaction is already EXITO, the commercial
        settlement is re-driven (it is idempotent) instead of returning early.

        Steps:
        1. Extract transactionId from the provider payload
        2. Load existing TransaccionPago by transactionId
        3. Verify the channel (provider signature and/or order ownership)
        4. Cross-check amount/order against the persisted transaction
        5. If already EXITO → re-drive the commercial settlement (idempotent)
           and return success
        6. Validate code == "00" for success
        7. Inside transaction.atomic:
           a. Update TransaccionPago with final status + sanitized metadata
           b. If EXITO → transition OrdenPago to PAGADA
        8. After the payment is committed, drive the commercial settlement
        9. Return IzipayConfirmResult

        NOTE: This does NOT transition Inscripcion or create AsignacionCupo.
        The commercial settlement is delegated to `salesianos_fest` through the
        `IConfirmadorOrdenPagoService` port.

        Args:
            kr_answer: Provider payload. Shape: { code, message, transactionId,
                       response: {...}, orderNumber?, amount?, signature?,
                       payloadHttp? }
            persona_id: UUID of the authenticated person (browser channel).
            es_admin: True when the caller has administrative authority.
            canal: CanalConfirmacionPago.BROWSER or .NOTIFICACION.
            payload_http: Raw signed payload (notification channel).
            signature: Provider signature (notification channel).

        Returns:
            IzipayConfirmResult

        Raises:
            TransaccionPagoNoEncontradaError: the transaction does not exist.
            PagoDatosInconsistentesError: the payload contradicts the order.
            PagoNoAutorizadoError: the caller does not own the order.
            PagoFirmaInvalidaError: the provider signature does not verify.
            PagoNotificacionNoVerificableError: the notification is unverifiable.
        """
        # 1. Extract transactionId from the provider payload
        transaction_id = self.verificacion_pago.extraer_transaction_id(kr_answer)
        if not transaction_id:
            raise PagoDatosInconsistentesError()

        # 2. Load existing transaction
        tx = await sync_to_async(
            self.izipay_core.obtener_por_transaction_id
        )(transaction_id)
        if tx is None:
            raise TransaccionPagoNoEncontradaError()

        response_code = self._extraer_codigo(kr_answer)
        response_message = kr_answer.get("message") or "Operación finalizada"

        # 3. Verify the channel BEFORE any mutation. An untrusted payload
        #    must not change a single row.
        await self._verificar_canal(
            canal=canal,
            kr_answer=kr_answer,
            transaccion=tx,
            persona_id=persona_id,
            es_admin=es_admin,
            payload_http=payload_http,
            signature=signature,
            es_pago_exitoso=(response_code == "00"),
        )

        # 4. Cross-check the provider values against the persisted order
        self.verificacion_pago.validar_correlacion(kr_answer, tx)

        # 5. Idempotency: the payment is already successful. The commercial
        #    settlement is re-driven here — it is idempotent — so a retry
        #    after a partial failure converges instead of staying pending.
        if tx.status == IzipayStatus.EXITO:
            settlement_status = await self._liquidar_orden_pagada(
                str(tx.orden_pago_id)
            )
            return IzipayConfirmResult(
                transaction_id=transaction_id,
                success=True,
                status=IzipayStatus.EXITO,
                orden_pago_id=str(tx.orden_pago_id),
                response_code=tx.response_code,
                response_message=tx.response_message,
                metodo_pago=tx.metodo_pago,
                already_confirmed=True,
                settlement_status=settlement_status,
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

        # 8. Atomic DB update + OrdenPago state transition
        await sync_to_async(
            self._confirmar_sync
        )(
            transaction_id=transaction_id,
            orden_pago_id=str(tx.orden_pago_id),
            final_status=final_status,
            response_code=response_code,
            response_message=response_message,
            metodo_pago=metodo_pago,
            sanitized_metadata=sanitized_metadata,
        )

        # 9. The payment is durable at this point (its own committed
        #    transaction). The commercial settlement runs afterwards in its own
        #    transaction — a failure there never rolls back the payment.
        settlement_status = SettlementStatus.NOT_APPLICABLE
        if final_status == IzipayStatus.EXITO:
            settlement_status = await self._liquidar_orden_pagada(
                str(tx.orden_pago_id)
            )

        return IzipayConfirmResult(
            transaction_id=transaction_id,
            success=(final_status == IzipayStatus.EXITO),
            status=final_status,
            orden_pago_id=str(tx.orden_pago_id) if final_status == IzipayStatus.EXITO else None,
            response_code=response_code,
            response_message=response_message,
            metodo_pago=metodo_pago,
            already_confirmed=False,
            settlement_status=settlement_status,
        )

    async def _confirmar_notificacion(
        self,
        payload_http: str,
        signature: str,
        transaction_id: str | None = None,
    ) -> IzipayConfirmResult:
        """
        Confirm a payment from the server-to-server provider notification.

        The notification body carries the raw signed payload (`payloadHttp`)
        and its signature. The payload is parsed and processed exactly like a
        browser relay, but the trust comes from the merchant signature — the
        caller is the provider, not a session.

        Args:
            payload_http: The raw signed payload, exactly as received.
            signature: The provider signature (Base64).
            transaction_id: Transaction id delivered next to the payload.

        Returns:
            IzipayConfirmResult

        Raises:
            PagoNotificacionNoVerificableError: the merchant key is missing.
            PagoFirmaInvalidaError: the signature does not verify.
            PagoDatosInconsistentesError: the payload is not a valid JSON object.
        """
        if not payload_http or not signature:
            raise PagoNotificacionNoVerificableError()

        try:
            kr_answer = json.loads(payload_http)
        except (ValueError, TypeError):
            raise PagoDatosInconsistentesError()

        if not isinstance(kr_answer, dict):
            raise PagoDatosInconsistentesError()

        if not self.verificacion_pago.extraer_transaction_id(kr_answer) and transaction_id:
            kr_answer = {**kr_answer, "transactionId": transaction_id}

        return await self._confirmar_pago(
            kr_answer=kr_answer,
            canal=CanalConfirmacionPago.NOTIFICACION,
            payload_http=payload_http,
            signature=signature,
        )

    # ── Trust verification ────────────────────────────────────────────────────

    async def _verificar_canal(
        self,
        canal: str,
        kr_answer: dict,
        transaccion,
        persona_id: str | None,
        es_admin: bool,
        payload_http: str | None,
        signature: str | None,
        es_pago_exitoso: bool,
    ) -> None:
        """
        Verify that the channel that delivered the confirmation is trusted.

        Server-to-server notification (NO fallback):
          the merchant key must be configured AND the signature must verify.

        Browser relay:
          the caller must be authenticated and must own the order. The
          provider signature is verified whenever the merchant key is
          configured; an invalid signature is always refused and a successful
          payment without a verifiable signature is refused too.

        Raises:
            PagoNotificacionNoVerificableError: unverifiable notification.
            PagoFirmaInvalidaError: invalid (or missing) provider signature.
            PagoNoAutorizadoError: the caller does not own the order.
        """
        estado = self._estado_verificacion(kr_answer, payload_http, signature)

        if canal == CanalConfirmacionPago.NOTIFICACION:
            if not self.verificador_firma.disponible:
                logger.error(
                    "Izipay notification refused: IZIPAY_KEY_HASH is not configured"
                )
                raise PagoNotificacionNoVerificableError()
            if estado != EstadoVerificacionPago.FIRMADA:
                logger.warning("Izipay notification refused: invalid signature")
                raise PagoFirmaInvalidaError()
            return

        # ── Browser relay ──────────────────────────────────────────────────────
        if estado == EstadoVerificacionPago.NO_FIRMADA:
            logger.warning(
                "Izipay relay refused: the provider signature does not verify"
            )
            raise PagoFirmaInvalidaError()

        if (
            estado == EstadoVerificacionPago.NO_VERIFICABLE
            and self.verificador_firma.disponible
            and es_pago_exitoso
            and self._extraer_codigo(kr_answer) != CODIGO_COMUNICACION_ERROR
        ):
            logger.warning(
                "Izipay relay refused: a successful payment arrived without a "
                "verifiable provider signature"
            )
            raise PagoFirmaInvalidaError()

        if estado == EstadoVerificacionPago.NO_VERIFICABLE:
            logger.warning(
                "Izipay relay accepted WITHOUT provider verification: "
                "IZIPAY_KEY_HASH is not configured. The release must stay "
                "blocked until the merchant key is delivered."
            )

        if es_admin:
            return

        if not persona_id:
            raise PagoNoAutorizadoError()

        es_propietario = await sync_to_async(
            self.propietario_orden_pago.es_propietario
        )(str(transaccion.orden_pago_id), persona_id)
        if not es_propietario:
            raise PagoNoAutorizadoError()

    def _estado_verificacion(
        self,
        kr_answer: dict,
        payload_http: str | None,
        signature: str | None,
    ) -> str:
        """
        Resolve the verification state of the provider payload.

        Returns one of EstadoVerificacionPago.
        """
        payload = payload_http
        firma = signature

        if isinstance(kr_answer, dict):
            if not payload:
                payload = kr_answer.get("payloadHttp")
            if not firma:
                firma = kr_answer.get("signature")

        if not payload or not firma:
            return EstadoVerificacionPago.NO_VERIFICABLE

        if not self.verificador_firma.disponible:
            # Without the merchant key the provider cannot be authenticated.
            return EstadoVerificacionPago.NO_VERIFICABLE

        if self.verificador_firma.verificar(payload, firma):
            return EstadoVerificacionPago.FIRMADA

        return EstadoVerificacionPago.NO_FIRMADA

    def _extraer_codigo(self, kr_answer: dict) -> str:
        """Return the provider response code of the payload."""
        if not isinstance(kr_answer, dict):
            return ""
        codigo = kr_answer.get("code")
        if codigo is None:
            return ""
        return str(codigo)

    # ── Protected reads ───────────────────────────────────────────────────────

    async def _obtener_transaccion(
        self,
        transaction_id: str,
        persona_id: str | None,
        es_admin: bool,
    ):
        """
        Load a transaction, enforcing that the caller owns its order.

        Raises:
            TransaccionPagoNoEncontradaError: the transaction does not exist.
            PagoNoAutorizadoError: the caller does not own the order.
        """
        tx = await sync_to_async(
            self.izipay_core.obtener_por_transaction_id
        )(transaction_id)
        if tx is None:
            raise TransaccionPagoNoEncontradaError()

        await self._verificar_propiedad(tx, persona_id, es_admin)
        return tx

    async def _obtener_orden(self, orden_id: str, persona_id: str | None, es_admin: bool):
        """
        Load a payment order, enforcing that the caller owns it.

        Raises:
            OrdenPagoNoEncontradaError: the order does not exist.
            PagoNoAutorizadoError: the caller does not own the order.
        """
        orden = await sync_to_async(
            self.izipay_core.obtener_orden_pago_por_id
        )(orden_id)
        if orden is None:
            raise OrdenPagoNoEncontradaError()

        await self._verificar_propiedad(orden, persona_id, es_admin)
        return orden

    async def _verificar_propiedad(self, recurso, persona_id: str | None, es_admin: bool) -> None:
        """Raise when the caller may not read the given payment resource."""
        if es_admin:
            return
        if not persona_id:
            raise PagoNoAutorizadoError()

        orden_pago_id = str(
            getattr(recurso, "orden_pago_id", None) or getattr(recurso, "id", "")
        )
        es_propietario = await sync_to_async(
            self.propietario_orden_pago.es_propietario
        )(orden_pago_id, persona_id)
        if not es_propietario:
            raise PagoNoAutorizadoError()

    async def _liquidar_orden_pagada(self, orden_pago_id: str) -> str:
        """
        Drive the commercial settlement of a paid order.

        The payment is already committed when this runs — the money is real, so
        a settlement failure must never undo it. Failures are logged and
        reported as PENDING; the settlement is idempotent, so a later
        confirmation converges it.

        Returns:
            SettlementStatus.SETTLED when the purchase was settled,
            SettlementStatus.PENDING when it was not.
        """
        try:
            resultado = await self.confirmador_orden_pago.confirmar_orden_pagada(
                orden_pago_id
            )
        except Exception:
            logger.exception(
                "Commercial settlement failed for orden_pago %s — "
                "the payment stays recorded and the activation stays pending",
                orden_pago_id,
            )
            return SettlementStatus.PENDING

        if not resultado.settled:
            logger.warning(
                "orden_pago %s has no purchase to settle — activation pending",
                orden_pago_id,
            )
            return SettlementStatus.PENDING

        return SettlementStatus.SETTLED

    @transaction.atomic()
    def _confirmar_sync(
        self,
        transaction_id: str,
        orden_pago_id: str,
        final_status: str,
        response_code: str,
        response_message: str,
        metodo_pago: str,
        sanitized_metadata: dict,
    ) -> None:
        """
        Sync wrapper with transaction.atomic for confirm step.

        Updates TransaccionPago status and transitions OrdenPago to PAGADA
        on success — all within the same DB transaction.

        NOTE: Does NOT transition Inscripcion or create AsignacionCupo.
        The commercial settlement is driven by the flow right after this
        transaction commits, so a settlement failure cannot roll back the
        payment.
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

        # If successful, transition OrdenPago to PAGADA
        if final_status == IzipayStatus.EXITO:
            orden_pago = self.izipay_core.obtener_orden_pago_por_id(orden_pago_id)
            if orden_pago is not None:
                self.izipay_core.marcar_orden_pagada(orden_pago)
