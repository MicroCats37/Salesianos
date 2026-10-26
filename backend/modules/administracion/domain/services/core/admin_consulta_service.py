"""
AdminConsultaService — read-only composition of the operational aggregates.

Sync by contract (`contract/django-app-architecture-contract.md` §4.3): no
`async def`, no `transaction.atomic`, no write path. The service is the only
place that ASSEMBLES the metrics of the overview and the option lists of the
filters; it never re-implements a business rule of the owning modules — it
reads their selectors and their domain constants.

- The aggregates come from `AdminResumenSelector` (this module).
- The access counters come from `ControlAccesoSelector` (`salesianos_fest`).
- The catalogs come from `DisciplinaSelector`, `PromocionSelector`,
  `CategoriaSelector` and `PaqueteSelector` (`salesianos_fest`).
"""
from injector import inject

from modules.administracion.domain.results.admin_catalogos_results import (
    AdminCatalogoItemResult,
    AdminCatalogoPaqueteResult,
    AdminCatalogosResult,
    AdminEstadosCatalogosResult,
)
from modules.administracion.domain.results.admin_resumen_results import (
    AdminAcreditacionesResumenResult,
    AdminAccesosResumenResult,
    AdminCuposResumenResult,
    AdminDisciplinaConteoResult,
    AdminEquiposResumenResult,
    AdminInscripcionesResumenResult,
    AdminPagosResumenResult,
    AdminParticipantesResumenResult,
    AdminResumenResult,
    EventoResumenResult,
)
from modules.administracion.domain.selectors.admin_resumen_selector import (
    AdminResumenSelector,
)
from modules.commerce.domain.constants import EstadoCompraChoices
from modules.eventos.domain.models import Evento
from modules.pagos.domain.constants import OrdenPagoStatus
from modules.salesianos_fest.domain.constants import (
    AutorizacionFiestaChoices,
    EstadoAcreditacionChoices,
    EstadoAsignacionCupoChoices,
    EstadoEquipoChoices,
    EstadoInscripcionChoices,
    EstadoPoolChoices,
    ResultadoAccesoChoices,
    RolParticipanteChoices,
)
from modules.salesianos_fest.domain.selectors import (
    CategoriaSelector,
    ControlAccesoSelector,
    DisciplinaSelector,
    PaqueteSelector,
    PromocionSelector,
)


