"""Esquemas HTTP del acta de auditoría.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`
"""

from datetime import datetime
from typing import List, Optional

from core.types import BaseSchema


class AuditoriaItemOut(BaseSchema):
    """Un acta de auditoría, ya saneada para publicarse.

    El `motivo` es la razón que escribió el actor. El acta NO publica el
    contexto crudo: el servicio lo saneó al escribir y aquí sólo viaja la
    identidad, el momento y el motivo.
    """

    id: str
    edicion_id: Optional[str]
    actor: str
    accion: str
    entidad: str
    entidad_id: str
    motivo: str
    registrado_en: datetime


class AuditoriaListadoOut(BaseSchema):
    """Una página de actas de auditoría."""

    items: List[AuditoriaItemOut]
    total: int
    page: int
    page_size: int
    total_pages: int


__all__ = ["AuditoriaItemOut", "AuditoriaListadoOut"]
