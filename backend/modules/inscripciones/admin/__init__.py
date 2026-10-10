"""Admin package — ModelAdmin + NestedInline registrations for inscripciones module."""

from django.contrib import admin
from import_export import fields, resources
from import_export.admin import ExportMixin
from nested_admin import NestedTabularInline, NestedModelAdmin
from simple_history.admin import SimpleHistoryAdmin

from modules.pagos.domain.models.pago import IzipayTransaccion

from ..domain.models import (
    Disciplina,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    Evento,
    Promocion,
    Inscripcion,
    InscripcionDelegado,
    EquipoInscrito,
    ParticipacionDisciplina,
    ParticipanteInscripcion,
)


# ── Catalog admins (flat, no inlines) ──────────────────────────────────────────

@admin.register(Disciplina)
class DisciplinaAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "sigla", "modalidad", "min_jugadores", "max_jugadores", "esta_activa"]
    list_filter = ["modalidad", "esta_activa"]
    search_fields = ["nombre", "sigla"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Categoria)
class CategoriaAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "disciplina", "anio_minimo", "anio_maximo", "esta_activa"]
    list_filter = ["disciplina", "esta_activa"]
    search_fields = ["nombre", "disciplina__nombre"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Paquete)
class PaqueteAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "cantidad_maxima_participantes", "precio_regular", "precio_promocional", "valido_desde", "valido_hasta", "esta_activo"]
    list_filter = ["esta_activo"]
    search_fields = ["nombre"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(PaqueteDisciplina)
class PaqueteDisciplinaAdmin(SimpleHistoryAdmin):
    list_display = ["paquete", "disciplina"]
    list_filter = ["paquete", "disciplina"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Evento)
class EventoAdmin(SimpleHistoryAdmin):
    list_display = ["nombre", "fecha_inicio", "fecha_fin", "esta_activo"]
    list_filter = ["esta_activo"]
    search_fields = ["nombre"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Promocion)
class PromocionAdmin(SimpleHistoryAdmin):
    list_display = ["anio", "nombre", "colegio", "activa"]
    list_filter = ["colegio", "activa"]
    search_fields = ["nombre", "anio"]
    readonly_fields = ["created_at", "updated_at"]


# ── Inlines ────────────────────────────────────────────────────────────────────

class InscripcionResource(resources.ModelResource):
    responsable_documento = fields.Field(column_name="responsable_documento")
    responsable_nombre = fields.Field(column_name="responsable_nombre")
    evento_nombre = fields.Field(column_name="evento")
    paquete_nombre = fields.Field(column_name="paquete")
    promocion_anio = fields.Field(column_name="promocion")
    equipos_count = fields.Field(column_name="equipos_count")
    participantes_count = fields.Field(column_name="participantes_count")
    equipos = fields.Field(column_name="equipos")
    participantes = fields.Field(column_name="participantes")

    class Meta:
        model = Inscripcion
        fields = [
            "id",
            "estado",
            "responsable_documento",
            "responsable_nombre",
            "evento_nombre",
            "paquete_nombre",
            "promocion_anio",
            "equipos_count",
            "participantes_count",
            "equipos",
            "participantes",
            "created_at",
            "updated_at",
        ]
        export_order = fields

    def dehydrate_responsable_documento(self, obj):
        return obj.responsable.numero_documento

    def dehydrate_responsable_nombre(self, obj):
        return f"{obj.responsable.nombres} {obj.responsable.apellidos}"

    def dehydrate_evento_nombre(self, obj):
        return obj.evento.nombre

    def dehydrate_paquete_nombre(self, obj):
        return obj.paquete.nombre

    def dehydrate_promocion_anio(self, obj):
        return obj.promocion.anio

    def dehydrate_equipos_count(self, obj):
        return obj.equipos.count()

    def dehydrate_participantes_count(self, obj):
        return sum(equipo.participaciones.count() for equipo in obj.equipos.all())

    def dehydrate_equipos(self, obj):
        return " | ".join(
            f"{equipo.nombre} ({equipo.disciplina.nombre})"
            for equipo in obj.equipos.all()
        )

    def dehydrate_participantes(self, obj):
        participantes = []
        for equipo in obj.equipos.all():
            for participacion in equipo.participaciones.all():
                participantes.append(
                    f"{participacion.persona.numero_documento} - "
                    f"{participacion.persona.nombres} {participacion.persona.apellidos} "
                    f"({participacion.disciplina.nombre} / {equipo.nombre})"
                )
        return " | ".join(participantes)


class ParticipanteInscripcionResource(resources.ModelResource):
    """Export UNROLLED — una fila por ParticipanteInscripcion.

    A diferencia de InscripcionResource (que concatena participantes en una
    celda separada por `|`), este recurso aplana la jerarquía para que cada
    participante tenga su propia fila. Esto permite filtrar en Excel por
    `rol`, `talle_camiseta`, `disciplina`, `equipo`, etc.
    """

    inscripcion_id = fields.Field(column_name="inscripcion_id")
    inscripcion_estado = fields.Field(column_name="inscripcion_estado")
    evento = fields.Field(column_name="evento")
    paquete = fields.Field(column_name="paquete")
    promocion = fields.Field(column_name="promocion")
    responsable_documento = fields.Field(column_name="responsable_documento")
    responsable_nombre = fields.Field(column_name="responsable_nombre")
    equipo = fields.Field(column_name="equipo")
    equipo_disciplina = fields.Field(column_name="equipo_disciplina")
    equipo_categoria = fields.Field(column_name="equipo_categoria")
    participacion_disciplina = fields.Field(column_name="participacion_disciplina")
    participante_documento = fields.Field(column_name="participante_documento")
    participante_nombre = fields.Field(column_name="participante_nombre")
    participante_telefono = fields.Field(column_name="participante_telefono")
    participante_whatsapp = fields.Field(column_name="participante_whatsapp")
    rol = fields.Field(column_name="rol")
    talle_camiseta = fields.Field(column_name="talle_camiseta")
    notas = fields.Field(column_name="notas")
    created_at = fields.Field(column_name="created_at")

    class Meta:
        model = ParticipanteInscripcion
        fields = [
            "inscripcion_id",
            "inscripcion_estado",
            "evento",
            "paquete",
            "promocion",
            "responsable_documento",
            "responsable_nombre",
            "equipo",
            "equipo_disciplina",
            "equipo_categoria",
            "participacion_disciplina",
            "participante_documento",
            "participante_nombre",
            "participante_telefono",
            "participante_whatsapp",
            "rol",
            "talle_camiseta",
            "notas",
            "created_at",
        ]
        export_order = fields

    def get_queryset(self):
        return super().get_queryset().select_related(
            "participacion",
            "participacion__persona",
            "participacion__disciplina",
            "participacion__equipo",
            "participacion__equipo__disciplina",
            "participacion__equipo__categoria",
            "participacion__equipo__inscripcion",
            "participacion__equipo__inscripcion__evento",
            "participacion__equipo__inscripcion__paquete",
            "participacion__equipo__inscripcion__promocion",
            "participacion__equipo__inscripcion__responsable",
            "equipo",
        )

    def dehydrate_inscripcion_id(self, obj):
        return obj.participacion.equipo.inscripcion_id

    def dehydrate_inscripcion_estado(self, obj):
        return obj.participacion.equipo.inscripcion.get_estado_display()

    def dehydrate_evento(self, obj):
        return obj.participacion.equipo.inscripcion.evento.nombre

    def dehydrate_paquete(self, obj):
        return obj.participacion.equipo.inscripcion.paquete.nombre

    def dehydrate_promocion(self, obj):
        return obj.participacion.equipo.inscripcion.promocion.anio

    def dehydrate_responsable_documento(self, obj):
        return obj.participacion.equipo.inscripcion.responsable.numero_documento

    def dehydrate_responsable_nombre(self, obj):
        r = obj.participacion.equipo.inscripcion.responsable
        return f"{r.nombres} {r.apellidos}"

    def dehydrate_equipo(self, obj):
        return obj.participacion.equipo.nombre

    def dehydrate_equipo_disciplina(self, obj):
        return obj.participacion.equipo.disciplina.nombre

    def dehydrate_equipo_categoria(self, obj):
        cat = obj.participacion.equipo.categoria
        return cat.nombre if cat else ""

    def dehydrate_participacion_disciplina(self, obj):
        return obj.participacion.disciplina.nombre

    def dehydrate_participante_documento(self, obj):
        return obj.participacion.persona.numero_documento

    def dehydrate_participante_nombre(self, obj):
        p = obj.participacion.persona
        return f"{p.nombres} {p.apellidos}"

    def dehydrate_participante_telefono(self, obj):
        return obj.participacion.persona.telefono or ""

    def dehydrate_participante_whatsapp(self, obj):
        return obj.participacion.persona.whatsapp or ""

    def dehydrate_rol(self, obj):
        return obj.get_rol_display()

    def dehydrate_talle_camiseta(self, obj):
        return obj.get_talle_camiseta_display()

    def dehydrate_notas(self, obj):
        return obj.notas or ""

    def dehydrate_created_at(self, obj):
        return obj.created_at.isoformat() if obj.created_at else ""


class ParticipanteInscripcionInline(NestedTabularInline):
    """Level 3 — participant within a participation."""
    model = ParticipanteInscripcion
    extra = 0
    show_change_link = False
    fields = [
        "persona_nombre",
        "persona_documento",
        "disciplina_nombre",
        "equipo",
        "rol",
        "talle_camiseta",
        "created_at",
        "updated_at",
    ]
    readonly_fields = [
        "persona_nombre",
        "persona_documento",
        "disciplina_nombre",
        "created_at",
        "updated_at",
    ]
    autocomplete_fields = ["equipo"]

    @admin.display(description="Participante")
    def persona_nombre(self, obj):
        if not obj or not obj.participacion_id:
            return "-"
        persona = obj.participacion.persona
        return f"{persona.nombres} {persona.apellidos}"

    @admin.display(description="Documento")
    def persona_documento(self, obj):
        if not obj or not obj.participacion_id:
            return "-"
        return obj.participacion.persona.numero_documento

    @admin.display(description="Disciplina")
    def disciplina_nombre(self, obj):
        if not obj or not obj.participacion_id:
            return "-"
        return obj.participacion.disciplina.nombre

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "participacion__persona",
            "participacion__disciplina",
            "equipo",
        )


