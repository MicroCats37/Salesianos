"""HTTP schemas for Evento."""

from datetime import date

from ninja import Schema


class EventoOut(Schema):
    """Evento response schema."""

    id: str
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    esta_activo: bool
