"""
EventoSelector — read-only queries for Evento.

The `eventos` module owns the resolution of the active edition: the frontend
never sends `evento_id`, the backend derives it from
`settings.EVENTO_ACTIVO_NOMBRE`. Every operational list of the administration
surface is scoped to that event, so the query surface belongs HERE and not in
the admin module.

Read-only by construction: no method in this selector writes.
"""
from django.db.models import QuerySet

from modules.eventos.domain.models import Evento


class EventoSelector:
    """Read-only queries for Evento."""

    def obtener_por_id(self, evento_id: str) -> Evento | None:
        """Return the event with the given id, or None."""
        return Evento.objects.filter(id=evento_id).first()

    def obtener_por_nombre(self, nombre: str) -> Evento | None:
        """Return the event with the given name, or None."""
        return Evento.objects.filter(nombre=nombre).first()

    def obtener_activo_por_nombre(self, nombre: str) -> Evento | None:
        """Return the ACTIVE event with the given name, or None."""
        return (
            Evento.objects
            .filter(nombre=nombre, esta_activo=True)
            .first()
        )

    def obtener_activo(self) -> Evento | None:
        """Return the active event (most recent edition), or None.

        Ties are broken by `created_at` so the result is deterministic when two
        active editions share the same start date.
        """
        return (
            Evento.objects
            .filter(esta_activo=True)
            .order_by("-fecha_inicio", "-created_at")
            .first()
        )

    def listar(self, solo_activos: bool = False) -> QuerySet[Evento]:
        """Return the events, newest edition first.

        Returns an unevaluated QuerySet: the caller decides how to paginate it.
        """
        qs = Evento.objects.all()
        if solo_activos:
            qs = qs.filter(esta_activo=True)
        return qs.order_by("-fecha_inicio", "-created_at")
