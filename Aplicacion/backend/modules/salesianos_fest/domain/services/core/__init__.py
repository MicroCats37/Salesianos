"""Servicios core del módulo `salesianos_fest`."""

from modules.salesianos_fest.domain.services.core.catalogo_core_service import (
    CatalogoCoreService,
)
from modules.salesianos_fest.domain.services.core.inscripcion_core_service import (
    InscripcionCoreService,
)

__all__ = ["CatalogoCoreService", "InscripcionCoreService"]
