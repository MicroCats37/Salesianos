"""Registro en el Django Admin del módulo `salesianos_fest`.

Contract: `contract/django-app-architecture-contract.md` §4.13

El admin es una SUPERFICIE DE OPERACIÓN, no de negocio: los campos
`readonly_fields` son las marcas de tiempo y el estado comercial congelado.
"""

from django.contrib import admin

from modules.salesianos_fest.domain.models import (
    ActivacionCapacidad,
    ActivacionPase,
    BeneficioConcedido,
    Categoria,
    CompraPase,
    CortesiaPase,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    PaqueteBeneficio,
    PaquetePrecio,
    Pase,
    PaseBeneficiario,
    PasePrecio,
    Participacion,
    Promocion,
)


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    """Las cohortes de promoción.

    Son GLOBALES: no cuelgan de ninguna edición. El `anio` es su clave
    natural y no se edita a mano una vez que hay inscripciones que lo usan.
    """

    list_display = ("nombre", "anio", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Las bandas competitivas de una edición.

    El rango de promociones es la regla de derivación cohorte → categoría:
    no se edita a mano sin revisar las inscripciones afectadas.
    """

    list_display = ("nombre", "edicion", "promocion_desde", "promocion_hasta", "estado")
    list_filter = ("estado", "edicion")
    search_fields = ("nombre",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "estado", "modalidad")
    list_filter = ("estado", "modalidad", "edicion")
    search_fields = ("nombre", "slug")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Paquete)
class PaqueteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "edicion",
        "estado",
        "tipo",
        "minimo_compra_inicial",
    )
    list_filter = ("estado", "tipo", "modo_disciplinas", "edicion")
    search_fields = ("nombre", "slug")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PaqueteBeneficio)
class PaqueteBeneficioAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "paquete", "tipo", "cantidad")
    list_filter = ("tipo", "paquete")
    search_fields = ("codigo", "nombre")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PaquetePrecio)
class PaquetePrecioAdmin(admin.ModelAdmin):
    list_display = ("paquete", "monto", "moneda", "vigente_desde", "vigente_hasta")
    list_filter = ("paquete", "moneda")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "edicion",
        "responsable",
        "paquete",
        "promocion",
        "estado",
        "cupos_pagados",
        "cupos_asignados",
    )
    list_filter = ("estado", "edicion", "paquete", "promocion")
    search_fields = ("referencia",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "referencia",
        "promocion",
        "fusion_promocion",
        "cupos_solicitados",
        "cupos_pagados",
        "cupos_asignados",
    )


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "inscripcion", "disciplina", "categoria", "estado")
    list_filter = ("estado", "disciplina", "categoria")
    search_fields = ("nombre",)
    readonly_fields = ("created_at", "updated_at", "categoria")


@admin.register(Participacion)
class ParticipacionAdmin(admin.ModelAdmin):
    """La plantilla de la inscripción.

    Los campos de capacidad son de SOLO LECTURA: los mueve el servicio de
    capacidad con sentencias atómicas, no un operador del admin.
    """

    list_display = (
        "id",
        "inscripcion",
        "persona",
        "equipo",
        "rol",
        "estado",
    )
    list_filter = ("estado", "rol", "edicion", "disciplina")
    search_fields = ("inscripcion__referencia",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "edicion",
        "disciplina",
        "retirada_en",
    )


@admin.register(ActivacionCapacidad)
class ActivacionCapacidadAdmin(admin.ModelAdmin):
    """El acta de las activaciones de capacidad.

    `clave` es de SOLO LECTURA: es la clave de idempotencia que produce el
    coordinador de `commerce` y es la autoridad del "exactamente una vez".
    """

    list_display = (
        "id",
        "inscripcion",
        "tipo",
        "cupos",
        "compra_id",
        "aplicada_en",
    )
    list_filter = ("tipo",)
    search_fields = ("clave", "compra_id")
    readonly_fields = ("created_at", "updated_at", "clave", "aplicada_en")


@admin.register(BeneficioConcedido)
class BeneficioConcedidoAdmin(admin.ModelAdmin):
    """La concesión efectiva de los beneficios del paquete."""

    list_display = (
        "id",
        "inscripcion",
        "beneficio",
        "cantidad",
        "concedido_en",
    )
    list_filter = ("beneficio__tipo",)
    search_fields = ("inscripcion__referencia", "beneficio__codigo")
    readonly_fields = ("created_at", "updated_at", "concedido_en")


@admin.register(Pase)
class PaseAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "estado")
    list_filter = ("estado", "edicion")
    search_fields = ("nombre", "slug")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PasePrecio)
class PasePrecioAdmin(admin.ModelAdmin):
    list_display = ("pase", "monto", "moneda", "vigente_desde", "vigente_hasta")
    list_filter = ("pase", "moneda")
    readonly_fields = ("created_at", "updated_at")


@admin.register(CompraPase)
class CompraPaseAdmin(admin.ModelAdmin):
    """El lote de pases comprado.

    `token` es de SOLO LECTURA: es la credencial del enlace de gestión y
    nunca se edita a mano. `asignados` lo mueve el servicio de capacidad con
    una sentencia atómica: tampoco se edita a mano.
    """

    list_display = (
        "id",
        "pase",
        "comprador",
        "cantidad",
        "asignados",
        "estado",
        "total",
    )
    list_filter = ("estado", "edicion", "pase")
    search_fields = ("referencia", "contacto_email")
    readonly_fields = (
        "created_at",
        "updated_at",
        "token",
        "token_expira_en",
        "token_revocado_en",
        "referencia",
        "asignados",
        "precio_unitario",
        "total",
    )


@admin.register(PaseBeneficiario)
class PaseBeneficiarioAdmin(admin.ModelAdmin):
    """El derecho efectivo de entrada de una persona."""

    list_display = (
        "id",
        "persona",
        "pase",
        "origen",
        "estado",
        "cantidad",
        "cantidad_consumida",
    )
    list_filter = ("estado", "origen", "edicion")
    search_fields = ("persona__numero_documento",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "asignado_en",
        "revocado_en",
        "cantidad_consumida",
    )


@admin.register(CortesiaPase)
class CortesiaPaseAdmin(admin.ModelAdmin):
    """El acta auditada de una cortesía.

    El motivo y el actor son de SOLO LECTURA: son la auditoría del
    otorgamiento y no se editan a mano.
    """

    list_display = (
        "id",
        "pase",
        "persona",
        "estado",
        "concedido_en",
    )
    list_filter = ("estado", "edicion")
    search_fields = ("motivo", "persona__numero_documento")
    readonly_fields = (
        "created_at",
        "updated_at",
        "motivo",
        "concedido_en",
        "revocado_en",
        "motivo_revocacion",
    )


@admin.register(ActivacionPase)
class ActivacionPaseAdmin(admin.ModelAdmin):
    """El acta de las activaciones de derechos de pases.

    `clave` es de SOLO LECTURA: es la clave de idempotencia que produce el
    coordinador de `commerce` y es la autoridad del "exactamente una vez".
    """

    list_display = (
        "id",
        "compra_pase",
        "cantidad",
        "compra_id",
        "aplicada_en",
    )
    search_fields = ("clave", "compra_id")
    readonly_fields = ("created_at", "updated_at", "clave", "aplicada_en")


__all__ = [
    "ActivacionCapacidadAdmin",
    "ActivacionPaseAdmin",
    "BeneficioConcedidoAdmin",
    "CategoriaAdmin",
    "CompraPaseAdmin",
    "CortesiaPaseAdmin",
    "DisciplinaAdmin",
    "EquipoAdmin",
    "InscripcionAdmin",
    "PaqueteAdmin",
    "PaqueteBeneficioAdmin",
    "PaquetePrecioAdmin",
    "PaseAdmin",
    "PaseBeneficiarioAdmin",
    "PasePrecioAdmin",
    "ParticipacionAdmin",
    "PromocionAdmin",
]
