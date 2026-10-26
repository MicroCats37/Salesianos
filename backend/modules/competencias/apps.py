from django.apps import AppConfig


class CompetenciasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.competencias"
    label = "competencias"
    verbose_name = "Competencias"

    def ready(self):
        """Import admin package to trigger admin registration."""
        from . import admin  # noqa: F401
