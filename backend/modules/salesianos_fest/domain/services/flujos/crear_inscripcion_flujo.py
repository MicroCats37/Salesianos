"""CrearInscripcionFlujo — async flow for creating an inscripcion with equipos opcionales."""
from asgiref.sync import sync_to_async
from django.db import transaction

from ..core.inscripcion_service import InscripcionCoreService
from ...schemas.inscripcion_schemas import InscripcionCreateData
from ...results.inscripcion_results import InscripcionResult


class CrearInscripcionFlujo:
    """Async flow for creating an inscripcion atomically."""

    @sync_to_async
    def _crear_atomico(self, data: InscripcionCreateData) -> InscripcionResult:
        """Create inscripcion in a transaction."""
        with transaction.atomic():
            inscripcion = self._inscripcion_core.crear(data)
            return InscripcionResult(
                id=str(inscripcion.id),
                evento_id=str(inscripcion.evento_id),
                evento_nombre=inscripcion.evento.nombre,
                responsable_id=str(inscripcion.responsable_id),
                responsable_nombre=f"{inscripcion.responsable.nombres} {inscripcion.responsable.apellidos}",
                paquete_id=str(inscripcion.paquete_id),
                paquete_nombre=inscripcion.paquete.nombre,
                promocion_id=str(inscripcion.promocion_id),
                promocion_nombre=inscripcion.promocion.nombre,
                fusion_promocion_id=str(inscripcion.fusion_promocion_id) if inscripcion.fusion_promocion_id else None,
                delegado_id=str(inscripcion.delegado_id) if inscripcion.delegado_id else None,
                estado=inscripcion.estado,
                observacion=inscripcion.observacion,
                created_at=inscripcion.created_at,
            )

    async def ejecutar(self, data: InscripcionCreateData) -> InscripcionResult:
        """Execute the crear inscripcion flow."""
        return await self._crear_atomico(data)

    def __init__(self, inscripcion_core: InscripcionCoreService):
        self._inscripcion_core = inscripcion_core
