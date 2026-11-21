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

**EL PUERTO `IEmisorCredencialService`** sí se liga aquí, porque este módulo
es su CONSUMIDOR: lo DECLARA (`domain/ports/emisor_credencial.py`) y lo
IMPLEMENTA el dueño del derecho (`salesianos_fest`). El `import` del
adaptador es PEREZOSO para que un módulo que no emite credenciales no cargue
al dueño del derecho.
"""

from injector import Binder, Module, singleton

from modules.validaciones.domain.ports.emisor_credencial import (
    IEmisorCredencialService,
)
from modules.validaciones.domain.services.core.emision_credencial_core_service import (
    EmisionCredencialCoreService,
)
from modules.validaciones.domain.services.core.validacion_core_service import (
    ValidacionCoreService,
)
from modules.validaciones.domain.services.flujos.confirmar_ticket_flujo import (
    ConfirmarTicketFlujo,
)
from modules.validaciones.domain.services.flujos.emitir_ticket_flujo import (
    EmitirTicketFlujo,
)
from modules.validaciones.domain.services.flujos.preview_ticket_flujo import (
    PreviewTicketFlujo,
)
from modules.validaciones.domain.services.orchestrators.validacion_orchestrator import (
    ValidacionOrchestrator,
)
from modules.validaciones.domain.selectors.ticket_selector import TicketSelector
from modules.validaciones.infrastructure.services import RegistroVerificadoresDerecho


def _emisor_credencial_factory() -> IEmisorCredencialService:
    """Construye el adaptador de emisión del módulo DUEÑO del derecho.

    El `import` es PEREZOSO a propósito: `validaciones` no carga a
    `salesianos_fest` al importarse, sólo cuando alguien emite una credencial.
    """
    from modules.salesianos_fest.infrastructure.services.emisor_credencial import (
        EmisorCredencialService,
    )

    return EmisorCredencialService()


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
        binder.bind(
            EmisionCredencialCoreService,
            to=EmisionCredencialCoreService,
            scope=singleton,
        )
        binder.bind(
            IEmisorCredencialService,
            to=_emisor_credencial_factory,
            scope=singleton,
        )
        binder.bind(PreviewTicketFlujo, to=PreviewTicketFlujo, scope=singleton)
        binder.bind(ConfirmarTicketFlujo, to=ConfirmarTicketFlujo, scope=singleton)
        binder.bind(EmitirTicketFlujo, to=EmitirTicketFlujo, scope=singleton)
        binder.bind(
            ValidacionOrchestrator, to=ValidacionOrchestrator, scope=singleton
        )


__all__ = ["ValidacionesModule"]
