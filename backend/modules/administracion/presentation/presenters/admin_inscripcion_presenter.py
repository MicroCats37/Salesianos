"""
AdminInscripcionPresenter — pure transformer of the registrations, teams and
participants.

The presenter NEVER queries the database and NEVER calls a selector
(`contract/api-wrapper-presenter-contract.md` §3): it only maps result objects
into the typed HTTP wrappers.
"""

from core.pagination import PaginatedData
from modules.administracion.domain.results.admin_inscripcion_results import (
    AdminAceptacionListItemResult,
    AdminAsignacionListItemResult,
    AdminEquipoDetalleResult,
    AdminEquipoListItemResult,
    AdminInscripcionDetalleResult,
    AdminInscripcionListItemResult,
    AdminParticipacionListItemResult,
    AdminParticipanteListItemResult,
    AdminSaldoResult,
)
from modules.administracion.domain.results.admin_listado_results import (
    AdminListadoResult,
)
from modules.administracion.presentation.presenters.admin_paginacion_presenter import (
    AdminPaginacionPresenter,
)
from modules.administracion.presentation.presenters.admin_pago_presenter import (
    AdminPagoPresenter,
)
from modules.administracion.presentation.schemas.admin_inscripcion_schemas import (
    AdminAceptacionListItemOut,
    AdminAsignacionListItemOut,
    AdminEquipoDetalleOut,
    AdminEquipoListItemOut,
    AdminInscripcionDetailOut,
    AdminInscripcionListItemOut,
    AdminParticipacionListItemOut,
    AdminParticipanteListItemOut,
    AdminSaldoOut,
)


