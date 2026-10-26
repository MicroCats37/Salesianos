"""
PagosOrchestrator — async thin facade for Izipay Perú payment operations.

Orchestrator — async thin facade that delegates to flujos.
No business logic here — only delegation.

Note: This orchestrator handles generic payment operations (OrdenPago, TransaccionPago).
Business-state transitions (Inscripcion, AsignacionCupo) are handled by
salesianos_fest.CompraOrchestrator after payment confirmation.
"""

from injector import inject

from modules.pagos.domain.constants import CanalConfirmacionPago
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
from modules.pagos.domain.schemas.result import IzipayPrepareResult, IzipayConfirmResult


class PagosOrchestrator:
    """
    Thin async facade for Izipay Perú payment operations.

    All methods delegate to their respective flujos.
    Ownership and signature validation live in the flow, so every entry
    point (browser relay and provider notification) is protected by the
    same rules.
    """

    @inject
    def __init__(
        self,
        registrar_flujo: RegistrarPagoIzipayFlujo,
    ):
        self.registrar_flujo = registrar_flujo

    # ── Prepare ────────────────────────────────────────────────────────────────

    async def preparar_pago_izipay(
        self,
        orden_pago_id: str,
        buyer_email: str,
        buyer_name: str,
        buyer_surname: str,
        buyer_document: str = "00000000",
        buyer_phone: str = "999999999",
    ) -> IzipayPrepareResult:
        """
        Prepare an Izipay Perú payment session for an OrdenPago.

        Calls Izipay Perú Token/Generate, persists a PENDIENTE transaction,
        and returns the token + SDK config for the frontend popup.

        See RegistrarPagoIzipayFlujo._preparar_pago for full docs.
        """
        return await self.registrar_flujo._preparar_pago(
            orden_pago_id=orden_pago_id,
            buyer_email=buyer_email,
            buyer_name=buyer_name,
            buyer_surname=buyer_surname,
            buyer_document=buyer_document,
            buyer_phone=buyer_phone,
        )

    # ── Confirm ──────────────────────────────────────────────────────────────

    async def confirmar_pago_izipay(
        self,
        kr_answer: dict,
        persona_id: str | None = None,
        es_admin: bool = False,
    ) -> IzipayConfirmResult:
        """
        Confirm an Izipay Perú payment from the browser relay.

        The frontend SDK sends the provider payload after the popup closes.
        The caller must be authenticated and must own the order; the flow
        enforces both and refuses anything that contradicts the persisted
        transaction.

        See RegistrarPagoIzipayFlujo._confirmar_pago for full docs.
        """
        return await self.registrar_flujo._confirmar_pago(
            kr_answer=kr_answer,
            persona_id=persona_id,
            es_admin=es_admin,
            canal=CanalConfirmacionPago.BROWSER,
        )

    async def confirmar_pago_por_notificacion(
        self,
        payload_http: str,
        signature: str,
        transaction_id: str | None = None,
    ) -> IzipayConfirmResult:
        """
        Confirm an Izipay Perú payment from the server-to-server notification.

        The provider calls us directly with the raw signed payload. Its
        authority comes from the merchant signature — there is no session
        and no fallback.

        See RegistrarPagoIzipayFlujo._confirmar_notificacion for full docs.
        """
        return await self.registrar_flujo._confirmar_notificacion(
            payload_http=payload_http,
            signature=signature,
            transaction_id=transaction_id,
        )

    async def obtener_transaccion(
        self,
        transaction_id: str,
        persona_id: str | None = None,
        es_admin: bool = False,
    ):
        """
        Get a transaction, restricted to the owner of its order.

        See RegistrarPagoIzipayFlujo._obtener_transaccion for full docs.
        """
        return await self.registrar_flujo._obtener_transaccion(
            transaction_id=transaction_id,
            persona_id=persona_id,
            es_admin=es_admin,
        )

    async def obtener_orden(
        self,
        orden_id: str,
        persona_id: str | None = None,
        es_admin: bool = False,
    ):
        """
        Get a payment order, restricted to its owner.

        See RegistrarPagoIzipayFlujo._obtener_orden for full docs.
        """
        return await self.registrar_flujo._obtener_orden(
            orden_id=orden_id,
            persona_id=persona_id,
            es_admin=es_admin,
        )
