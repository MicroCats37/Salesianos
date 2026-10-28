"""
PaseCoreService — reusable sync operations of the party-pass catalogue.

Sync by contract (`contract/django-app-architecture-contract.md` §4.3): no
`async def`, no `transaction.atomic` of its own, no write path. The caller
(the flujo) provides the transaction when the operation needs atomicity.

It owns the two operations that the pass catalogue and the pass purchase
share, so the rule lives in ONE place:

1. the resolution of the ACTIVE edition (server-side — the client never
   sends an `evento_id`);
2. the locked read of the pass performed inside the purchase transaction.
"""
from injector import inject

from modules.eventos.domain.models import Evento
from modules.eventos.domain.selectors.evento_selector import EventoSelector
from modules.salesianos_fest.domain.models import Pase
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector


class PaseCoreService:
    """Sync operations over the party-pass catalogue."""

    @inject
    def __init__(
        self,
        pase_selector: PaseSelector,
        evento_selector: EventoSelector,
    ):
        self.pase_selector = pase_selector
        self.evento_selector = evento_selector

    def resolver_evento_activo(self) -> Evento | None:
        """
        Return the ACTIVE edition, or None when there is none.

        Rule (the same one the administrative surface applies): the edition
        named in `settings.EVENTO_ACTIVO_NOMBRE` when it is active;
        otherwise the most recent active edition; otherwise nothing.
        """
        from django.conf import settings

        nombre_evento = getattr(settings, "EVENTO_ACTIVO_NOMBRE", "")
        if nombre_evento:
            evento = self.evento_selector.obtener_activo_por_nombre(nombre_evento)
            if evento is not None:
                return evento
        return self.evento_selector.obtener_activo()

    def obtener_pase_bloqueado(self, pase_id: str) -> Pase | None:
        """
        Load the pass with a row lock, or None when it does not exist.

        The lock serializes concurrent purchases of the SAME pass, so the
        inventory is recalculated against a stable value inside the caller's
        transaction. It MUST be called within that transaction.

        `of=("self",)` locks ONLY the pass row: locking the joined event
        would serialize purchases of different passes of the same edition.
        """
        return (
            Pase.objects
            .select_for_update(of=("self",))
            .select_related("evento")
            .filter(id=pase_id)
            .first()
        )
