"""`CatalogoSelector` — consultas de SOLO LECTURA del catálogo por edición.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

El selector NO decide: sólo consulta. Las decisiones (qué paquete está a la
venta, qué precio rige, qué disciplina está permitida) viven en los
servicios.

Reglas que se respetan aquí:

- **Todo el catálogo se filtra por EDICIÓN** (`RN-E01`). No hay consulta de
  "los paquetes" sin edición.
- **Un paquete sin precio vigente no se ofrece**: la consulta de precio
  vigente es explícita y su ausencia es un hecho, no un precio de reserva.
"""

from datetime import date

from django.db.models import Q, QuerySet

from modules.salesianos_fest.domain.constants import EstadoDisciplina, EstadoPaquete
from modules.salesianos_fest.domain.models import (
    Disciplina,
    Paquete,
    PaquetePrecio,
)


class CatalogoSelector:
    """Consultas de solo lectura sobre el catálogo de una edición."""

    def listar_paquetes(self, edicion_id) -> QuerySet[Paquete]:
        """Los paquetes VIGENTES de la edición, con sus relaciones cargadas.

        Returns:
            QuerySet de `Paquete` de esa edición y sólo de esa edición.
        """
        return (
            Paquete.objects.filter(
                edicion_id=edicion_id,
                estado=EstadoPaquete.VIGENTE,
            )
            .select_related("edicion")
            .prefetch_related("beneficios", "disciplinas_vinculadas__disciplina")
            .order_by("nombre")
        )

    def obtener_paquete(self, edicion_id, paquete_id) -> Paquete | None:
        """El paquete indicado DENTRO de la edición, o `None`.

        Un identificador mal formado no es un error de servidor: es "no
        existe" (`FR-02` §2.3, misma convención que `EdicionSelector`).
        """
        paquete = (
            Paquete.objects.filter(id=paquete_id, edicion_id=edicion_id)
            .select_related("edicion")
            .prefetch_related("beneficios", "disciplinas_vinculadas__disciplina")
            .first()
        )
        return paquete

    def listar_disciplinas(self, edicion_id) -> QuerySet[Disciplina]:
        """Las disciplinas de la edición, en orden estable."""
        return (
            Disciplina.objects.filter(edicion_id=edicion_id)
            .select_related("edicion")
            .order_by("nombre")
        )

    def obtener_disciplina(self, edicion_id, disciplina_id) -> Disciplina | None:
        """La disciplina indicada DENTRO de la edición, o `None`."""
        return Disciplina.objects.filter(
            id=disciplina_id,
            edicion_id=edicion_id,
        ).first()

    def listar_disciplinas_activas(self, edicion_id) -> QuerySet[Disciplina]:
        """Las disciplinas ACTIVAS de la edición."""
        return self.listar_disciplinas(edicion_id).filter(
            estado=EstadoDisciplina.ACTIVA
        )

    def obtener_precio_vigente(self, paquete_id, hoy: date | None = None) -> PaquetePrecio | None:
        """El precio vigente del paquete, o `None` si no hay ninguno.

        "Vigente" es un hecho del catálogo: el precio cuyo inicio ya pasó y
        cuyo fin (si lo tiene) todavía no pasó. La ausencia de precio
        vigente NO se rellena con un importe por defecto: significa que el
        paquete no está a la venta (`FL-01` paso 3).
        """
        momento = hoy or date.today()
        return (
            PaquetePrecio.objects.filter(
                paquete_id=paquete_id,
                vigente_desde__lte=momento,
            )
            .filter(
                Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=momento),
            )
            .order_by("-vigente_desde")
            .first()
        )


__all__ = ["CatalogoSelector"]
