"""
Módulo Usuarios — Cableado de Inyección de Dependencias.

Usa el patrón Module de injector para vincular servicios.
Se registra en settings vía NINJA_EXTRA["INJECTOR_MODULES"] o similar.
"""

from django.conf import settings
from injector import Module, singleton, Binder

from .domain.services.core.auth_core_service import AuthCoreService
from .domain.services.core.persona_core_service import PersonaCoreService
from .domain.services.flujos.auth_flujo import AuthFlujo
from .domain.services.flujos.registro_flujo import RegistroFlujo
from .domain.services.flujos.persona_busqueda_flujo import PersonaBusquedaFlujo
from .domain.services.orchestrators.auth_orchestrator import AuthOrchestrator
from .domain.services.orchestrators.registro_orchestrator import RegistroOrchestrator
from .domain.services.orchestrators.persona_busqueda_orchestrator import PersonaBusquedaOrchestrator
from .domain.ports import IConsultaExternaClient
from .infrastructure.services import ConsultaExternaSimulator, RealConsultaExternaClient


class UsuariosModule(Module):
    """
    Módulo DI para el paquete usuarios.

    Vincula:
    - AuthCoreService (operaciones síncronas)
    - PersonaCoreService (operaciones síncronas de Persona)
    - AuthFlujo (flujos asíncronos, depende de AuthCoreService)
    - RegistroFlujo (flujo de registro, depende de PersonaCoreService + AuthCoreService)
    - AuthOrchestrator (fachada ligera, depende de AuthFlujo)
    - RegistroOrchestrator (fachada ligera, depende de RegistroFlujo)
    - PersonaBusquedaFlujo (flujo de búsqueda, depende de IConsultaExternaClient)
    - PersonaBusquedaOrchestrator (fachada ligera, depende de PersonaBusquedaFlujo)
    - IConsultaExternaClient (reutilizado de entidades: simulador o cliente real)

    Todos los servicios son de ámbito singleton.
    """

    def configure(self, binder: Binder) -> None:
        # Servicios de auth — ámbito singleton
        binder.bind(AuthCoreService, to=AuthCoreService, scope=singleton)
        binder.bind(AuthFlujo, to=AuthFlujo, scope=singleton)
        binder.bind(AuthOrchestrator, to=AuthOrchestrator, scope=singleton)

        # Servicios de registro — ámbito singleton
        binder.bind(PersonaCoreService, to=PersonaCoreService, scope=singleton)
        binder.bind(RegistroFlujo, to=RegistroFlujo, scope=singleton)
        binder.bind(RegistroOrchestrator, to=RegistroOrchestrator, scope=singleton)

        # Servicios de búsqueda de personas — ámbito singleton
        binder.bind(PersonaBusquedaFlujo, to=PersonaBusquedaFlujo, scope=singleton)
        binder.bind(PersonaBusquedaOrchestrator, to=PersonaBusquedaOrchestrator, scope=singleton)

        # External Clients (reutilizado de entidades)
        # En DEBUG: usar simulador para desarrollo
        # En producción: usar cliente real (scraper worker)
        if getattr(settings, "CONSULTA_EXTERNA_USE_SIMULATOR", settings.DEBUG):
            binder.bind(IConsultaExternaClient, to=ConsultaExternaSimulator, scope=singleton)
        else:
            binder.bind(IConsultaExternaClient, to=RealConsultaExternaClient, scope=singleton)
