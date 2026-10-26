"""Admin registrations for pagos module — OrdenPago and TransaccionPago."""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from modules.pagos.domain.models import OrdenPago, TransaccionPago


@admin.register(OrdenPago)
class OrdenPagoAdmin(SimpleHistoryAdmin):
    """Admin for generic payment orders."""

    list_display = [
        "numero",
        "monto_total",
        "moneda",
        "estado",
        "pagada_en",
        "expires_at",
        "descripcion",
        "referencia_externa",
        "created_at",
    ]
    list_filter = ["estado", "moneda"]
    search_fields = ["numero", "descripcion", "referencia_externa"]
    readonly_fields = ["created_at", "updated_at", "pagada_en"]
    ordering = ["-created_at"]


@admin.register(TransaccionPago)
class TransaccionPagoAdmin(SimpleHistoryAdmin):
    """Read-only admin for payment transactions — records are immutable audit trail."""

    list_display = [
        "transaction_id",
        "orden_pago",
        "amount",
        "currency",
        "status",
        "response_code",
        "metodo_pago",
        "created_at",
    ]
    list_filter = ["status", "currency", "metodo_pago", "proveedor"]
    search_fields = [
        "transaction_id",
        "order_number",
    ]
    readonly_fields = [
        "orden_pago",
        "proveedor",
        "transaction_id",
        "order_number",
        "amount",
        "currency",
        "status",
        "response_code",
        "response_message",
        "metodo_pago",
        "metadata",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("orden_pago")
