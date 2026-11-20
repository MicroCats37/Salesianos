"""Contrato HTTP del catálogo de inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §5 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición de bloques) ·
          `contract/PLAN_REFACTORIZACION.md` §1.C (todo schema hereda
          `BaseSchema`).

Los wrappers se COMPONEN con los tres bloques conceptuales:

- **Identidad** — identificador y marcas de tiempo.
- **General** — la familia a la que pertenece (la edición).
- **Específico** — lo propio de cada caso de uso.

No hay `z.any()`, ni campos genéricos, ni campos de otros dominios.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


class PrecioOut(BaseSchema):
    """Bloque general del precio de catálogo."""

    monto: Decimal = Field(..., ge=0, description="Monto del catálogo.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    vigente_desde: date = Field(..., description="Inicio de la vigencia.")
    vigente_hasta: date | None = Field(
        default=None,
        description="Fin de la vigencia. Vacío significa vigencia abierta.",
    )


class BeneficioOut(BaseSchema):
    """Bloque general de un beneficio OFRECIDO por un paquete (`RN-P01`)."""

    codigo: str = Field(..., description="Código del beneficio.")
    nombre: str = Field(..., description="Nombre del beneficio.")
    tipo: str = Field(..., description="FIJO_INICIAL o POR_CUPO.")
    cantidad: int = Field(..., ge=1, description="Cantidad declarada.")


class DisciplinaIdentidadOut(BaseSchema):
    """Bloque de identidad de una disciplina."""

    id: UUID = Field(..., description="Identificador de la disciplina.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class DisciplinaGeneralOut(BaseSchema):
    """Bloque general de una disciplina: la edición a la que pertenece."""

    edicion_id: UUID = Field(..., description="Edición de la disciplina.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")


class DisciplinaEspecificaOut(BaseSchema):
    """Bloque específico de una disciplina."""

    nombre: str = Field(..., description="Nombre de la disciplina.")
    slug: str = Field(..., description="Identificador de la disciplina.")
    estado: str = Field(..., description="Estado de la disciplina.")
    modalidad: str = Field(..., description="Modalidad de la disciplina.")
    minimo_por_equipo: int = Field(..., ge=1, description="Mínimo por equipo.")
    maximo_por_equipo: int = Field(..., ge=1, description="Máximo por equipo.")


class DisciplinaOut(
    DisciplinaIdentidadOut,
    DisciplinaGeneralOut,
    DisciplinaEspecificaOut,
):
    """Salida de una disciplina del catálogo."""


class PaqueteIdentidadOut(BaseSchema):
    """Bloque de identidad de un paquete."""

    id: UUID = Field(..., description="Identificador del paquete.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class PaqueteGeneralOut(BaseSchema):
    """Bloque general de un paquete: la edición a la que pertenece."""

    edicion_id: UUID = Field(..., description="Edición del paquete.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")


class PaqueteEspecificoOut(BaseSchema):
    """Bloque específico de un paquete."""

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
            "el comprador compra, sino el hecho de catálogo de la oferta."
        ),
    )
    minimo_compra_inicial: int = Field(
        ...,
        ge=1,
        description="Mínimo comercial de participantes.",
    )
    precio: PrecioOut = Field(..., description="Precio vigente del catálogo.")
    beneficios: list[BeneficioOut] = Field(
        default_factory=list,
        description="Beneficios ofrecidos por el paquete.",
    )
    disciplinas: list[DisciplinaOut] = Field(
        default_factory=list,
        description="Disciplinas permitidas por el paquete.",
    )


class PaqueteOut(PaqueteIdentidadOut, PaqueteGeneralOut, PaqueteEspecificoOut):
    """Salida de un paquete del catálogo."""


class CatalogoPaquetesOut(BaseSchema):
    """El catálogo de paquetes de UNA edición."""

    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    paquetes: list[PaqueteOut] = Field(
        default_factory=list,
        description="Paquetes comprables de la edición.",
    )


class CatalogoDisciplinasOut(BaseSchema):
    """El catálogo de disciplinas de UNA edición."""

    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    disciplinas: list[DisciplinaOut] = Field(
        default_factory=list,
        description="Disciplinas activas de la edición.",
    )


class PromocionIdentidadOut(BaseSchema):
    """Bloque de identidad de una promoción."""

    id: UUID = Field(..., description="Identificador de la promoción.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class PromocionEspecificaOut(BaseSchema):
    """Bloque específico de una promoción (cohorte de nacimiento)."""

    anio: int = Field(..., ge=1, description="Año de la cohorte.")
    nombre: str = Field(..., description="Nombre de la promoción.")
    estado: str = Field(..., description="Estado de la promoción.")


class PromocionOut(PromocionIdentidadOut, PromocionEspecificaOut):
    """Salida de una promoción del catálogo global."""


class CatalogoPromocionesOut(BaseSchema):
    """El catálogo GLOBAL de promociones activas del alcance.

    La promoción es GLOBAL (`D-CAT-04`): no lleva edición. La EDICIÓN que
    scopea el catálogo va en el ENVOLTORIO, igual que en el catálogo de
    categorías.
    """

    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    promociones: list[PromocionOut] = Field(
        default_factory=list,
        description="Promociones activas del catálogo global.",
    )


class CategoriaIdentidadOut(BaseSchema):
    """Bloque de identidad de una categoría."""

    id: UUID = Field(..., description="Identificador de la categoría.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class CategoriaGeneralOut(BaseSchema):
    """Bloque general de una categoría: la edición a la que pertenece."""

    edicion_id: UUID = Field(..., description="Edición de la categoría.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")


class CategoriaEspecificaOut(BaseSchema):
    """Bloque específico de una categoría (banda competitiva)."""

    nombre: str = Field(..., description="Nombre de la categoría.")
    promocion_desde: int = Field(..., ge=1, description="Cohorte más reciente.")
    promocion_hasta: int = Field(..., ge=1, description="Cohorte más antigua.")
    estado: str = Field(..., description="Estado de la categoría.")


class CategoriaOut(
    CategoriaIdentidadOut,
    CategoriaGeneralOut,
    CategoriaEspecificaOut,
):
    """Salida de una categoría del catálogo."""


class CatalogoCategoriasOut(BaseSchema):
    """El catálogo de categorías de UNA edición."""

    edicion_id: UUID = Field(..., description="Edición del alcance.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    categorias: list[CategoriaOut] = Field(
        default_factory=list,
        description="Categorías activas de la edición.",
    )


class CotizacionOut(BaseSchema):
    """La cotización de un paquete para una cantidad de participantes.

    El total lo deriva el servidor como `cantidad × precio_unitario`: el
    cliente nunca envía un importe (`RN-C02`).

    `version` es el TOKEN DE CONCURRENCIA del precio cotizado: el alta lo
    devuelve para que el servidor detecte que el catálogo se movió entre la
    cotización y la confirmación.
    """

    paquete_id: UUID = Field(..., description="Paquete cotizado.")
    paquete_nombre: str = Field(..., description="Nombre del paquete.")
    minimo_cantidad: int = Field(..., ge=1, description="Mínimo comercial.")
    cantidad_cotizada: int = Field(..., ge=1, description="Cantidad cotizada.")
    precio_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Precio unitario vigente del catálogo.",
    )
    total: Decimal = Field(..., ge=0, description="Total derivado por el servidor.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    version: int = Field(..., ge=1, description="Versión del precio cotizado.")
    estado: str = Field(..., description="Estado de la cotización.")
    validez_hasta: datetime = Field(..., description="Instante de caducidad.")


__all__ = [
    "BeneficioOut",
    "CatalogoCategoriasOut",
    "CatalogoDisciplinasOut",
    "CatalogoPaquetesOut",
    "CatalogoPromocionesOut",
    "CategoriaEspecificaOut",
    "CategoriaGeneralOut",
    "CategoriaIdentidadOut",
    "CategoriaOut",
    "CotizacionOut",
    "DisciplinaEspecificaOut",
    "DisciplinaGeneralOut",
    "DisciplinaIdentidadOut",
    "DisciplinaOut",
    "PaqueteEspecificoOut",
    "PaqueteGeneralOut",
    "PaqueteIdentidadOut",
    "PaqueteOut",
    "PrecioOut",
    "PromocionEspecificaOut",
    "PromocionIdentidadOut",
    "PromocionOut",
]
