"""
Registro en el Django Admin del módulo `usuarios`.

`contract/django-app-architecture-contract.md` §4.13: un `ModelAdmin` por
modelo, con `list_display` acotado, `list_filter`, `search_fields` y
`readonly_fields` de auditoría.
"""

from django.contrib import admin

from modules.usuarios.domain.models import Persona, Usuario


@admin.register(Persona)
class PersonaAdmin(admin.ModelAdmin):
    """Admin de la identidad civil."""

    list_display = [
        "nombres",
        "apellidos",
        "tipo_documento",
        "numero_documento",
        "origen_datos",
    ]
    list_display_links = ["nombres"]
    list_filter = ["tipo_documento", "origen_datos"]
    search_fields = ["numero_documento", "nombres", "apellidos"]
    readonly_fields = ["id", "created_at", "updated_at", "origen_datos"]
    ordering = ["-created_at"]


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    """Admin de las cuentas.

    La cuenta tiene una `Persona` OPCIONAL: las cuentas técnicas (superusuario)
    no la tienen y las personas sin cuenta no aparecen aquí.
    """

    list_display = [
        "username",
        "email",
        "persona_fk",
        "is_staff",
        "is_active",
    ]
    list_display_links = ["username"]
    list_filter = ["is_staff", "is_active", "is_superuser"]
    search_fields = [
        "username",
        "email",
        "persona_fk__numero_documento",
        "persona_fk__nombres",
        "persona_fk__apellidos",
    ]
    readonly_fields = ["id", "created_at", "updated_at", "last_login"]
    raw_id_fields = ["persona_fk"]
    filter_horizontal = ["groups", "user_permissions"]
    ordering = ["-created_at"]


__all__ = ["PersonaAdmin", "UsuarioAdmin"]
