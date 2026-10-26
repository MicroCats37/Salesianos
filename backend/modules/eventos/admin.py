"""Admin registrations for eventos module."""
from django.contrib import admin

from .domain.models import Evento


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    """Admin configuration for Evento model."""

    list_display = ["nombre", "fecha_inicio", "fecha_fin", "esta_activo", "fecha_limite_modificacion", "created_at"]
    list_filter = ["esta_activo", "fecha_inicio", "fecha_limite_modificacion"]
    search_fields = ["nombre"]
    readonly_fields = ["created_at", "updated_at"]
    date_hierarchy = "fecha_inicio"
    ordering = ["-fecha_inicio"]
