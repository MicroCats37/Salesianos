"""Core sync service for Equipo — no transaction.atomic itself."""
from typing import Optional

from ...models import Equipo, Inscripcion, Disciplina, Categoria, PaqueteDisciplina
from ...schemas.inscripcion_schemas import EquipoCreateData, EquipoUpdateData
from ...exceptions import (
    EquipoNotFoundError,
    DisciplinaNotInPaqueteError,
    DisciplinaNotFoundError,
)
from .inscripcion_service import InscripcionCoreService


class EquipoCoreService:
    """Sync operations for Equipo — caller provides transaction.atomic."""

    def crear(self, data: EquipoCreateData) -> Equipo:
        """Create an equipo.

        Validates: disciplina belongs to paquete of inscripcion.
        categoria is optional and resolved from inscripcion.promocion + evento.
        """
        # Get inscripcion with related
        inscripcion = Inscripcion.objects.select_related(
            "evento", "paquete", "promocion"
        ).get(id=data.inscripcion_id)

        # Validate disciplina belongs to paquete
        disciplina_exists = PaqueteDisciplina.objects.filter(
            paquete_id=inscripcion.paquete_id,
            disciplina_id=data.disciplina_id,
        ).exists()
        if not disciplina_exists:
            raise DisciplinaNotInPaqueteError()

        # Resolve categoria from inscripcion.promocion + evento
        categoria_id = data.categoria_id
        if categoria_id is None:
            # Try to find matching categoria
            categoria = Categoria.objects.filter(
                evento_id=inscripcion.evento_id,
                esta_activa=True,
                promocion_desde__lte=inscripcion.promocion.anio,
                promocion_hasta__gte=inscripcion.promocion.anio,
            ).first()
            if categoria:
                categoria_id = str(categoria.id)

        equipo = Equipo(
            inscripcion_id=data.inscripcion_id,
            disciplina_id=data.disciplina_id,
            categoria_id=categoria_id,
            promocion_id=inscripcion.promocion_id,  # Inherit from inscripcion
            nombre=data.nombre,
            estado=data.estado,
        )
        equipo.save()
        return equipo

    def actualizar(self, equipo: Equipo, data: EquipoUpdateData) -> Equipo:
        """Update equipo fields."""
        update_fields = data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(equipo, field, value)
        equipo.save()
        return equipo

    def obtener_por_id(self, equipo_id: str) -> Equipo:
        """Get an equipo by ID or raise EquipoNotFoundError."""
        try:
            return Equipo.objects.get(id=equipo_id)
        except Equipo.DoesNotExist:
            raise EquipoNotFoundError()
