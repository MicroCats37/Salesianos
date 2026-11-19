"""AppConfig del módulo `commerce`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class CommerceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.commerce"
    label = "commerce"
    verbose_name = "Comercio"

    def ready(self):
        """Importa el paquete de admin para activar el registro de modelos."""
        from modules.commerce import admin  # noqa: F401
