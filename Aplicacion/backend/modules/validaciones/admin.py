"""El administration de Django del módulo `validaciones`.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

El ACTA de validación es un hecho que NO se edita a mano: se registra. Por
eso todo es de sólo lectura (`contract/django-app-architecture-contract.md`
§10, "Admin").
"""

from django.contrib import admin

from modules.validaciones.domain.models import Ticket, ValidacionTicket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """La credencial emitida."""

    list_display = [
        "edicion",
        "tipo_derecho",
        "operacion",
        "estado",
        "emitido_en",
    ]
    list_filter = ["tipo_derecho", "operacion", "estado", "edicion"]
    search_fields = ["codigo"]
    readonly_fields = ["created_at", "updated_at", "emitido_en"]
    date_hierarchy = "emitido_en"
    ordering = ["-emitido_en"]

    def has_add_permission(self, request, obj=None) -> bool:
        """La credencial se emite con el comando, no a mano."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """La credencial no se edita: se revoca o no se toca."""
        return False


@admin.register(ValidacionTicket)
class ValidacionTicketAdmin(admin.ModelAdmin):
    """El acta de cada intento de validación."""

    list_display = [
        "ticket",
        "operacion",
        "resultado",
        "cantidad",
        "actor_usuario",
        "registrado_en",
    ]
    list_filter = ["operacion", "resultado", "registrado_en"]
    search_fields = ["ticket__codigo", "motivo_codigo"]
    readonly_fields = ["created_at", "updated_at", "registrado_en"]
    date_hierarchy = "registrado_en"
    ordering = ["-registrado_en"]

    def has_add_permission(self, request, obj=None) -> bool:
        """El acta se registra por la operación, no a mano."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """El acta es un hecho consumed: no se edita."""
        return False


__all__ = ["TicketAdmin", "ValidacionTicketAdmin"]
