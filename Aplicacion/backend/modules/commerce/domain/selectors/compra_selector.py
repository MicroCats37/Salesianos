"""Selectores de lectura del módulo `commerce`.

Contract: `contract/django-app-architecture-contract.md` §4.12 · §8
"""

from django.db.models import QuerySet

from modules.commerce.domain.constants import EstadoCompra
from modules.commerce.domain.models import Compra
from modules.commerce.domain.results.compra_result import CompraResult


class CompraSelector:
    """Consultas de lectura de las compras."""

    def obtener_por_id(self, compra_id) -> Compra | None:
        """La compra por su identificador."""
        return Compra.objects.filter(id=compra_id).first()

    def obtener_pendiente_por_referencia(
        self, persona_id, referencia: str
    ) -> Compra | None:
        """La compra PENDIENTE de una persona para una intención de compra.

        Es la consulta de `RN-C04` e I-4: antes de crear un intento se
        consulta el estado existente. Una compra ya pagada o cancelada NO se
        reutiliza: la misma intención puede abrir una compra nueva.
        """
        if not referencia:
            return None
        return (
            Compra.objects.filter(
                persona_id=persona_id,
                referencia=referencia,
                estado=EstadoCompra.PENDIENTE,
            )
            .order_by("-created_at")
            .first()
        )

    def listar_por_persona(self, persona_id) -> QuerySet:
        """Las compras de una persona."""
        return Compra.objects.filter(persona_id=persona_id).order_by("-created_at")

    def obtener_por_orden_pago(self, orden_pago_id) -> Compra | None:
        """La compra que financia una orden de pago."""
        if not orden_pago_id:
            return None
        return Compra.objects.filter(orden_pago_id=orden_pago_id).first()

    def como_result(self, compra: Compra, *, reutilizada: bool = False) -> CompraResult:
        """Proyecta una compra a su result object."""
        return CompraResult(
            id=str(compra.id),
            persona_id=str(compra.persona_id),
            origen=compra.origen,
            estado=compra.estado,
            total=compra.total,
            moneda=compra.moneda,
            lineas_snapshot=list(compra.lineas_snapshot or []),
            orden_pago_id=str(compra.orden_pago_id) if compra.orden_pago_id else None,
            referencia=compra.referencia,
            creada_en=compra.created_at,
            reutilizada=reutilizada,
        )


__all__ = ["CompraSelector"]
