"""Admin registrations for pagos module — IzipayTransaccion read-only admin."""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from modules.pagos.domain.models.pago import IzipayTransaccion


@admin.register(IzipayTransaccion)
class IzipayTransaccionAdmin(SimpleHistoryAdmin):
    """Read-only admin for Izipay transactions — payment records are immutable audit trail."""

    list_display = [
        "transaction_id",
        "inscripcion",
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
        "inscripcion__responsable__nombres",
        "inscripcion__responsable__apellidos",
    ]
    readonly_fields = [
        "inscripcion",
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
        return super().get_queryset(request).select_related("inscripcion")
