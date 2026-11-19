"""Re-export de los results del módulo `salesianos_fest`."""

from modules.salesianos_fest.domain.results.catalogo_result import (
    BeneficioCatalogoResult,
    CatalogoDisciplinasResult,
    CatalogoPaquetesResult,
    DisciplinaCatalogoResult,
    PaqueteCatalogoResult,
    PrecioCatalogoResult,
)
from modules.salesianos_fest.domain.results.inscripcion_result import (
    CompraInscripcionResult,
    EquipoResult,
    InscripcionDetalleResult,
    InscripcionInicialResult,
)
from modules.salesianos_fest.domain.results.pool_result import (
    CompraCuposResult,
    ImpedimentoResult,
    ParticipacionResult,
    PoolResult,
)

__all__ = [
    "BeneficioCatalogoResult",
    "CatalogoDisciplinasResult",
    "CatalogoPaquetesResult",
    "CompraCuposResult",
    "CompraInscripcionResult",
    "DisciplinaCatalogoResult",
    "EquipoResult",
    "ImpedimentoResult",
    "InscripcionDetalleResult",
    "InscripcionInicialResult",
    "PaqueteCatalogoResult",
    "ParticipacionResult",
    "PoolResult",
    "PrecioCatalogoResult",
]
