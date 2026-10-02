"""Usuario and Persona model admins."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from simple_history.admin import SimpleHistoryAdmin

from modules.usuarios.domain.models import Usuario, Persona


# ── Usuario admin ───────────────────────────────────────────────────────────────

@admin.register(Usuario)
class UsuarioAdmin(SimpleHistoryAdmin, UserAdmin):
    """Admin for custom Usuario model (username-based auth + Persona relation)."""

    list_display = [
        "username",
        "email",
        "persona_fk",
        "is_staff",
        "is_active",
    ]
    search_fields = [
        "username",
        "email",
        "persona_fk__numero_documento",
        "persona_fk__nombres",
        "persona_fk__apellidos",
    ]
    list_filter = ["is_staff", "is_active", "is_superuser"]
    raw_id_fields = ["persona_fk"]

    # Fieldsets for existing user editing
    # Completely override UserAdmin.fieldsets — Usuario lacks first_name, last_name, date_joined
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            "Datos personales",
            {
                "fields": (
                    "persona_fk",
                    "dni",
                    "email",
                )
            },
        ),
        (
            "Permisos",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Fechas importantes",
            {"fields": ("last_login",)},
        ),
    )

    # Fields shown when creating a user — must include persona_fk (required) and password fields
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "persona_fk", "password1", "password2"),
        }),
    )

    readonly_fields = ["created_at", "updated_at"]


# ── Persona admin ───────────────────────────────────────────────────────────────

@admin.register(Persona)
class PersonaAdmin(SimpleHistoryAdmin):
    """Admin for Persona — civil identity data with organized fieldsets."""

    list_display = [
        "numero_documento",
        "tipo_documento",
        "nombres",
        "apellidos",
        "genero",
        "telefono",
        "acepto_bases",
        "acepto_aptitud_fisica",
        "acepto_imagen",
    ]
    search_fields = ["nombres", "apellidos", "numero_documento", "telefono"]
    list_filter = ["tipo_documento", "genero", "acepto_bases", "acepto_aptitud_fisica", "acepto_imagen"]
    ordering = ["-created_at"]
    raw_id_fields = []

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Identidad civil",
            {
                "fields": ("tipo_documento", "numero_documento", "nombres", "apellidos", "genero"),
            },
        ),
        (
            "Contacto",
            {
                "fields": ("telefono", "whatsapp"),
            },
        ),
        (
            "Contacto de emergencia",
            {
                "fields": ("contacto_emergencia_nombre", "contacto_emergencia_telefono"),
            },
        ),
        (
            "Seguro / Salud",
            {
                "fields": ("aseguradora_nombre", "aseguradora_numero_poliza"),
            },
        ),
        (
            "Aceptaciones",
            {
                "fields": ("acepto_bases", "acepto_aptitud_fisica", "acepto_imagen"),
            },
        ),
        (
            "Auditoría",
            {
                "fields": ("created_at", "updated_at"),
            },
        ),
    )
