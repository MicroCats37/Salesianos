"""AppConfig del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class PatrocinadoresConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.patrocinadores"
    label = "patrocinadores"
    verbose_name = "Patrocinadores"

    def ready(self):
        """Importa el paquete de admin para activar el registro de modelos."""
        from modules.patrocinadores import admin  # noqa: F401
