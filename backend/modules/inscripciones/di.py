"""
Inscripciones module — Dependency Injection wiring.
"""
from injector import Module, singleton, Binder

from modules.inscripciones.domain.services.core.disciplina_service import DisciplinaService
from modules.inscripciones.domain.services.core.paquete_service import PaqueteService
from modules.inscripciones.domain.services.core.evento_service import EventoService
from modules.inscripciones.domain.services.core.inscripcion_service import InscripcionService
from modules.inscripciones.domain.services.core.equipo_service import EquipoService
from modules.inscripciones.domain.services.core.participacion_service import ParticipacionService
from modules.inscripciones.domain.services.core.participante_service import ParticipanteService
from modules.inscripciones.domain.services.flujos.crear_inscripcion_flujo import CrearInscripcionFlujo
from modules.inscripciones.domain.services.flujos.agregar_participante_flujo import AgregarParticipanteFlujo
from modules.inscripciones.domain.services.flujos.agregar_participantes_flujo import AgregarParticipantesFlujo
from modules.inscripciones.domain.services.flujos.cambiar_estado_inscripcion_flujo import (
    CambiarEstadoInscripcionFlujo,
)
from modules.inscripciones.domain.services.flujos.asignar_delegado_flujo import AsignarDelegadoFlujo
from modules.inscripciones.domain.services.flujos.participante_accion_flujo import ParticipanteAccionFlujo
from modules.inscripciones.domain.services.orchestrators.inscripcion_orchestrator import (
    InscripcionOrchestrator,
)
from modules.inscripciones.domain.selectors.inscripcion_selector import InscripcionSelector
from modules.usuarios.domain.services.core.persona_core_service import PersonaCoreService


class InscripcionesModule(Module):
    """
    DI module for the inscripciones package.
    """

    def configure(self, binder: Binder) -> None:
        # Core services
        binder.bind(DisciplinaService, to=DisciplinaService, scope=singleton)
        binder.bind(PaqueteService, to=PaqueteService, scope=singleton)
        binder.bind(EventoService, to=EventoService, scope=singleton)
        binder.bind(InscripcionService, to=InscripcionService, scope=singleton)
        binder.bind(EquipoService, to=EquipoService, scope=singleton)
        binder.bind(ParticipacionService, to=ParticipacionService, scope=singleton)
        binder.bind(ParticipanteService, to=ParticipanteService, scope=singleton)

        # Cross-module: PersonaCoreService (usuarios module)
        binder.bind(PersonaCoreService, to=PersonaCoreService, scope=singleton)

        # Flujos
        binder.bind(CrearInscripcionFlujo, to=CrearInscripcionFlujo, scope=singleton)
        binder.bind(AgregarParticipanteFlujo, to=AgregarParticipanteFlujo, scope=singleton)
        binder.bind(AgregarParticipantesFlujo, to=AgregarParticipantesFlujo, scope=singleton)
        binder.bind(CambiarEstadoInscripcionFlujo, to=CambiarEstadoInscripcionFlujo, scope=singleton)
        binder.bind(AsignarDelegadoFlujo, to=AsignarDelegadoFlujo, scope=singleton)
        binder.bind(ParticipanteAccionFlujo, to=ParticipanteAccionFlujo, scope=singleton)

        # Orchestrator
        binder.bind(InscripcionOrchestrator, to=InscripcionOrchestrator, scope=singleton)

        # Selector
        binder.bind(InscripcionSelector, to=InscripcionSelector, scope=singleton)
