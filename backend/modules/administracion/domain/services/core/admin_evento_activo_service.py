"""
AdminEventoActivoService — resolution of the ACTIVE event.

The administrative surface ALWAYS operates on the active edition of the
server: the client NEVER sends `evento_id`. The rule is owned by
`modules.eventos` (`EventoSelector`) and applied here, in ONE place, so every
endpoint of the area shares exactly the same scope.

Rule (`settings.EVENTO_ACTIVO_NOMBRE`):

1. the edition named in the setting, when it is flagged as active;
2. otherwise, the most recent active edition;
3. otherwise, nothing → `EventoActivoNoEncontradoError` (404).

Sync by contract (`contract/django-app-architecture-contract.md` §4.3): no
`async def`, no `transaction.atomic`, no write path.
"""
from django.conf import settings
from injector import inject

from modules.administracion.domain.exceptions import EventoActivoNoEncontradoError
from modules.eventos.domain.models import Evento
from modules.eventos.domain.selectors.evento_selector import EventoSelector


class AdminEventoActivoService:
    """Resolution of the active event — the scope of every admin read."""

    @inject
    def __init__(self, evento_selector: EventoSelector):
        self.evento_selector = evento_selector

    def resolver_evento_activo(self) -> Evento:
        """Return the ACTIVE event, or raise the typed 404.

        Raises:
            EventoActivoNoEncontradoError: when there is no active edition at
                all — the administration surface has no scope to report.
        """
        nombre_evento = getattr(settings, "EVENTO_ACTIVO_NOMBRE", "")

        evento = None
        if nombre_evento:
            evento = self.evento_selector.obtener_activo_por_nombre(nombre_evento)

        if evento is None:
            evento = self.evento_selector.obtener_activo()

        if evento is None:
            raise EventoActivoNoEncontradoError()

        return evento


__all__ = ["AdminEventoActivoService"]