class AdminConsultaService:
    """Composition of the operational aggregates and the filter catalogs."""

    @inject
    def __init__(
        self,
        resumen_selector: AdminResumenSelector,
        control_acceso_selector: ControlAccesoSelector,
        disciplina_selector: DisciplinaSelector,
        promocion_selector: PromocionSelector,
        categoria_selector: CategoriaSelector,
        paquete_selector: PaqueteSelector,
    ):
        self.resumen_selector = resumen_selector
        self.control_acceso_selector = control_acceso_selector
        self.disciplina_selector = disciplina_selector
        self.promocion_selector = promocion_selector
        self.categoria_selector = categoria_selector
        self.paquete_selector = paquete_selector

    # ── Overview ────────────────────────────────────────────────────────────

    def construir_resumen(self, evento: Evento) -> AdminResumenResult:
        """Build the eight blocks of the operational overview.

        Args:
            evento: the ACTIVE event, resolved by the orchestrator.

        Returns:
            The result DTO the presenter maps into the HTTP wrapper.
        """
        evento_id = str(evento.id)

        inscripciones = self.resumen_selector.contar_inscripciones(evento_id)
        pagos = self.resumen_selector.contar_compras(evento_id)
        cupos = self.resumen_selector.contar_cupos(evento_id)
        equipos = self.resumen_selector.contar_equipos(evento_id)
        participantes = self.resumen_selector.contar_participantes(evento_id)
        acreditaciones = self.resumen_selector.contar_acreditaciones(evento_id)

        accesos = self.control_acceso_selector.contar_por_evento(evento_id)
        ultimo_acceso = self.control_acceso_selector.ultimo_acceso_por_evento(evento_id)

        return AdminResumenResult(
            evento=EventoResumenResult(
                id=str(evento.id),
                nombre=evento.nombre,
                fecha_inicio=evento.fecha_inicio,
                fecha_fin=evento.fecha_fin,
                esta_activo=evento.esta_activo,
                fecha_limite_modificacion=evento.fecha_limite_modificacion,
                puede_modificar=evento.puede_modificar(),
            ),
            inscripciones=AdminInscripcionesResumenResult(
                total=inscripciones["total"],
                por_estado=self._completar_vocabulario(
                    inscripciones["por_estado"], EstadoInscripcionChoices
                ),
                creadas_ultimos_7_dias=inscripciones["creadas_ultimos_7_dias"],
            ),
            pagos=AdminPagosResumenResult(
                compras_total=pagos["compras_total"],
                compras_pagadas=pagos["compras_pagadas"],
                compras_pendientes=pagos["compras_pendientes"],
                compras_canceladas=pagos["compras_canceladas"],
                monto_pagado=float(pagos["monto_pagado"]),
                monto_pendiente=float(pagos["monto_pendiente"]),
                ordenes_vencidas=pagos["ordenes_vencidas"],
                compras_pagadas_sin_liquidar=pagos["compras_pagadas_sin_liquidar"],
            ),
            cupos=AdminCuposResumenResult(
                contratado=cupos["contratado"],
                pagado=cupos["pagado"],
                asignado_activo=cupos["asignado_activo"],
                disponible_pagado=cupos["disponible_pagado"],
                inscripciones_con_capacidad_exhaustada=cupos[
                    "inscripciones_con_capacidad_exhaustada"
                ],
            ),
            equipos=AdminEquiposResumenResult(
                total=equipos["total"],
                completos=equipos["completos"],
                incompletos=equipos["incompletos"],
                por_disciplina=[
                    AdminDisciplinaConteoResult(
                        disciplina_id=item["disciplina_id"],
                        sigla=item["sigla"],
                        nombre=item["nombre"],
                        total=item["total"],
                    )
                    for item in equipos["por_disciplina"]
                ],
            ),
            participantes=AdminParticipantesResumenResult(
                personas_distintas=participantes["personas_distintas"],
                participaciones_activas=participantes["participaciones_activas"],
                en_pool=participantes["en_pool"],
                sin_cupo_activo=participantes["sin_cupo_activo"],
            ),
            acreditaciones=AdminAcreditacionesResumenResult(
                total=acreditaciones["total"],
                por_estado=self._completar_vocabulario(
                    acreditaciones["por_estado"], EstadoAcreditacionChoices
                ),
                con_acceso_fiesta=acreditaciones["con_acceso_fiesta"],
                bloqueadas_por_admin=acreditaciones["bloqueadas_por_admin"],
            ),
            accesos=AdminAccesosResumenResult(
                permitidos=accesos[ResultadoAccesoChoices.PERMITIDO],
                denegados=accesos[ResultadoAccesoChoices.DENEGADO],
                ultimo_acceso=ultimo_acceso,
            ),
        )

    # ── Catalogs ────────────────────────────────────────────────────────────

    def construir_catalogos(self, evento: Evento) -> AdminCatalogosResult:
        """Build the filter option lists of the active event.

        The option lists come from the OWNING modules' selectors — the admin
        module never re-implements the catalog rules, it only scopes the
        packages to the active event.
        """
        evento_id = str(evento.id)

        disciplinas = [
            AdminCatalogoItemResult(
                id=item.id,
                nombre=item.nombre,
                sigla=item.sigla,
            )
            for item in self.disciplina_selector.get_activas()
        ]

        promociones = [
            AdminCatalogoItemResult(id=item.id, nombre=item.nombre)
            for item in self.promocion_selector.get_activas()
        ]

        categorias = [
            AdminCatalogoItemResult(id=item.id, nombre=item.nombre)
            for item in self.categoria_selector.get_by_evento(evento_id)
        ]

        paquetes = [
            AdminCatalogoPaqueteResult(
                id=item.id,
                nombre=item.nombre,
                tipo=item.tipo,
            )
            for item in self.paquete_selector.get_activos()
            if str(item.evento_id) == evento_id
        ]

        return AdminCatalogosResult(
            evento_id=evento_id,
            evento_nombre=evento.nombre,
            disciplinas=disciplinas,
            paquetes=paquetes,
            promociones=promociones,
            categorias=categorias,
            puntos_acceso=self.control_acceso_selector.puntos_acceso_por_evento(
                evento_id
            ),
            estados=AdminEstadosCatalogosResult(
                inscripcion=self._valores(EstadoInscripcionChoices),
                compra=self._valores(EstadoCompraChoices),
                orden_pago=self._valores(OrdenPagoStatus),
                asignacion_cupo=self._valores(EstadoAsignacionCupoChoices),
                equipo=self._valores(EstadoEquipoChoices),
                acreditacion=self._valores(EstadoAcreditacionChoices),
                autorizacion_fiesta=self._valores(AutorizacionFiestaChoices),
                acceso=self._valores(ResultadoAccesoChoices),
                pool=self._valores(EstadoPoolChoices),
                rol_participante=self._valores(RolParticipanteChoices),
            ),
        )

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _valores(choices) -> list[str]:
        """Return the values of a domain vocabulary, in declaration order."""
        return [valor for valor, _etiqueta in choices.choices]

    @staticmethod
    def _completar_vocabulario(conteo: dict[str, int], choices) -> dict[str, int]:
        """Complete a counter map with the whole vocabulary.

        A state with no rows is reported as ZERO, never as a missing key: the
        frontend never has to guess whether the state exists.
        """
        completo = {valor: 0 for valor, _etiqueta in choices.choices}
        completo.update(conteo)
        return completo


__all__ = ["AdminConsultaService"]
