"""`EventoSelector` — superficie de lectura de eventos.

Freeze: `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-02-edition-scope.md`
Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

El selector congelado (`backend/modules/eventos/domain/selectors/evento_selector.py`)
tenía `obtener_activo()` — "la edición más reciente" — y
`obtener_activo_por_nombre()` — "la edición cuyo nombre coincide con la
constante de settings". Ambos son el supuesto que FR-02 §2 elimina: un
singleton por nombre no puede sostener dos ediciones simultáneas ni historial
(RN-E01).

Por eso este selector NO tiene ningún método "activo" y NO lee ninguna
constante de settings. Sólo expone la familia de eventos.
"""

import uuid

from django.db.models import QuerySet

from modules.eventos.domain.models import Evento


def _normalizar_uuid(valor) -> uuid.UUID | None:
    """Convierte a `uuid.UUID` o devuelve `None` si el valor no es un UUID."""
    if isinstance(valor, uuid.UUID):
        return valor
    if valor in (None, ""):
        return None
    try:
        return uuid.UUID(str(valor))
    except (AttributeError, TypeError, ValueError):
        return None


class EventoSelector:
    """Consultas de solo lectura sobre `Evento`."""

    def obtener_por_id(self, evento_id) -> Evento | None:
        """El evento con ese identificador, o `None` si no existe."""
        identificador = _normalizar_uuid(evento_id)
        if identificador is None:
            return None
        return Evento.objects.filter(id=identificador).first()

    def obtener_por_slug(self, slug: str) -> Evento | None:
        """El evento con ese identificador estable, o `None`."""
        if not slug:
            return None
        return Evento.objects.filter(slug=slug).first()

    def listar(self) -> QuerySet[Evento]:
        """Todos los eventos, por nombre."""
        return Evento.objects.order_by("nombre")


__all__ = ["EventoSelector"]
