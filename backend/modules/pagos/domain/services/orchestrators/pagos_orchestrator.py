"""
PagosOrchestrator — async thin facade for Izipay Perú payment operations.

Orchestrator — async thin facade that delegates to flujos.
No business logic here — only delegation.
"""
import asyncio

from injector import inject

from modules.inscripciones.domain.selectors.inscripcion_selector import InscripcionSelector
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
from modules.pagos.domain.schemas.result import IzipayPrepareResult, IzipayConfirmResult


class PagosOrchestrator:
    """
    Thin async facade for Izipay Perú payment operations.

    All methods delegate to their respective flujos.
    Ownership validation is performed here before delegation.
    """

    @inject
    def __init__(
        self,
        registrar_flujo: RegistrarPagoIzipayFlujo,
        selector: InscripcionSelector,
    ):
        self.registrar_flujo = registrar_flujo
        self.selector = selector

    # ── Prepare ────────────────────────────────────────────────────────────────

    async def preparar_pago_izipay(
        self,
        inscripcion_id: str,
        buyer_email: str | None = None,
        buyer_name: str | None = None,
        buyer_surname: str | None = None,
        buyer_document: str | None = "00000000",
        buyer_phone: str | None = "999999999",
    ) -> IzipayPrepareResult:
        """
        Prepare an Izipay Perú payment session for an inscription.

        Calls Izipay Perú Token/Generate, persists a PENDIENTE transaction,
        and returns the token + SDK config for the frontend popup.

        Buyer fields are optional — when not provided the flujo derives them
        server-side from the authenticated user's Persona via the inscription's
        responsable relation.

        See RegistrarPagoIzipayFlujo._preparar_pago for full docs.
        """
        return await self.registrar_flujo._preparar_pago(
            inscripcion_id=inscripcion_id,
            buyer_email=buyer_email,
            buyer_name=buyer_name,
            buyer_surname=buyer_surname,
            buyer_document=buyer_document,
            buyer_phone=buyer_phone,
        )

    # ── Confirm ──────────────────────────────────────────────────────────────

    def _validar_propietario_transaccion_sync(
        self,
        transaction_id: str,
        authenticated_persona_id: str,
    ) -> None:
        """
        Sync helper to validate that a transaction belongs to the authenticated user.

        Raises BusinessError if the transaction is not found or belongs to a
        different user's inscription.
        """
        from core.exceptions import BusinessError

        tx = self.registrar_flujo.izipay_core.obtener_por_transaction_id(transaction_id)
        if tx is None:
            raise BusinessError(f"Transacción {transaction_id} no encontrada.")

        # Load the inscription to check ownership
        inscripcion = self.selector.obtener_inscripcion(str(tx.inscripcion_id))
        if inscripcion is None:
            raise BusinessError(f"Inscripción asociada a {transaction_id} no encontrada.")

        if str(inscripcion.responsable_id) != authenticated_persona_id:
            raise BusinessError("No tienes permiso para confirmar esta transacción.")

    async def confirmar_pago_izipay(
        self,
        kr_answer: dict,
        authenticated_persona_id: str,
    ) -> IzipayConfirmResult:
        """
        Confirm an Izipay Perú payment from the frontend callback.

        The frontend SDK sends kr_answer directly after the popup closes.
        This is NOT a server-to-server retrieval (Izipay Perú Web Core 2.0
        does not require one).

        Before delegating, validates that the transaction belongs to an
        inscription owned by the authenticated user.

        See RegistrarPagoIzipayFlujo._confirmar_pago for full docs.
        """
        # Extract transactionId for ownership validation
        transaction_id = kr_answer.get("transactionId") or (
            kr_answer.get("response", {}).get("transactionId")
            if isinstance(kr_answer.get("response"), dict)
            else None
        )

        if transaction_id:
            # Validate ownership before delegating to flujo
            await asyncio.to_thread(
                self._validar_propietario_transaccion_sync,
                transaction_id,
                authenticated_persona_id,
            )

        return await self.registrar_flujo._confirmar_pago(
            kr_answer=kr_answer,
        )
