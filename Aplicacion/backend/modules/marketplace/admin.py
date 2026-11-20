"""Registro en el Django Admin del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.13
"""

from django.contrib import admin

from modules.marketplace.domain.models import (
    CategoriaProducto,
    EntregaPedido,
    MovimientoInventario,
    Pedido,
    PedidoDetalle,
    Producto,
    ProductoImagen,
    ReservaInventario,
)


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    """Configuración de admin de `CategoriaProducto`."""

    list_display = ["nombre", "slug", "edicion", "orden", "created_at"]
    list_filter = ["edicion"]
    search_fields = ["nombre", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["orden", "nombre"]


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Configuración de admin de `Producto`."""

    list_display = [
        "nombre",
        "slug",
        "edicion",
        "categoria",
        "precio",
        "precio_oferta",
        "estado",
        "created_at",
    ]
    list_filter = ["estado", "edicion", "categoria"]
    search_fields = ["nombre", "slug"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["nombre"]


@admin.register(ProductoImagen)
class ProductoImagenAdmin(admin.ModelAdmin):
    """Configuración de admin de `ProductoImagen`."""

    list_display = ["producto", "orden", "es_principal", "imagen", "created_at"]
    list_filter = ["es_principal", "producto"]
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["producto", "orden", "id"]


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """Configuración de admin de `Pedido`.

    El `estado_entrega` NO lo edita el admin: lo avanza `DOM-06` (inventario y
    entrega). El pago NUNCA lo habilita (RN-M07).
    """

    list_display = [
        "id",
        "comprador",
        "edicion",
        "estado",
        "estado_entrega",
        "total",
        "moneda",
        "created_at",
    ]
    list_filter = ["estado", "estado_entrega", "edicion"]
    search_fields = ["huella", "referencia"]
    readonly_fields = [
        "id",
        "edicion",
        "comprador",
        "compra",
        "huella",
        "referencia",
        "total",
        "moneda",
        "token",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]


@admin.register(PedidoDetalle)
class PedidoDetalleAdmin(admin.ModelAdmin):
    """Configuración de admin de `PedidoDetalle`.

    El detalle es el SNAPSHOT CONGELADO del pedido (RN-M03): no se edita a
    mano. Sólo la lectura es posible desde el admin.
    """

    list_display = [
        "pedido",
        "tipo_concepto",
        "concepto_nombre",
        "cantidad",
        "precio_unitario",
        "precio_aplicado",
    ]
    list_filter = ["tipo_concepto"]
    search_fields = ["concepto_nombre", "concepto_id"]
    readonly_fields = [
        "id",
        "pedido",
        "tipo_concepto",
        "concepto_id",
        "concepto_nombre",
        "cantidad",
        "precio_unitario",
        "precio_aplicado",
        "created_at",
        "updated_at",
    ]
    ordering = ["pedido", "id"]


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    """La BITÁCORA del inventario: de SOLO LECTURA.

    Los movimientos los escribe el DOMINIO (venta, reposición, merma,
    consumo, ajuste y su reversa). El admin los muestra: no los crea, no los
    edita y no los borra (`RN-M04`).
    """

    list_display = [
        "producto",
        "tipo",
        "cantidad",
        "motivo",
        "referencia",
        "actor",
        "created_at",
    ]
    list_filter = ["tipo", "producto"]
    search_fields = ["motivo", "referencia"]
    readonly_fields = [
        "id",
        "producto",
        "cantidad",
        "tipo",
        "motivo",
        "referencia",
        "actor",
        "compensatorio",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at", "-id"]

    def has_add_permission(self, request) -> bool:
        """La bitácora no se escribe a mano: la escribe el dominio."""
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        """Un movimiento no se edita: se compensa con otro."""
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        """Un movimiento no se borra: se compensa con otro."""
        return False


@admin.register(ReservaInventario)
class ReservaInventarioAdmin(admin.ModelAdmin):
    """Las reservas de existencias: de SOLO LECTURA.

    Las reserva, confirma y libera el DOMINIO (RN-M06).
    """

    list_display = ["producto", "pedido", "cantidad", "estado", "created_at"]
    list_filter = ["estado", "producto"]
    search_fields = ["referencia"]
    readonly_fields = [
        "id",
        "producto",
        "pedido",
        "cantidad",
        "estado",
        "referencia",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at", "-id"]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EntregaPedido)
class EntregaPedidoAdmin(admin.ModelAdmin):
    """Los actas de entrega: de SOLO LECTURA.

    La entrega la confirma el OPERADOR por la ruta de entrega (RN-M07).
    """

    list_display = [
        "pedido",
        "cantidad_total",
        "actor",
        "created_at",
    ]
    search_fields = ["referencia"]
    readonly_fields = [
        "id",
        "pedido",
        "actor",
        "referencia",
        "cantidad_total",
        "detalle",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at", "-id"]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
