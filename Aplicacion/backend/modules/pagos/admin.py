"""Registro en el admin de Django del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.13

El admin es una superficie de OPERACIÓN. Los campos que son hechos
irreversibles —el monto congelado de la orden, el estado del intento, la
evidencia de la verificación— son de sólo lectura: escribirlos a mano
destruiría la cadena de auditoría del pago.
"""

from django.contrib import admin

from modules.pagos.domain.models import (
    OrdenPago,
    RegistroIdempotencia,
    TransaccionPago,
)


@admin.register(OrdenPago)
class OrdenPagoAdmin(admin.ModelAdmin):
    """Admin de las órdenes de pago."""

    list_display = (
        "referencia",
        "estado",
        "monto",
        "moneda",
        "pagada_en",
        "vence_en",
        "created_at",
    )
    list_filter = ("estado", "moneda")
    search_fields = ("referencia",)
    readonly_fields = (
        "id",
        "referencia",
        "monto",
        "moneda",
        "pagada_en",
        "vence_en",
        "metadata",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)


@admin.register(TransaccionPago)
class TransaccionPagoAdmin(admin.ModelAdmin):
    """Admin de los intentos de pago.

    Un intento es una **traza de auditoría**: nunca se edita ni se borra desde
    el admin.
    """

    list_display = (
        "orden_pago",
        "intento",
        "estado",
        "verificada",
        "codigo_respuesta",
        "metodo_pago",
        "created_at",
    )
    list_filter = ("estado", "verificada")
    search_fields = ("referencia_proveedor", "orden_pago__referencia")
    readonly_fields = (
        "id",
        "orden_pago",
        "intento",
        "referencia_proveedor",
        "estado",
        "verificada",
        "evidencia",
        "codigo_respuesta",
        "mensaje_respuesta",
        "metodo_pago",
        "metadata",
        "created_at",
        "updated_at",
    )
    ordering = ("orden_pago", "intento")
    list_select_related = ("orden_pago",)


@admin.register(RegistroIdempotencia)
class RegistroIdempotenciaAdmin(admin.ModelAdmin):
    """Admin de las claves de idempotencia.

    Sólo lectura: el registro es la prueba de que una intención se ejecutó una
    sola vez.
    """

    list_display = ("ambito", "clave", "codigo_estado", "created_at")
    list_filter = ("ambito", "codigo_estado")
    search_fields = ("ambito", "clave")
    readonly_fields = (
        "id",
        "ambito",
        "clave",
        "huella",
        "respuesta",
        "codigo_estado",
        "created_at",
        "updated_at",
    )
    ordering = ("-created_at",)
