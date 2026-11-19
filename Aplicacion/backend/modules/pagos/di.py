"""Wiring de dependencias (DI) del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las liaisons del módulo (petición A0-04 del evidence de FND-04).

Los puertos cuyo proveedor es `commerce` se ligan con una **fábrica perezosa**:
el import del módulo proveedor ocurre cuando el puerto se resuelve por
primera vez, nunca al importar este archivo. Así el grafo de módulos queda
acíclico y el orden de carga de Django no importa.
"""

from injector import Binder, Module, singleton

from modules.pagos.domain.ports import (
    IActivacionCompraService,
    IEstadoCompraOrdenPagoService,
    IPropietarioOrdenPagoService,
    IProveedorPagoService,
)
from modules.pagos.domain.selectors.pago_selector import (
    OrdenPagoSelector,
    TransaccionPagoSelector,
)
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)
from modules.pagos.domain.services.core.idempotencia_pago_service import (
    IdempotenciaPagoService,
)
from modules.pagos.domain.services.core.orden_pago_core_service import (
    OrdenPagoCoreService,
)
from modules.pagos.domain.services.core.transaccion_pago_core_service import (
    TransaccionPagoCoreService,
)
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.domain.services.flujos.pago_confirmacion_flujo import (
    PagoConfirmacionFlujo,
)
from modules.pagos.domain.services.flujos.pago_intento_flujo import PagoIntentoFlujo
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import (
    PagosOrchestrator,
)
from modules.pagos.infrastructure.services import ProveedorPagoIzipayAdapter


def _estado_compra_service_factory() -> IEstadoCompraOrdenPagoService:
    """Construye el adaptador de `commerce` para el estado de la compra.

    El import es perezoso a propósito: `pagos` no importa `commerce` en tiempo
    de módulo, sólo cuando el puerto se resuelve.
    """
    from modules.commerce.infrastructure.services.estado_compra_orden_pago import (
        EstadoCompraOrdenPagoAdapter,
    )

    return EstadoCompraOrdenPagoAdapter()


def _propietario_service_factory() -> IPropietarioOrdenPagoService:
    """Construye el adaptador de `commerce` para la titularidad de la orden."""
    from modules.commerce.infrastructure.services.propietario_orden_pago import (
        PropietarioOrdenPagoAdapter,
    )

    return PropietarioOrdenPagoAdapter()


def _activacion_service_factory() -> IActivacionCompraService:
    """Construye el coordinador de activación de derechos de `commerce`."""
    from modules.commerce.infrastructure.services.activacion_compra import (
        ActivacionCompraAdapter,
    )

    return ActivacionCompraAdapter()


class PagosModule(Module):
    """Bindings de dependencias del módulo `pagos`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(OrdenPagoSelector, to=OrdenPagoSelector, scope=singleton)
        binder.bind(
            TransaccionPagoSelector, to=TransaccionPagoSelector, scope=singleton
        )
        binder.bind(OrdenPagoCoreService, to=OrdenPagoCoreService, scope=singleton)
        binder.bind(
            TransaccionPagoCoreService, to=TransaccionPagoCoreService, scope=singleton
        )
        binder.bind(
            VerificacionPagoService, to=VerificacionPagoService, scope=singleton
        )
        binder.bind(
            IdempotenciaPagoService, to=IdempotenciaPagoService, scope=singleton
        )
        binder.bind(
            ProveedorPagoIzipayAdapter, to=ProveedorPagoIzipayAdapter, scope=singleton
        )
        binder.bind(
            IProveedorPagoService, to=ProveedorPagoIzipayAdapter, scope=singleton
        )
        binder.bind(
            IEstadoCompraOrdenPagoService,
            to=_estado_compra_service_factory,
            scope=singleton,
        )
        binder.bind(
            IPropietarioOrdenPagoService,
            to=_propietario_service_factory,
            scope=singleton,
        )
        binder.bind(
            IActivacionCompraService,
            to=_activacion_service_factory,
            scope=singleton,
        )
        binder.bind(
            EstadoOperativoPagoService, to=EstadoOperativoPagoService, scope=singleton
        )
        binder.bind(PagoConfirmacionFlujo, to=PagoConfirmacionFlujo, scope=singleton)
        binder.bind(PagoIntentoFlujo, to=PagoIntentoFlujo, scope=singleton)
        binder.bind(PagosOrchestrator, to=PagosOrchestrator, scope=singleton)


__all__ = ["PagosModule"]
