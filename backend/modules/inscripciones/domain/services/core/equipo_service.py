"""
EquipoService — sync operations for EquipoInscrito.

Core service — no transaction.atomic own, no async.
"""

from injector import inject

from modules.inscripciones.domain.models import EquipoInscrito
from modules.inscripciones.domain import exceptions as exc
from modules.inscripciones.domain.services.core import validators


class EquipoService:
    """
    Core service for EquipoInscrito operations.
    """

    @inject
    def __init__(self):
        pass

    def crear(self, data) -> EquipoInscrito:
        """
        Create a new EquipoInscrito.
        """
        return EquipoInscrito.objects.create(
            inscripcion_id=data.inscripcion_id,
            disciplina_id=data.disciplina_id,
            categoria_id=data.categoria_id,
            nombre=data.nombre,
        )

    def actualizar(self, equipo: EquipoInscrito, data) -> EquipoInscrito:
        """Update an existing EquipoInscrito."""
        update_fields = data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(equipo, field, value)
        equipo.save()
        return equipo

    def obtener(self, equipo_id: str) -> EquipoInscrito | None:
        """Get an EquipoInscrito by ID."""
        return EquipoInscrito.objects.filter(id=equipo_id).first()

    def listar_por_inscripcion(self, inscripcion_id: str) -> list[EquipoInscrito]:
        """List all equipos for an inscription."""
        return list(
            EquipoInscrito.objects
            .filter(inscripcion_id=inscripcion_id)
            .select_related("disciplina", "categoria")
            .order_by("disciplina__nombre")
        )

    def listar_por_disciplina(self, disciplina_id: str) -> list[EquipoInscrito]:
        """List all equipos for a discipline."""
        return list(
            EquipoInscrito.objects
            .filter(disciplina_id=disciplina_id)
            .select_related("inscripcion", "categoria")
            .order_by("nombre")
        )

    def contar_participantes(self, equipo_id: str) -> int:
        """Count participants in an equipo."""
        return (
            self.obtener(equipo_id)
            .participaciones.count()
        )
