"""
AdminPagoSelector — read queries of the purchases and their payment orders
(A5, A6).

The payment surface is deliberately EXPLICIT and RESTRICTED
(`sdd/administracion-operativa-fest/admin-surface` §5.4):

- `OrdenPago.metadata` and `TransaccionPago.metadata` are NEVER read,
- `token_sesion` is NEVER read,
- `response_message` (the raw provider message) is NEVER read,
- `transaction_id` (a sensitive provider identifier) is NEVER read.

The commercial amounts come from the FROZEN snapshot of the purchase line
(`CompraInscripcion.cantidad`, `precio_unitario`, `total` — or the same
fields of `CompraPase`), never from a recomputed price.

ONE ROW, ONE COMPOSITION: the list paginates the GENERIC `commerce.Compra`
scoped to the active event, and every row is one purchase with exactly ONE
supported composition — a sports `CompraInscripcion` OR a pass `CompraPase`.
The two populations are NEVER merged in Python: the page is ONE query over
`Compra` and the compositions of the page are BULK-LOADED with two more
queries (one per composition). The number of queries does NOT grow with the
number of pass purchases.

Read-only by construction: no method in this selector writes.
"""
from datetime import date
from decimal import Decimal

from django.db.models import Count, IntegerField, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce

from modules.administracion.domain.exceptions import AdminResourceNotFoundError
from modules.administracion.domain.results.admin_pago_results import (
    AdminAprobacionManualResult,
    AdminPagoComposiciónResult,
    AdminPagoDetalleResult,
    AdminPagoListItemResult,
    AdminPaseBeneficiarioConteoResult,
    AdminPaseBeneficiarioResult,
    AdminTransaccionListItemResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.commerce.domain.models import Compra
from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    IzipayStatus,
    OrigenPago,
)
from modules.pagos.domain.models import AprobacionPagoManual, TransaccionPago
from modules.salesianos_fest.domain.constants import EstadoPaseBeneficiarioChoices
from modules.salesianos_fest.domain.models import (
    CompraInscripcion,
    CompraPase,
    PaseBeneficiario,
)


def _nombre_completo(nombres: str, apellidos: str) -> str:
    """Return the display name of a person."""
    return f"{nombres} {apellidos}".strip()


