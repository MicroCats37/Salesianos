"""
AdminOperacionOrchestrator — thin async facade of the operational queries
(A3–A14).

One public method per endpoint, and nothing else: it resolves the ACTIVE
event, delegates to `AdminOperacionService` and returns a result object. No
business rule lives here (`contract/django-app-architecture-contract.md` §4.5).

The ORM calls are sync, so they are wrapped with `sync_to_async` — never
`asyncio.to_thread` (the project convention for Django ORM in async code).
"""
from asgiref.sync import sync_to_async
from injector import inject

from modules.administracion.domain.results.admin_acreditacion_results import (
    AdminAccesoListItemResult,
    AdminAcreditacionDetalleResult,
    AdminAcreditacionListItemResult,
)
from modules.administracion.domain.results.admin_inscripcion_results import (
    AdminInscripcionDetalleResult,
    AdminInscripcionListItemResult,
    AdminParticipacionListItemResult,
    AdminParticipanteListItemResult,
)
from modules.administracion.domain.results.admin_listado_results import (
    AdminListadoResult,
)
from modules.administracion.domain.results.admin_pases_results import (
    AdminPaseCanceladaResult,
)
from modules.administracion.domain.results.admin_pago_results import (
    AdminPagoAnularManualResult,
    AdminPagoAprobarManualResult,
    AdminPagoDetalleResult,
    AdminPagoListItemResult,
)
from modules.administracion.domain.results.admin_usuario_results import (
    AdminUsuarioDetalleResult,
    AdminUsuarioListItemResult,
)
from modules.administracion.domain.services.core.admin_evento_activo_service import (
    AdminEventoActivoService,
)
from modules.administracion.domain.services.core.admin_operacion_service import (
    AdminOperacionService,
)
from modules.pagos.domain.schemas.aprobacion_pago_manual_schemas import (
    AprobacionPagoManualData,
)
from modules.pagos.domain.services.flujos.aprobar_pago_manual_flujo import (
    AprobarPagoManualFlujo,
)
from modules.salesianos_fest.domain.services.flujos.cancelar_compra_flujo import (
    CancelarCompraFlujo,
)