class ParticipacionDisciplinaInline(NestedTabularInline):
    """Level 2 — participation within an equipo. Contains participants."""
    model = ParticipacionDisciplina
    extra = 0
    show_change_link = False
    fields = [
        "persona_nombre",
        "persona_documento",
        "evento_nombre",
        "disciplina_nombre",
        "created_at",
        "updated_at",
    ]
    readonly_fields = [
        "persona_nombre",
        "persona_documento",
        "evento_nombre",
        "disciplina_nombre",
        "created_at",
        "updated_at",
    ]
    inlines = [ParticipanteInscripcionInline]

    @admin.display(description="Participante")
    def persona_nombre(self, obj):
        if not obj or not obj.persona_id:
            return "-"
        return f"{obj.persona.nombres} {obj.persona.apellidos}"

    @admin.display(description="Documento")
    def persona_documento(self, obj):
        if not obj or not obj.persona_id:
            return "-"
        return obj.persona.numero_documento

    @admin.display(description="Evento")
    def evento_nombre(self, obj):
        if not obj or not obj.evento_id:
            return "-"
        return obj.evento.nombre

    @admin.display(description="Disciplina")
    def disciplina_nombre(self, obj):
        if not obj or not obj.disciplina_id:
            return "-"
        return obj.disciplina.nombre

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("persona", "evento", "disciplina")


