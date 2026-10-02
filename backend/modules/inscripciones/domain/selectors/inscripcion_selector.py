"""
InscripcionSelector — complex queries for the inscripciones module.

Selector — read-only queries, no business logic.
"""

from injector import inject

from modules.inscripciones.domain.models import (
    Inscripcion,
    InscripcionDelegado,
    EquipoInscrito,
    ParticipacionDisciplina,
    ParticipanteInscripcion,
    Disciplina,
    Paquete,
    PaqueteDisciplina,
    Evento,
)


class InscripcionSelector:
    """
    Read-only queries for Inscripcion and related entities.
    """

    @inject
    def __init__(self):
        pass

    # ── Inscripcion ─────────────────────────────────────────────────────────

    def obtener_inscripcion(self, inscripcion_id: str) -> Inscripcion | None:
        """Get an inscripcion with related data fully prefetched for async context."""
        return (
            Inscripcion.objects
            .filter(id=inscripcion_id)
            .select_related("evento", "responsable", "paquete", "promocion", "fusion_promocion")
            .prefetch_related(
                "equipos__disciplina",
                "equipos__categoria",
                "equipos__participantes_inscripcion__participacion__persona",
                "delegados__persona",
            )
            .first()
        )

    def listar_inscripciones_por_responsable(self, responsable_id: str) -> list[Inscripcion]:
        """List all inscripciones for a responsible person."""
        return list(
            Inscripcion.objects
            .filter(responsable_id=responsable_id)
            .select_related("evento", "paquete", "promocion", "fusion_promocion")
            .prefetch_related(
                "equipos__participantes_inscripcion__participacion",
            )
            .order_by("-created_at")
        )

    def listar_inscripciones_por_evento(self, evento_id: str) -> list[Inscripcion]:
        """List all inscripciones for an event."""
        return list(
            Inscripcion.objects
            .filter(evento_id=evento_id)
            .select_related("responsable", "paquete", "promocion", "fusion_promocion")
            .order_by("-created_at")
        )

    def inscripcion_tiene_responsable_activa_en_evento(
        self,
        responsable_id: str,
        evento_id: str,
    ) -> bool:
        """Check if a responsible already has an active inscription in an event."""
        return Inscripcion.objects.filter(
            responsable_id=responsable_id,
            evento_id=evento_id,
            estado__in=["RECIBIDA", "EN_REVISION", "VALIDADA", "PAGO_PENDIENTE", "PAGADA", "CONFIRMADA"],
        ).exists()

    # ── EquipoInscrito ─────────────────────────────────────────────────────

    def obtener_equipos_de_inscripcion(self, inscripcion_id: str) -> list[EquipoInscrito]:
        """Get all equipos for an inscription."""
        return list(
            EquipoInscrito.objects
            .filter(inscripcion_id=inscripcion_id)
            .select_related("disciplina", "categoria")
            .order_by("disciplina__nombre")
        )

    def obtener_detalle_equipo(self, equipo_id: str) -> EquipoInscrito | None:
        """Get equipo with related data."""
        return (
            EquipoInscrito.objects
            .filter(id=equipo_id)
            .select_related("inscripcion", "disciplina", "categoria")
            .first()
        )

    # ── ParticipacionDisciplina ─────────────────────────────────────────────

    def obtener_participaciones_de_equipo(self, equipo_id: str) -> list[ParticipacionDisciplina]:
        """Get all participaciones for an equipo."""
        return list(
            ParticipacionDisciplina.objects
            .filter(equipo_id=equipo_id)
            .select_related("persona", "evento", "disciplina")
            .order_by("persona__apellidos")
        )

    def obtener_participaciones_de_inscripcion(self, inscripcion_id: str) -> list[ParticipacionDisciplina]:
        """Get all participaciones for an inscription (all equipos)."""
        return list(
            ParticipacionDisciplina.objects
            .filter(equipo__inscripcion_id=inscripcion_id)
            .select_related("persona", "evento", "disciplina", "equipo")
            .order_by("disciplina__nombre", "persona__apellidos")
        )

    def contar_personas_unicas_en_inscripcion(self, inscripcion_id: str) -> int:
        """Count distinct persons in an inscription (D6)."""
        return (
            ParticipacionDisciplina.objects
            .filter(equipo__inscripcion_id=inscripcion_id)
            .values("persona")
            .distinct()
            .count()
        )

    # ── ParticipanteInscripcion ─────────────────────────────────────────────

    def obtener_participantes_de_equipo(self, equipo_id: str) -> list[ParticipanteInscripcion]:
        """Get all participantes for an equipo."""
        return list(
            ParticipanteInscripcion.objects
            .filter(equipo_id=equipo_id)
            .select_related("participacion", "participacion__persona")
            .order_by("participacion__persona__apellidos")
        )

    # ── Delegado ────────────────────────────────────────────────────────────

    def obtener_delegado_de_inscripcion(self, inscripcion_id: str) -> InscripcionDelegado | None:
        """Get the delegate for an inscription."""
        return (
            InscripcionDelegado.objects
            .filter(inscripcion_id=inscripcion_id)
            .select_related("persona")
            .first()
        )

    # ── Catalogos ───────────────────────────────────────────────────────────

    def listar_disciplinas_activas(self) -> list[Disciplina]:
        """List all active disciplines."""
        return list(
            Disciplina.objects
            .filter(esta_activa=True)
            .order_by("nombre")
        )

    def listar_paquetes_activos(self) -> list[Paquete]:
        """List all active packages."""
        return list(
            Paquete.objects
            .filter(esta_activo=True)
            .order_by("nombre")
        )

    def listar_disciplinas_de_paquete(self, paquete_id: str) -> list[Disciplina]:
        """List disciplines included in a package."""
        return list(
            Disciplina.objects
            .filter(paquete_disciplinas__paquete_id=paquete_id, esta_activa=True)
            .order_by("nombre")
        )

    def listar_eventos_activos(self) -> list[Evento]:
        """List all active events."""
        return list(
            Evento.objects
            .filter(esta_activo=True)
            .order_by("-fecha_inicio")
        )
