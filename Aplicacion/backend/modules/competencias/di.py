"""Wiring de dependencias (DI) del módulo `competencias`.

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las ligas del módulo.

**Las dos ligas que cruzan de dominio son PUERTOS**, y los implementa la
infraestructura de ESTE módulo para que el dominio no dependa del módulo
ajeno:

- `IEquipoElegibleService` → `EquipoElegibleAdapter`: la elegibilidad
  deportiva de un equipo, que decide `modules.salesianos_fest`
  (`RN-K01`, `QA-K01`). El adaptador consulta al DUEÑO y traduce su
  veredicto; no reimplementa ninguna regla.
- `IAlcanceEdicion` → `AlcanceEdicionEventos`: el alcance de edición, que
  decide `modules.eventos` con el ORDEN CONGELADO de `FR-02` §2.2.

El adaptador de elegibilidad necesita el modelo `Equipo` y el modelo
`Participacion` de `salesianos_fest`: son los HECHOS que consulta, no una
regla que reinterprete.
"""

from injector import Binder, Module, singleton

from modules.competencias.domain.ports import (
    IAlcanceEdicion,
    IEquipoElegibleService,
    IEquiposDeParticipante,
)
from modules.competencias.domain.selectors.competencia_selector import (
    CompetenciaSelector,
)
from modules.competencias.domain.selectors.encuentro_selector import (
    EncuentroSelector,
)
from modules.competencias.domain.services.core.auditoria_core_service import (
    AuditoriaCoreService,
)
from modules.competencias.domain.services.core.avance_core_service import (
    AvanceCoreService,
)
from modules.competencias.domain.services.core.competencia_core_service import (
    CompetenciaCoreService,
    CompetenciaEquipoCoreService,
    RondaCoreService,
)
from modules.competencias.domain.services.core.correccion_core_service import (
    CorreccionCoreService,
)
from modules.competencias.domain.services.core.encuentro_core_service import (
    EncuentroCoreService,
)
from modules.competencias.domain.services.core.programacion_core_service import (
    ProgramacionCoreService,
)
from modules.competencias.domain.services.core.resultado_core_service import (
    ResultadoCoreService,
)
from modules.competencias.domain.services.flujos.avance_flujo import AvanceFlujo
from modules.competencias.domain.services.flujos.correccion_flujo import CorreccionFlujo
from modules.competencias.domain.services.flujos.cuadro_flujo import CuadroFlujo
from modules.competencias.domain.services.flujos.encuentro_flujo import EncuentroFlujo
from modules.competencias.domain.services.flujos.resultado_flujo import ResultadoFlujo
from modules.competencias.domain.services.orchestrators.competencias_orchestrator import (
    CompetenciasOrchestrator,
)
from modules.competencias.infrastructure.services.alcance_edicion_eventos import (
    AlcanceEdicionEventos,
)
from modules.competencias.infrastructure.services.equipo_elegible_adapter import (
    EquipoElegibleAdapter,
)
from modules.competencias.infrastructure.services.equipos_participante_adapter import (
    EquiposDeParticipanteAdapter,
)


class CompetenciasModule(Module):
    """Bindings de dependencias del módulo `competencias`."""

    def configure(self, binder: Binder) -> None:
        # ── Puertos hacia los módulos DUEÑOS ───────────────────────────────
        binder.bind(
            IEquipoElegibleService,
            to=EquipoElegibleAdapter,
            scope=singleton,
        )
        binder.bind(
            IAlcanceEdicion,
            to=AlcanceEdicionEventos,
            scope=singleton,
        )
        binder.bind(
            IEquiposDeParticipante,
            to=EquiposDeParticipanteAdapter,
            scope=singleton,
        )

        # ── Selectores ─────────────────────────────────────────────────────
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

        # ── Servicios core (sync) ──────────────────────────────────────────
        binder.bind(AuditoriaCoreService, to=AuditoriaCoreService, scope=singleton)
        binder.bind(
            CompetenciaCoreService,
            to=CompetenciaCoreService,
            scope=singleton,
        )
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
        binder.bind(ResultadoCoreService, to=ResultadoCoreService, scope=singleton)
        binder.bind(AvanceCoreService, to=AvanceCoreService, scope=singleton)
        binder.bind(CorreccionCoreService, to=CorreccionCoreService, scope=singleton)

        # ── Flujos (async) y orquestador ────────────────────────────────────
        binder.bind(CuadroFlujo, to=CuadroFlujo, scope=singleton)
        binder.bind(EncuentroFlujo, to=EncuentroFlujo, scope=singleton)
        binder.bind(ResultadoFlujo, to=ResultadoFlujo, scope=singleton)
        binder.bind(AvanceFlujo, to=AvanceFlujo, scope=singleton)
        binder.bind(CorreccionFlujo, to=CorreccionFlujo, scope=singleton)
        binder.bind(
            CompetenciasOrchestrator,
            to=CompetenciasOrchestrator,
            scope=singleton,
        )


__all__ = ["CompetenciasModule"]