class EquipoInscritoInline(NestedTabularInline):
    """Level 1 — equipo within an inscripcion. Contains participaciones."""
    model = EquipoInscrito
    extra = 0
    show_change_link = False
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["disciplina", "categoria"]
    inlines = [ParticipacionDisciplinaInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("disciplina", "categoria", "inscripcion")


class InscripcionDelegadoInline(NestedTabularInline):
    """Delegate inline within inscripcion."""
    model = InscripcionDelegado
    extra = 0
    show_change_link = False
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["persona"]


class IzipayTransaccionInline(NestedTabularInline):
    """Read-only payment transactions inline within inscripcion."""
    model = IzipayTransaccion
    extra = 0
    show_change_link = False
    readonly_fields = [
        "transaction_id", "order_number", "amount", "currency",
        "status", "response_code", "response_message",
        "metodo_pago", "created_at",
    ]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ── Main nested admin ──────────────────────────────────────────────────────────

@admin.register(Inscripcion)
class InscripcionAdmin(ExportMixin, NestedModelAdmin):
    resource_classes = [InscripcionResource]
    list_display = ["id", "evento", "responsable", "paquete", "promocion", "estado", "created_at"]
    list_filter = ["estado", "evento", "paquete", "promocion"]
    search_fields = ["responsable__nombres", "responsable__apellidos", "responsable__numero_documento"]
    readonly_fields = [
        "responsable_nombre",
        "responsable_documento",
        "created_at",
        "updated_at",
    ]
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Responsable",
            {
                "fields": (
                    "responsable_nombre",
                    "responsable_documento",
                    "responsable",
                )
            },
        ),
        (
            "Inscripción",
            {
                "fields": (
                    "evento",
                    "paquete",
                    "promocion",
                    "fusion_promocion",
                    "estado",
                    "observacion",
                    "comprobante_pago",
                )
            },
        ),
        ("Auditoría", {"fields": ("created_at", "updated_at")}),
    )

    autocomplete_fields = [
        "responsable",
        "evento",
        "paquete",
        "promocion",
        "fusion_promocion",
    ]

    inlines = [
        InscripcionDelegadoInline,
        EquipoInscritoInline,
        IzipayTransaccionInline,
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "evento", "responsable", "paquete",
            "promocion", "fusion_promocion",
        ).prefetch_related(
            "delegados__persona",
            "equipos__disciplina",
            "equipos__categoria",
            "equipos__participaciones__persona",
            "equipos__participaciones__evento",
            "equipos__participaciones__disciplina",
            "equipos__participaciones__participantes",
            "transacciones_izipay",
        )

    @admin.display(description="Responsable")
    def responsable_nombre(self, obj):
        if not obj or not obj.responsable_id:
            return "-"
        return f"{obj.responsable.nombres} {obj.responsable.apellidos}"

    @admin.display(description="Documento")
    def responsable_documento(self, obj):
        if not obj or not obj.responsable_id:
            return "-"
        return obj.responsable.numero_documento

    def get_readonly_fields(self, request, obj=None):
        # Keep estado immutable from inline edit; provide actions for state changes
        readonly = list(super().get_readonly_fields(request, obj))
        if obj:  # existing object — lock estado
            readonly.append("estado")
        return readonly


