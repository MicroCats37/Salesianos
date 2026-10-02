from django.apps import AppConfig


class InscripcionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.inscripciones"
    label = "inscripciones"
    verbose_name = "Inscripciones"

    def ready(self):
        """Import admin package to trigger admin registration."""
        from . import admin  # noqa: F401
