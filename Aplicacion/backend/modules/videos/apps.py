"""AppConfig del módulo `videos`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class VideosConfig(AppConfig):
    """Configuración de la aplicación de videos públicos."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.videos"
    label = "videos"
    verbose_name = "Videos"
