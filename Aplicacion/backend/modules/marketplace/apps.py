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
        """Importa el paquete de admin para activar el registro de modelos."""
        from modules.marketplace import admin  # noqa: F401
