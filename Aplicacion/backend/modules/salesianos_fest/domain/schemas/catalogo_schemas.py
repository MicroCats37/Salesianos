"""DTOs internos del catálogo de inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros, NO schemas HTTP. Heredan de `pydantic.BaseModel`.
"""

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PaqueteOfertaData(BaseModel):
    """La oferta de un paquete tal como el servidor la resuelve.

    El precio es un hecho RESUELTO por el servidor contra el catálogo
    vigente: el cliente nunca lo impone (`RN-C02`).
    """

    paquete_id: str = Field(..., description="Identificador del paquete.")
    edicion_id: str = Field(..., description="Identificador de la edición.")
    nombre: str = Field(..., description="Nombre del paquete.")
    descripcion: str = Field(default="", description="Descripción del paquete.")
    cupos_incluidos: int = Field(..., gt=0, description="Cupos que otorga el paquete.")
    monto: Decimal = Field(..., ge=0, description="Monto vigente del catálogo.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217 del monto.")


class DisciplinaOfertaData(BaseModel):
    """La disciplina tal como el servidor la resuelve para el paquete."""

    disciplina_id: str = Field(..., description="Identificador de la disciplina.")
    nombre: str = Field(..., description="Nombre de la disciplina.")
    modalidad: str = Field(..., description="Modalidad de la disciplina.")
    minimo_por_equipo: int = Field(..., ge=1, description="Mínimo por equipo.")
    maximo_por_equipo: int = Field(..., ge=1, description="Máximo por equipo.")


__all__ = ["DisciplinaOfertaData", "PaqueteOfertaData"]
