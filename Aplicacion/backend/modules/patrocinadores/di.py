"""Wiring de dependencias (DI) del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las ligas del módulo (petición A0-01 de la evidencia de DOM-08).

La única liga que cruza de dominio es `IAlcanceEdicion`: el PUERTO lo declara
`patrocinadores` y lo IMPLEMENTA el adaptador de `infrastructure/`, de modo que
el dominio no depende del módulo `eventos` (FR-02 §2.2).
"""

from injector import Binder, Module, singleton

from modules.patrocinadores.domain.ports.alcance_edicion import IAlcanceEdicion
from modules.patrocinadores.domain.selectors.patrocinador_selector import (
    PatrocinadorSelector,
)
from modules.patrocinadores.domain.services.core.patrocinador_core_service import (
    PatrocinadorCoreService,
)
from modules.patrocinadores.domain.services.core.patrocinador_media_service import (
    PatrocinadorMediaService,
)
from modules.patrocinadores.domain.services.flujos.patrocinador_flujo import (
    PatrocinadorFlujo,
)
from modules.patrocinadores.domain.services.orchestrators.patrocinador_orchestrator import (
    PatrocinadorOrchestrator,
)
from modules.patrocinadores.infrastructure.services.alcance_edicion_eventos import (
    AlcanceEdicionEventos,
)


class PatrocinadoresModule(Module):
    """Bindings de dependencias del módulo `patrocinadores`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(PatrocinadorSelector, to=PatrocinadorSelector, scope=singleton)
        binder.bind(PatrocinadorMediaService, to=PatrocinadorMediaService, scope=singleton)
        binder.bind(PatrocinadorCoreService, to=PatrocinadorCoreService, scope=singleton)
        binder.bind(PatrocinadorFlujo, to=PatrocinadorFlujo, scope=singleton)
        binder.bind(IAlcanceEdicion, to=AlcanceEdicionEventos, scope=singleton)
        binder.bind(PatrocinadorOrchestrator, to=PatrocinadorOrchestrator, scope=singleton)


__all__ = ["PatrocinadoresModule"]
