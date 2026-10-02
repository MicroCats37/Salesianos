"""
EventoService — sync CRUD operations for Evento.

Core service — no transaction.atomic own, no async.
"""

from injector import inject

from modules.inscripciones.domain.models import Evento


class EventoService:
    """
    Core service for Evento operations.
    """

    @inject
    def __init__(self):
        pass

    def crear(self, data) -> Evento:
        """Create a new Evento."""
        return Evento.objects.create(
            nombre=data.nombre,
            fecha_inicio=data.fecha_inicio,
            fecha_fin=data.fecha_fin,
            esta_activo=data.esta_activo,
        )

    def actualizar(self, evento: Evento, data) -> Evento:
        """Update an existing Evento."""
        update_fields = data.model_dump(exclude_none=True)
        for field, value in update_fields.items():
            setattr(evento, field, value)
        evento.save()
        return evento

    def obtener(self, evento_id: str) -> Evento | None:
        """Get an Evento by ID."""
        return Evento.objects.filter(id=evento_id).first()

    def listar_activos(self) -> list[Evento]:
        """List all active Eventos."""
        return list(
            Evento.objects
            .filter(esta_activo=True)
            .order_by("-fecha_inicio")
        )

    def listar_todos(self) -> list[Evento]:
        """List all Eventos regardless of status."""
        return list(Evento.objects.order_by("-fecha_inicio"))
