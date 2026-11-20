"""
Cableado de inyección de dependencias del módulo `usuarios`.

`contract/django-app-architecture-contract.md` §4.15.

Se registra en `NINJA_EXTRA["INJECTOR_MODULES"]` (archivo de settings, propiedad
de A0). Mientras A0 no lo registre, el módulo sigue siendo usable: los tests
lo instalan con `ninja_extra.dependency_resolver.register_injector_modules`.

Los servicios NO se declaran como `singleton`: el puerto de la fuente externa
se resuelve en cada construcción, de modo que un test puede inyectar su doble
por el grafo de fixtures sin `unittest.mock.patch`
(`contract/TEST_ARCHITECTURE_CONTRACT.md` §6).
"""

from injector import Binder, Module

from modules.usuarios.domain.ports import IConsultaDocumentoClient
from modules.usuarios.domain.selectors import PersonaSelector, UsuarioSelector
from modules.usuarios.domain.services.core.auth_core_service import AuthCoreService
from modules.usuarios.domain.services.core.grupo_service import GrupoFuncionalService
from modules.usuarios.domain.services.core.persona_core_service import (
    PersonaCoreService,
)
from modules.usuarios.domain.services.core.titularidad_service import (
    TitularidadService,
)
from modules.usuarios.domain.services.core.usuario_core_service import (
    UsuarioCoreService,
)
from modules.usuarios.domain.services.flujos.auth_flujo import AuthFlujo
from modules.usuarios.domain.services.flujos.persona_resolucion_flujo import (
    PersonaResolucionFlujo,
)
from modules.usuarios.domain.services.orchestrators.auth_orchestrator import (
    AuthOrchestrator,
)
from modules.usuarios.domain.services.orchestrators.persona_orchestrator import (
    PersonaOrchestrator,
)
from modules.usuarios.infrastructure.services import ConsultaDocumentoClient
from modules.usuarios.presentation.presenters.auth_presenter import AuthPresenter
from modules.usuarios.presentation.presenters.persona_presenter import (
    PersonaBusquedaPresenter,
    PersonaConfirmarPresenter,
    PersonaResolverPresenter,
)


class UsuariosModule(Module):
    """Vínculos del módulo `usuarios`."""

    def configure(self, binder: Binder) -> None:
        # Puerto de la fuente externa de documentos → implementación HTTP.
        binder.bind(IConsultaDocumentoClient, to=ConsultaDocumentoClient)

        # Selectores (sólo lectura).
        binder.bind(PersonaSelector, to=PersonaSelector)
        binder.bind(UsuarioSelector, to=UsuarioSelector)

        # Servicios core (sync).
        binder.bind(PersonaCoreService, to=PersonaCoreService)
        binder.bind(UsuarioCoreService, to=UsuarioCoreService)
        binder.bind(GrupoFuncionalService, to=GrupoFuncionalService)
        binder.bind(TitularidadService, to=TitularidadService)
        binder.bind(AuthCoreService, to=AuthCoreService)

        # Flujo y fachada.
        binder.bind(PersonaResolucionFlujo, to=PersonaResolucionFlujo)
        binder.bind(PersonaOrchestrator, to=PersonaOrchestrator)
        binder.bind(AuthFlujo, to=AuthFlujo)
        binder.bind(AuthOrchestrator, to=AuthOrchestrator)

        # Presenters.
        binder.bind(PersonaBusquedaPresenter, to=PersonaBusquedaPresenter)
        binder.bind(PersonaResolverPresenter, to=PersonaResolverPresenter)
        binder.bind(PersonaConfirmarPresenter, to=PersonaConfirmarPresenter)
        binder.bind(AuthPresenter, to=AuthPresenter)


__all__ = ["UsuariosModule"]
