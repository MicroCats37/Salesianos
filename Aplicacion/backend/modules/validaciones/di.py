"""El wiring de dependencias del módulo `validaciones`.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

**REGISTRO PENDIENTE DE A0** (`A0-XCT01-01`): este módulo tiene que estar en
`NINJA_EXTRA["INJECTOR_MODULES"]` de `config/settings/base.py`, que es de A0.
Hasta que A0 lo registre, la verificación local usa
`modules/validaciones/tests/settings_overlay.py`, que replica exactamente el
registro que A0 debe hacer.

Los adaptadores del puerto `VerificarDerecho` NO se registran aquí: viven en
su módulo dueño (`salesianos_fest`, `marketplace`) y el registro de
`validaciones` los reúne (`infrastructure/services.py`).
"""

from injector import Binder, Module, singleton

from modules.validaciones.domain.services.core.validacion_core_service import (
    ValidacionCoreService,
)
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)
from modules.validaciones.domain.services.flujos.preview_ticket_flujo import (
    PreviewTicketFlujo,
)
from modules.validaciones.domain.services.orchestrators.validacion_orchestrator import (
    ValidacionOrchestrator,
)
from modules.validaciones.domain.selectors.ticket_selector import TicketSelector
from modules.validaciones.infrastructure.services import RegistroVerificadoresDerecho


class ValidacionesModule(Module):
    """El módulo de inyección de `validaciones`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(
            RegistroVerificadoresDerecho,
            to=RegistroVerificadoresDerecho,
            scope=singleton,
        )
        binder.bind(TicketSelector, to=TicketSelector, scope=singleton)
        binder.bind(
            ValidacionCoreService, to=ValidacionCoreService, scope=singleton
        )
        binder.bind(PreviewTicketFlujo, to=PreviewTicketFlujo, scope=singleton)
        binder.bind(ConfirmarTicketFlujo, to=ConfirmarTicketFlujo, scope=singleton)
        binder.bind(
            ValidacionOrchestrator, to=ValidacionOrchestrator, scope=singleton
        )


__all__ = ["ValidacionesModule"]
