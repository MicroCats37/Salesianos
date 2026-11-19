"""Results del catálogo de inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros que el PRESENTER proyecta a schemas HTTP.
"""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PrecioCatalogoResult(BaseModel):
    """El precio vigente de un paquete, ya resuelto por el servidor."""

    monto: Decimal = Field(..., ge=0, description="Monto del catálogo.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    vigente_desde: date = Field(..., description="Inicio de la vigencia.")
    vigente_hasta: date | None = Field(
        default=None,
        description="Fin de la vigencia. Vacío significa vigencia abierta.",
    )


class BeneficioCatalogoResult(BaseModel):
    """Un beneficio OFRECIDO por el paquete (`RN-P01`)."""

    codigo: str = Field(..., description="Código del beneficio.")
    nombre: str = Field(..., description="Nombre del beneficio.")
    tipo: str = Field(..., description="FIJO_INICIAL o POR_CUPO.")
    cantidad: int = Field(..., ge=1, description="Cantidad declarada.")


class DisciplinaCatalogoResult(BaseModel):
    """Una disciplina del catálogo de la edición."""

    id: str = Field(..., description="Identificador de la disciplina.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")
    edicion_id: str = Field(..., description="Edición de la disciplina.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    nombre: str = Field(..., description="Nombre de la disciplina.")
    slug: str = Field(..., description="Identificador de la disciplina.")
    estado: str = Field(..., description="Estado de la disciplina.")
    modalidad: str = Field(..., description="Modalidad de la disciplina.")
    minimo_por_equipo: int = Field(..., ge=1, description="Mínimo por equipo.")
    maximo_por_equipo: int = Field(..., ge=1, description="Máximo por equipo.")


class PaqueteCatalogoResult(BaseModel):
    """Un paquete del catálogo, con su precio vigente y sus beneficios.

    `precio` NUNCA es un precio de reserva: si el paquete no tiene precio
    vigente, el paquete NO aparece en el catálogo (`FL-01` paso 3).
    """

    id: str = Field(..., description="Identificador del paquete.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")
    edicion_id: str = Field(..., description="Edición del paquete.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    nombre: str = Field(..., description="Nombre del paquete.")
    slug: str = Field(..., description="Identificador del paquete.")
    descripcion: str = Field(default="", description="Descripción del paquete.")
    estado: str = Field(..., description="Estado del paquete.")
    cupos_incluidos: int = Field(..., ge=1, description="Cupos que otorga.")
    precio: PrecioCatalogoResult = Field(..., description="Precio vigente.")
    beneficios: list[BeneficioCatalogoResult] = Field(
        default_factory=list,
        description="Beneficios ofrecidos por el paquete.",
    )
    disciplinas: list[DisciplinaCatalogoResult] = Field(
        default_factory=list,
        description="Disciplinas permitidas por el paquete.",
    )


class CatalogoPaquetesResult(BaseModel):
    """El catálogo de paquetes de UNA edición."""

    edicion_id: str = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    paquetes: list[PaqueteCatalogoResult] = Field(
        default_factory=list,
        description="Paquetes comprables de la edición.",
    )


class CatalogoDisciplinasResult(BaseModel):
    """El catálogo de disciplinas de UNA edición."""

    edicion_id: str = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    disciplinas: list[DisciplinaCatalogoResult] = Field(
        default_factory=list,
        description="Disciplinas activas de la edición.",
    )


__all__ = [
    "BeneficioCatalogoResult",
    "CatalogoDisciplinasResult",
    "CatalogoPaquetesResult",
    "DisciplinaCatalogoResult",
    "PaqueteCatalogoResult",
    "PrecioCatalogoResult",
]
