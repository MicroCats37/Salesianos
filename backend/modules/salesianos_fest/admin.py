"""Admin registrations for salesianos_fest module."""
from django.contrib import admin

from .domain.models import (
    Disciplina,
    Promocion,
    Categoria,
    Paquete,
    PaqueteDisciplina,
    PaquetePrecio,
    PaqueteBeneficio,
    Pase,
    PasePrecio,
    CompraPase,
    PaseBeneficiario,
    Inscripcion,
    Equipo,
    InscripcionPersona,
    Participacion,
    CompraInscripcion,
    AsignacionCupo,
    AcreditacionEvento,
    ControlAcceso,
    AceptacionInscripcion,
)
from modules.commerce.domain.models import Compra

from .forms import DisciplinaAdminForm, ParticipacionAdminForm


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    """Admin configuration for Disciplina model."""

    # Guards a `modalidad` change that would break an ACTIVE participacion.
    form = DisciplinaAdminForm

    list_display = ["nombre", "sigla", "modalidad", "min_jugadores", "max_jugadores", "esta_activa"]
    list_filter = ["modalidad", "esta_activa"]
    search_fields = ["nombre", "sigla"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["nombre"]


@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    """Admin configuration for Promocion model."""

    list_display = ["nombre", "anio", "activa", "created_at"]
    list_filter = ["activa"]
    search_fields = ["nombre"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["-anio"]


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Admin configuration for Categoria model."""

    list_display = ["nombre", "evento", "promocion_desde", "promocion_hasta", "esta_activa"]
    list_filter = ["esta_activa", "evento"]
    search_fields = ["nombre", "evento__nombre"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["evento"]
    ordering = ["evento__nombre", "nombre"]


class PaqueteDisciplinaInline(admin.TabularInline):
    """Inline for PaqueteDisciplina within PaqueteAdmin."""

    model = PaqueteDisciplina
    extra = 1
    raw_id_fields = ["disciplina"]


class PaquetePrecioInline(admin.TabularInline):
    """Inline for PaquetePrecio within PaqueteAdmin."""

    model = PaquetePrecio
    extra = 1


class PaqueteBeneficioInline(admin.TabularInline):
    """Inline for PaqueteBeneficio within PaqueteAdmin."""

    model = PaqueteBeneficio
    extra = 1


@admin.register(Paquete)
class PaqueteAdmin(admin.ModelAdmin):
    """Admin configuration for Paquete model."""

    list_display = ["nombre", "evento", "tipo", "modo_disciplinas", "cantidad_disciplinas", "activo"]
    list_filter = ["tipo", "modo_disciplinas", "activo", "evento"]
    search_fields = ["nombre", "evento__nombre"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["evento"]
    inlines = [PaqueteDisciplinaInline, PaquetePrecioInline, PaqueteBeneficioInline]
    ordering = ["evento__nombre", "nombre"]


class PasePrecioInline(admin.TabularInline):
    """Inline for PasePrecio within PaseAdmin.

    The operator configures the stage prices (and activates them) from here.
    """

    model = PasePrecio
    extra = 1


@admin.register(Pase)
class PaseAdmin(admin.ModelAdmin):
    """Admin configuration for Pase model.

    The pass is the operator's switch for the catalogue: `activo` publishes
    it (together with the rollout flag `PASES_FIESTA_ENABLED`) and
    `cantidad_maxima` caps the inventory (0 = unlimited).
    """

    list_display = [
        "id",
        "nombre",
        "evento",
        "cantidad_maxima",
        "activo",
        "created_at",
    ]
    list_filter = ["activo", "evento"]
    search_fields = ["nombre", "evento__nombre"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["evento"]
    inlines = [PasePrecioInline]
    ordering = ["evento__nombre", "nombre"]


@admin.register(PasePrecio)
class PasePrecioAdmin(admin.ModelAdmin):
    """Admin configuration for PasePrecio model."""

    list_display = [
        "id",
        "pase",
        "etapa",
        "precio_unitario",
        "vigente_desde",
        "vigente_hasta",
        "activo",
    ]
    list_filter = ["etapa", "activo", "pase__evento"]
    search_fields = ["pase__nombre"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["pase"]
    ordering = ["pase", "etapa"]


@admin.register(CompraPase)
class CompraPaseAdmin(admin.ModelAdmin):
    """Admin configuration for CompraPase model (audit of the sold batches)."""

    list_display = [
        "id",
        "compra",
        "pase",
        "evento",
        "cantidad",
        "precio_unitario",
        "total",
        "compra_estado",
        "created_at",
    ]
    list_filter = ["evento", "pase"]
    search_fields = [
        "compra__responsable__numero_documento",
        "compra__responsable__nombres",
        "compra__responsable__apellidos",
        "pase__nombre",
        "compra__referencia_externa",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["compra", "pase", "evento"]
    ordering = ["-created_at"]

    def compra_estado(self, obj):
        return obj.compra.estado
    compra_estado.short_description = "Estado Compra"


@admin.register(PaseBeneficiario)
class PaseBeneficiarioAdmin(admin.ModelAdmin):
    """Admin configuration for PaseBeneficiario model (audit of the rights)."""

    list_display = [
        "id",
        "compra_pase",
        "persona",
        "evento",
        "slot",
        "estado",
        "asignado_por",
        "asignado_en",
        "revocado_en",
    ]
    list_filter = ["estado", "evento"]
    search_fields = [
        "persona__numero_documento",
        "persona__nombres",
        "persona__apellidos",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "asignado_en",
        "revocado_en",
        "motivo_revocacion",
    ]
    raw_id_fields = ["compra_pase", "persona", "evento", "asignado_por", "revocado_por"]
    ordering = ["compra_pase", "slot"]


class ParticipacionInline(admin.TabularInline):
    """Inline for Participacion within EquipoAdmin."""
    model = Participacion
    # Same form as the standalone admin: the model safety net rejects an
    # incompatible ACTIVE participacion and reports it once.
    form = ParticipacionAdminForm
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    can_delete = True


class EquipoInline(admin.TabularInline):
    """Inline for Equipo within InscripcionAdmin."""

    model = Equipo
    extra = 1
    readonly_fields = ["created_at", "updated_at"]


class InscripcionPersonaInline(admin.TabularInline):
    """Inline for InscripcionPersona within InscripcionAdmin."""

    model = InscripcionPersona
    extra = 1
    readonly_fields = ["created_at", "updated_at"]


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    """Admin configuration for Inscripcion model."""

    list_display = ["id", "evento", "responsable", "paquete", "promocion", "estado", "created_at"]
    list_filter = ["estado", "evento", "paquete"]
    search_fields = ["responsable__numero_documento", "responsable__nombres", "responsable__apellidos"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["evento", "responsable", "paquete", "promocion", "delegado"]
    inlines = [InscripcionPersonaInline, EquipoInline]
    ordering = ["-created_at"]


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    """Admin configuration for Equipo model."""

    list_display = ["id", "nombre", "inscripcion", "disciplina", "categoria", "estado", "created_at"]
    list_filter = ["estado", "disciplina"]
    search_fields = ["nombre", "inscripcion__responsable__nombres"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["inscripcion", "disciplina", "categoria", "promocion"]
    inlines = [ParticipacionInline]
    ordering = ["inscripcion", "nombre"]


@admin.register(InscripcionPersona)
class InscripcionPersonaAdmin(admin.ModelAdmin):
    """Admin configuration for InscripcionPersona model."""

    list_display = ["id", "inscripcion", "persona", "estado", "created_at"]
    list_filter = ["estado", "inscripcion__evento"]
    search_fields = ["persona__numero_documento", "persona__nombres", "persona__apellidos"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["inscripcion", "persona"]
    ordering = ["inscripcion", "persona"]


@admin.register(Participacion)
class ParticipacionAdmin(admin.ModelAdmin):
    """Admin configuration for Participacion model."""

    # `Participacion.clean()` is the safety net: an incompatible ACTIVE row
    # is rejected with a form-level validation error.
    form = ParticipacionAdminForm

    list_display = ["id", "persona", "equipo", "disciplina", "evento", "rol", "estado", "created_at"]
    list_filter = ["estado", "rol", "disciplina"]
    search_fields = [
        "persona__numero_documento",
        "persona__nombres",
        "persona__apellidos",
        "equipo__nombre",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["inscripcion_persona", "equipo", "evento", "disciplina", "persona"]
    ordering = ["equipo", "persona"]


@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    """Admin configuration for commerce.Compra model."""

    list_display = [
        "id",
        "responsable",
        "descripcion",
        "referencia_externa",
        "total",
        "estado",
        "orden_pago",
        "created_at",
    ]
    list_filter = ["estado"]
    search_fields = [
        "responsable__numero_documento",
        "responsable__nombres",
        "responsable__apellidos",
        "referencia_externa",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["responsable", "orden_pago"]
    ordering = ["-created_at"]


@admin.register(CompraInscripcion)
class CompraInscripcionAdmin(admin.ModelAdmin):
    """Admin configuration for CompraInscripcion model."""

    list_display = [
        "id",
        "compra",
        "inscripcion",
        "tipo",
        "cantidad",
        "precio_unitario",
        "total",
        "compra_estado",
        "created_at",
    ]
    list_filter = ["tipo", "inscripcion__evento"]
    search_fields = [
        "inscripcion__responsable__numero_documento",
        "inscripcion__responsable__nombres",
        "inscripcion__responsable__apellidos",
        "compra__referencia_externa",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["compra", "inscripcion"]
    ordering = ["-created_at"]

    def compra_estado(self, obj):
        return obj.compra.estado
    compra_estado.short_description = "Estado Compra"


@admin.register(AsignacionCupo)
class AsignacionCupoAdmin(admin.ModelAdmin):
    """Admin configuration for AsignacionCupo model."""

    list_display = [
        "id",
        "inscripcion",
        "compra",
        "inscripcion_persona",
        "estado",
        "created_at",
    ]
    list_filter = ["estado", "inscripcion__evento"]
    search_fields = [
        "inscripcion__responsable__nombres",
        "inscripcion__responsable__apellidos",
        "inscripcion_persona__persona__numero_documento",
        "inscripcion_persona__persona__nombres",
        "inscripcion_persona__persona__apellidos",
    ]
    readonly_fields = ["created_at", "updated_at", "liberada_en"]
    raw_id_fields = ["inscripcion", "compra", "inscripcion_persona"]
    ordering = ["-created_at"]


@admin.register(AcreditacionEvento)
class AcreditacionEventoAdmin(admin.ModelAdmin):
    """Admin configuration for AcreditacionEvento model."""

    list_display = [
        "id",
        "evento",
        "persona",
        "estado",
        "acceso_fiesta",
        "autorizacion_fiesta",
        "habilitado",
        "created_at",
    ]
    list_filter = ["estado", "acceso_fiesta", "autorizacion_fiesta", "evento"]
    search_fields = [
        "persona__numero_documento",
        "persona__nombres",
        "persona__apellidos",
    ]
    readonly_fields = ["created_at", "updated_at", "codigo_qr"]
    raw_id_fields = ["evento", "persona"]
    ordering = ["-created_at"]


@admin.register(ControlAcceso)
class ControlAccesoAdmin(admin.ModelAdmin):
    """Admin configuration for ControlAcceso model."""

    list_display = [
        "id",
        "acreditacion",
        "resultado",
        "punto_acceso",
        "operador",
        "fecha_hora",
    ]
    list_filter = ["resultado", "punto_acceso"]
    search_fields = [
        "acreditacion__persona__numero_documento",
        "acreditacion__persona__nombres",
        "acreditacion__persona__apellidos",
    ]
    readonly_fields = ["fecha_hora"]
    raw_id_fields = ["acreditacion", "operador"]
    ordering = ["-fecha_hora"]


@admin.register(AceptacionInscripcion)
class AceptacionInscripcionAdmin(admin.ModelAdmin):
    """Admin configuration for AceptacionInscripcion model."""

    list_display = [
        "id",
        "inscripcion_persona",
        "tipo_aceptacion",
        "documento_version",
        "aceptado_en",
        "actor_id",
        "medio",
        "ip_address",
    ]
    list_filter = ["tipo_aceptacion", "medio", "aceptado_en"]
    search_fields = [
        "inscripcion_persona__persona__numero_documento",
        "inscripcion_persona__persona__nombres",
        "inscripcion_persona__persona__apellidos",
        "actor_id",
    ]
    readonly_fields = ["aceptado_en"]
    raw_id_fields = ["inscripcion_persona"]
    ordering = ["-aceptado_en"]
