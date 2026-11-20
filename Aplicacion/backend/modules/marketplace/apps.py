"""AppConfig del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class MarketplaceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.marketplace"
    label = "marketplace"
    verbose_name = "Marketplace"

    def ready(self):
        """Importa el paquete de admin y registra el ACTIVADOR de stock.

        El registro del activador es lo que permite que un pago confirmado
        descuente el stock de la tienda (`RN-M06`, `FR-04` §2.3).

        Se hace AQUÍ, y no en un binding de DI, porque el registro de
        activadores de `commerce` es un objeto ÚNICO DEL PROCESO
        (`D-FND-05-04`): un dominio registra su activador sin tocar el
        código de `commerce`. Y se hace en `ready()` porque es el punto en
        que la aplicación está lista y cualquier camino que llegue al
        coordinador encuentra el activador.

        Es idempotente: registrar dos veces el mismo origen sustituye el
        activador, no lo duplica.
        """
        from modules.marketplace import admin  # noqa: F401

        from modules.commerce.domain.constants import OrigenCompra
        from modules.commerce.domain.services.core.registro_activadores_compra import (
            obtener_registro,
        )
        from modules.marketplace.domain.services.core.activador_marketplace import (
            ActivadorMarketplace,
        )

        registro = obtener_registro()
        registro.registrar(
            OrigenCompra.MARKETPLACE,
            ActivadorMarketplace(),
        )
