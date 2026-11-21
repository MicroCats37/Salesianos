"""Los esquemas HTTP de los comandos ADMINISTRATIVOS asistidos.

Change: `admin-client-purchases-and-participants`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §7, §8 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición sobre herencia) ·
          `contract/PLAN_REFACTORIZACION.md` §1.C (`BaseSchema`)

## La COMPOSICIÓN de los schemas

No hay un schema monolítico por endpoint: los bloques se ensamblan.

| Bloque | Qué aporta | Dónde se usa |
|---|---|---|
| `IdentidadCivilIn` | el documento y, si la persona no existe, sus nombres, apellidos y género (general) | los TRES comandos |
| `ClienteCompraIn` | la identidad civil del cliente y su correo de contacto (general) | las dos compras asistidas |
| `EvidenciaPagoManualIn` | el canal, la referencia y el motivo del pago (general) | las dos compras asistidas |
| `ItemPedidoClienteIn` | un artículo del pedido (específico) | la compra de tienda |
| `AgregarParticipanteEquipoIn` | el rol y el motivo (específico) | el alta de participante |
| `CompraAsistidaOut` | los identificadores y los hechos del resultado (identidad) | las dos compras asistidas |

El frontend refleja estos schemas 1:1 en sus esquemas Zod: sin `z.any()` y
sin campo genérico (`contract/api-wrapper-presenter-contract.md` §7).

## La IDENTIDAD es un BLOQUE, no un campo suelto

Un comando administrativo puede declarar una persona que todavía NO está en
el padrón. Por eso la identidad viaja como un bloque completo: el documento
la DECLARA y los nombres, los apellidos y el género permiten REGISTRARLA.

Cuando la identidad YA existe, el servidor la REUTILIZA y no reescribe sus
nombres: por eso los tres campos son OPCIONALES aquí.
"""

from typing import Literal, Optional
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


# ── Bloques generales ───────────────────────────────────────────────────────


class IdentidadCivilIn(BaseSchema):
    """La identidad CIVIL que declara el administrador.

    El documento NO es una credencial (`RN-U04`): declara QUIÉN es la
    persona, nunca QUÉ puede hacer.

    `nombres`, `apellidos` y `genero` son OPCIONALES porque sólo hacen falta
    cuando la persona todavía NO está en el padrón: en ese caso el servidor la
    REGISTRA como identidad civil **sin cuenta**. Cuando ya existe, el
    servidor REUTILIZA la `Persona` del padrón y no reescribe sus nombres.
    """

    tipo_documento: str = Field(
        ...,
        max_length=3,
        description="Tipo de documento de la persona.",
    )
    numero_documento: str = Field(
        ...,
        max_length=20,
        description="Número de documento de la persona.",
    )
    nombres: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Nombres. Sólo se usan si la persona se registra.",
    )
    apellidos: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Apellidos. Sólo se usan si la persona se registra.",
    )
    genero: Optional[Literal["M", "F"]] = Field(
        default=None,
        description=(
            "Género de la persona. Lo exige la elegibilidad de una disciplina "
            "que no es mixta."
        ),
    )


class ClienteCompraIn(IdentidadCivilIn):
    """La identidad CIVIL del cliente de una compra asistida.

    El servidor resuelve esa identidad en el padrón y la registra si no
    existía. El correo es un dato de contacto: NO habilita ningún derecho y
    NO se guarda en la `Persona`.
    """

    contacto_email: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Correo de contacto. No habilita ningún derecho.",
    )


class EvidenciaPagoManualIn(BaseSchema):
    """La EVIDENCIA del pago externo que registra el administrador.

    Es la misma evidencia que exige la aprobación manual del pago: un canal,
    una referencia que lo prueba y un motivo auditado. La liquidación la
    aplica el dueño del pago; este schema sólo declara los hechos.
    """

    canal: str = Field(
        ...,
        max_length=32,
        description="Canal del pago externo.",
    )
    referencia: str = Field(
        ...,
        max_length=100,
        description="Referencia, recibo u operación que prueba el pago.",
    )
    motivo: str = Field(
        ...,
        max_length=1000,
        description="Motivo auditado del registro del pago.",
    )


# ── Bloques específicos ─────────────────────────────────────────────────────