# ── Standalone nested admins for aggregate sub-models ─────────────────────────

@admin.register(InscripcionDelegado)
class InscripcionDelegadoAdmin(NestedModelAdmin):
    list_display = ["inscripcion", "persona", "created_at"]
    list_filter = ["inscripcion__evento"]
    search_fields = ["persona__nombres", "persona__apellidos", "persona__numero_documento"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["inscripcion", "persona"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("inscripcion", "persona")


@admin.register(EquipoInscrito)
class EquipoInscritoAdmin(NestedModelAdmin):
    list_display = ["nombre", "inscripcion", "disciplina", "categoria", "created_at"]
    list_filter = ["disciplina", "categoria"]
    search_fields = ["nombre", "inscripcion__responsable__nombres"]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["inscripcion", "disciplina", "categoria"]
    inlines = [ParticipacionDisciplinaInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "inscripcion", "disciplina", "categoria",
        ).prefetch_related(
            "participaciones__persona",
            "participaciones__evento",
            "participaciones__disciplina",
            "participaciones__participantes",
        )


@admin.register(ParticipacionDisciplina)
class ParticipacionDisciplinaAdmin(NestedModelAdmin):
    list_display = ["persona", "evento", "disciplina", "equipo", "created_at"]
    list_filter = ["evento", "disciplina"]
    search_fields = ["persona__nombres", "persona__apellidos", "persona__numero_documento"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["persona", "equipo"]
    autocomplete_fields = ["evento", "disciplina"]
    inlines = [ParticipanteInscripcionInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "persona", "evento", "disciplina", "equipo",
        ).prefetch_related("participantes")


@admin.register(ParticipanteInscripcion)
class ParticipanteInscripcionAdmin(ExportMixin, NestedModelAdmin):
    resource_classes = [ParticipanteInscripcionResource]
    list_display = [
        "participacion",
        "equipo",
        "rol",
        "talle_camiseta",
        "created_at",
    ]
    list_filter = [
        "rol",
        "talle_camiseta",
        "equipo__disciplina",
        "participacion__equipo__inscripcion__estado",
        "participacion__equipo__inscripcion__evento",
        "participacion__equipo__inscripcion__promocion",
    ]
    search_fields = [
        "participacion__persona__nombres",
        "participacion__persona__apellidos",
        "participacion__persona__numero_documento",
        "equipo__nombre",
        "equipo__inscripcion__responsable__numero_documento",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["participacion", "equipo"]
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "participacion__persona",
            "participacion__disciplina",
            "participacion__equipo__disciplina",
            "participacion__equipo__categoria",
            "participacion__equipo__inscripcion__evento",
            "participacion__equipo__inscripcion__paquete",
            "participacion__equipo__inscripcion__promocion",
            "participacion__equipo__inscripcion__responsable",
            "equipo",
        )
