"""commerce module app config."""
from django.apps import AppConfig


class CommerceConfig(AppConfig):
    """Commerce module configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.commerce"
    label = "commerce"
    verbose_name = "Commerce"
