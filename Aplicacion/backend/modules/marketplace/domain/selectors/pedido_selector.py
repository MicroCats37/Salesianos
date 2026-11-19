"""Selectores del pedido de marketplace.

Contract: `contract/django-app-architecture-contract.md` §8

REGLA (F-26): un selector que devuelve un `QuerySet` es una mina en un
contexto async: la consulta es perezosa y recorrerla dentro de una función
async lanza `SynchronousOnlyOperation`. Por eso TODOS los selectores de este
módulo devuelven LISTAS ya evaluadas.

Las consultas son de lectura y no modifican el alcance: el filtro por edición
es siempre explícito (`edicion_id`), nunca implícito.
"""

from modules.marketplace.domain.models import Pedido, PedidoDetalle


class PedidoSelector:
    """Consultas de lectura sobre `Pedido` y su detalle."""

    def obtener_por_token(self, token: str) -> Pedido | None:
        """Un pedido por su token privado de seguimiento, o `None`.

        El token es una credencial: la consulta no filtra por edición porque
        el token ES el ámbito. La autorización la decide el flujo.
        """
        if not token:
            return None
        return (
            Pedido.objects.filter(token=token)
            .select_related("edicion", "comprador", "compra")
            .first()
        )

    def obtener_por_huella(self, comprador_id, edicion_id, huella: str) -> Pedido | None:
        """El pedido de una INTENCIÓN de compra, en cualquier estado.

        La búsqueda NO filtra por estado a propósito: el flujo reconcilia el
        pedido encontrado con el hecho del pago antes de decidir si se
        recupera o si hay que crear uno nuevo (RN-C04).
        """
        if not huella:
            return None
        return (
            Pedido.objects.filter(
                comprador_id=comprador_id,
                edicion_id=edicion_id,
                huella=huella,
            )
            .select_related("edicion", "comprador", "compra")
            .order_by("-created_at", "-id")
            .first()
        )

    def listar_detalles(self, pedido_id) -> list[PedidoDetalle]:
        """El detalle de un pedido, en su orden canónico."""
        return list(PedidoDetalle.objects.filter(pedido_id=pedido_id).order_by("id"))


__all__ = ["PedidoSelector"]
