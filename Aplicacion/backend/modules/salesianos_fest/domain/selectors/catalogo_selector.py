"""`CatalogoSelector` — consultas de SOLO LECTURA del catálogo por edición.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

El selector NO decide: sólo consulta. Las decisiones (qué paquete está a la
venta, qué precio rige, qué disciplina está permitida, qué categoría
corresponde a una promoción) viven en los servicios.

Reglas que se respetan aquí:

- **Todo el catálogo se filtra por EDICIÓN** (`RN-E01`). No hay consulta de
  "los paquetes" sin edición.
- **La promoción es GLOBAL** (`D-CAT-04`): es lo único del catálogo que NO
  cuelga de una edición, porque una cohorte de nacimiento es una propiedad
  de la persona.
- **Un paquete sin precio vigente no se ofrece**: la consulta de precio
  vigente es explícita y su ausencia es un hecho, no un precio de reserva.
"""

from datetime import date

from django.db.models import Q, QuerySet

from modules.salesianos_fest.domain.constants import (
    EstadoCategoria,
    EstadoDisciplina,
    EstadoPaquete,
    EstadoPromocion,
)
from modules.salesianos_fest.domain.models import (
    Categoria,
    Disciplina,
    Paquete,
    PaquetePrecio,
    Promocion,
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

        El monto es UNITARIO: es el precio de UNA persona (`D-CAT-01`).
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

    def obtener_version_precio(self, paquete_id, hoy: date | None = None) -> int:
        """La VERSIÓN del precio vigente de un paquete.

        Es el ordinal del precio vigente dentro de la HISTORIA de precios
        del paquete: cuenta cuántas ventanas de vigencia ya empezaron. Sube
        cuando el catálogo añade una ventana nueva, así que sirve como TOKEN
        DE CONCURRENCIA entre una cotización y el alta.

        Nunca es cero: un paquete sin precio no está a la venta y el flujo lo
        rechaza antes de llegar aquí.
        """
        momento = hoy or date.today()
        return max(
            PaquetePrecio.objects.filter(
                paquete_id=paquete_id,
                vigente_desde__lte=momento,
            ).count(),
            1,
        )

    # ── Promociones y categorías (restore-registration-promotion-…) ────────

    def listar_promociones(self) -> QuerySet[Promocion]:
        """Las promociones ACTIVAS, de la más reciente a la más antigua.

        Son GLOBALES: no se filtran por edición (`D-CAT-04`).
        """
        return Promocion.objects.filter(
            estado=EstadoPromocion.ACTIVA,
        ).order_by("-anio")

    def obtener_promocion(self, promocion_id) -> Promocion | None:
        """La promoción indicada, o `None`.

        La promoción es global: se resuelve por su identificador, sin
        alcance de edición.
        """
        return Promocion.objects.filter(id=promocion_id).first()

    def listar_categorias(self, edicion_id) -> QuerySet[Categoria]:
        """Las categorías ACTIVAS de la edición, en orden estable."""
        return (
            Categoria.objects.filter(
                edicion_id=edicion_id,
                estado=EstadoCategoria.ACTIVA,
            )
            .select_related("edicion")
            .order_by("-promocion_hasta", "nombre")
        )

    def obtener_categoria_por_promocion(
        self,
        edicion_id,
        anio: int,
    ) -> Categoria | None:
        """La categoría ACTIVA de la edición que contiene ese año de cohorte.

        Es la DERIVACIÓN cohorte → banda: el rango de la categoría es
        `[promocion_desde, promocion_hasta]`. El rango se guarda como años
        enteros, así que la derivación NO necesita un JOIN con `Promocion`.

        Devuelve `None` cuando ninguna categoría activa contiene el año: el
        flujo traduce ese `None` en el error de dominio que corresponda. NO
        se inventa una categoría.

        El orden (`-promocion_hasta`) hace la resolución DETERMINISTA si el
        catálogo llegara a tener rangos solapados: gana la banda más
        reciente.
        """
        return (
            Categoria.objects.filter(
                edicion_id=edicion_id,
                estado=EstadoCategoria.ACTIVA,
                promocion_desde__lte=anio,
                promocion_hasta__gte=anio,
            )
            .select_related("edicion")
            .order_by("-promocion_hasta", "nombre")
            .first()
        )


__all__ = ["CatalogoSelector"]
