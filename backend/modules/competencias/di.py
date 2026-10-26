"""Dependency injection bindings for the competencias module."""
from injector import Binder, Module, singleton

from .domain.selectors import (
    AlcanceEventoSelector,
    CompetenciaSelector,
    EncuentroSelector,
)
from .domain.services.core.avance_service import AvanceCoreService
from .domain.services.core.competencia_equipo_service import (
    CompetenciaEquipoCoreService,
)
from .domain.services.core.competencia_service import CompetenciaCoreService
from .domain.services.core.correccion_service import CorreccionCoreService
from .domain.services.core.encuentro_service import EncuentroCoreService
from .domain.services.core.programacion_service import ProgramacionCoreService
from .domain.services.core.resultado_service import ResultadoCoreService
from .domain.services.core.ronda_service import RondaCoreService
from .domain.services.orchestrators.avance_orchestrator import AvanceOrchestrator
from .domain.services.orchestrators.competencia_equipo_orchestrator import (
    CompetenciaEquipoOrchestrator,
)
from .domain.services.orchestrators.competencia_lectura_orchestrator import (
    CompetenciaLecturaOrchestrator,
    CompetenciaPublicaLecturaOrchestrator,
)
from .domain.services.orchestrators.competencia_orchestrator import (
    CompetenciaOrchestrator,
)
from .domain.services.orchestrators.correccion_orchestrator import (
    CorreccionOrchestrator,
)
from .domain.services.orchestrators.encuentro_orchestrator import (
    EncuentroOrchestrator,
)
from .domain.services.orchestrators.resultado_orchestrator import (
    ResultadoOrchestrator,
)
from .domain.services.orchestrators.ronda_orchestrator import RondaOrchestrator


class CompetenciasModule(Module):
    """Injector module of the competencias module.

    The core services are singletons: they are stateless and the bracket is
    always consistent inside a single transaction.
    """

    def configure(self, binder: Binder) -> None:
        """Bind the services and the orchestrators of the module."""
        binder.bind(CompetenciaCoreService, to=CompetenciaCoreService, scope=singleton)
        binder.bind(
            CompetenciaEquipoCoreService,
            to=CompetenciaEquipoCoreService,
            scope=singleton,
        )
        binder.bind(RondaCoreService, to=RondaCoreService, scope=singleton)
        binder.bind(EncuentroCoreService, to=EncuentroCoreService, scope=singleton)
        binder.bind(
            ProgramacionCoreService,
            to=ProgramacionCoreService,
            scope=singleton,
        )
        binder.bind(
            CompetenciaOrchestrator,
            to=CompetenciaOrchestrator,
            scope=singleton,
        )
        binder.bind(
            CompetenciaEquipoOrchestrator,
            to=CompetenciaEquipoOrchestrator,
            scope=singleton,
        )
        binder.bind(RondaOrchestrator, to=RondaOrchestrator, scope=singleton)
        binder.bind(EncuentroOrchestrator, to=EncuentroOrchestrator, scope=singleton)
        binder.bind(ResultadoCoreService, to=ResultadoCoreService, scope=singleton)
        binder.bind(AvanceCoreService, to=AvanceCoreService, scope=singleton)
        binder.bind(CorreccionCoreService, to=CorreccionCoreService, scope=singleton)
        binder.bind(ResultadoOrchestrator, to=ResultadoOrchestrator, scope=singleton)
        binder.bind(AvanceOrchestrator, to=AvanceOrchestrator, scope=singleton)
        binder.bind(
            CorreccionOrchestrator,
            to=CorreccionOrchestrator,
            scope=singleton,
        )
        # ── Phase 3: the read surface (selectors + read orchestrators) ──────
        binder.bind(
            AlcanceEventoSelector,
            to=AlcanceEventoSelector,
            scope=singleton,
        )
        binder.bind(
            CompetenciaSelector,
            to=CompetenciaSelector,
            scope=singleton,
        )
        binder.bind(
            EncuentroSelector,
            to=EncuentroSelector,
            scope=singleton,
        )
        binder.bind(
            CompetenciaLecturaOrchestrator,
            to=CompetenciaLecturaOrchestrator,
            scope=singleton,
        )
        binder.bind(
            CompetenciaPublicaLecturaOrchestrator,
            to=CompetenciaPublicaLecturaOrchestrator,
            scope=singleton,
        )
