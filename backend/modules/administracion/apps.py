from django.apps import AppConfig


class AdministracionConfig(AppConfig):
    """Django AppConfig for the operational administration module."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.administracion"
    label = "administracion"
    verbose_name = "Administración"
