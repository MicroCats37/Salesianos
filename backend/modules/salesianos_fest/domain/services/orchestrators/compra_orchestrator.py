"""
CompraOrchestrator — async thin facade for Compra operations.

Orchestrator — async thin facade that delegates to flujos.
No business logic here — only delegation.
"""
from injector import inject

from modules.salesianos_fest.domain.schemas.compra_schemas import CompraCreateData
from modules.salesianos_fest.domain.results.compra_results import (
    CompraCreatedResult,
    CompraIzipayPreparedResult,
    CompraConfirmedResult,
    CompraCanceladaResult,
)
from modules.salesianos_fest.domain.services.flujos.crear_compra_flujo import CrearCompraFlujo
from modules.salesianos_fest.domain.services.flujos.iniciar_pago_flujo import IniciarPagoFlujo
from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import ConfirmarPagoFlujo
from modules.salesianos_fest.domain.services.flujos.cancelar_compra_flujo import CancelarCompraFlujo


class CompraOrchestrator:
    """
    Thin async facade for Compra operations.

    All methods delegate to their respective flujos.
    """

    @inject
    def __init__(
        self,
        crear_flujo: CrearCompraFlujo,
        iniciar_flujo: IniciarPagoFlujo,
        confirmar_flujo: ConfirmarPagoFlujo,
        cancelar_flujo: CancelarCompraFlujo,
    ):
        self.crear_flujo = crear_flujo
        self.iniciar_flujo = iniciar_flujo
        self.confirmar_flujo = confirmar_flujo
        self.cancelar_flujo = cancelar_flujo

    async def crear_compra(
        self,
        data: CompraCreateData,
    ) -> CompraCreatedResult:
        """
        Create a Compra and its associated OrdenPago.

        See CrearCompraFlujo._crear_compra for full docs.
        """
        return await self.crear_flujo._crear_compra(data)

    async def iniciar_pago(
        self,
        compra_id: str,
    ) -> CompraIzipayPreparedResult:
        """
        Initiate Izipay payment for an existing Compra.

        See IniciarPagoFlujo._iniciar_pago for full docs.
        """
        return await self.iniciar_flujo._iniciar_pago(compra_id)

    async def cancelar_compra(
        self,
        compra_id: str,
    ) -> CompraCanceladaResult:
        """
        Cancel a Compra (refund) and revoke the rights it funded.

        See CancelarCompraFlujo._cancelar_compra for full docs.
        """
        return await self.cancelar_flujo._cancelar_compra(compra_id)
