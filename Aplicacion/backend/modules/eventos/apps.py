"""AppConfig del módulo `eventos`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class EventosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.eventos"
    label = "eventos"
    verbose_name = "Eventos"

    def ready(self):
        """Importa el paquete de admin para activar el registro de modelos."""
        from modules.eventos import admin  # noqa: F401