class AdminOperacionOrchestrator:
    """Async facade of the operational queries of the administration area."""

    @inject
    def __init__(
        self,
        evento_activo_service: AdminEventoActivoService,
        operacion_service: AdminOperacionService,
        aprobar_pago_manual_flujo: AprobarPagoManualFlujo,
        cancelar_compra_flujo: CancelarCompraFlujo,
    ):
        self.evento_activo_service = evento_activo_service
        self.operacion_service = operacion_service
        self.aprobar_pago_manual_flujo = aprobar_pago_manual_flujo
        self.cancelar_compra_flujo = cancelar_compra_flujo

        self._resolver_evento = sync_to_async(
            evento_activo_service.resolver_evento_activo
        )

    async def _evento_activo(self):
        """Resolve the ACTIVE event, server-side.

        Raises:
            EventoActivoNoEncontradoError: when there is no active edition.
        """
        return await self._resolver_evento()

    # ── A3 / A4 ───────────────────────────────────────────────────────────

    async def listar_inscripciones(self, **filtros) -> AdminListadoResult[
        AdminInscripcionListItemResult
    ]:
        """Return the page of registrations of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.listar_inscripciones)(
            evento, **filtros
        )

    async def obtener_inscripcion_detalle(
        self,
        inscripcion_id: str,
    ) -> AdminInscripcionDetalleResult:
        """Return the drilldown of one registration of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(
            self.operacion_service.obtener_inscripcion_detalle
        )(evento, inscripcion_id)

    # ── A5 / A6 ───────────────────────────────────────────────────────────

    async def listar_pagos(self, **filtros) -> AdminListadoResult[
        AdminPagoListItemResult
    ]:
        """Return the page of purchases of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.listar_pagos)(
            evento, **filtros
        )

    async def obtener_pago_detalle(
        self,
        orden_pago_id: str,
    ) -> AdminPagoDetalleResult:
        """Return the drilldown of one payment order of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.obtener_pago_detalle)(
            evento, orden_pago_id
        )

    # ── Aprobación y anulación manual del pago ─────────────────────────────

    async def aprobar_pago_manual(
        self,
        orden_pago_id: str,
        data: AprobacionPagoManualData,
        actor_id: str,
    ) -> AdminPagoAprobarManualResult:
        """
        Register the administrative approval of a manual payment.

        Delegates to `AprobarPagoManualFlujo`, the owner of the evidence and
        of the idempotency. The flow NEVER creates a provider transaction.
        """
        result = await self.aprobar_pago_manual_flujo._aprobar_pago_manual(
            orden_pago_id, data, actor_id
        )

        return AdminPagoAprobarManualResult(
            resultado=result.resultado,
            settlement_status=result.settlement_status,
            orden_pago_id=result.orden_pago_id,
            numero_orden=result.numero_orden,
            estado_orden=result.estado_orden,
            aprobacion_id=result.aprobacion_id,
            estado_aprobacion=result.estado_aprobacion,
            canal=result.canal,
            referencia=result.referencia,
            monto=float(result.monto),
            moneda=result.moneda,
            motivo=result.motivo,
            actor=result.actor,
            approved_at=result.approved_at,
        )

    async def anular_pago_manual(
        self,
        orden_pago_id: str,
        actor_id: str,
        motivo: str,
    ) -> AdminPagoAnularManualResult:
        """
        Annul the administrative approval of a manual payment.

        Delegates to `CancelarCompraFlujo`, the canonical owner of the
        revocation of the rights: the approval, the order and the purchase
        are updated atomically and only the rights funded by that purchase
        are revoked.
        """
        result = await self.cancelar_compra_flujo._anular_pago_manual(
            orden_pago_id, actor_id, motivo
        )

        return AdminPagoAnularManualResult(
            resultado=result.resultado,
            orden_pago_id=result.orden_pago_id,
            compra_id=result.compra_id,
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
            estado_aprobacion=result.estado_aprobacion,
            asignaciones_revocadas=result.asignaciones_revocadas,
            beneficiarios_revocados=result.beneficiarios_revocados,
            personas_afectadas=result.personas_afectadas,
            anulada_por=result.anulada_por,
            anulada_en=result.anulada_en,
            motivo_anulacion=result.motivo_anulacion,
        )

    # ── Cancelación administrativa de una compra de pases ───────────────────

    async def cancelar_compra_pase(
        self,
        compra_id: str,
        actor_id: str,
        motivo: str,
    ) -> AdminPaseCanceladaResult:
        """
        Cancel a pass purchase (administrative).

        Delegates to `CancelarCompraFlujo`, the canonical owner of the
        revocation of the rights: the purchase and its order are cancelled
        atomically, the nominative rights it funded are revoked and the
        effective access of every affected person is recomputed.

        It is NOT a monetary refund.
        """
        result = await self.cancelar_compra_flujo._cancelar_compra_pase(
            compra_id, actor_id, motivo
        )

        return AdminPaseCanceladaResult(
            compra_id=result.compra_id,
            estado_compra=result.estado_compra,
            estado_orden=result.estado_orden,
            ya_cancelada=result.ya_cancelada,
            beneficiarios_revocados=result.beneficiarios_revocados,
            personas_afectadas=result.personas_afectadas,
            motivo=result.motivo,
        )

    # ── A7 ────────────────────────────────────────────────────────────────

    async def listar_equipos(self, **filtros) -> AdminListadoResult:
        """Return the page of teams of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.listar_equipos)(
            evento, **filtros
        )

    # ── A8 / A9 ───────────────────────────────────────────────────────────

    async def listar_participantes(self, **filtros) -> AdminListadoResult[
        AdminParticipanteListItemResult
    ]:
        """Return the page of registered people of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.listar_participantes)(
            evento, **filtros
        )

    async def listar_participaciones(self, **filtros) -> AdminListadoResult[
        AdminParticipacionListItemResult
    ]:
        """Return the page of roster rows of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.listar_participaciones)(
            evento, **filtros
        )

    # ── A10 / A11 / A12 ───────────────────────────────────────────────────

    async def listar_acreditaciones(self, **filtros) -> AdminListadoResult[
        AdminAcreditacionListItemResult
    ]:
        """Return the page of accreditations of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.listar_acreditaciones)(
            evento, **filtros
        )

    async def obtener_acreditacion_detalle(
        self,
        acreditacion_id: str,
    ) -> AdminAcreditacionDetalleResult:
        """Return the drilldown of one accreditation of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(
            self.operacion_service.obtener_acreditacion_detalle
        )(evento, acreditacion_id)

    async def listar_accesos(self, **filtros) -> AdminListadoResult[
        AdminAccesoListItemResult
    ]:
        """Return the page of access records of the active event."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.listar_accesos)(
            evento, **filtros
        )

    # ── A13 / A14 ─────────────────────────────────────────────────────────

    async def listar_usuarios(self, **filtros) -> AdminListadoResult[
        AdminUsuarioListItemResult
    ]:
        """Return the page of accounts."""
        return await sync_to_async(self.operacion_service.listar_usuarios)(**filtros)

    async def obtener_usuario_detalle(
        self,
        usuario_id: str,
    ) -> AdminUsuarioDetalleResult:
        """Return the drilldown of one account."""
        evento = await self._evento_activo()
        return await sync_to_async(self.operacion_service.obtener_usuario_detalle)(
            evento, usuario_id
        )


__all__ = ["AdminOperacionOrchestrator"]
