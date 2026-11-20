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

    El precio es UNITARIO (`D-CAT-01`): es el precio de UNA persona.
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
    tipo: str = Field(..., description="PACK o DISCIPLINA.")
    modo_disciplinas: str = Field(..., description="FIJO o ELEGIBLE.")
    cantidad_disciplinas: int = Field(
        ...,
        ge=1,
        description="Cuántas disciplinas puede declarar la inscripción.",
    )
    cupos_incluidos: int = Field(
        ...,
        ge=1,
        description=(
            "Cupos que declara la oferta. Deprecado: no es la cantidad que "
            "el comprador compra."
        ),
    )
    minimo_compra_inicial: int = Field(
        ...,
        ge=1,
        description="Mínimo comercial de participantes.",
    )
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


class PromocionCatalogoResult(BaseModel):
    """Una promoción (cohorte de nacimiento) del catálogo GLOBAL."""

    id: str = Field(..., description="Identificador de la promoción.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")
    anio: int = Field(..., ge=1, description="Año de la cohorte.")
    nombre: str = Field(..., description="Nombre de la promoción.")
    estado: str = Field(..., description="Estado de la promoción.")


class CatalogoPromocionesResult(BaseModel):
    """El catálogo de promociones activas del alcance.

    La promoción es GLOBAL (`D-CAT-04`): no lleva edición. La EDICIÓN que
    la scopea es la del ENVOLTORIO del catálogo, igual que en el catálogo de
    categorías.
    """

    edicion_id: str = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    promociones: list[PromocionCatalogoResult] = Field(
        default_factory=list,
        description="Promociones activas del catálogo global.",
    )


class CategoriaCatalogoResult(BaseModel):
    """Una categoría (banda competitiva) de UNA edición."""

    id: str = Field(..., description="Identificador de la categoría.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")
    edicion_id: str = Field(..., description="Edición de la categoría.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    nombre: str = Field(..., description="Nombre de la categoría.")
    promocion_desde: int = Field(..., ge=1, description="Cohorte más reciente.")
    promocion_hasta: int = Field(..., ge=1, description="Cohorte más antigua.")
    estado: str = Field(..., description="Estado de la categoría.")


class CatalogoCategoriasResult(BaseModel):
    """El catálogo de categorías de UNA edición."""

    edicion_id: str = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    categorias: list[CategoriaCatalogoResult] = Field(
        default_factory=list,
        description="Categorías activas de la edición.",
    )


class CotizacionResult(BaseModel):
    """La cotización de un paquete para una cantidad de participantes.

    Es un cálculo de LECTURA: el precio es el vigente del catálogo y el
    total lo deriva el servidor como `cantidad × precio_unitario`
    (`RN-C02`). El cliente nunca envía un importe.

    `version` es el TOKEN DE CONCURRENCIA del precio: viaja de vuelta en el
    alta para que el servidor detecte que el catálogo se movió entre la
    cotización y la confirmación, en vez de aceptarlo en silencio.
    """

    paquete_id: str = Field(..., description="Paquete cotizado.")
    paquete_nombre: str = Field(..., description="Nombre del paquete.")
    minimo_cantidad: int = Field(..., ge=1, description="Mínimo comercial.")
    cantidad_cotizada: int = Field(..., ge=1, description="Cantidad cotizada.")
    precio_unitario: Decimal = Field(..., ge=0, description="Precio unitario vigente.")
    total: Decimal = Field(..., ge=0, description="Total derivado por el servidor.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    version: int = Field(..., ge=1, description="Versión del precio cotizado.")
    estado: str = Field(..., description="Estado de la cotización.")
    validez_hasta: datetime = Field(..., description="Instante de caducidad.")


__all__ = [
    "BeneficioCatalogoResult",
    "CatalogoCategoriasResult",
    "CatalogoDisciplinasResult",
    "CatalogoPaquetesResult",
    "CatalogoPromocionesResult",
    "CategoriaCatalogoResult",
    "CotizacionResult",
    "DisciplinaCatalogoResult",
    "PaqueteCatalogoResult",
    "PrecioCatalogoResult",
    "PromocionCatalogoResult",
]
