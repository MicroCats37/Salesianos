"""Registro en el admin de Django del módulo `commerce`.

Contract: `contract/django-app-architecture-contract.md` §4.13

El admin es una superficie de OPERACIÓN, no de negocio: por eso los campos
congelados (el total y el snapshot de líneas) son de sólo lectura. Editar el
total a mano rompería `RN-C02`.
"""

from django.contrib import admin

from modules.commerce.domain.models import ActivacionCompra, Compra


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    """Admin de las compras comerciales."""

    list_display = (
        "id",
        "origen",
        "estado",
        "total",
        "moneda",
        "persona",
        "created_at",
    )
    list_filter = ("origen", "estado", "moneda")
    search_fields = ("referencia", "persona__numero_documento", "persona__nombres")
    readonly_fields = (
        "id",
        "persona",
        "origen",
        "total",
        "moneda",
        "lineas_snapshot",
        "orden_pago",
        "referencia",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    list_select_related = ("persona", "orden_pago")


@admin.register(ActivacionCompra)
class ActivacionCompraAdmin(admin.ModelAdmin):
    """Admin de las activaciones de derechos.

    Es una superficie de OPERACIÓN: la clave de activación, el origen y el
    estado son de sólo lectura. Editarlos a mano rompería la idempotencia de
    la activación (`FR-04` I-2).
    """

    list_display = (
        "id",
        "compra",
        "origen",
        "estado",
        "intentos",
        "en_curso",
        "activada_en",
        "created_at",
    )
    list_filter = ("origen", "estado", "en_curso")
    search_fields = ("clave", "compra__referencia")
    readonly_fields = (
        "id",
        "compra",
        "origen",
        "clave",
        "estado",
        "intentos",
        "en_curso",
        "ultimo_intento_en",
        "activada_en",
        "incidencia",
        "detalle",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
    list_select_related = ("compra",)