class AgregarParticipanteEquipoIn(IdentidadCivilIn):
    """El comando de agregar una persona a un equipo.

    La persona se identifica por DOCUMENTO EXACTO. Si ya está en el padrón se
    REUTILIZA; si no, se REGISTRA como identidad civil **sin cuenta** y recién
    después se la agrega al equipo. La UI administrativa no expone un CRUD
    de `Persona`: no la borra ni la reescribe nunca.
    """

    rol: str = Field(
        default="JUGADOR",
        max_length=16,
        description="Rol de la persona en el equipo.",
    )
    motivo: str = Field(
        ...,
        max_length=1000,
        description="Motivo auditado del alta.",
    )


class ItemPedidoClienteIn(BaseSchema):
    """Un artículo del pedido de tienda que se compra para el cliente."""

    tipo: str = Field(
        default="PRODUCTO",
        max_length=16,
        description="Tipo de concepto pedido.",
    )
    producto_id: UUID = Field(..., description="Identificador del producto.")
    cantidad: int = Field(..., gt=0, description="Cantidad pedida.")


class ComprarPaseClienteIn(BaseSchema):
    """El comando de comprar un lote de pases PARA un cliente."""

    pase_id: UUID = Field(..., description="Pase del catálogo que se compra.")
    cantidad: int = Field(
        ...,
        gt=0,
        description="Número de pases que se compran.",
    )
    cliente: ClienteCompraIn = Field(..., description="Identidad del cliente.")
    evidencia: EvidenciaPagoManualIn = Field(
        ...,
        description="Evidencia del pago externo que se registra.",
    )


class ComprarPedidoClienteIn(BaseSchema):
    """El comando de comprar un pedido de tienda PARA un cliente."""

    items: list[ItemPedidoClienteIn] = Field(
        ...,
        min_length=1,
        description="Artículos del pedido.",
    )
    cliente: ClienteCompraIn = Field(..., description="Identidad del cliente.")
    evidencia: EvidenciaPagoManualIn = Field(
        ...,
        description="Evidencia del pago externo que se registra.",
    )


# ── Bloque de identidad ─────────────────────────────────────────────────────


class ParticipanteAsistidoOut(BaseSchema):
    """La participación que la administración acaba de dar de alta."""

    participacion_id: str = Field(..., description="Identificador de la participación.")
    persona_id: str = Field(..., description="Identificador de la persona.")
    nombre: str = Field(..., description="Nombre legible de la persona.")
    documento: str = Field(..., description="Número de documento de la persona.")
    equipo_id: str = Field(..., description="Equipo al que pertenece.")
    inscripcion_id: str = Field(..., description="Inscripción a la que pertenece.")
    rol: str = Field(..., description="Rol de la persona en el equipo.")
    estado: str = Field(..., description="Estado de la participación.")


class CompraAsistidaOut(BaseSchema):
    """La compra asistida que la administración acaba de crear y liquidar.

    `comprador_persona_id` y `comprador_nombre` son el CLIENTE: el
    administrador es el actor de la operación y no el dueño de la compra.
    """

    compra_id: str = Field(..., description="Identificador de la compra de `commerce`.")
    recurso_id: str = Field(
        ...,
        description="Identificador del lote de pases o del pedido.",
    )
    orden_pago_id: str = Field(..., description="Orden de pago que financia la compra.")
    tipo: str = Field(..., description="PASE o PEDIDO.")
    concepto: str = Field(..., description="Concepto de lo comprado.")
    total: str = Field(..., description="Total congelado por el servidor.")
    moneda: str = Field(..., description="Moneda del total.")
    estado: str = Field(..., description="Estado del lote o del pedido.")
    estado_pago: str = Field(..., description="Veredicto del pago tras el registro.")
    comprador_persona_id: str = Field(..., description="Persona compradora.")
    comprador_nombre: str = Field(..., description="Nombre del comprador.")
    cantidad: int = Field(..., ge=1, description="Unidades compradas.")


__all__ = [
    "AgregarParticipanteEquipoIn",
    "ClienteCompraIn",
    "CompraAsistidaOut",
    "ComprarPaseClienteIn",
    "ComprarPedidoClienteIn",
    "EvidenciaPagoManualIn",
    "IdentidadCivilIn",
    "ItemPedidoClienteIn",
    "ParticipanteAsistidoOut",
]
