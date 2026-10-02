"""
PagosModule — Dependency Injection wiring for pagos package.
"""
from injector import Module, singleton, Binder

from modules.pagos.infrastructure.services import IzipayClient
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from modules.pagos.domain.services.flujos.registrar_pago_izipay_flujo import RegistrarPagoIzipayFlujo
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import PagosOrchestrator


class PagosModule(Module):
    """
    DI module for the pagos package (Izipay Perú Web Core 2.0).
    """

    def configure(self, binder: Binder) -> None:
        # Infrastructure: Izipay HTTP client (singleton per process)
        binder.bind(IzipayClient, to=IzipayClient, scope=singleton)

        # Core service: transaction CRUD, idempotency, ID generation
        binder.bind(IzipayCoreService, to=IzipayCoreService, scope=singleton)

        # Flow: async use-case with transaction.atomic for confirm step
        # Depends on: IzipayCoreService, InscripcionService (from InscripcionesModule),
        #            IzipayClient (from infrastructure)
        binder.bind(RegistrarPagoIzipayFlujo, to=RegistrarPagoIzipayFlujo, scope=singleton)

        # Orchestrator: thin async facade with ownership validation
        # Depends on: RegistrarPagoIzipayFlujo, InscripcionSelector (from InscripcionesModule)
        binder.bind(PagosOrchestrator, to=PagosOrchestrator, scope=singleton)
