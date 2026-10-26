"""
AdminResumenOrchestrator — thin async facade of the operational overview.

One public method per endpoint, and nothing else: it resolves the ACTIVE
event, delegates the aggregation to `AdminConsultaService` and returns a
result object. No business rule lives here
(`contract/django-app-architecture-contract.md` §4.5).

The ACTIVE event is resolved by `AdminEventoActivoService` — ONE rule shared
with the operational tables (A3–A14), so the scope of the whole
administrative area can never diverge.

The ORM calls are sync, so they are wrapped with `sync_to_async` — never
`asyncio.to_thread` (the project convention for Django ORM in async code).
"""
from asgiref.sync import sync_to_async
from injector import inject

from modules.administracion.domain.results.admin_catalogos_results import (
    AdminCatalogosResult,
)
from modules.administracion.domain.results.admin_resumen_results import (
    AdminResumenResult,
)
from modules.administracion.domain.services.core.admin_consulta_service import (
    AdminConsultaService,
)
from modules.administracion.domain.services.core.admin_evento_activo_service import (
    AdminEventoActivoService,
)
from modules.eventos.domain.models import Evento


class AdminResumenOrchestrator:
    """Async facade of the operational overview and its filter catalogs."""

    @inject
    def __init__(
        self,
        evento_activo_service: AdminEventoActivoService,
        consulta_service: AdminConsultaService,
    ):
        self.evento_activo_service = evento_activo_service
        self.consulta_service = consulta_service

        self._resolver_evento = sync_to_async(
            evento_activo_service.resolver_evento_activo
        )
        self._construir_resumen = sync_to_async(consulta_service.construir_resumen)
        self._construir_catalogos = sync_to_async(consulta_service.construir_catalogos)

    async def _resolver_evento_activo(self) -> Evento:
        """Resolve the ACTIVE event, server-side.

        The event is derived from `settings.EVENTO_ACTIVO_NOMBRE`: the client
        never sends `evento_id`. When the named edition is not flagged as
        active, the most recent active edition is used as a fallback.

        Raises:
            EventoActivoNoEncontradoError: when there is NO active event at
                all — the administration surface has no scope to report.
        """
        return await self._resolver_evento()

    async def obtener_resumen(self) -> AdminResumenResult:
        """Return the eight blocks of the operational overview."""
        evento = await self._resolver_evento_activo()
        return await self._construir_resumen(evento)

    async def obtener_catalogos(self) -> AdminCatalogosResult:
        """Return the filter option lists of the active event."""
        evento = await self._resolver_evento_activo()
        return await self._construir_catalogos(evento)


__all__ = ["AdminResumenOrchestrator"]
