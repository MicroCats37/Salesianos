"""
InscripcionService — sync operations for Inscripcion and InscripcionDelegado.

Core service — no transaction.atomic own, no async.
"""

from injector import inject

from modules.inscripciones.domain.models import Inscripcion, InscripcionDelegado
from modules.inscripciones.domain import exceptions as exc


class InscripcionService:
    """
    Core service for Inscripcion operations.
    """

    @inject
    def __init__(self):
        pass

    def crear(self, data) -> Inscripcion:
        """Create a new Inscripcion."""
        inscripcion = Inscripcion.objects.create(
            evento_id=data.evento_id,
            responsable_id=data.responsable_id,
            paquete_id=data.paquete_id,
            promocion_id=data.promocion_id,
            fusion_promocion_id=data.fusion_promocion_id if data.fusion_promocion_id else None,
            estado=data.estado if hasattr(data, 'estado') else 'RECIBIDA',
            observacion=data.observacion,
        )
        # Re-fetch with related objects for presenter compatibility
        return Inscripcion.objects.select_related("evento", "paquete", "promocion", "fusion_promocion").get(id=inscripcion.id)

    def actualizar_estado(
        self,
        inscripcion: Inscripcion,
        nuevo_estado: str,
        observacion: str | None = None,
    ) -> Inscripcion:
        """Update the estado of an Inscripcion."""
        inscripcion.estado = nuevo_estado
        if observacion is not None:
            inscripcion.observacion = observacion
        inscripcion.save()
        return inscripcion

    def obtener(self, inscripcion_id: str) -> Inscripcion | None:
        """Get an Inscripcion by ID."""
        return Inscripcion.objects.filter(id=inscripcion_id).first()

    def listar_por_responsable(self, responsable_id: str) -> list[Inscripcion]:
        """List all inscripciones for a responsible person."""
        return list(
            Inscripcion.objects
            .filter(responsable_id=responsable_id)
            .select_related("evento", "paquete")
            .order_by("-created_at")
        )

    def listar_por_evento(self, evento_id: str) -> list[Inscripcion]:
        """List all inscripciones for an event."""
        return list(
            Inscripcion.objects
            .filter(evento_id=evento_id)
            .select_related("responsable", "paquete")
            .order_by("-created_at")
        )

    def listar_todas(self) -> list[Inscripcion]:
        """List all inscripciones."""
        return list(
            Inscripcion.objects
            .select_related("evento", "responsable", "paquete")
            .order_by("-created_at")
        )

    # ── InscripcionDelegado ──────────────────────────────────────────────────

    def asignar_delegado(
        self,
        inscripcion_id: str,
        persona_id: str,
    ) -> InscripcionDelegado:
        """
        Assign or replace a delegate for an inscription.

        If a delegate already exists, it will be replaced (UniqueConstraint on inscripcion).
        """
        # Delete existing delegate if any
        InscripcionDelegado.objects.filter(inscripcion_id=inscripcion_id).delete()
        return InscripcionDelegado.objects.create(
            inscripcion_id=inscripcion_id,
            persona_id=persona_id,
        )

    def obtener_delegado(self, inscripcion_id: str) -> InscripcionDelegado | None:
        """Get the delegate for an inscription."""
        return InscripcionDelegado.objects.filter(inscripcion_id=inscripcion_id).first()

    def eliminar_delegado(self, inscripcion_id: str) -> int:
        """Remove the delegate from an inscription. Returns number of deleted rows."""
        return InscripcionDelegado.objects.filter(inscripcion_id=inscripcion_id).delete()[0]
