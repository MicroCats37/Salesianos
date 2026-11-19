"""Wiring de dependencias (DI) del módulo `commerce`.

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las liaisons del módulo (petición A0-04 del evidence de FND-04).

`commerce` depende de `pagos` (la FK de `Compra.orden_pago` y el servicio de
órdenes). `pagos` NO depende de `commerce`: pregunta por el estado comercial
de la compra a través de un puerto, cuya implementación vive en
`commerce/infrastructure/services/`.
"""

from injector import Binder, Module, singleton

from modules.commerce.domain.selectors.compra_selector import CompraSelector
from modules.commerce.domain.services.core.activacion_compra_core_service import (
    ActivacionCompraCoreService,
)
from modules.commerce.domain.services.core.compra_core_service import (
    CompraCoreService,
)
from modules.commerce.domain.services.core.coordinador_activacion_compra import (
    CoordinadorActivacionCompra,
)
from modules.commerce.domain.services.core.registro_activadores_compra import (
    RegistroActivadoresCompra,
    obtener_registro,
)
from modules.commerce.domain.services.flujos.compra_flujo import CompraFlujo
from modules.commerce.domain.services.orchestrators.compra_orchestrator import (
    CompraOrchestrator,
)


def _registro_activadores_factory() -> RegistroActivadoresCompra:
    """El registro único de activadores de dominio.

    Es un objeto del proceso, no un binding: los dominios de origen registran
    SU activador sin tocar este módulo (DOM-02, DOM-03, DOM-06).
    """
    return obtener_registro()


class CommerceModule(Module):
    """Bindings de dependencias del módulo `commerce`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(CompraSelector, to=CompraSelector, scope=singleton)
        binder.bind(CompraCoreService, to=CompraCoreService, scope=singleton)
        binder.bind(CompraFlujo, to=CompraFlujo, scope=singleton)
        binder.bind(CompraOrchestrator, to=CompraOrchestrator, scope=singleton)
        binder.bind(
            ActivacionCompraCoreService,
            to=ActivacionCompraCoreService,
            scope=singleton,
        )
        binder.bind(
            RegistroActivadoresCompra,
            to=_registro_activadores_factory,
            scope=singleton,
        )
        binder.bind(
            CoordinadorActivacionCompra,
            to=CoordinadorActivacionCompra,
            scope=singleton,
        )


__all__ = ["CommerceModule"]
