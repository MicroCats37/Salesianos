"""Implementaciones concretas de los puertos del módulo `salesianos_fest`."""

from modules.salesianos_fest.infrastructure.services.alcance_y_titularidad import (
    AlcanceEdicionAdapter,
    ResolucionPersonaAdapter,
    TitularidadAdapter,
)
from modules.salesianos_fest.infrastructure.services.obtencion_persona import (
    ObtencionPersonaAdapter,
)

__all__ = [
    "AlcanceEdicionAdapter",
    "ObtencionPersonaAdapter",
    "ResolucionPersonaAdapter",
    "TitularidadAdapter",
]
