"""
Admin registrations for the competencias module.

The bracket is operated by the administrators through the API of the module
(Phase 3+); this admin surface is read-oriented and exists to expose the
audit trail (`SimpleHistoryAdmin` shows the before/after diff, the actor and
the date of every change).
"""
from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from .domain.models import Competencia, CompetenciaEquipo, Encuentro, Ronda


@admin.register(Competencia)
class CompetenciaAdmin(SimpleHistoryAdmin):
    """Admin configuration for the Competencia model."""

    list_display = [
        "nombre",
        "evento",
        "disciplina",
        "categoria",
        "fecha",
        "estado",
        "created_at",
    ]
    list_filter = ["estado", "evento", "disciplina", "categoria"]
    search_fields = ["nombre"]
    readonly_fields = ["created_at", "updated_at", "version"]
    date_hierarchy = "fecha"
    ordering = ["-fecha", "nombre"]


@admin.register(CompetenciaEquipo)
class CompetenciaEquipoAdmin(SimpleHistoryAdmin):
    """Admin configuration for the CompetenciaEquipo model."""

    list_display = [
        "equipo",
        "competencia",
        "orden",
        "estado",
        "created_at",
    ]
    list_filter = ["estado", "competencia"]
    readonly_fields = ["created_at", "updated_at", "version"]
    ordering = ["competencia", "orden"]


@admin.register(Ronda)
class RondaAdmin(SimpleHistoryAdmin):
    """Admin configuration for the Ronda model."""

    list_display = ["etiqueta", "competencia", "orden", "estado", "created_at"]
    list_filter = ["estado", "competencia"]
    search_fields = ["etiqueta"]
    readonly_fields = ["created_at", "updated_at", "version"]
    ordering = ["competencia", "orden"]


@admin.register(Encuentro)
class EncuentroAdmin(SimpleHistoryAdmin):
    """Admin configuration for the Encuentro model."""

    list_display = [
        "orden",
        "ronda",
        "participante_1",
        "participante_2",
        "inicio_programado",
        "estado",
        "es_bye",
        "created_at",
    ]
    list_filter = ["estado", "es_bye", "ronda"]
    readonly_fields = ["created_at", "updated_at", "version"]
    ordering = ["ronda", "orden"]
