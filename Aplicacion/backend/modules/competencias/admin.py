"""Admin de Django del módulo `competencias`.

Contract: `contract/django-app-architecture-contract.md` §4.13

El admin es una SUPERFICIE DE LECTURA y de apoyo: los cambios de negocio
(incorporar un equipo, programar un encuentro, registrar un resultado,
corregir un ganador) NO se hacen aquí: pasan por la API, que es la que
aplica el bloqueo optimista, la auditoría y las reglas.

Por eso los campos de estado y de versión son de SOLO LECTURA: el admin no
puede saltarse el `expected_version`.
"""

from django.contrib import admin

from modules.competencias.domain.models import (
    AuditoriaOperacion,
    Competencia,
    CompetenciaEquipo,
    Encuentro,
    Ronda,
)


@admin.register(Competencia)
class CompetenciaAdmin(admin.ModelAdmin):
    """Listado de competencias por edición y disciplina."""

    list_display = ("nombre", "edicion", "disciplina", "fecha", "estado", "version")
    list_filter = ("estado", "edicion", "disciplina")
    search_fields = ("nombre",)
    date_hierarchy = "fecha"
    readonly_fields = ("id", "version", "created_at", "updated_at")
    ordering = ("-fecha", "nombre")


@admin.register(CompetenciaEquipo)
class CompetenciaEquipoAdmin(admin.ModelAdmin):
    """Participaciones de los equipos en los cuadros."""

    list_display = ("equipo", "competencia", "orden", "estado", "version")
    list_filter = ("estado", "competencia")
    search_fields = ("equipo__nombre",)
    readonly_fields = ("id", "version", "created_at", "updated_at")


@admin.register(Ronda)
class RondaAdmin(admin.ModelAdmin):
    """Rondas de los cuadros."""

    list_display = ("etiqueta", "competencia", "orden", "estado", "version")
    list_filter = ("estado", "competencia")
    search_fields = ("etiqueta",)
    readonly_fields = ("id", "version", "created_at", "updated_at")


@admin.register(Encuentro)
class EncuentroAdmin(admin.ModelAdmin):
    """Encuentros de los cuadros."""

    list_display = (
        "orden",
        "ronda",
        "estado",
        "es_bye",
        "inicio_programado",
        "version",
    )
    list_filter = ("estado", "es_bye", "ronda__competencia")
    date_hierarchy = "inicio_programado"
    readonly_fields = (
        "id",
        "version",
        "ganador",
        "ganador_propagado",
        "iniciado_en",
        "finalizado_en",
        "created_at",
        "updated_at",
    )


@admin.register(AuditoriaOperacion)
class AuditoriaOperacionAdmin(admin.ModelAdmin):
    """El ACTA de las operaciones protegidas.

    El `detalle` es contexto técnico del servidor: se puede leer en el admin
    (que es interno) pero NUNCA sale en una respuesta HTTP.
    """

    list_display = ("accion", "competencia", "encuentro", "actor", "created_at")
    list_filter = ("accion", "created_at")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("-created_at",)


__all__ = [
    "AuditoriaOperacionAdmin",
    "CompetenciaAdmin",
    "CompetenciaEquipoAdmin",
    "EncuentroAdmin",
    "RondaAdmin",
]
