"""
AdminFundacionOrchestrator — thin async facade of the administration module.

One public method per endpoint, and nothing else: it resolves the active
event through the OWNING module's selector (`modules.eventos`) and returns a
result object. No business rule lives here
(`contract/django-app-architecture-contract.md` §4.5).

The ORM call is sync, so it is wrapped with `sync_to_async` — never
`asyncio.to_thread` (the project convention for Django ORM in async code).
"""
from asgiref.sync import sync_to_async
from django.conf import settings
from injector import inject

from modules.administracion.domain.results.admin_fundacion_results import (
    AdminFundacionResult,
)
from modules.eventos.domain.selectors.evento_selector import EventoSelector


class AdminFundacionOrchestrator:
    """Async facade of the administration foundation."""

    @inject
    def __init__(self, evento_selector: EventoSelector):
        self.evento_selector = evento_selector
        self._obtener_activo_por_nombre = sync_to_async(
            evento_selector.obtener_activo_por_nombre
        )
        self._obtener_activo = sync_to_async(evento_selector.obtener_activo)

    async def obtener_fundacion(self) -> AdminFundacionResult:
        """Resolve the active event and describe the module state.

        The active event is resolved SERVER-SIDE from
        `settings.EVENTO_ACTIVO_NOMBRE` — the client never sends `evento_id`.
        When the named event is not flagged as active, the most recent active
        edition is used as a fallback.
        """
        nombre_evento = getattr(settings, "EVENTO_ACTIVO_NOMBRE", "")

        evento = None
        if nombre_evento:
            evento = await self._obtener_activo_por_nombre(nombre_evento)

        if evento is None:
            evento = await self._obtener_activo()

        return AdminFundacionResult(
            modulo="administracion",
            estado="ok",
            evento_activo_id=str(evento.id) if evento else None,
            evento_activo_nombre=evento.nombre if evento else None,
        )


__all__ = ["AdminFundacionOrchestrator"]
