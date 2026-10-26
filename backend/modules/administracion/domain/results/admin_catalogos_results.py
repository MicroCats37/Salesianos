"""
AdminCatalogosResult — internal DTOs of the filter catalogs (A2).

The catalogs do NOT re-implement the catalog business logic: they collect the
result objects of the OWNING modules' selectors (`DisciplinaSelector`,
`PromocionSelector`, `CategoriaSelector`, `PaqueteSelector`) and scope them to
the active event.

Only option lists live here — never a business entity with PII, a credential
or a payment detail.
"""

from pydantic import BaseModel


class AdminCatalogoItemResult(BaseModel):
    """A filter option of a catalog (id + display name)."""

    id: str
    nombre: str
    sigla: str | None = None


class AdminCatalogoPaqueteResult(BaseModel):
    """A package filter option."""

    id: str
    nombre: str
    tipo: str


class AdminEstadosCatalogosResult(BaseModel):
    """The state vocabularies the filters use.

    The values come from the domain constants of the OWNING modules — the
    admin area never declares a second vocabulary.
    """

    inscripcion: list[str]
    compra: list[str]
    orden_pago: list[str]
    asignacion_cupo: list[str]
    equipo: list[str]
    acreditacion: list[str]
    autorizacion_fiesta: list[str]
    acceso: list[str]
    pool: list[str]
    rol_participante: list[str]


class AdminCatalogosResult(BaseModel):
    """The filter option lists of the active event."""

    evento_id: str
    evento_nombre: str
    disciplinas: list[AdminCatalogoItemResult]
    paquetes: list[AdminCatalogoPaqueteResult]
    promociones: list[AdminCatalogoItemResult]
    categorias: list[AdminCatalogoItemResult]
    puntos_acceso: list[str]
    estados: AdminEstadosCatalogosResult


__all__ = [
    "AdminCatalogoItemResult",
    "AdminCatalogoPaqueteResult",
    "AdminEstadosCatalogosResult",
    "AdminCatalogosResult",
]
