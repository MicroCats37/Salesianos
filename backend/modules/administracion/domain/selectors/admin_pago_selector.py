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
(`CompraInscripcion.cantidad`, `precio_unitario`, `total`), never from a
recomputed price.

Read-only by construction: no method in this selector writes.
"""
from datetime import date

from django.db.models import Q

from modules.administracion.domain.exceptions import AdminResourceNotFoundError
from modules.administracion.domain.results.admin_pago_results import (
    AdminPagoDetalleResult,
    AdminPagoListItemResult,
    AdminTransaccionListItemResult,
)
from modules.administracion.domain.schemas.admin_paginacion_schemas import (
    AdminPaginacionParams,
)
from modules.pagos.domain.models import TransaccionPago
from modules.salesianos_fest.domain.models import CompraInscripcion


def _nombre_completo(nombres: str, apellidos: str) -> str:
    """Return the display name of a person."""
    return f"{nombres} {apellidos}".strip()


class AdminPagoSelector:
    """Read-only queries for the purchases of an event."""

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

        The event scope travels through `inscripcion__evento`:
        `commerce.Compra` is generic and has no event of its own.

        Args:
            evento_id: the ACTIVE event (resolved server-side).
            estado_compra: commercial state of the purchase.
            estado_orden: state of the payment order.
            tipo: INICIAL / AMPLIACION.
            desde: only purchases created on or after this date.
            hasta: only purchases created on or before this date.
            q: free text over the order number and the responsible.
            params: the normalized pagination parameters.

        Returns:
            `(items, total)`.
        """
        qs = self._base(evento_id)

        if estado_compra:
            qs = qs.filter(compra__estado=estado_compra)

        if estado_orden:
            qs = qs.filter(compra__orden_pago__estado=estado_orden)

        if tipo:
            qs = qs.filter(tipo=tipo)

        if desde is not None:
            qs = qs.filter(created_at__date__gte=desde)

        if hasta is not None:
            qs = qs.filter(created_at__date__lte=hasta)

        if q:
            qs = qs.filter(
                Q(compra__orden_pago__numero__icontains=q)
                | Q(inscripcion__responsable__nombres__icontains=q)
                | Q(inscripcion__responsable__apellidos__icontains=q)
                | Q(inscripcion__responsable__numero_documento__icontains=q)
            )

        qs = qs.order_by(params.ordering)

        total = qs.count()
        filas = list(qs[params.offset: params.offset + params.page_size])

        return [self._map(fila) for fila in filas], total

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
        fila = (
            self._base(evento_id)
            .filter(compra__orden_pago_id=orden_pago_id)
            .first()
        )

        if fila is None:
            raise AdminResourceNotFoundError("Orden de pago")

        base = self._map(fila)

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
        )

    # ── Blocks ─────────────────────────────────────────────────────────────

    def listar_compras_de_inscripcion(
        self,
        inscripcion_id: str,
    ) -> list[AdminPagoListItemResult]:
        """Return the purchases of one registration (the block of A4)."""
        filas = (
            CompraInscripcion.objects
            .filter(inscripcion_id=inscripcion_id)
            .select_related("compra__orden_pago", "inscripcion__responsable")
            .order_by("-created_at")
        )
        return [self._map(fila) for fila in filas]

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _base(evento_id: str):
        """Return the base queryset of the purchase lines of an event."""
        return (
            CompraInscripcion.objects
            .filter(inscripcion__evento_id=evento_id)
            .select_related("compra__orden_pago", "inscripcion__responsable")
        )

    @staticmethod
    def _map(fila: CompraInscripcion) -> AdminPagoListItemResult:
        """Map a purchase line into its result DTO (explicit fields only)."""
        orden = fila.compra.orden_pago
        responsable = fila.inscripcion.responsable

        return AdminPagoListItemResult(
            compra_id=str(fila.compra_id),
            orden_pago_id=str(orden.id) if orden else None,
            numero_orden=orden.numero if orden else None,
            inscripcion_id=str(fila.inscripcion_id),
            responsable_nombre=_nombre_completo(
                responsable.nombres, responsable.apellidos
            ),
            tipo=fila.tipo,
            cantidad=fila.cantidad,
            precio_unitario=float(fila.precio_unitario),
            total=float(fila.total),
            estado_compra=fila.compra.estado,
            estado_orden=orden.estado if orden else None,
            pagada_en=orden.pagada_en if orden else None,
            created_at=fila.created_at,
        )


__all__ = ["AdminPagoSelector"]
