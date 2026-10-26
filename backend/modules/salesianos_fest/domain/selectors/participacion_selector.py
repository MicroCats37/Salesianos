"""ParticipacionSelector — read-only queries for participaciones."""
from typing import Optional

from ..models import Participacion
from ..results.inscripcion_results import ParticipacionResult


class ParticipacionSelector:
    """Queries for Participacion entities."""

    @staticmethod
    def get_by_id(participacion_id: str) -> Optional[ParticipacionResult]:
        """Return a participacion by ID or None."""
        try:
            p = Participacion.objects.select_related(
                "inscripcion_persona__persona",
                "equipo__disciplina",
                "evento",
            ).get(id=participacion_id)
            return ParticipacionResult(
                id=str(p.id),
                inscripcion_persona_id=str(p.inscripcion_persona_id),
                equipo_id=str(p.equipo_id),
                equipo_nombre=p.equipo.nombre,
                evento_id=str(p.evento_id),
                disciplina_id=str(p.disciplina_id),
                disciplina_nombre=p.disciplina.nombre,
                disciplina_sigla=p.disciplina.sigla,
                persona_id=str(p.persona_id),
                persona_nombre=f"{p.inscripcion_persona.persona.nombres} {p.inscripcion_persona.persona.apellidos}",
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )
        except Participacion.DoesNotExist:
            return None

    @staticmethod
    def get_by_equipo(equipo_id: str) -> list[ParticipacionResult]:
        """Return all participaciones for an equipo."""
        qs = Participacion.objects.select_related(
            "inscripcion_persona__persona",
            "equipo",
            "disciplina",
            "evento",
        ).filter(equipo_id=equipo_id).order_by("created_at")
        return [
            ParticipacionResult(
                id=str(p.id),
                inscripcion_persona_id=str(p.inscripcion_persona_id),
                equipo_id=str(p.equipo_id),
                equipo_nombre=p.equipo.nombre,
                evento_id=str(p.evento_id),
                disciplina_id=str(p.disciplina_id),
                disciplina_nombre=p.disciplina.nombre,
                disciplina_sigla=p.disciplina.sigla,
                persona_id=str(p.persona_id),
                persona_nombre=f"{p.inscripcion_persona.persona.nombres} {p.inscripcion_persona.persona.apellidos}",
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )
            for p in qs
        ]

    @staticmethod
    def get_active_by_evento_disciplina_persona(
        evento_id: str, disciplina_id: str, persona_id: str,
    ) -> Optional[ParticipacionResult]:
        """Return active participacion for R11 check."""
        try:
            p = Participacion.objects.select_related(
                "inscripcion_persona__persona",
                "equipo",
                "disciplina",
                "evento",
            ).get(
                evento_id=evento_id,
                disciplina_id=disciplina_id,
                persona_id=persona_id,
                estado="A",
            )
            return ParticipacionResult(
                id=str(p.id),
                inscripcion_persona_id=str(p.inscripcion_persona_id),
                equipo_id=str(p.equipo_id),
                equipo_nombre=p.equipo.nombre,
                evento_id=str(p.evento_id),
                disciplina_id=str(p.disciplina_id),
                disciplina_nombre=p.disciplina.nombre,
                disciplina_sigla=p.disciplina.sigla,
                persona_id=str(p.persona_id),
                persona_nombre=f"{p.inscripcion_persona.persona.nombres} {p.inscripcion_persona.persona.apellidos}",
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )
        except Participacion.DoesNotExist:
            return None