class AdminPagoSelector:
    """Read-only queries for the purchases of an event."""

    #: The commercial kind of a PASS purchase. The sports kinds (INICIAL,
    #: AMPLIACION) live in the domain vocabulary of the composition.
    TIPO_PASE = "PASE"

    #: The public ordering field of the line amount. It is an ANNOTATION: the
    #: amount lives in the composition, not in the generic purchase.
    CAMPO_CANTIDAD = "cantidad_linea"

    # ── List (A5) ──────────────────────────────────────────────────────────

    def listar(
        self,
        evento_id: str,
        *,
        estado_compra: str | None = None,
        estado_orden: str | None = None,
        tipo: str | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        q: str | None = None,
        params: AdminPaginacionParams,
    ) -> tuple[list[AdminPagoListItemResult], int]:
        """Return the page of purchases and the total of matching rows.

        The page is paginated over the GENERIC `commerce.Compra`, scoped to
        the active event through the composition: a sports purchase through
        its inscription, a pass purchase through its batch. A purchase has
        exactly one composition, so the OR never duplicates a row.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            estado_compra: commercial state of the purchase.
            estado_orden: state of the payment order.
            tipo: INICIAL / AMPLIACION (sports) or PASE (pass batch).
            desde: only purchases created on or after this date.
            hasta: only purchases created on or before this date.
            q: free text over the order number, the buyer and the pass name.
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = self._base(evento_id)

        if estado_compra:
            qs = qs.filter(estado=estado_compra)

        if estado_orden:
            qs = qs.filter(orden_pago__estado=estado_orden)

        if tipo:
            qs = self._filtrar_tipo(qs, tipo)

        if desde is not None:
            qs = qs.filter(created_at__date__gte=desde)

        if hasta is not None:
            qs = qs.filter(created_at__date__lte=hasta)

        if q:
            qs = self._filtrar_busqueda(qs, q)

        # The count is taken BEFORE the ordering annotation: an annotated
        # queryset would be counted through a subquery.
        total = qs.count()

        qs = self._con_ordenacion(qs, params.ordering).order_by(params.ordering)
        compras = list(qs[params.offset: params.offset + params.page_size])

        composiciones = self._composiciones(compras)
        origenes = self._origenes(compras)
        beneficiarios = self._beneficiarios_por_compra(compras)

        return [
            self._map(
                compra,
                composiciones.get(str(compra.id)),
                origenes,
                beneficiarios.get(str(compra.id)),
            )
            for compra in compras
        ], total

    # ── Detail (A6) ────────────────────────────────────────────────────────

    def obtener_detalle(
        self,
        evento_id: str,
        orden_pago_id: str,
    ) -> AdminPagoDetalleResult:
        """Return the drilldown of one payment order.

        Raises:
            AdminResourceNotFoundError: when the order does not exist or does
                not belong to the active event.
        """
        compra = (
            self._base(evento_id)
            .filter(orden_pago_id=orden_pago_id)
            .first()
        )

        if compra is None:
            raise AdminResourceNotFoundError("Orden de pago")

        composiciones = self._composiciones([compra])
        origenes = self._origenes([compra])
        beneficiarios = self._beneficiarios_por_compra([compra])
        base = self._map(
            compra,
            composiciones.get(str(compra.id)),
            origenes,
            beneficiarios.get(str(compra.id)),
        )

        transacciones = (
            TransaccionPago.objects
            .filter(orden_pago_id=orden_pago_id)
            .order_by("created_at")
        )

        return AdminPagoDetalleResult(
            **base.model_dump(),
            transacciones=[
                AdminTransaccionListItemResult(
                    id=str(transaccion.id),
                    status=transaccion.status,
                    amount=float(transaccion.amount),
                    currency=transaccion.currency,
                    metodo_pago=transaccion.metodo_pago,
                    response_code=transaccion.response_code,
                    created_at=transaccion.created_at,
                )
                for transaccion in transacciones
            ],
            aprobaciones=self._aprobaciones(orden_pago_id),
            beneficiarios=self._beneficiarios(str(compra.id)),
        )

    # ── Blocks ─────────────────────────────────────────────────────────────

    def listar_compras_de_inscripcion(
        self,
        inscripcion_id: str,
    ) -> list[AdminPagoListItemResult]:
        """Return the purchases of one registration (the block of A4).

        A registration only has SPORTS purchases: a pass batch has no
        inscription and never appears here.
        """
        compras = list(
            Compra.objects
            .filter(compra_inscripcion__inscripcion_id=inscripcion_id)
            .select_related("orden_pago", "responsable")
            .order_by("-created_at")
        )
        composiciones = self._composiciones(compras)
        origenes = self._origenes(compras)
        beneficiarios = self._beneficiarios_por_compra(compras)
        return [
            self._map(
                compra,
                composiciones.get(str(compra.id)),
                origenes,
                beneficiarios.get(str(compra.id)),
            )
            for compra in compras
        ]

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _base(evento_id: str):
        """
        Return the base queryset: the generic purchases of an event.

        The event scope travels through the composition: a sports purchase
        through its inscription, a pass purchase through its batch.

        Only the FORWARD relations of the purchase are joined here (the
        order and the buyer). The compositions are bulk-loaded separately:
        joining them here would make the OR of the scope and the relation of
        the composition compete for the same join.
        """
        return Compra.objects.filter(
            Q(compra_inscripcion__inscripcion__evento_id=evento_id)
            | Q(compra_pase__evento_id=evento_id)
        ).select_related("orden_pago", "responsable")

    @staticmethod
    def _filtrar_tipo(qs, tipo: str):
        """Filter by the commercial kind of the purchase.

        `PASE` selects the independent pass batches; `INICIAL` / `AMPLIACION`
        select the sports kinds.
        """
        if tipo == AdminPagoSelector.TIPO_PASE:
            return qs.filter(compra_pase__isnull=False)
        return qs.filter(compra_inscripcion__tipo=tipo)

    @staticmethod
    def _filtrar_busqueda(qs, q: str):
        """Free text over the order number, the buyer and the pass name."""
        return qs.filter(
            Q(orden_pago__numero__icontains=q)
            | Q(responsable__nombres__icontains=q)
            | Q(responsable__apellidos__icontains=q)
            | Q(responsable__numero_documento__icontains=q)
            | Q(compra_pase__pase__nombre__icontains=q)
        )

    @staticmethod
    def _con_ordenacion(qs, ordering: str | None):
        """
        Add the line-amount annotation only when the ordering needs it.

        The amount of a purchase lives in its composition, not in the generic
        purchase: ordering by it needs an annotation over the two
        compositions. The annotation is a constant cost (two correlated
        subqueries), never an N+1 over the page.
        """
        if not ordering or AdminPagoSelector.CAMPO_CANTIDAD not in ordering:
            return qs

        return qs.annotate(
            cantidad_linea=Coalesce(
                Subquery(
                    CompraInscripcion.objects
                    .filter(compra=OuterRef("pk"))
                    .values("cantidad")[:1]
                ),
                Subquery(
                    CompraPase.objects
                    .filter(compra=OuterRef("pk"))
                    .values("cantidad")[:1]
                ),
                output_field=IntegerField(),
            )
        )

    @staticmethod
    def _composiciones(
        compras: list[Compra],
    ) -> dict[str, AdminPagoComposiciónResult]:
        """
        Bulk-load the composition of every purchase of the page.

        TWO queries for the whole page (one per composition): the table never
        grows an N+1 over the purchases and the two populations are never
        merged in Python.
        """
        compra_ids = [str(compra.id) for compra in compras]
        if not compra_ids:
            return {}

        composiciones: dict[str, AdminPagoComposiciónResult] = {}

        for linea in (
            CompraInscripcion.objects
            .filter(compra_id__in=compra_ids)
            .select_related("inscripcion__paquete")
        ):
            composiciones[str(linea.compra_id)] = AdminPagoComposiciónResult(
                tipo=linea.tipo,
                inscripcion_id=str(linea.inscripcion_id),
                producto_nombre=linea.inscripcion.paquete.nombre,
                cantidad=linea.cantidad,
                precio_unitario=float(linea.precio_unitario),
                total=float(linea.total),
            )

        for linea in (
            CompraPase.objects
            .filter(compra_id__in=compra_ids)
            .select_related("pase")
        ):
            composiciones[str(linea.compra_id)] = AdminPagoComposiciónResult(
                tipo=AdminPagoSelector.TIPO_PASE,
                pase_id=str(linea.pase_id),
                producto_nombre=linea.pase.nombre,
                cantidad=linea.cantidad,
                precio_unitario=float(linea.precio_unitario),
                total=float(linea.total),
            )

        return composiciones

    @staticmethod
    def _origenes(compras: list[Compra]) -> dict[str, str]:
        """
        Derive the origin of the payment of every order of the given rows.

        The origin is DERIVED from the evidence, never typed by anybody:

        - `MANUAL`   — the order carries an active manual approval,
        - `IZIPAY`   — the order carries a CORRELATED successful transaction,
        - `SIN_PAGO` — no verifiable evidence at all.

        Two bulk queries answer the whole page: the table never grows an
        N+1 over the payment attempts.
        """
        ordenes = {
            str(compra.orden_pago_id): compra.orden_pago
            for compra in compras
            if compra.orden_pago_id
        }
        if not ordenes:
            return {}

        orden_ids = list(ordenes.keys())

        manuales = {
            str(orden_pago_id)
            for orden_pago_id in AprobacionPagoManual.objects
            .filter(
                orden_pago_id__in=orden_ids,
                estado=EstadoAprobacionPagoManual.APROBADA,
            )
            .values_list("orden_pago_id", flat=True)
        }

        exitosas = TransaccionPago.objects.filter(
            orden_pago_id__in=orden_ids,
            status=IzipayStatus.EXITO,
        ).values_list("orden_pago_id", "amount", "currency")

        izipay = {
            str(orden_pago_id)
            for orden_pago_id, amount, currency in exitosas
            if AdminPagoSelector._correlaciona(ordenes.get(str(orden_pago_id)), amount, currency)
        }

        origenes: dict[str, str] = {}
        for orden_id in orden_ids:
            if orden_id in manuales:
                origenes[orden_id] = OrigenPago.MANUAL
            elif orden_id in izipay:
                origenes[orden_id] = OrigenPago.IZIPAY
            else:
                origenes[orden_id] = OrigenPago.SIN_PAGO

        return origenes

    @staticmethod
    def _beneficiarios_por_compra(
        compras: list[Compra],
    ) -> dict[str, AdminPaseBeneficiarioConteoResult]:
        """
        Count the pass rights of every purchase of the page, by state.

        ONE bulk query for the whole page: the number of queries never grows
        with the number of pass purchases. The ACTIVE and the REVOCATED
        rights are reported separately: a revoked right keeps its slot
        consumed forever, but it grants no access.

        Returns:
            One TYPED count per purchase id (`AdminPaseBeneficiarioConteoResult`).
        """
        compra_ids = [str(compra.id) for compra in compras]
        if not compra_ids:
            return {}

        conteos: dict[str, AdminPaseBeneficiarioConteoResult] = {}
        for fila in (
            PaseBeneficiario.objects
            .filter(compra_pase__compra_id__in=compra_ids)
            .values("compra_pase__compra_id", "estado")
            .annotate(cantidad=Count("id"))
        ):
            compra_id = str(fila["compra_pase__compra_id"])
            conteo = conteos.setdefault(
                compra_id, AdminPaseBeneficiarioConteoResult()
            )
            if fila["estado"] == EstadoPaseBeneficiarioChoices.ACTIVA:
                conteo.activos = fila["cantidad"]
            else:
                conteo.revocados = fila["cantidad"]

        return conteos

    @staticmethod
    def _beneficiarios(compra_id: str) -> list[AdminPaseBeneficiarioResult]:
        """
        Return the nominative rights of a pass purchase.

        Only the SLOT, the state and the internal identifier of the holder
        travel: no names, no documents. The names of the buyers are never
        part of the payment surface.
        """
        linea_pase = CompraPase.objects.filter(compra_id=compra_id).first()
        if linea_pase is None:
            return []

        return [
            AdminPaseBeneficiarioResult(
                persona_id=str(beneficiario.persona_id),
                slot=beneficiario.slot,
                estado=beneficiario.estado,
            )
            for beneficiario in PaseBeneficiario.objects
            .filter(compra_pase_id=linea_pase.id)
            .order_by("slot")
        ]

    @staticmethod
    def _correlaciona(orden, amount, currency) -> bool:
        """Return True when a provider attempt matches its order exactly."""
        if orden is None:
            return False
        return (
            Decimal(str(amount)) == Decimal(str(orden.monto_total))
            and currency == orden.moneda
        )

    @staticmethod
    def _aprobaciones(orden_pago_id: str) -> list[AdminAprobacionManualResult]:
        """Return the manual approval history of an order (audit trail)."""
        from modules.usuarios.domain.models import Usuario

        aprobaciones = (
            AprobacionPagoManual.objects
            .filter(orden_pago_id=orden_pago_id)
            .select_related("actor", "anulada_por")
            .order_by("created_at")
        )

        actor_ids = {
            aprobacion.actor_id for aprobacion in aprobaciones
        } | {
            aprobacion.anulada_por_id for aprobacion in aprobaciones
        }
        actor_ids.discard(None)

        nombres = {
            str(usuario.id): usuario.username
            for usuario in Usuario.objects.filter(id__in=list(actor_ids))
        }

        return [
            AdminAprobacionManualResult(
                id=str(aprobacion.id),
                estado=aprobacion.estado,
                canal=aprobacion.canal,
                referencia=aprobacion.referencia,
                monto=float(aprobacion.monto),
                moneda=aprobacion.moneda,
                motivo=aprobacion.motivo,
                actor=nombres.get(str(aprobacion.actor_id), ""),
                anulada_por=nombres.get(str(aprobacion.anulada_por_id))
                if aprobacion.anulada_por_id
                else None,
                anulada_en=aprobacion.anulada_en,
                motivo_anulacion=aprobacion.motivo_anulacion,
                created_at=aprobacion.created_at,
            )
            for aprobacion in aprobaciones
        ]

    @staticmethod
    def _map(
        compra: Compra,
        composicion: AdminPagoComposiciónResult | None = None,
        origenes: dict[str, str] | None = None,
        beneficiarios: AdminPaseBeneficiarioConteoResult | None = None,
    ) -> AdminPagoListItemResult:
        """Map a purchase into its result DTO (explicit fields only)."""
        orden = compra.orden_pago
        responsable = compra.responsable
        composicion = composicion or AdminPagoComposiciónResult()
        origenes = origenes or {}
        conteo = beneficiarios or AdminPaseBeneficiarioConteoResult()

        return AdminPagoListItemResult(
            compra_id=str(compra.id),
            orden_pago_id=str(orden.id) if orden else None,
            numero_orden=orden.numero if orden else None,
            inscripcion_id=composicion.inscripcion_id,
            pase_id=composicion.pase_id,
            responsable_nombre=_nombre_completo(
                responsable.nombres, responsable.apellidos
            ) if responsable else "",
            tipo=composicion.tipo,
            producto_nombre=composicion.producto_nombre,
            cantidad=composicion.cantidad,
            precio_unitario=composicion.precio_unitario,
            total=composicion.total,
            estado_compra=compra.estado,
            estado_orden=orden.estado if orden else None,
            pagada_en=orden.pagada_en if orden else None,
            origen_pago=origenes.get(str(compra.orden_pago_id), OrigenPago.SIN_PAGO),
            monto_orden=float(orden.monto_total) if orden else None,
            moneda_orden=orden.moneda if orden else None,
            beneficiarios_activos=conteo.activos,
            beneficiarios_revocados=conteo.revocados,
            created_at=compra.created_at,
        )


__all__ = ["AdminPagoSelector"]
