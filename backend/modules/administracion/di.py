"""
Dependency injection wiring for the administracion module.

Registered in `config/settings/base.py` via
`NINJA_EXTRA["INJECTOR_MODULES"]`.

The module binds only what it OWNS:

- `AdminPaginacionService` — the canonical pagination/search/sort rules.
- `AdminFundacionOrchestrator` — the async facade of the foundation probe.
- `AdminResumenSelector` / `AdminConsultaService` /
  `AdminResumenOrchestrator` — the operational overview (A1) and its catalogs
  (A2).
- `AdminEventoActivoService` — the resolution of the ACTIVE event.
- The `Admin*Selector` of the operational tables (A3–A14),
  `AdminOperacionService` and `AdminOperacionOrchestrator`.

The selectors of the business modules (`EventoSelector`, `UsuarioSelector`,
`PersonaSelector`, `ControlAccesoSelector`, `AceptacionInscripcionSelector`)
are bound by THEIR OWN modules: each module wires the collaborators it owns,
so the dependency direction stays `administracion → business modules` and never
the other way round.
"""
from injector import Binder, Module, singleton

from modules.administracion.domain.selectors.admin_acreditacion_selector import (
    AdminAcreditacionSelector,
)
from modules.administracion.domain.selectors.admin_equipo_selector import (
    AdminEquipoSelector,
)
from modules.administracion.domain.selectors.admin_inscripcion_selector import (
    AdminInscripcionSelector,
)
from modules.administracion.domain.selectors.admin_pago_selector import (
    AdminPagoSelector,
)
from modules.administracion.domain.selectors.admin_participante_selector import (
    AdminParticipanteSelector,
)
from modules.administracion.domain.selectors.admin_resumen_selector import (
    AdminResumenSelector,
)
from modules.administracion.domain.selectors.admin_usuario_selector import (
    AdminUsuarioSelector,
)
from modules.administracion.domain.services.core.admin_consulta_service import (
    AdminConsultaService,
)
from modules.administracion.domain.services.core.admin_evento_activo_service import (
    AdminEventoActivoService,
)
from modules.administracion.domain.services.core.admin_operacion_service import (
    AdminOperacionService,
)
from modules.administracion.domain.services.core.admin_paginacion_service import (
    AdminPaginacionService,
)
from modules.administracion.domain.services.orchestrators.admin_fundacion_orchestrator import (
    AdminFundacionOrchestrator,
)
from modules.administracion.domain.services.orchestrators.admin_operacion_orchestrator import (
    AdminOperacionOrchestrator,
)
from modules.administracion.domain.services.orchestrators.admin_resumen_orchestrator import (
    AdminResumenOrchestrator,
)
from modules.pagos.domain.services.core.evidencia_pago_service import (
    EvidenciaPagoService,
)
from modules.pagos.domain.services.flujos.aprobar_pago_manual_flujo import (
    AprobarPagoManualFlujo,
)


class AdministracionModule(Module):
    """Injector module for the administracion module dependencies."""

    def configure(self, binder: Binder) -> None:
        """Register the admin services."""
        binder.bind(AdminPaginacionService, to=AdminPaginacionService, scope=singleton)
        binder.bind(AdminResumenSelector, to=AdminResumenSelector, scope=singleton)
        binder.bind(AdminConsultaService, to=AdminConsultaService, scope=singleton)
        binder.bind(
            AdminFundacionOrchestrator,
            to=AdminFundacionOrchestrator,
            scope=singleton,
        )
        binder.bind(
            AdminResumenOrchestrator,
            to=AdminResumenOrchestrator,
            scope=singleton,
        )

        # ── Operational tables (A3–A14) ────────────────────────────────────
        binder.bind(
            AdminEventoActivoService,
            to=AdminEventoActivoService,
            scope=singleton,
        )
        binder.bind(
            AdminInscripcionSelector,
            to=AdminInscripcionSelector,
            scope=singleton,
        )
        binder.bind(AdminPagoSelector, to=AdminPagoSelector, scope=singleton)
        binder.bind(AdminEquipoSelector, to=AdminEquipoSelector, scope=singleton)
        binder.bind(
            AdminParticipanteSelector,
            to=AdminParticipanteSelector,
            scope=singleton,
        )
        binder.bind(
            AdminAcreditacionSelector,
            to=AdminAcreditacionSelector,
            scope=singleton,
        )
        binder.bind(
            AdminUsuarioSelector,
            to=AdminUsuarioSelector,
            scope=singleton,
        )
        binder.bind(
            AdminOperacionService,
            to=AdminOperacionService,
            scope=singleton,
        )
        binder.bind(
            AdminOperacionOrchestrator,
            to=AdminOperacionOrchestrator,
            scope=singleton,
        )

        # ── Aprobación manual del pago ─────────────────────────────────────
        # The administration area is the CONSUMER of the manual approval: it
        # binds the flow of the payment module and the truth predicate of the
        # payment evidence.
        binder.bind(
            EvidenciaPagoService,
            to=EvidenciaPagoService,
            scope=singleton,
        )
        binder.bind(
            AprobarPagoManualFlujo,
            to=AprobarPagoManualFlujo,
            scope=singleton,
        )


__all__ = ["AdministracionModule"]
