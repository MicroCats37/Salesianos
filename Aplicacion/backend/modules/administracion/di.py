"""Wiring de dependencias del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild` (work unit 2)

El wiring lo registra A0 en `NINJA_EXTRA["INJECTOR_MODULES"]` (`A0-XCT02-01`).
El `settings_overlay` de `tests/` lo replica para poder verificar el módulo
sin tocar la configuración compartida.

## El ORDEN importa

Este módulo AGREGA: consume los servicios de `pagos`, `commerce`,
`salesianos_fest`, `usuarios` y `eventos`. Por eso su wiring tiene que
ir DETRÁS del de esos módulos en `INJECTOR_MODULES`: el binding de
`EstadoOperativoPagoService` (el veredicto del pago) lo publica `pagos`.
"""

from injector import Binder, Module, singleton

from modules.administracion.domain.selectors.admin_auditoria_selector import (
    AdminAuditoriaSelector,
)
from modules.administracion.domain.selectors.admin_operacion_selector import (
    AdminEquipoSelector,
    AdminInscripcionSelector,
    AdminParticipanteSelector,
    AdminPagoSelector,
    AdminPersonaSelector,
)
from modules.administracion.domain.selectors.admin_resumen_selector import (
    AdminResumenSelector,
)
from modules.administracion.domain.services.core.admin_accion_sensible_service import (
    AdminAccionSensibleService,
)
from modules.administracion.domain.services.core.admin_auditoria_service import (
    AdminAuditoriaService,
)
from modules.administracion.domain.services.core.admin_operacion_service import (
    AdminOperacionService,
)
from modules.administracion.domain.services.flujos.admin_accion_sensible_flujo import (
    AdminAccionSensibleFlujo,
)
from modules.administracion.domain.services.flujos.admin_asistido_flujo import (
    AdminAsistidoFlujo,
)
from modules.administracion.domain.services.orchestrators.admin_auditoria_orchestrator import (
    AdminAuditoriaOrchestrator,
)
from modules.administracion.domain.services.orchestrators.admin_asistido_orchestrator import (
    AdminAsistidoOrchestrator,
)
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.domain.services.orchestrators.admin_resumen_orchestrator import (
    AdminResumenOrchestrator,
)


class AdministracionModule(Module):
    """Injector module for the administracion module dependencies."""

    def configure(self, binder: Binder) -> None:
        """Register the admin services."""
        binder.bind(AdminResumenSelector, to=AdminResumenSelector, scope=singleton)
        binder.bind(AdminAuditoriaSelector, to=AdminAuditoriaSelector, scope=singleton)
        binder.bind(AdminAuditoriaService, to=AdminAuditoriaService, scope=singleton)
        binder.bind(
            AdminResumenOrchestrator,
            to=AdminResumenOrchestrator,
            scope=singleton,
        )
        binder.bind(
            AdminAuditoriaOrchestrator,
            to=AdminAuditoriaOrchestrator,
            scope=singleton,
        )

        # ── Work unit 2: la capa operativa ──────────────────────────────────
        binder.bind(AdminInscripcionSelector, to=AdminInscripcionSelector, scope=singleton)
        binder.bind(AdminEquipoSelector, to=AdminEquipoSelector, scope=singleton)
        binder.bind(AdminParticipanteSelector, to=AdminParticipanteSelector, scope=singleton)
        binder.bind(AdminPagoSelector, to=AdminPagoSelector, scope=singleton)
        binder.bind(AdminPersonaSelector, to=AdminPersonaSelector, scope=singleton)
        binder.bind(AdminOperacionService, to=AdminOperacionService, scope=singleton)
        binder.bind(
            AdminAccionSensibleService,
            to=AdminAccionSensibleService,
            scope=singleton,
        )
        binder.bind(
            AdminAccionSensibleFlujo,
            to=AdminAccionSensibleFlujo,
            scope=singleton,
        )
        binder.bind(
            AdminOperacionOrchestrator,
            to=AdminOperacionOrchestrator,
            scope=singleton,
        )

        # ── Comandos administrativos asistidos ────────────────────────────────
        # `admin-client-purchases-and-participants`: alta de participante por
        # documento y compras asistidas para un tercero. El flujo consume los
        # dueños (`salesianos_fest`, `marketplace` y `pagos`), de modo que su
        # wiring tiene que ir DETRÁS del de esos módulos.
        binder.bind(
            AdminAsistidoFlujo,
            to=AdminAsistidoFlujo,
            scope=singleton,
        )
        binder.bind(
            AdminAsistidoOrchestrator,
            to=AdminAsistidoOrchestrator,
            scope=singleton,
        )


__all__ = ["AdministracionModule"]
