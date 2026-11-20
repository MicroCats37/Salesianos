"""DTOs internos del catálogo de inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`
Cambio: `restore-registration-promotion-catalog-flow` (2026-11-20)

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros, NO schemas HTTP. Heredan de `pydantic.BaseModel`.
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from modules.salesianos_fest.domain.constants import MIN_CANTIDAD_POR_INSCRIPCION


class PaqueteOfertaData(BaseModel):
    """La oferta de un paquete tal como el servidor la resuelve.

    El precio es un hecho RESUELTO por el servidor contra el catálogo
    vigente: el cliente nunca lo impone (`RN-C02`). El monto es UNITARIO:
    es el precio de UNA persona (`D-CAT-01`).
    """

    paquete_id: str = Field(..., description="Identificador del paquete.")
    edicion_id: str = Field(..., description="Identificador de la edición.")
    nombre: str = Field(..., description="Nombre del paquete.")
    descripcion: str = Field(default="", description="Descripción del paquete.")
    tipo: str = Field(..., description="PACK o DISCIPLINA.")
    modo_disciplinas: str = Field(..., description="FIJO o ELEGIBLE.")
    cantidad_disciplinas: int = Field(
        ...,
        ge=1,
        description="Cuántas disciplinas puede declarar la inscripción.",
    )
    minimo_compra_inicial: int = Field(
        ...,
        ge=1,
        description="Mínimo comercial de participantes.",
    )
    monto: Decimal = Field(..., ge=0, description="Monto unitario vigente del catálogo.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217 del monto.")


class DisciplinaOfertaData(BaseModel):
    """La disciplina tal como el servidor la resuelve para el paquete."""

    disciplina_id: str = Field(..., description="Identificador de la disciplina.")
    nombre: str = Field(..., description="Nombre de la disciplina.")
    modalidad: str = Field(..., description="Modalidad de la disciplina.")
    minimo_por_equipo: int = Field(..., ge=1, description="Mínimo por equipo.")
    maximo_por_equipo: int = Field(..., ge=1, description="Máximo por equipo.")


class CotizacionData(BaseModel):
    """La intención de cotizar un paquete para una cantidad de participantes.

    Es una cotización SIN PERSISTIR: el servidor resuelve el precio vigente
    del catálogo y devuelve el desglose. El alta vuelve a resolver el precio
    contra el catálogo y CONGELA ese precio en la compra (`RN-C02`).
    """

    paquete_id: UUID = Field(..., description="Paquete a cotizar.")
    cantidad: int = Field(
        ...,
        ge=MIN_CANTIDAD_POR_INSCRIPCION,
        description="Número de participantes por los que se cotiza.",
    )


__all__ = ["CotizacionData", "DisciplinaOfertaData", "PaqueteOfertaData"]
