from django.apps import AppConfig


class SalesianosFestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.salesianos_fest"
    label = "salesianos_fest"
    verbose_name = "Salesianos FEST"

    def ready(self):
        """Import admin package to trigger admin registration."""
        from . import admin  # noqa: F401
