"""`CatalogoOrchestrator` — fachada async del catálogo de inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/django-app-architecture-contract.md` §4.5 — fachadas
async DELGADAS: un método público por endpoint y NADA de lógica de
negocio. Todas las reglas viven en `CatalogoFlujo`.
"""

from injector import inject

from modules.salesianos_fest.domain.results.catalogo_result import (
    CatalogoCategoriasResult,
    CatalogoDisciplinasResult,
    CatalogoPaquetesResult,
    CatalogoPromocionesResult,
    CotizacionResult,
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

    async def listar_promociones(self, edicion_id=None) -> CatalogoPromocionesResult:
        """El catálogo GLOBAL de promociones activas del alcance."""
        return await self.flujo.listar_promociones(edicion_id)

    async def listar_categorias(self, edicion_id=None) -> CatalogoCategoriasResult:
        """El catálogo de categorías activas de la edición del alcance."""
        return await self.flujo.listar_categorias(edicion_id)

    async def cotizar(self, paquete_id, cantidad: int) -> CotizacionResult:
        """La cotización de un paquete para una cantidad de participantes."""
        return await self.flujo.cotizar(paquete_id, cantidad)


__all__ = ["CatalogoOrchestrator"]
