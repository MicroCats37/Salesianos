"""
HTTP schemas for catalogo endpoints.
"""
from datetime import date
from typing import Optional

from core.types import BaseSchema


class DisciplinaOut(BaseSchema):
    """Schema for disciplina in catalog response."""

    id: str
    nombre: str
    sigla: str
    modalidad: str
    min_jugadores: int
    max_jugadores: int


class PromocionOut(BaseSchema):
    """Schema for promocion in catalog response."""

    id: str
    anio: int
    nombre: str


class CategoriaOut(BaseSchema):
    """Schema for categoria in catalog response."""

    id: str
    evento_id: str
    evento_nombre: str
    nombre: str
    promocion_desde: int
    promocion_hasta: int


class PaquetePrecioOut(BaseSchema):
    """Schema for paquete precio in catalog response."""

    etapa: str
    precio_unitario: float
    vigente_desde: date
    vigente_hasta: Optional[date]


class PaqueteBeneficioOut(BaseSchema):
    """Schema for paquete beneficio in catalog response."""

    tipo: str
    cantidad: int
    alcance: str
    modo_calculo: str


class PaqueteDisciplinaOut(BaseSchema):
    """Schema for paquete disciplina in catalog response.

    Mirrors the canonical contract (section 2.3): min/max jugadores are
    present so the frontend can render min/max validation client-side
    without a separate detail fetch.
    """

    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    min_jugadores: Optional[int]
    max_jugadores: Optional[int]


class PaqueteListOut(BaseSchema):
    """Schema for paquete list item in catalog response.

    The list endpoint now exposes the full `PaquetePresenter` per the
    inscripcion target contract (section 2): the wizard must be able to
    complete the inscription flow WITHOUT fetching /paquetes/{id}/.

    Includes `beneficios[]` and `precios[]` arrays so the quotation card
    can render full price/benefit info without a detail fetch.
    """

    id: str
    evento_id: str
    nombre: str
    descripcion: str
    tipo: str
    modo_disciplinas: str
    cantidad_disciplinas: int
    cantidad_minima_compra: int  # renamed from cantidad_maxima_participantes (misleading name)
    cantidad_maxima_equipos: int
    precio_preventa: Optional[float]
    precio_regular: Optional[float]
    precio_promocional: Optional[float]
    tiene_fiesta: bool
    tiene_box: bool
    tiene_cerveza: bool
    disciplinas_resumen: list[str]  # ["F7M", "VOL", "BAS"] for display chips
    disciplinas: list[PaqueteDisciplinaOut]  # full PaquetePresenter per section 2 contract
    beneficios: list[PaqueteBeneficioOut]  # full benefit list for wizard display
    precios: list[PaquetePrecioOut]  # full price timeline for quotation card


class PaqueteDetailOut(BaseSchema):
    """Schema for full paquete detail in catalog response."""

    id: str
    evento_id: str
    nombre: str
    descripcion: str
    tipo: str
    modo_disciplinas: str
    cantidad_disciplinas: int
    minimo_compra_inicial: int
    precios: list[PaquetePrecioOut]
    beneficios: list[PaqueteBeneficioOut]
    disciplinas: list[PaqueteDisciplinaOut]
