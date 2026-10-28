"""
ListarPasesFlujo — async flow for the public party-pass catalogue.

Business rules owned by this flow:

1. the rollout flag `settings.PASES_FIESTA_ENABLED` gates the whole surface:
   while it is off the catalogue publishes NOTHING;
2. only the ACTIVE event publishes passes — the catalogue never accepts an
   `evento_id` from the client, the edition is resolved server-side;
3. only the ACTIVE passes of that event are published.

Read-only flow: it opens no transaction and writes nothing.
"""
from asgiref.sync import sync_to_async
from django.conf import settings
from injector import inject

from modules.salesianos_fest.domain.results.pase_results import PaseCatalogoResult
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.pase_service import PaseCoreService


class ListarPasesFlujo:
    """Async flow that resolves the publishable party-pass catalogue."""

    @inject
    def __init__(
        self,
        pase_selector: PaseSelector,
        pase_core: PaseCoreService,
    ):
        self.pase_selector = pase_selector
        self.pase_core = pase_core

    async def _listar_pases(self) -> list[PaseCatalogoResult]:
        """
        Return the publishable catalogue of passes.

        Returns an EMPTY list when the rollout flag is off or when there is
        no active event: an unpublished catalogue is never leaked.
        """
        if not getattr(settings, "PASES_FIESTA_ENABLED", False):
            return []

        evento = await sync_to_async(self.pase_core.resolver_evento_activo)()
        if evento is None:
            return []

        return await sync_to_async(self.pase_selector.get_activos_del_evento)(
            str(evento.id)
        )
