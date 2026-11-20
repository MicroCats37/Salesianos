"""`PaseSelector` — consultas de SOLO LECTURA de pases, compras y derechos.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

El selector NO decide: sólo consulta. Las decisiones (qué pase está a la
venta, qué precio rige, si un derecho ya existe, si el token sigue vivo)
viven en los servicios.

Reglas que se respetan aquí:

- **Todo el catálogo se filtra por EDICIÓN** (`RN-E01`). No hay consulta de
  "los pases" sin edición.
- **Un pase sin precio vigente no se ofrece**: la consulta de precio
  vigente es explícita y su ausencia es un hecho, no un precio de reserva.
- **El token es una credencial**: se busca por token y por compra, y su
  estado (vencido, revocado) lo decide el servicio, no la consulta.
"""

from datetime import date

from django.db.models import Q, QuerySet

from modules.salesianos_fest.domain.constants import EstadoPase
from modules.salesianos_fest.domain.models import (
    ActivacionPase,
    CompraPase,
    CortesiaPase,
    Pase,
    PaseBeneficiario,
    PasePrecio,
)


class PaseSelector:
    """Consultas de solo lectura sobre el catálogo y los derechos de pase."""

    # ── Catálogo ────────────────────────────────────────────────────────────

    def listar_pases(self, edicion_id) -> QuerySet[Pase]:
        """Los pases VIGENTES de la edición, con su relación cargada.

        Returns:
            QuerySet de `Pase` de esa edición y sólo de esa edición.
        """
        return (
            Pase.objects.filter(
                edicion_id=edicion_id,
                estado=EstadoPase.VIGENTE,
            )
            .select_related("edicion")
            .order_by("nombre")
        )

    def obtener_pase(self, edicion_id, pase_id) -> Pase | None:
        """El pase indicado DENTRO de la edición, o `None`.

        Un identificador mal formado no es un error de servidor: es "no
        existe" (misma convención que `CatalogoSelector`).
        """
        return (
            Pase.objects.filter(id=pase_id, edicion_id=edicion_id)
            .select_related("edicion")
            .first()
        )

    def obtener_precio_vigente(
        self,
        pase_id,
        hoy: date | None = None,
    ) -> PasePrecio | None:
        """El precio vigente del pase, o `None` si no hay ninguno.

        "Vigente" es un hecho del catálogo: el precio cuyo inicio ya pasó y
        cuyo fin (si lo tiene) todavía no pasó. La ausencia de precio
        vigente NO se rellena con un importe por defecto: significa que el
        pase no está a la venta.
        """
        momento = hoy or date.today()
        return (
            PasePrecio.objects.filter(
                pase_id=pase_id,
                vigente_desde__lte=momento,
            )
            .filter(
                Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=momento),
            )
            .order_by("-vigente_desde")
            .first()
        )

    # ── Compras ────────────────────────────────────────────────────────────

    def obtener_compra_pase(self, compra_pase_id) -> CompraPase | None:
        """El lote de pases indicado, o `None`."""
        return (
            CompraPase.objects.filter(id=compra_pase_id)
            .select_related("edicion", "pase", "comprador")
            .first()
        )

    def obtener_compra_pase_por_compra(self, compra_id) -> CompraPase | None:
        """El lote de pases que financió una compra de `commerce`, o `None`.

        La compra de `commerce` es la clave: un lote por compra. La
        referencia de intención puede repetirse (una compra nueva tras
        pagar la anterior), así que NO es la clave.
        """
        return (
            CompraPase.objects.filter(compra_id=compra_id)
            .select_related("edicion", "pase", "comprador")
            .first()
        )

    def listar_compras_pase(self, edicion_id=None, estado: str | None = None):
        """Los lotes de pases, opcionalmente acotados por edición y estado."""
        queryset = CompraPase.objects.select_related(
            "edicion",
            "pase",
            "comprador",
        )
        if edicion_id:
            queryset = queryset.filter(edicion_id=edicion_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset.order_by("-created_at")

    def contar_compras_pase(self, edicion_id=None, estado: str | None = None) -> int:
        """Cuántos lotes de pases hay en el mismo ámbito que la lista."""
        return self.listar_compras_pase(edicion_id, estado).count()

    # ── Derechos ───────────────────────────────────────────────────────────

    def listar_beneficiarios(self, compra_pase_id) -> QuerySet[PaseBeneficiario]:
        """Los derechos de un lote, con sus relaciones cargadas."""
        return (
            PaseBeneficiario.objects.filter(compra_pase_id=compra_pase_id)
            .select_related("persona", "pase", "cortesia")
            .order_by("-asignado_en")
        )

    def obtener_beneficiario(
        self,
        compra_pase_id,
        persona_id,
    ) -> PaseBeneficiario | None:
        """El derecho de esa persona en ese lote, o `None`.

        No filtra por estado: la revocación se consulta sobre el MISMO
        derecho para poder informar del estado final (`FR-05` §2.3 — la
        revocación es idempotente).
        """
        return (
            PaseBeneficiario.objects.filter(
                compra_pase_id=compra_pase_id,
                persona_id=persona_id,
            )
            .select_related("persona", "pase", "cortesia")
            .first()
        )

    def contar_beneficiarios(self, compra_pase_id) -> int:
        """Cuántos derechos se han OTORGADO en ese lote, en cualquier estado.

        Cuenta los revocados: la revocación **no** devuelve el cupo
        (`FR-05` §2.3), así que un derecho revocado sigue consumiendo la
        unidad que ocupaba.
        """
        return PaseBeneficiario.objects.filter(compra_pase_id=compra_pase_id).count()

    def obtener_activacion_por_clave(self, clave: str) -> ActivacionPase | None:
        """El acta de activación de esa clave, o `None`.

        La clave es ÚNICA en la base de datos: es la autoridad del
        «exactamente una vez» (`FR-04` I-2).
        """
        return (
            ActivacionPase.objects.filter(clave=str(clave or "").strip())
            .select_related("compra_pase")
            .first()
        )

    # ── Cortesías ───────────────────────────────────────────────────────────

    def listar_cortesias(self, edicion_id=None, estado: str | None = None):
        """Las actas de cortesía, opcionalmente acotadas."""
        queryset = CortesiaPase.objects.select_related(
            "edicion",
            "pase",
            "persona",
            "actor_usuario",
            "actor_persona",
        )
        if edicion_id:
            queryset = queryset.filter(edicion_id=edicion_id)
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset.order_by("-concedido_en")

    def contar_cortesias(self, edicion_id=None, estado: str | None = None) -> int:
        """Cuántas actas de cortesía hay en el mismo ámbito que la lista."""
        return self.listar_cortesias(edicion_id, estado).count()


__all__ = ["PaseSelector"]
