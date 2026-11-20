"""AppConfig del módulo `competencias`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class CompetenciasConfig(AppConfig):
    """Configuración de la app de competencias."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.competencias"
    label = "competencias"
    verbose_name = "Competencias y encuentros"
