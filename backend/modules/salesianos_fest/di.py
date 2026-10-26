"""Dependency injection bindings for salesianos_fest module."""
from injector import Module, Binder, singleton

from modules.salesianos_fest.domain.selectors import (
    DisciplinaSelector,
    PromocionSelector,
    CategoriaSelector,
    PaqueteSelector,
    InscripcionSelector,
    EquipoSelector,
    ParticipacionSelector,
    CompraSelector,
    AsignacionSelector,
    AcreditacionSelector,
    ControlAccesoSelector,
    AceptacionInscripcionSelector,
)
from modules.salesianos_fest.domain.services.core.inscripcion_service import InscripcionCoreService
from modules.salesianos_fest.domain.services.core.equipo_service import EquipoCoreService
from modules.salesianos_fest.domain.services.core.participacion_service import ParticipacionCoreService
from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.services.orchestrators.inscripcion_orchestrator import InscripcionOrchestrator
from modules.salesianos_fest.domain.services.orchestrators.equipo_orchestrator import EquipoOrchestrator
from modules.salesianos_fest.domain.services.orchestrators.participacion_orchestrator import ParticipacionOrchestrator
from modules.salesianos_fest.domain.services.orchestrators.compra_orchestrator import CompraOrchestrator
from modules.salesianos_fest.domain.services.orchestrators.asignacion_orchestrator import AsignacionOrchestrator
from modules.salesianos_fest.domain.services.orchestrators.acreditacion_orchestrator import AcreditacionOrchestrator
from modules.salesianos_fest.domain.services.flujos.crear_compra_flujo import CrearCompraFlujo
from modules.salesianos_fest.domain.services.flujos.iniciar_pago_flujo import IniciarPagoFlujo
from modules.salesianos_fest.domain.services.flujos.confirmar_pago_flujo import ConfirmarPagoFlujo
from modules.salesianos_fest.domain.services.flujos.reconciliar_pagos_flujo import (
    ReconciliarPagosFlujo,
)
from modules.salesianos_fest.domain.services.flujos.reparar_cupos_flujo import (
    RepararCuposFlujo,
)
from modules.salesianos_fest.domain.services.flujos.cancelar_compra_flujo import CancelarCompraFlujo
from modules.salesianos_fest.domain.services.flujos.asignar_persona_flujo import AsignarPersonaFlujo
from modules.salesianos_fest.domain.services.flujos.liberar_cupo_flujo import LiberarCupoFlujo
from modules.salesianos_fest.domain.services.flujos.crear_asignaciones_flujo import CrearAsignacionesFlujo
from modules.salesianos_fest.domain.services.flujos.override_fiesta_flujo import OverrideFiestaFlujo
from modules.salesianos_fest.domain.services.flujos.registrar_acceso_flujo import RegistrarAccesoFlujo
from modules.pagos.domain.ports import IConfirmadorOrdenPagoService
from modules.pagos.domain.services.orchestrators.pagos_orchestrator import PagosOrchestrator
from modules.salesianos_fest.infrastructure.services import ConfirmadorOrdenPagoAdapter


class SalesianosFestModule(Module):
    """Injector module for salesianos_fest module dependencies."""

    def configure(self, binder: Binder) -> None:
        """Register selector and service bindings."""
        # Selectors
        binder.bind(DisciplinaSelector, to=DisciplinaSelector)
        binder.bind(PromocionSelector, to=PromocionSelector)
        binder.bind(CategoriaSelector, to=CategoriaSelector)
        binder.bind(PaqueteSelector, to=PaqueteSelector)
        binder.bind(InscripcionSelector, to=InscripcionSelector)
        binder.bind(EquipoSelector, to=EquipoSelector)
        binder.bind(ParticipacionSelector, to=ParticipacionSelector)
        binder.bind(CompraSelector, to=CompraSelector)
        binder.bind(AsignacionSelector, to=AsignacionSelector)
        binder.bind(AcreditacionSelector, to=AcreditacionSelector)
        binder.bind(ControlAccesoSelector, to=ControlAccesoSelector)
        binder.bind(AceptacionInscripcionSelector, to=AceptacionInscripcionSelector)

        # Core services
        binder.bind(InscripcionCoreService, to=InscripcionCoreService)
        binder.bind(EquipoCoreService, to=EquipoCoreService)
        binder.bind(ParticipacionCoreService, to=ParticipacionCoreService)
        binder.bind(AsignacionCoreService, to=AsignacionCoreService)
        binder.bind(AcreditacionCoreService, to=AcreditacionCoreService)

        # Orchestrators
        binder.bind(InscripcionOrchestrator, to=InscripcionOrchestrator)
        binder.bind(EquipoOrchestrator, to=EquipoOrchestrator)
        binder.bind(ParticipacionOrchestrator, to=ParticipacionOrchestrator)
        binder.bind(CompraOrchestrator, to=CompraOrchestrator)
        binder.bind(AsignacionOrchestrator, to=AsignacionOrchestrator)
        binder.bind(AcreditacionOrchestrator, to=AcreditacionOrchestrator)

        # Flujos
        binder.bind(CrearCompraFlujo, to=CrearCompraFlujo)
        binder.bind(IniciarPagoFlujo, to=IniciarPagoFlujo)
        binder.bind(ConfirmarPagoFlujo, to=ConfirmarPagoFlujo)
        binder.bind(ReconciliarPagosFlujo, to=ReconciliarPagosFlujo)
        binder.bind(RepararCuposFlujo, to=RepararCuposFlujo)
        binder.bind(CancelarCompraFlujo, to=CancelarCompraFlujo)
        binder.bind(AsignarPersonaFlujo, to=AsignarPersonaFlujo)
        binder.bind(LiberarCupoFlujo, to=LiberarCupoFlujo)
        binder.bind(CrearAsignacionesFlujo, to=CrearAsignacionesFlujo)
        binder.bind(OverrideFiestaFlujo, to=OverrideFiestaFlujo)
        binder.bind(RegistrarAccesoFlujo, to=RegistrarAccesoFlujo)

        # External orchestrator binding (pagos module)
        binder.bind(PagosOrchestrator, to=PagosOrchestrator)

        # Port binding: pagos drives the commercial settlement of a paid order.
        # Implemented here so `pagos` never imports `salesianos_fest`.
        binder.bind(
            IConfirmadorOrdenPagoService,
            to=ConfirmadorOrdenPagoAdapter,
            scope=singleton,
        )
