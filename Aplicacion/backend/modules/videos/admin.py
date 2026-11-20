"""Registro en el Django Admin del módulo `videos`.

Change: `public-video-streaming-crud`
Contract: `contract/django-app-architecture-contract.md` §4.13

Esta es la SUPERFICIE de Django (`/admin/`), distinta de la del producto
(`/administracion/**`). Ambas son legítimas: ninguna suplanta a la otra.
"""

from django.contrib import admin

from modules.videos.domain.models import Video


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Configuración de admin de `Video`."""

    list_display = ["titulo", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["titulo", "descripcion"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["-created_at"]
    fieldsets = (
        (
            "Contenido",
            {
                "fields": ("titulo", "descripcion", "url"),
            },
        ),
        (
            "Auditoría",
            {
                "fields": ("id", "created_at", "updated_at"),
            },
        ),
    )


__all__ = ["VideoAdmin"]
