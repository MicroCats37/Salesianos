"""AppConfig del módulo `notificaciones`.

Contract: `contract/django-app-architecture-contract.md` §4.16
"""

from django.apps import AppConfig


class NotificacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.notificaciones"
    label = "notificaciones"
    verbose_name = "Notificaciones"
