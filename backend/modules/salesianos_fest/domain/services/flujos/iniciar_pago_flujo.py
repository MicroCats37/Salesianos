"""
IniciarPagoFlujo — async flow for initiating Izipay payment for a Compra.

Flow:
1. Load commerce.Compra and validate it is PENDIENTE
2. Load CompraInscripcion to get Inscripcion.responsable (Persona) for buyer data
3. Call PagosOrchestrator.preparar_pago_izipay with OrdenPago data
4. Return Izipay token + config to frontend
"""
import logging

from asgiref.sync import sync_to_async
from injector import inject

from modules.salesianos_fest.domain.exceptions import CompraNotFoundError, CompraNoCobrableError
from modules.salesianos_fest.domain.results.compra_results import CompraIzipayPreparedResult
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import PagosOrchestrator
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.commerce.domain.models import Compra
from modules.commerce.domain.constants import EstadoCompraChoices

logger = logging.getLogger(__name__)


class IniciarPagoFlujo:
    """
    Async flow for initiating Izipay payment for an existing Compra.

    Uses the buyer data from the responsable Persona linked to the Inscripcion
    via CompraInscripcion.
    """

    @inject
    def __init__(
        self,
        pagos_orchestrator: PagosOrchestrator,
    ):
        self.pagos_orchestrator = pagos_orchestrator

    async def _iniciar_pago(
        self,
        compra_id: str,
    ) -> CompraIzipayPreparedResult:
        """
        Initiate Izipay payment for a Compra.

        Steps:
        1. Load commerce.Compra and validate it is PENDIENTE
        2. Load CompraInscripcion to get Inscripcion.responsable for buyer data
        3. Call PagosOrchestrator.preparar_pago_izipay
        4. Return Izipay token + config

        Raises:
            CompraNotFoundError: if compra not found
            CompraNoCobrableError: if compra is not PENDIENTE
        """
        compra, orden_pago, buyer = await sync_to_async(self._cargar_contexto_pago)(compra_id)

        # 2. Call PagosOrchestrator to generate Izipay token.
        prepare_result = await self.pagos_orchestrator.preparar_pago_izipay(
            orden_pago_id=str(orden_pago.id),
            buyer_email=buyer["email"],
            buyer_name=buyer["name"],
            buyer_surname=buyer["surname"],
            buyer_document=buyer["document"],
            buyer_phone=buyer["phone"],
        )

        return CompraIzipayPreparedResult(
            compra_id=str(compra.id),
            orden_pago_id=str(orden_pago.id),
            transaction_id=prepare_result.transaction_id,
            order_number=prepare_result.order_number,
            token=prepare_result.token,
            merchant_code=prepare_result.merchant_code,
            amount=prepare_result.amount,
            currency=prepare_result.currency,
            buyer_email=prepare_result.buyer_email,
            buyer_name=prepare_result.buyer_name,
            buyer_surname=prepare_result.buyer_surname,
        )

    def _cargar_contexto_pago(self, compra_id: str):
        """Load and validate all ORM-backed payment context synchronously."""
        compra = (
            Compra.objects
            .select_related("orden_pago", "compra_inscripcion", "compra_inscripcion__inscripcion__responsable")
            .filter(id=compra_id)
            .first()
        )
        if compra is None:
            raise CompraNotFoundError()

        if compra.estado != EstadoCompraChoices.PENDIENTE:
            raise CompraNoCobrableError()

        orden_pago = compra.orden_pago
        if orden_pago.estado != OrdenPagoStatus.PENDIENTE:
            raise CompraNoCobrableError()

        # Get responsable from Inscripcion via CompraInscripcion
        inscripcion = compra.compra_inscripcion.inscripcion
        responsable = inscripcion.responsable
        buyer = {
            "email": getattr(responsable, "email", None) or "sin-email@ejemplo.com",
            "name": getattr(responsable, "nombres", None) or "CLIENTE",
            "surname": getattr(responsable, "apellidos", None) or "VENTA",
            "document": getattr(responsable, "numero_documento", None) or "00000000",
            "phone": getattr(responsable, "telefono", None) or "999999999",
        }
        return compra, orden_pago, buyer
