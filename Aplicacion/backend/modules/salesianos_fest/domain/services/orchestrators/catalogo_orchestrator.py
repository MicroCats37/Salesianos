"""`CatalogoOrchestrator` — fachada async del catálogo de inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS: un método público por endpoint y NADA de lógica de
negocio. Todas las reglas viven en `CatalogoFlujo`.
"""

from injector import inject

from modules.salesianos_fest.domain.results.catalogo_result import (
    CatalogoDisciplinasResult,
    CatalogoPaquetesResult,
)
from modules.salesianos_fest.domain.services.flujos.catalogo_flujo import CatalogoFlujo


class CatalogoOrchestrator:
    """Fachada del catálogo."""

    @inject
    def __init__(self, flujo: CatalogoFlujo):
        self.flujo = flujo

    async def listar_paquetes(self, edicion_id=None) -> CatalogoPaquetesResult:
        """El catálogo de paquetes comprables de la edición del alcance."""
        return await self.flujo.listar_paquetes(edicion_id)

    async def listar_disciplinas(self, edicion_id=None) -> CatalogoDisciplinasResult:
        """El catálogo de disciplinas activas de la edición del alcance."""
        return await self.flujo.listar_disciplinas(edicion_id)


__all__ = ["CatalogoOrchestrator"]
