"""Registro en el Django Admin del módulo `patrocinadores`.

Contract: `contract/django-app-architecture-contract.md` §4.13
"""

from django.contrib import admin

from modules.patrocinadores.domain.models import (
    Patrocinador,
    PatrocinadorImagen,
)


@admin.register(Patrocinador)
class PatrocinadorAdmin(admin.ModelAdmin):
    """Configuración de admin de `Patrocinador`."""

    list_display = [
        "nombre",
        "slug",
        "edicion",
        "visible",
        "created_at",
    ]
    list_filter = ["visible", "edicion"]
    search_fields = ["nombre", "slug"]
    readonly_fields = ["id", "edicion", "created_at", "updated_at"]
    ordering = ["nombre"]


@admin.register(PatrocinadorImagen)
class PatrocinadorImagenAdmin(admin.ModelAdmin):
    """Configuración de admin de `PatrocinadorImagen`."""

    list_display = ["patrocinador", "orden", "imagen", "created_at"]
    list_filter = ["patrocinador"]
    readonly_fields = ["id", "patrocinador", "created_at", "updated_at"]
    ordering = ["patrocinador", "orden", "id"]
