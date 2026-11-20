"""Selectores de lectura del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.12 · §8

Un selector carga datos de la base de datos y devuelve **result objects**. No
conoce la capa HTTP y no construye schemas de respuesta.
"""

from modules.pagos.domain.constants import EstadoOrdenPago
from modules.pagos.domain.models import OrdenPago, TransaccionPago
from modules.pagos.domain.results.pago_result import IntentoPagoResult


class OrdenPagoSelector:
    """Consultas de lectura de las órdenes de pago."""

    def obtener_por_id(self, orden_pago_id) -> OrdenPago | None:
        """La orden por su identificador."""
        return OrdenPago.objects.filter(id=orden_pago_id).first()

    def obtener_por_referencia(self, referencia: str) -> OrdenPago | None:
        """La orden por su referencia visible del proveedor."""
        if not referencia:
            return None
        return OrdenPago.objects.filter(referencia=referencia).first()

    def listar_intentos(self, orden_pago_id) -> list:
        """Los intentos de una orden, del más reciente al más antiguo.

        Devuelve una LISTA, no un queryset: la evaluación de la consulta ocurre
        dentro del contexto sync del selector y nunca en un contexto async.
        """
        return list(
            TransaccionPago.objects.filter(orden_pago_id=orden_pago_id).order_by(
                "-intento"
            )
        )

    def listar_confirmadas(self, limite: int = 100) -> list:
        """Las órdenes de pago confirmadas, de la más reciente a la más antigua.

        Son las únicas candidatas a una conciliación: un pago verificado es el
        único hecho que puede tener un derecho pendiente (RN-C08).

        Devuelve una LISTA, no un queryset: la evaluación de la consulta ocurre
        dentro del contexto sync del selector y nunca en un contexto async.
        """
        return list(
            OrdenPago.objects.filter(estado=EstadoOrdenPago.CONFIRMADA)
            .order_by("-created_at")[: max(int(limite or 0), 0)]
        )


class TransaccionPagoSelector:
    """Consultas de lectura de los intentos de pago."""

    def obtener_por_referencia_proveedor(
        self, referencia_proveedor: str
    ) -> TransaccionPago | None:
        """El intento por su referencia técnica del proveedor."""
        if not referencia_proveedor:
            return None
        return (
            TransaccionPago.objects.filter(referencia_proveedor=referencia_proveedor)
            .select_related("orden_pago")
            .first()
        )

    def listar_por_orden(self, orden_pago_id) -> list:
        """Los intentos de una orden, del más reciente al más antiguo.

        Devuelve una LISTA, no un queryset: la evaluación de la consulta ocurre
        dentro del contexto sync del selector y nunca en un contexto async.
        """
        return list(
            TransaccionPago.objects.filter(orden_pago_id=orden_pago_id)
            .select_related("orden_pago")
            .order_by("-intento")
        )

    def listar_como_result(self, orden_pago_id) -> list[IntentoPagoResult]:
        """Los intentos de una orden proyectados a result objects."""
        return [
            IntentoPagoResult(
                id=str(intento.id),
                intento=intento.intento,
                referencia_proveedor=intento.referencia_proveedor,
                estado=intento.estado,
                verificada=intento.verificada,
                codigo_respuesta=intento.codigo_respuesta,
                metodo_pago=intento.metodo_pago,
                creada_en=intento.created_at,
            )
            for intento in self.listar_por_orden(orden_pago_id)
        ]


__all__ = [
    "OrdenPagoSelector",
    "TransaccionPagoSelector",
]
