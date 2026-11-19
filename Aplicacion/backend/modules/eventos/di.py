"""Wiring de dependencias (DI) del módulo `eventos`.

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las ligações del módulo (petición A0-02 del evidence de FND-02).
"""

from injector import Binder, Module, singleton

from modules.eventos.domain.selectors.edicion_selector import EdicionSelector
from modules.eventos.domain.selectors.evento_selector import EventoSelector
from modules.eventos.domain.services.core.edicion_core_service import EdicionCoreService
from modules.eventos.domain.services.core.edicion_scope_service import EdicionScopeService
from modules.eventos.domain.services.flujos.edicion_flujo import EdicionFlujo
from modules.eventos.domain.services.orchestrators.edicion_orchestrator import (
    EdicionOrchestrator,
)


class EventosModule(Module):
    """Bindings de dependencias del módulo `eventos`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(EventoSelector, to=EventoSelector, scope=singleton)
        binder.bind(EdicionSelector, to=EdicionSelector, scope=singleton)
        binder.bind(EdicionScopeService, to=EdicionScopeService, scope=singleton)
        binder.bind(EdicionCoreService, to=EdicionCoreService, scope=singleton)
        binder.bind(EdicionFlujo, to=EdicionFlujo, scope=singleton)
        binder.bind(EdicionOrchestrator, to=EdicionOrchestrator, scope=singleton)


__all__ = ["EventosModule"]
