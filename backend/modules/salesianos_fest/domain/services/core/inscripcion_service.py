"""Core sync service for Inscripcion — no transaction.atomic itself."""
from typing import Optional

from django.db.models import Model

from modules.usuarios.domain.models.persona import Persona
from ...models import Inscripcion, Paquete, Promocion
from ...schemas.inscripcion_schemas import InscripcionCreateData, InscripcionUpdateData
from ...exceptions import (
    InscripcionNotFoundError,
    PaqueteEventoMismatchError,
)


class InscripcionCoreService:
    """Sync operations for Inscripcion — caller provides transaction.atomic."""

    def crear(self, data: InscripcionCreateData) -> Inscripcion:
        """Create an inscripcion.

        Validates: paquete.evento == evento_id.
        Does NOT validate fusion_promocion policy (pending product decision).
        """
        # Validate paquete belongs to evento
        try:
            paquete = Paquete.objects.select_related("evento").get(id=data.paquete_id)
        except Paquete.DoesNotExist:
            raise PaqueteEventoMismatchError()

        if str(paquete.evento_id) != data.evento_id:
            raise PaqueteEventoMismatchError()

        # Validate promocion exists
        if not Promocion.objects.filter(id=data.promocion_id).exists():
            from ..exceptions import PromocionNotFoundError
            raise PromocionNotFoundError()

        # Validate fusion_promocion if provided (no policy — just check existence)
        if data.fusion_promocion_id:
            if not Promocion.objects.filter(id=data.fusion_promocion_id).exists():
                from ..exceptions import PromocionNotFoundError
                raise PromocionNotFoundError()

        inscripcion = Inscripcion(
            evento_id=data.evento_id,
            responsable_id=data.responsable_id,
            paquete_id=data.paquete_id,
            promocion_id=data.promocion_id,
            fusion_promocion_id=data.fusion_promocion_id,
            delegado_id=data.delegado_id,
            estado=data.estado,
            observacion=data.observacion,
        )
        inscripcion.save()
        return inscripcion

    def actualizar(self, inscripcion: Inscripcion, data: InscripcionUpdateData) -> Inscripcion:
        """Update an inscripcion fields."""
        update_fields = data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(inscripcion, field, value)
        inscripcion.save()
        return inscripcion

    def obtener_por_id(self, inscripcion_id: str) -> Inscripcion:
        """Get an inscripcion by ID or raise InscripcionNotFoundError."""
        try:
            return Inscripcion.objects.get(id=inscripcion_id)
        except Inscripcion.DoesNotExist:
            raise InscripcionNotFoundError()

    def obtener_por_id_with_related(self, inscripcion_id: str) -> Inscripcion:
        """Get an inscripcion with related objects."""
        try:
            return Inscripcion.objects.select_related(
                "evento", "responsable", "paquete", "promocion",
                "fusion_promocion", "delegado",
            ).get(id=inscripcion_id)
        except Inscripcion.DoesNotExist:
            raise InscripcionNotFoundError()
