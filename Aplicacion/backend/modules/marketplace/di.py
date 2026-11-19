"""Wiring de dependencias (DI) del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las ligas del módulo (petición A0-02 del evidence de DOM-04).

La única liga que cruza de dominio es `IAlcanceEdicion`: el PUERTO lo
declara `marketplace` y lo IMPLEMENTA el adaptador de `infrastructure/`, de
modo que el dominio no depende del módulo `eventos` (FR-02 §2.2).

`DOM-05` añade dos puertos más, con el MISMO patrón (el dominio declara el
puerto, la infraestructura lo implementa):

- `ICommerceMarketplaceService` — la frontera con la infraestructura
  comercial compartida (`commerce`). El módulo NO importa `commerce`: el
  adaptador traduce su vocabulario al del módulo (RN-M07).
- `ITitularidadActorService` — la persona de la cuenta autenticada. El
  documento de identidad NO es una credencial (RN-U04).
"""

from injector import Binder, Module, singleton

from modules.marketplace.domain.ports.alcance_edicion import IAlcanceEdicion
from modules.marketplace.domain.ports.comercio import ICommerceMarketplaceService
from modules.marketplace.domain.ports.titularidad import ITitularidadActorService
from modules.marketplace.domain.selectors.categoria_selector import (
    CategoriaProductoSelector,
)
from modules.marketplace.domain.selectors.pedido_selector import PedidoSelector
from modules.marketplace.domain.selectors.producto_selector import ProductoSelector
from modules.marketplace.domain.services.core.pedido_core_service import (
    PedidoCoreService,
)
from modules.marketplace.domain.services.core.producto_core_service import (
    ProductoCoreService,
)
from modules.marketplace.domain.services.core.producto_media_service import (
    ProductoMediaService,
)
from modules.marketplace.domain.services.flujos.pedido_flujo import PedidoFlujo
from modules.marketplace.domain.services.flujos.producto_flujo import ProductoFlujo
from modules.marketplace.domain.services.orchestrators.pedido_orchestrator import (
    PedidoOrchestrator,
)
from modules.marketplace.domain.services.orchestrators.producto_orchestrator import (
    ProductoOrchestrator,
)
from modules.marketplace.infrastructure.services.alcance_edicion_eventos import (
    AlcanceEdicionEventos,
)
from modules.marketplace.infrastructure.services.comercio_adapter import (
    CommerceMarketplaceAdapter,
)
from modules.marketplace.infrastructure.services.titularidad_actor import (
    TitularidadActorAdapter,
)


class MarketplaceModule(Module):
    """Bindings de dependencias del módulo `marketplace`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(CategoriaProductoSelector, to=CategoriaProductoSelector, scope=singleton)
        binder.bind(ProductoSelector, to=ProductoSelector, scope=singleton)
        binder.bind(ProductoMediaService, to=ProductoMediaService, scope=singleton)
        binder.bind(ProductoCoreService, to=ProductoCoreService, scope=singleton)
        binder.bind(ProductoFlujo, to=ProductoFlujo, scope=singleton)
        binder.bind(IAlcanceEdicion, to=AlcanceEdicionEventos, scope=singleton)
        binder.bind(ProductoOrchestrator, to=ProductoOrchestrator, scope=singleton)
        # ── DOM-05 · pedido de marketplace ───────────────────────────────────
        binder.bind(PedidoSelector, to=PedidoSelector, scope=singleton)
        binder.bind(PedidoCoreService, to=PedidoCoreService, scope=singleton)
        binder.bind(
            ICommerceMarketplaceService,
            to=CommerceMarketplaceAdapter,
            scope=singleton,
        )
        binder.bind(
            ITitularidadActorService,
            to=TitularidadActorAdapter,
            scope=singleton,
        )
        binder.bind(PedidoFlujo, to=PedidoFlujo, scope=singleton)
        binder.bind(PedidoOrchestrator, to=PedidoOrchestrator, scope=singleton)


__all__ = ["MarketplaceModule"]
