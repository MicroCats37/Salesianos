from django.apps import AppConfig


class EventosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.eventos"
    label = "eventos"
    verbose_name = "Eventos"

    def ready(self):
        """Import admin package to trigger admin registration."""
        from . import admin  # noqa: F401