class AdminInscripcionPresenter:
    """Transformers of the registrations, teams and participants."""

    # ── Registrations ─────────────────────────────────────────────────────

    @staticmethod
    def present_item(result: AdminInscripcionListItemResult) -> AdminInscripcionListItemOut:
        """Map one registration into its list wrapper."""
        return AdminInscripcionListItemOut(
            id=result.id,
            evento_nombre=result.evento_nombre,
            responsable_nombre=result.responsable_nombre,
            responsable_documento=result.responsable_documento,
            paquete_nombre=result.paquete_nombre,
            promocion_nombre=result.promocion_nombre,
            estado=result.estado,
            equipos_total=result.equipos_total,
            equipos_completos=result.equipos_completos,
            personas=result.personas,
            participaciones=result.participaciones,
            cupos_contratados=result.cupos_contratados,
            cupos_pagados=result.cupos_pagados,
            cupos_disponibles=result.cupos_disponibles,
            monto_pagado=result.monto_pagado,
            created_at=result.created_at,
        )

    @staticmethod
    def present_listado(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminInscripcionListItemOut]:
        """Map a page of registrations into the canonical paginated payload."""
        items = [AdminInscripcionPresenter.present_item(item) for item in result.items]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )

    @staticmethod
    def present_detalle(
        result: AdminInscripcionDetalleResult,
    ) -> AdminInscripcionDetailOut:
        """Map the drilldown of a registration into its wrapper."""
        return AdminInscripcionDetailOut(
            **AdminInscripcionPresenter.present_item(result).model_dump(),
            delegado_nombre=result.delegado_nombre,
            observacion=result.observacion,
            fecha_limite_modificacion=result.fecha_limite_modificacion,
            equipos=[
                AdminInscripcionPresenter.present_equipo_detalle(equipo)
                for equipo in result.equipos
            ],
            participantes=[
                AdminInscripcionPresenter.present_participante(participante)
                for participante in result.participantes
            ],
            compras=[AdminPagoPresenter.present_item(compra) for compra in result.compras],
            asignaciones=[
                AdminInscripcionPresenter.present_asignacion(asignacion)
                for asignacion in result.asignaciones
            ],
            aceptaciones=[
                AdminInscripcionPresenter.present_aceptacion(aceptacion)
                for aceptacion in result.aceptaciones
            ],
            saldo=AdminInscripcionPresenter.present_saldo(result.saldo),
        )

    # ── Teams ─────────────────────────────────────────────────────────────

    @staticmethod
    def present_equipo(result: AdminEquipoListItemResult) -> AdminEquipoListItemOut:
        """Map one team into its list wrapper."""
        return AdminEquipoListItemOut(
            id=result.id,
            nombre=result.nombre,
            disciplina_sigla=result.disciplina_sigla,
            disciplina_nombre=result.disciplina_nombre,
            categoria_nombre=result.categoria_nombre,
            inscripcion_id=result.inscripcion_id,
            inscripcion_ref=result.inscripcion_ref,
            estado=result.estado,
            jugadores_registrados=result.jugadores_registrados,
            minimo_deportivo=result.minimo_deportivo,
            faltantes=result.faltantes,
            estado_roster=result.estado_roster,
            created_at=result.created_at,
        )

    @staticmethod
    def present_equipo_detalle(
        result: AdminEquipoDetalleResult,
    ) -> AdminEquipoDetalleOut:
        """Map one team with its roster rows into its drilldown wrapper."""
        return AdminEquipoDetalleOut(
            **AdminInscripcionPresenter.present_equipo(result).model_dump(),
            participaciones=[
                AdminInscripcionPresenter.present_participacion(participacion)
                for participacion in result.participaciones
            ],
        )

    @staticmethod
    def present_equipo_listado(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminEquipoListItemOut]:
        """Map a page of teams into the canonical paginated payload."""
        items = [AdminInscripcionPresenter.present_equipo(item) for item in result.items]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )

    # ── Participants ──────────────────────────────────────────────────────

    @staticmethod
    def present_participante(
        result: AdminParticipanteListItemResult,
    ) -> AdminParticipanteListItemOut:
        """Map one registered person into its wrapper."""
        return AdminParticipanteListItemOut(
            inscripcion_persona_id=result.inscripcion_persona_id,
            persona_id=result.persona_id,
            persona_nombre=result.persona_nombre,
            persona_documento=result.persona_documento,
            inscripcion_id=result.inscripcion_id,
            estado=result.estado,
            estado_pool=result.estado_pool,
            motivo_bloqueo=result.motivo_bloqueo,
            tiene_cupo_activo=result.tiene_cupo_activo,
            disciplinas=result.disciplinas,
            created_at=result.created_at,
        )

    @staticmethod
    def present_participacion(
        result: AdminParticipacionListItemResult,
    ) -> AdminParticipacionListItemOut:
        """Map one roster row into its wrapper."""
        return AdminParticipacionListItemOut(
            id=result.id,
            inscripcion_persona_id=result.inscripcion_persona_id,
            persona_nombre=result.persona_nombre,
            persona_documento=result.persona_documento,
            equipo_nombre=result.equipo_nombre,
            disciplina_sigla=result.disciplina_sigla,
            inscripcion_id=result.inscripcion_id,
            rol=result.rol,
            talla_camiseta=result.talla_camiseta,
            estado=result.estado,
            created_at=result.created_at,
        )

    @staticmethod
    def present_participante_listado(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminParticipanteListItemOut]:
        """Map a page of registered people into the canonical paginated payload."""
        items = [
            AdminInscripcionPresenter.present_participante(item)
            for item in result.items
        ]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )

    @staticmethod
    def present_participacion_listado(
        result: AdminListadoResult,
    ) -> PaginatedData[AdminParticipacionListItemOut]:
        """Map a page of roster rows into the canonical paginated payload."""
        items = [
            AdminInscripcionPresenter.present_participacion(item)
            for item in result.items
        ]
        return AdminPaginacionPresenter.present_paginado(
            items, result.total, result.params
        )

    # ── Blocks of the drilldown ───────────────────────────────────────────

    @staticmethod
    def present_asignacion(
        result: AdminAsignacionListItemResult,
    ) -> AdminAsignacionListItemOut:
        """Map one cup assignment into its wrapper."""
        return AdminAsignacionListItemOut(
            id=result.id,
            persona_nombre=result.persona_nombre,
            estado=result.estado,
            motivo=result.motivo,
            liberada_en=result.liberada_en,
            compra_id=result.compra_id,
            created_at=result.created_at,
        )

    @staticmethod
    def present_aceptacion(
        result: AdminAceptacionListItemResult,
    ) -> AdminAceptacionListItemOut:
        """Map one legal acceptance into its wrapper."""
        return AdminAceptacionListItemOut(
            persona_id=result.persona_id,
            tipo_aceptacion=result.tipo_aceptacion,
            documento_version=result.documento_version,
            aceptado_en=result.aceptado_en,
            medio=result.medio,
        )

    @staticmethod
    def present_saldo(result: AdminSaldoResult) -> AdminSaldoOut:
        """Map the cup balance into its wrapper."""
        return AdminSaldoOut(
            contratados=result.contratados,
            pagados=result.pagados,
            asignados_pagados=result.asignados_pagados,
            disponibles_pagados=result.disponibles_pagados,
        )


__all__ = ["AdminInscripcionPresenter"]
