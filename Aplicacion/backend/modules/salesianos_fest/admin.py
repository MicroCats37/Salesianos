"""Registro en el Django Admin del módulo `salesianos_fest`.

Contract: `contract/django-app-architecture-contract.md` §4.13

El admin es una SUPERFICIE DE OPERACIÓN, no de negocio: los campos
`readonly_fields` son las marcas de tiempo y el estado comercial congelado.
"""

from django.contrib import admin

from modules.salesianos_fest.domain.models import (
    ActivacionCapacidad,
    BeneficioConcedido,
    Disciplina,
    Equipo,
    Inscripcion,
    Paquete,
    PaqueteBeneficio,
    PaquetePrecio,
    Participacion,
)


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "estado", "modalidad")
    list_filter = ("estado", "modalidad", "edicion")
    search_fields = ("nombre", "slug")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Paquete)
class PaqueteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "estado", "cupos_incluidos")
    list_filter = ("estado", "edicion")
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
        "estado",
        "cupos_pagados",
        "cupos_asignados",
    )
    list_filter = ("estado", "edicion", "paquete")
    search_fields = ("referencia",)
    readonly_fields = (
        "created_at",
        "updated_at",
        "referencia",
        "cupos_solicitados",
        "cupos_pagados",
        "cupos_asignados",
    )


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "inscripcion", "disciplina", "estado")
    list_filter = ("estado", "disciplina")
    search_fields = ("nombre",)
    readonly_fields = ("created_at", "updated_at")


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


__all__ = [
    "ActivacionCapacidadAdmin",
    "BeneficioConcedidoAdmin",
    "DisciplinaAdmin",
    "EquipoAdmin",
    "InscripcionAdmin",
    "PaqueteAdmin",
    "PaqueteBeneficioAdmin",
    "PaquetePrecioAdmin",
    "ParticipacionAdmin",
]
