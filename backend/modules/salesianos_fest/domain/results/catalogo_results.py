"""Result DTOs for catalog queries."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class DisciplinaResult:
    """Result for disciplina query."""

    id: str
    nombre: str
    sigla: str
    modalidad: str
    min_jugadores: int
    max_jugadores: int


@dataclass
class PromocionResult:
    """Result for promocion query."""

    id: str
    anio: int
    nombre: str


@dataclass
class CategoriaResult:
    """Result for categoria query."""

    id: str
    evento_id: str
    evento_nombre: str
    nombre: str
    promocion_desde: int
    promocion_hasta: int


@dataclass
class PaquetePrecioResult:
    """Result for paquete precio query."""

    etapa: str
    precio_unitario: Decimal
    vigente_desde: date
    vigente_hasta: Optional[date]


@dataclass
class PaqueteBeneficioResult:
    """Result for paquete beneficio query."""

    tipo: str
    cantidad: int
    alcance: str
    modo_calculo: str


@dataclass
class PaqueteDisciplinaResult:
    """Result for paquete disciplina query.

    Mirrors the canonical contract shape (section 2.3 of the inscripcion target
    contract): disciplina_id/nombre/sigla plus min/max jugadores per team.
    """

    disciplina_id: str
    disciplina_nombre: str
    disciplina_sigla: str
    min_jugadores: Optional[int]
    max_jugadores: Optional[int]


@dataclass
class PaqueteResult:
    """Result for paquete query with prices and benefits."""

    id: str
    evento_id: str
    nombre: str
    descripcion: str
    tipo: str
    modo_disciplinas: str
    cantidad_disciplinas: int
    minimo_compra_inicial: int
    precios: list[PaquetePrecioResult]
    beneficios: list[PaqueteBeneficioResult]
    disciplinas: list[PaqueteDisciplinaResult]


@dataclass
class PaqueteListResult:
    """Result for paquete list query.

    The list endpoint now returns the full `PaquetePresenter`: includes
    `disciplinas[]` (per-section 2 contract) so the wizard does NOT need to
    fetch detail after package selection.

    Also includes `beneficios[]` and `precios[]` for the quotation card.
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
    precio_preventa: Optional[Decimal]
    precio_regular: Optional[Decimal]
    tiene_fiesta: bool
    tiene_box: bool
    tiene_cerveza: bool
    disciplinas_resumen: list[str]  # ["F7M", "VOL", "BAS"] for display chips
    disciplinas: list[PaqueteDisciplinaResult]
    beneficios: list[PaqueteBeneficioResult]
    precios: list[PaquetePrecioResult]
