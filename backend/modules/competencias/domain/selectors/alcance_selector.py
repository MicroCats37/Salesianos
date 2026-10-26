"""
AlcanceEventoSelector — the AUTHORIZED events of a reader.

The spec requires every read to be limited to the events the reader is
authorized for ("Las lecturas MUST limitarse a eventos autorizados para el
lector"). This module has NO parallel table of permissions
(`contract/django-app-architecture-contract.md` §10 — "no inventar sistemas de
permisos paralelos"), so the scope is derived from the edition itself:

- the PUBLIC surface may read the ACTIVE editions (`Evento.esta_activo`),
- the ADMINISTRATIVE surface may read every edition and may narrow it with
  the `evento_id` filter.

The scope is ALWAYS resolved on the server: the client never chooses the
scope, it only asks for a competition and the surface answers 404 when that
competition is outside of it.

Read-only by construction: no method in this selector writes.
"""
from modules.eventos.domain.models import Evento


class AlcanceEventoSelector:
    """Resolution of the events a reader is authorized to read."""

    def eventos_autorizados(self) -> list[str]:
        """Return the ids of the events the public reader may read.

        An edition is authorized for the public surface when it is ACTIVE:
        the administration team deactivates an edition when it must leave
        the public surface, and no other table is needed for that.
        """
        return [
            str(evento_id)
            for evento_id in Evento.objects.filter(esta_activo=True).values_list(
                "id", flat=True
            )
        ]

    def eventos_visibles(self) -> list[str]:
        """Return the ids of EVERY edition (the administrative scope)."""
        return [
            str(evento_id)
            for evento_id in Evento.objects.all().values_list("id", flat=True)
        ]


__all__ = ["AlcanceEventoSelector"]
