"""AppConfig del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class PagosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.pagos"
    label = "pagos"
    verbose_name = "Pagos"

    def ready(self):
        """Importa el paquete de admin para activar el registro de modelos."""
        from modules.pagos import admin  # noqa: F401
