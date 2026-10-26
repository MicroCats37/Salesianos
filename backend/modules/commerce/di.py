"""commerce module dependency injection wiring."""
from injector import Module, singleton, Binder

from modules.commerce.domain.services.core.compra_core_service import CompraCoreService
from modules.commerce.infrastructure.services import PropietarioOrdenPagoAdapter
from modules.pagos.domain.ports import IPropietarioOrdenPagoService


class CommerceModule(Module):
    """Dependency injection module for commerce."""

    def configure(self, binder: Binder) -> None:
        binder.bind(CompraCoreService, to=CompraCoreService, scope=singleton)

        # Port binding: `pagos` asks who owns a payment order before it
        # accepts a browser relay. The implementation lives here so `pagos`
        # never imports `commerce`.
        binder.bind(
            IPropietarioOrdenPagoService,
            to=PropietarioOrdenPagoAdapter,
            scope=singleton,
        )
