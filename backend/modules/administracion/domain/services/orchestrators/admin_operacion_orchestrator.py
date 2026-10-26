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
from modules.administracion.domain.results.admin_pago_results import (
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


class AdminOperacionOrchestrator:
    """Async facade of the operational queries of the administration area."""

    @inject
    def __init__(
        self,
        evento_activo_service: AdminEventoActivoService,
        operacion_service: AdminOperacionService,
    ):
        self.evento_activo_service = evento_activo_service
        self.operacion_service = operacion_service

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
