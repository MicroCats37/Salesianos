"""El puerto de COMERCIO de `marketplace` (`DOM-05`).

Contract: `contract/django-app-architecture-contract.md` §4.10

`commerce` es la INFRAESTRUCTURA comercial compartida y su interfaz está
CONGELADA (`FREEZE-CM-1.0.0`, `RN-C01`, `D-FND-04-06`): los dominios crean su
compra **in-process**, no por una ruta HTTP compartida.

Este puerto es la FRONTERA del módulo con esa infraestructura:

- El DOMINIO de `marketplace` no importa `commerce`: conoce este puerto.
- La IMPLEMENTACIÓN vive en `marketplace/infrastructure/services/` y traduce
  el vocabulario de `commerce` al del módulo (el `estado_pago` que sale de
  aquí ya está traducido).

Por qué un puerto y no el consumo directo de `CompraFlujo` (que es lo que hace
DOM-01): este paquete necesita, además de CREAR la compra, LEER su estado
para distinguir pago, pedido y entrega (RN-M07). El puerto expone las dos
operaciones con el vocabulario del módulo y sin filtrar la terminología de
`commerce` al dominio ni a la presentación.
"""

from abc import ABC, abstractmethod

from modules.marketplace.domain.schemas.pedido_schemas import (
    CompraMarketplaceData,
    CompraMarketplaceFact,
)


class ICommerceMarketplaceService(ABC):
    """La frontera de `marketplace` con la infraestructura comercial."""

    @abstractmethod
    async def crear_o_reutilizar_compra(
        self,
        data: CompraMarketplaceData,
    ) -> CompraMarketplaceFact:
        """Crea la compra de una intención o reutiliza la pendiente.

        Es I-4 de FR-04: reabrir el checkout NO crea otra compra.

        Args:
            data: la intención ya resuelta por el servidor (líneas congeladas).

        Returns:
            Los hechos de la compra, con el estado del pago ya traducido.

        Raises:
            `CompraTotalIncoherenteError`: el total declarado no coincide con
                el derivado de las líneas (RN-C02).
            `CompraReferenciaInvalidaError`: la referencia de la intención no
                es válida.
        """
        ...

    @abstractmethod
    async def hechos_compra(self, compra_id) -> CompraMarketplaceFact | None:
        """Los hechos de una compra, en el vocabulario del módulo.

        Es la lectura que permite distinguir PEDIDO, PAGO y ENTREGA: el
        estado del pago es un hecho de `commerce` y el módulo lo proyecta
        sin exponer la terminología de otro dominio (RN-M07, RN-C08).

        Args:
            compra_id: identificador de la compra.

        Returns:
            Los hechos de la compra, o `None` cuando la compra no existe.
        """
        ...


__all__ = ["ICommerceMarketplaceService"]
