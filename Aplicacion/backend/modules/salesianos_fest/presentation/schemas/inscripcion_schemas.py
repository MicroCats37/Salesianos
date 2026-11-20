"""Contrato HTTP de las inscripciones.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §5 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición de bloques) ·
          `contract/PLAN_REFACTORIZACION.md` §1.C (todo schema hereda
          `BaseSchema`).

Los wrappers se COMPONEN con los tres bloques conceptuales (identidad,
general, específico). No hay `z.any()`, ni campos genéricos, ni campos de
otros dominios: la compra que se publica es la PROYECCIÓN de la compra de
`commerce`, no su modelo.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema
from modules.salesianos_fest.domain.constants import (
    MAX_EQUIPOS_POR_INSCRIPCION,
    MIN_CANTIDAD_POR_INSCRIPCION,
    MIN_EQUIPOS_POR_INSCRIPCION,
)


class EquipoIdentidadOut(BaseSchema):
    """Bloque de identidad de un equipo."""

    id: UUID = Field(..., description="Identificador del equipo.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class CategoriaReferenciaOut(BaseSchema):
    """La banda competitiva de un equipo, como REFERENCIA.

    La publica el servidor: el cliente NO la declara y NO la deriva
    (`D-CAT-05`).
    """

    id: UUID = Field(..., description="Identificador de la categoría.")
    nombre: str = Field(..., description="Nombre de la categoría.")


class EquipoEspecificoOut(BaseSchema):
    """Bloque específico de un equipo."""

    disciplina_id: UUID = Field(..., description="Disciplina del equipo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    categoria: CategoriaReferenciaOut = Field(
        ...,
        description=(
            "Banda competitiva del equipo. La deriva el servidor desde la "
            "promoción de la inscripción."
        ),
    )
    nombre: str = Field(..., description="Nombre del equipo.")
    estado: str = Field(..., description="Estado del equipo.")


class EquipoOut(EquipoIdentidadOut, EquipoEspecificoOut):
    """Salida de un equipo de la inscripción."""


class InscripcionIdentidadOut(BaseSchema):
    """Bloque de identidad de una inscripción."""

    id: UUID = Field(..., description="Identificador de la inscripción.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")


class InscripcionGeneralOut(BaseSchema):
    """Bloque general de una inscripción: edición y responsable."""

    edicion_id: UUID = Field(..., description="Edición de la inscripción.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    responsable_id: UUID = Field(..., description="Persona responsable.")


class PromocionReferenciaOut(BaseSchema):
    """La promoción (cohorte) de una inscripción.

    Se llama `…ReferenciaOut` y no `PromocionOut` a propósito: el catálogo
    publica su propia `PromocionOut` y dos schemas con el mismo nombre en
    módulos distintos colisionan en el registro de componentes OpenAPI.
    """

    id: UUID = Field(..., description="Identificador de la promoción.")
    anio: int = Field(..., ge=1, description="Año de la cohorte.")
    nombre: str = Field(..., description="Nombre de la promoción.")


class InscripcionEspecificaOut(BaseSchema):
    """Bloque específico de una inscripción: paquete, promoción, estado y saldo."""

    paquete_id: UUID = Field(..., description="Paquete contratado.")
    paquete_nombre: str = Field(..., description="Nombre del paquete.")
    promocion: PromocionReferenciaOut = Field(..., description="Promoción que compra.")
    fusion_promocion: PromocionReferenciaOut | None = Field(
        default=None,
        description=(
            "Promoción fusionada. Es metadato descriptivo: no altera cupos, "
            "pago, categoría, elegibilidad ni cuadro competitivo."
        ),
    )
    estado: str = Field(..., description="Estado de la inscripción.")
    referencia: str = Field(..., description="Referencia de la inscripción.")
    cupos_solicitados: int = Field(..., ge=0, description="Cupos que compra el alta.")
    cupos_pagados: int = Field(..., ge=0, description="Cupos pagados y activados.")
    cupos_asignados: int = Field(..., ge=0, description="Cupos asignados a personas.")
    cupos_disponibles: int = Field(..., ge=0, description="Cupos pagados sin asignar.")


class InscripcionDetalleOut(
    InscripcionIdentidadOut,
    InscripcionGeneralOut,
    InscripcionEspecificaOut,
):
    """Salida del detalle de una inscripción, con sus equipos."""

    equipos: list[EquipoOut] = Field(
        default_factory=list,
        description="Equipos declarados en la inscripción.",
    )


class EquiposInscripcionOut(BaseSchema):
    """Salida de los equipos de una inscripción."""

    inscripcion_id: UUID = Field(..., description="Inscripción consultada.")
    equipos: list[EquipoOut] = Field(
        default_factory=list,
        description="Equipos declarados en la inscripción.",
    )


class CompraOut(BaseSchema):
    """La compra que financia la inscripción, proyectada por este módulo.

    Es una PROYECCIÓN de la compra de `commerce`: este módulo no es su
    dueño y no publica su modelo entero.

    El total lo derivó `commerce` de las líneas del snapshot, que congela
    la cantidad y el precio unitario que resolvió el servidor (`RN-C02`).
    """

    compra_id: UUID = Field(..., description="Identificador de la compra.")
    orden_pago_id: UUID = Field(..., description="Identificador de la orden de pago.")
    estado: str = Field(..., description="Estado comercial de la compra.")
    total: Decimal = Field(..., ge=0, description="Total congelado de la compra.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    reutilizada: bool = Field(
        default=False,
        description="Si la compra pendiente ya existía y se reutilizó.",
    )


class InscripcionInicialOut(BaseSchema):
    """Salida del alta de una inscripción inicial.

    `causa_operativa` es la CAUSA que el presenter publica: por qué la
    operación devolvió esto. El controller no la decide (`RN-A02`).
    """

    inscripcion: InscripcionDetalleOut = Field(..., description="La inscripción.")
    compra: CompraOut = Field(..., description="La compra pendiente.")
    causa_operativa: str = Field(..., description="Causa operativa de la respuesta.")


# ── Entradas ────────────────────────────────────────────────────────────────


class EquipoIn(BaseSchema):
    """Un equipo declarado en el alta."""

    disciplina_id: UUID = Field(..., description="Disciplina del equipo.")
    nombre: str = Field(
        ...,
        min_length=1,
        max_length=160,
        description="Nombre del equipo.",
    )


class InscripcionInicialIn(BaseSchema):
    """El payload del alta de una inscripción inicial.

    El responsable NO se declara: lo resuelve el servidor desde la cuenta
    autenticada (`RN-U04`). El precio tampoco: lo resuelve el servidor
    contra el catálogo vigente (`RN-C02`).

    `promocion_id` es OBLIGATORIA: es la cohorte que compra y la que
    determina la categoría del equipo. `fusion_promocion_id` es OPCIONAL y
    DESCRIPTIVA.

    `cantidad` es el número de PARTICIPANTES que se inscriben. El total lo
    deriva el servidor como `cantidad × precio_unitario`.
    """

    edicion_id: UUID = Field(..., description="Edición del alcance.")
    paquete_id: UUID = Field(..., description="Paquete de inscripción.")
    promocion_id: UUID = Field(
        ...,
        description="Promoción (cohorte) que compra la inscripción.",
    )
    fusion_promocion_id: UUID | None = Field(
        default=None,
        description=(
            "Promoción fusionada. Es metadato descriptivo: no altera cupos, "
            "pago, categoría, elegibilidad ni cuadro competitivo."
        ),
    )
    cantidad: int = Field(
        ...,
        ge=MIN_CANTIDAD_POR_INSCRIPCION,
        description="Número de participantes que se inscriben.",
    )
    cotizacion_version: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Token de concurrencia de la cotización. Viaja sólo si el "
            "comprador cotizó antes."
        ),
    )
    equipos: list[EquipoIn] = Field(
        ...,
        min_length=MIN_EQUIPOS_POR_INSCRIPCION,
        max_length=MAX_EQUIPOS_POR_INSCRIPCION,
        description="Equipos declarados en el alta.",
    )


__all__ = [
    "CategoriaReferenciaOut",
    "CompraOut",
    "EquipoEspecificoOut",
    "EquipoIdentidadOut",
    "EquipoIn",
    "EquipoOut",
    "EquiposInscripcionOut",
    "InscripcionDetalleOut",
    "InscripcionEspecificaOut",
    "InscripcionGeneralOut",
    "InscripcionIdentidadOut",
    "InscripcionInicialIn",
    "InscripcionInicialOut",
    "PromocionReferenciaOut",
]
