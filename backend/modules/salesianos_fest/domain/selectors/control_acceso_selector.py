"""
ControlAccesoSelector — read-only queries for the access log (ControlAcceso).

The access log had NO query surface until now: the only way to read it was
walking down from an acreditación. The operational administration surface needs
an event-wide, filterable read of it, and the access log belongs to THIS
module (it is written by the scanner flow, not by the admin module).

Read-only by construction: no method in this selector writes.
"""
from datetime import datetime

from django.db.models import Count, QuerySet

from modules.salesianos_fest.domain.constants import ResultadoAccesoChoices
from modules.salesianos_fest.domain.models import ControlAcceso


class ControlAccesoSelector:
    """Read-only queries for ControlAcceso."""

    def obtener_por_id(self, control_acceso_id: str) -> ControlAcceso | None:
        """Return the access record with the given id, or None."""
        return (
            ControlAcceso.objects
            .select_related(
                "acreditacion__evento",
                "acreditacion__persona",
                "operador__persona_fk",
            )
            .filter(id=control_acceso_id)
            .first()
        )

    def listar_por_evento(
        self,
        evento_id: str,
        *,
        resultado: str | None = None,
        punto_acceso: str | None = None,
        desde: datetime | None = None,
        hasta: datetime | None = None,
    ) -> QuerySet[ControlAcceso]:
        """Return the access records of an event, newest first.

        The event scope travels through `acreditacion__evento`: an access
        record belongs to the event of the accreditation it used.

        Args:
            evento_id: the event the records must belong to.
            resultado: filter by `PERMITIDO` / `DENEGADO` when not None.
            punto_acceso: filter by the scanner location when not None.
            desde: only records at or after this instant when not None.
            hasta: only records at or before this instant when not None.

        Returns:
            An unevaluated QuerySet: the caller decides how to paginate it.
        """
        qs = ControlAcceso.objects.filter(acreditacion__evento_id=evento_id)

        if resultado:
            qs = qs.filter(resultado=resultado)

        if punto_acceso:
            qs = qs.filter(punto_acceso=punto_acceso)

        if desde is not None:
            qs = qs.filter(fecha_hora__gte=desde)

        if hasta is not None:
            qs = qs.filter(fecha_hora__lte=hasta)

        return qs.select_related(
            "acreditacion__evento",
            "acreditacion__persona",
            "operador__persona_fk",
        ).order_by("-fecha_hora")

    def contar_por_evento(self, evento_id: str) -> dict[str, int]:
        """Return the access counters of an event.

        Returns:
            A dict with BOTH keys always present:
            `{"PERMITIDO": n, "DENEGADO": n}` — a missing key means zero, not
            "unknown", so the caller never has to guess the vocabulary.
        """
        filas = (
            ControlAcceso.objects
            .filter(acreditacion__evento_id=evento_id)
            .values("resultado")
            .annotate(total=Count("id"))
        )
        conteo = {fila["resultado"]: fila["total"] for fila in filas}
        return {
            ResultadoAccesoChoices.PERMITIDO: conteo.get(
                ResultadoAccesoChoices.PERMITIDO, 0
            ),
            ResultadoAccesoChoices.DENEGADO: conteo.get(
                ResultadoAccesoChoices.DENEGADO, 0
            ),
        }

    def ultimo_acceso_por_evento(self, evento_id: str) -> datetime | None:
        """Return the timestamp of the most recent access of an event."""
        control = (
            ControlAcceso.objects
            .filter(acreditacion__evento_id=evento_id)
            .order_by("-fecha_hora")
            .first()
        )
        return control.fecha_hora if control else None

    def puntos_acceso_por_evento(self, evento_id: str) -> list[str]:
        """Return the distinct scanner locations of an event.

        The access log belongs to this module, so the filter options of the
        administration surface are read here instead of being re-implemented
        in the admin module.
        """
        valores = (
            ControlAcceso.objects
            .filter(acreditacion__evento_id=evento_id)
            .exclude(punto_acceso__isnull=True)
            .exclude(punto_acceso="")
            .order_by("punto_acceso")
            .values_list("punto_acceso", flat=True)
            .distinct()
        )
        return list(valores)
