"""Registro en el Django Admin del módulo `marketplace`.

Contract: `contract/django-app-architecture-contract.md` §4.13
"""

from django.contrib import admin

from modules.marketplace.domain.models import (
    CategoriaProducto,
    Pedido,
    PedidoDetalle,
    Producto,
    ProductoImagen,
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
