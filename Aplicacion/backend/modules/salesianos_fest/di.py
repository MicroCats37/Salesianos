"""Wiring de dependencias (DI) del módulo `salesianos_fest`.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las liaisons del módulo (petición A0-01 de este paquete).

Este módulo NO liga las clases de `eventos`, `usuarios`, `commerce` ni
`pagos`: esos módulos son sus dueños y los ligation en sus propios `di.py`.
Lo que este módulo sí liga son sus PUERTOS (`IAlcanceEdicionService`,
`ITitularidadService`, `IResolucionPersonaService`, `IObtensionPersonaService`
e `ICorreccionGeneroPersonaService`), cuyo adaptador vive en
`infrastructure/services/`.

El activador de derechos (`ActivadorInscripcion`) NO se liga aquí: lo
registra el PROCESO en el coordinador de `commerce` (`apps.py::ready`),
porque ese registro es único y por proceso (`D-FND-05-04`).
"""

from injector import Binder, Module, singleton

from modules.salesianos_fest.domain.ports import (
    IAlcanceEdicionService,
    ICorreccionGeneroPersonaService,
    IObtensionPersonaService,
    IResolucionPersonaService,
    ITitularidadService,
)
from modules.salesianos_fest.domain.selectors.catalogo_selector import CatalogoSelector
from modules.salesianos_fest.domain.selectors.cortesia_selector import CortesiaSelector
from modules.salesianos_fest.domain.selectors.inscripcion_selector import (
    InscripcionSelector,
)
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.selectors.pool_selector import PoolSelector
from modules.salesianos_fest.domain.services.core.beneficiario_core_service import (
    BeneficiarioCoreService,
)
from modules.salesianos_fest.domain.services.core.beneficio_core_service import (
    BeneficioCoreService,
)
from modules.salesianos_fest.domain.services.core.catalogo_core_service import (
    CatalogoCoreService,
)
from modules.salesianos_fest.domain.services.core.capacidad_core_service import (
    CapacidadCoreService,
)
from modules.salesianos_fest.domain.services.core.cortesia_core_service import (
    CortesiaCoreService,
)
from modules.salesianos_fest.domain.services.core.inscripcion_core_service import (
    InscripcionCoreService,
)
from modules.salesianos_fest.domain.services.core.pase_acceso_service import (
    PaseAccesoService,
)
from modules.salesianos_fest.domain.services.core.pase_core_service import (
    PaseCoreService,
)
from modules.salesianos_fest.domain.services.core.pool_core_service import (
    PoolCoreService,
)
from modules.salesianos_fest.domain.services.flujos.beneficiario_flujo import (
    BeneficiarioFlujo,
)
from modules.salesianos_fest.domain.services.flujos.catalogo_flujo import CatalogoFlujo
from modules.salesianos_fest.domain.services.flujos.compra_cupos_flujo import (
    CompraCuposFlujo,
)
from modules.salesianos_fest.domain.services.flujos.compra_pase_flujo import (
    CompraPaseFlujo,
)
from modules.salesianos_fest.domain.services.flujos.cortesia_flujo import CortesiaFlujo
from modules.salesianos_fest.domain.services.flujos.inscripcion_flujo import (
    InscripcionFlujo,
)
from modules.salesianos_fest.domain.services.flujos.pase_flujo import PaseFlujo
from modules.salesianos_fest.domain.services.flujos.pool_flujo import PoolFlujo
from modules.salesianos_fest.domain.services.orchestrators.beneficiario_orchestrator import (
    BeneficiarioOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.catalogo_orchestrator import (
    CatalogoOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.compra_cupos_orchestrator import (
    CompraCuposOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.cortesia_orchestrator import (
    CortesiaOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.inscripcion_orchestrator import (
    InscripcionOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.pase_orchestrator import (
    PaseOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.pool_orchestrator import (
    PoolOrchestrator,
)
from modules.salesianos_fest.infrastructure.services import (
    AlcanceEdicionAdapter,
    CorreccionGeneroPersonaAdapter,
    EmisorCredencialService,
    ObtencionPersonaAdapter,
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


def _obtencion_persona_factory() -> IObtensionPersonaService:
    """Construye el adaptador de obtención de identidades de `usuarios`."""
    return ObtencionPersonaAdapter()


def _correccion_genero_persona_factory() -> ICorreccionGeneroPersonaService:
    """Construye el adaptador de corrección de género de `usuarios`."""
    return CorreccionGeneroPersonaAdapter()


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
        # ── DOM-03 · PASES, BENEFICIARIOS Y CORTESÍA ──────────────────────
        binder.bind(PaseSelector, to=PaseSelector, scope=singleton)
        binder.bind(CortesiaSelector, to=CortesiaSelector, scope=singleton)
        binder.bind(PaseCoreService, to=PaseCoreService, scope=singleton)
        binder.bind(
            BeneficiarioCoreService,
            to=BeneficiarioCoreService,
            scope=singleton,
        )
        binder.bind(CortesiaCoreService, to=CortesiaCoreService, scope=singleton)
        binder.bind(
            EmisorCredencialService,
            to=EmisorCredencialService,
            scope=singleton,
        )
        binder.bind(PaseAccesoService, to=PaseAccesoService, scope=singleton)
        binder.bind(
            IObtensionPersonaService,
            to=_obtencion_persona_factory,
            scope=singleton,
        )
        binder.bind(
            ICorreccionGeneroPersonaService,
            to=_correccion_genero_persona_factory,
            scope=singleton,
        )
        binder.bind(PaseFlujo, to=PaseFlujo, scope=singleton)
        binder.bind(CompraPaseFlujo, to=CompraPaseFlujo, scope=singleton)
        binder.bind(BeneficiarioFlujo, to=BeneficiarioFlujo, scope=singleton)
        binder.bind(CortesiaFlujo, to=CortesiaFlujo, scope=singleton)
        binder.bind(PaseOrchestrator, to=PaseOrchestrator, scope=singleton)
        binder.bind(
            BeneficiarioOrchestrator,
            to=BeneficiarioOrchestrator,
            scope=singleton,
        )
        binder.bind(
            CortesiaOrchestrator,
            to=CortesiaOrchestrator,
            scope=singleton,
        )


__all__ = ["SalesianosFestModule"]
