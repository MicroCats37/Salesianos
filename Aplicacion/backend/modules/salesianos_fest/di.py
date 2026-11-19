"""Wiring de dependencias (DI) del módulo `salesianos_fest`.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las liaisons del módulo (petición A0-01 de este paquete).

Este módulo NO liga las clases de `eventos`, `usuarios`, `commerce` ni
`pagos`: esos módulos son sus dueños y los ligation en sus propios `di.py`.
Lo que este módulo sí liga son sus PUERTOS (`IAlcanceEdicionService`,
`ITitularidadService`, `IResolucionPersonaService`), cuyo adaptador vive en
`infrastructure/services/`.

El activador de derechos (`ActivadorInscripcion`) NO se liga aquí: lo
registra el PROCESO en el coordinador de `commerce` (`apps.py::ready`),
porque ese registro es único y por proceso (`D-FND-05-04`).
"""

from injector import Binder, Module, singleton

from modules.salesianos_fest.domain.ports import (
    IAlcanceEdicionService,
    IResolucionPersonaService,
    ITitularidadService,
)
from modules.salesianos_fest.domain.selectors.catalogo_selector import CatalogoSelector
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)
from modules.salesianos_fest.domain.selectors.pool_selector import PoolSelector
from modules.salesianos_fest.domain.services.core.beneficio_core_service import (
    BeneficioCoreService,
)
from modules.salesianos_fest.domain.services.core.catalogo_core_service import (
    CatalogoCoreService,
)
from modules.salesianos_fest.domain.services.core.capacidad_core_service import (
    CapacidadCoreService,
)
from modules.salesianos_fest.domain.services.core.inscripcion_core_service import (
    InscripcionCoreService,
)
from modules.salesianos_fest.domain.services.core.pool_core_service import (
    PoolCoreService,
)
from modules.salesianos_fest.domain.services.flujos.catalogo_flujo import CatalogoFlujo
from modules.salesianos_fest.domain.services.flujos.compra_cupos_flujo import (
    CompraCuposFlujo,
)
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo
from modules.salesianos_fest.domain.services.orchestrators.catalogo_orchestrator import (
    CatalogoOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.compra_cupos_orchestrator import (
    CompraCuposOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.inscripcion_orchestrator import (
    InscripcionOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.pool_orchestrator import (
    PoolOrchestrator,
)
from modules.salesianos_fest.infrastructure.services import (
    AlcanceEdicionAdapter,
    ResolucionPersonaAdapter,
    TitularidadAdapter,
)


def _alcance_edicion_factory() -> IAlcanceEdicionService:
    """Construye el adaptador del alcance de edición de `eventos`."""
    return AlcanceEdicionAdapter()


def _titularidad_factory() -> ITitularidadService:
    """Construye el adaptador de titularidad de `usuarios`."""
    return TitularidadAdapter()


def _resolucion_persona_factory() -> IResolucionPersonaService:
    """Construye el adaptador de resolución de identidades de `usuarios`."""
    return ResolucionPersonaAdapter()


class SalesianosFestModule(Module):
    """Bindings de dependencias del módulo `salesianos_fest`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(CatalogoSelector, to=CatalogoSelector, scope=singleton)
        binder.bind(InscripcionSelector, to=InscripcionSelector, scope=singleton)
        binder.bind(PoolSelector, to=PoolSelector, scope=singleton)
        binder.bind(CatalogoCoreService, to=CatalogoCoreService, scope=singleton)
        binder.bind(
            InscripcionCoreService,
            to=InscripcionCoreService,
            scope=singleton,
        )
        binder.bind(PoolCoreService, to=PoolCoreService, scope=singleton)
        binder.bind(
            CapacidadCoreService,
            to=CapacidadCoreService,
            scope=singleton,
        )
        binder.bind(
            BeneficioCoreService,
            to=BeneficioCoreService,
            scope=singleton,
        )
        binder.bind(
            IAlcanceEdicionService,
            to=_alcance_edicion_factory,
            scope=singleton,
        )
        binder.bind(
            ITitularidadService,
            to=_titularidad_factory,
            scope=singleton,
        )
        binder.bind(
            IResolucionPersonaService,
            to=_resolucion_persona_factory,
            scope=singleton,
        )
        binder.bind(CatalogoFlujo, to=CatalogoFlujo, scope=singleton)
        binder.bind(InscripcionFlujo, to=InscripcionFlujo, scope=singleton)
        binder.bind(PoolFlujo, to=PoolFlujo, scope=singleton)
        binder.bind(CompraCuposFlujo, to=CompraCuposFlujo, scope=singleton)
        binder.bind(
            CatalogoOrchestrator,
            to=CatalogoOrchestrator,
            scope=singleton,
        )
        binder.bind(
            InscripcionOrchestrator,
            to=InscripcionOrchestrator,
            scope=singleton,
        )
        binder.bind(PoolOrchestrator, to=PoolOrchestrator, scope=singleton)
        binder.bind(
            CompraCuposOrchestrator,
            to=CompraCuposOrchestrator,
            scope=singleton,
        )


__all__ = ["SalesianosFestModule"]
