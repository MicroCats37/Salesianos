"""`CommerceMarketplaceAdapter` — la implementación del puerto de comercio.

Packet: `DOM-05` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.10

Este adaptador es el ÚNICO punto del módulo que habla con `commerce`. Aquí
ocurre la traducción entre el vocabulario de los dos módulos:

| `commerce` (su vocabulario) | `marketplace` (el nuestro) |
|---|---|
| `Compra.estado = PENDIENTE` | `EstadoPagoPedido.PENDIENTE` |
| `Compra.estado = PAGADA` | `EstadoPagoPedido.CONFIRMADO` |
| `Compra.estado = CANCELADA` | `EstadoPagoPedido.NO_COMPLETADO` |

La terminología de `commerce` NO cruza la frontera: el dominio y el presenter
sólo ven el vocabulario de `marketplace` (api-wrapper-presenter-contract §6).

**Por qué un adaptador y no el consumo directo de `CompraFlujo`:** el módulo
necesita, además de crear la compra, LEER su estado para distinguir el
pago, el pedido y la entrega (RN-M07). El puerto expone las dos
operaciones; este adaptador las implementa.

**Quién construye el adaptador.** `modules/marketplace/di.py`, con una
fábrica perezosa: `commerce` liga su propio `CompraFlujo` en
`modules/commerce/di.py` y este adaptador lo CONSUME por el inyector. Así
el grafo de módulos queda acíclico, el orden de carga de Django no importa y
este módulo NO duplica el wiring de `commerce`.
"""

import logging
from uuid import UUID

from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError as DjangoValidationError

from modules.marketplace.domain.constants import EstadoPagoPedido
from modules.marketplace.domain.ports.comercio import ICommerceMarketplaceService
from modules.marketplace.domain.schemas.pedido_schemas import (
    CompraMarketplaceData,
    CompraMarketplaceFact,
)

logger = logging.getLogger(__name__)


class CommerceMarketplaceAdapter(ICommerceMarketplaceService):
    """La frontera de `marketplace` con la infraestructura comercial."""

    def __init__(self, compra_flujo, compra_selector):
        self.compra_flujo = compra_flujo
        self.compra_selector = compra_selector

    # ── Escritura ───────────────────────────────────────────────────────────

    async def crear_o_reutilizar_compra(
        self,
        data: CompraMarketplaceData,
    ) -> CompraMarketplaceFact:
        """Crea la compra de la intención, o reutiliza la pendiente.

        La compra la crea `commerce` a través de su interfaz CONGELADA
        (`FREEZE-CM-1.0.0`): este adaptador sólo traduce el snapshot ya
        resuelto por el servidor de `marketplace`.
        """
        from modules.commerce.domain.constants import OrigenCompra
        from modules.commerce.domain.schemas.compra_schemas import (
            CompraCreateData,
            LineaCompraSnapshot,
        )

        intencion = CompraCreateData(
            persona_id=UUID(str(data.persona_id)),
            origen=OrigenCompra.MARKETPLACE,
            lineas=[
                LineaCompraSnapshot(**linea.model_dump()) for linea in data.lineas
            ],
            referencia=data.referencia,
            moneda=data.moneda,
            total=data.total,
        )
        compra, reutilizada = await self.compra_flujo.crear_o_reutilizar_compra(
            intencion
        )
        return self._hechos(compra, reutilizada=reutilizada)

    # ── Lectura ─────────────────────────────────────────────────────────────

    async def hechos_compra(self, compra_id) -> CompraMarketplaceFact | None:
        """Los hechos de una compra, o `None` si no existe.

        Un identificador mal formado NO concede acceso ni lanza: se
        registra y se devuelve `None`.
        """
        compra = await sync_to_async(self._obtener_compra)(compra_id)
        if compra is None:
            return None
        return self._hechos(compra)

    def _obtener_compra(self, compra_id):
        """La compra por su identificador, o `None`."""
        if not compra_id:
            return None
        try:
            return self.compra_selector.obtener_por_id(compra_id)
        except (ValueError, TypeError, DjangoValidationError):
            logger.warning(
                "La consulta de la compra del pedido rechazó un identificador "
                "mal formado."
            )
            return None

    # ── Traducción ──────────────────────────────────────────────────────────

    def _hechos(self, compra, *, reutilizada: bool = False) -> CompraMarketplaceFact:
        """Proyecta una compra a los hechos que el módulo necesita."""
        return CompraMarketplaceFact(
            compra_id=str(compra.id),
            orden_pago_id=str(compra.orden_pago_id) if compra.orden_pago_id else None,
            estado_pago=self._traducir_estado(compra.estado),
            total=compra.total,
            moneda=compra.moneda,
            reutilizada=reutilizada,
        )

    @staticmethod
    def _traducir_estado(estado: str) -> str:
        """Traduce el estado comercial de `commerce` al del módulo."""
        from modules.commerce.domain.constants import EstadoCompra

        if estado == EstadoCompra.PAGADA:
            return EstadoPagoPedido.CONFIRMADO
        if estado == EstadoCompra.CANCELADA:
            return EstadoPagoPedido.NO_COMPLETADO
        return EstadoPagoPedido.PENDIENTE


__all__ = ["CommerceMarketplaceAdapter"]
