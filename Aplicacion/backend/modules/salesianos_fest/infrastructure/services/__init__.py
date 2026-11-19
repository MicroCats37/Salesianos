"""Implementaciones concretas de los puertos del módulo `salesianos_fest`."""

from modules.salesianos_fest.infrastructure.services.alcance_y_titularidad import (
    AlcanceEdicionAdapter,
    ResolucionPersonaAdapter,
    TitularidadAdapter,
)

__all__ = [
    "AlcanceEdicionAdapter",
    "ResolucionPersonaAdapter",
    "TitularidadAdapter",
]
