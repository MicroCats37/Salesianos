"""Results de la inscripción.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.6 — DTOs
Pydantic puros que el PRESENTER proyecta a schemas HTTP.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class EquipoResult(BaseModel):
    """Un equipo de la inscripción.

    `categoria` es la banda competitiva DERIVADA por el servidor desde la
    promocion de la inscripcion (`D-CAT-05`): el cliente nunca la declara.
    """

    id: str = Field(..., description="Identificador del equipo.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")
    disciplina_id: str = Field(..., description="Disciplina del equipo.")
    disciplina_nombre: str = Field(..., description="Nombre de la disciplina.")
    categoria_id: str = Field(..., description="Identificador de la categoría.")
    categoria_nombre: str = Field(..., description="Nombre de la categoría.")
    nombre: str = Field(..., description="Nombre del equipo.")
    estado: str = Field(..., description="Estado del equipo.")


class PromocionResult(BaseModel):
    """La promoción (cohorte) de una inscripción."""

    id: str = Field(..., description="Identificador de la promoción.")
    anio: int = Field(..., ge=1, description="Año de la cohorte.")
    nombre: str = Field(..., description="Nombre de la promoción.")


class InscripcionDetalleResult(BaseModel):
    """El detalle de una inscripción, con su saldo de cupos.

    `cupos_disponibles` es la diferencia entre cupos pagados y asignados
    (`RN-I03`): la calcula el SERVIDOR. El cliente nunca resta.
    """

    id: str = Field(..., description="Identificador de la inscripción.")
    created_at: datetime = Field(..., description="Momento de creación.")
    updated_at: datetime = Field(..., description="Última actualización.")
    edicion_id: str = Field(..., description="Edición de la inscripción.")
    edicion_nombre: str = Field(..., description="Nombre de la edición.")
    responsable_id: str = Field(..., description="Persona responsable.")
    paquete_id: str = Field(..., description="Paquete contratado.")
    paquete_nombre: str = Field(..., description="Nombre del paquete.")
    promocion: PromocionResult = Field(..., description="Promoción que compra.")
    fusion_promocion: PromocionResult | None = Field(
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
    equipos: list[EquipoResult] = Field(
        default_factory=list,
        description="Equipos declarados.",
    )


class CompraInscripcionResult(BaseModel):
    """La compra comercial que financia la inscripción.

    Es un hecho de `commerce`: su vida es de `commerce` y `pagos`. Este
    módulo sólo proyecta lo que necesita el comprador.
    """

    compra_id: str = Field(..., description="Identificador de la compra.")
    orden_pago_id: str = Field(..., description="Identificador de la orden de pago.")
    estado: str = Field(..., description="Estado comercial de la compra.")
    cantidad: int = Field(..., ge=1, description="Participantes comprados.")
    precio_unitario: Decimal = Field(
        ...,
        ge=0,
        description="Precio unitario congelado del catálogo.",
    )
    total: Decimal = Field(..., ge=0, description="Total congelado de la compra.")
    moneda: str = Field(..., max_length=3, description="Código ISO-4217.")
    reutilizada: bool = Field(
        default=False,
        description="Si la compra pendiente ya existía y se reutilizó.",
    )


class InscripcionInicialResult(BaseModel):
    """El resultado del alta de una inscripción inicial.

    `causa_operativa` es la CAUSA que el presenter publica: por qué la
    operación devolvió esto (`RN-C07`, `RN-A02`).
    """

    inscripcion: InscripcionDetalleResult = Field(..., description="La inscripción.")
    compra: CompraInscripcionResult = Field(..., description="La compra pendiente.")
    causa_operativa: str = Field(
        ...,
        description="Causa operativa de la respuesta.",
    )


__all__ = [
    "CompraInscripcionResult",
    "EquipoResult",
    "InscripcionDetalleResult",
    "InscripcionInicialResult",
    "PromocionResult",
]
