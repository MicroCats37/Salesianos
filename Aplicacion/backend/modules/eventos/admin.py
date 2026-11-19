"""Registro en el Django Admin del módulo `eventos`.

Contract: `contract/django-app-architecture-contract.md` §4.13
"""

from django.contrib import admin

from modules.eventos.domain.models import Edicion, Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Configuración de admin de `Evento`."""

    list_display = ["nombre", "slug", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["nombre", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["nombre"]


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    """Configuración de admin de `Edicion`."""

    list_display = [
        "nombre",
        "anio",
        "evento",
        "estado",
        "modulos_habilitados",
        "created_at",
    ]
    list_filter = ["estado", "anio", "evento"]
    search_fields = ["nombre", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-anio", "nombre"]
