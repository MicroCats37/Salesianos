"""El contrato HTTP de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/api-wrapper-presenter-contract.md` §2, §5 ·
          `contract/SCHEMA_DRY_INTENTION.md` (composición de bloques)

Ledger: `RT-RT-01` (`TicketPreviewPresenter` → `TicketPreviewOut`) ·
        `RT-RT-02` (`TicketConfirmPresenter` → `TicketConfirmadoOut`).

Los wrappers se COMPONEN con los tres bloques conceptuales:

- **Identidad** — el identificador y las marcas de tiempo.
- **General** — la familia a la que pertenece (la edición).
- **Específico** — lo propio de cada caso de uso.

La FORMA está CONGELADA en `FR-05` §3.1 y §3.2: los wrappers reproducen
exactamente esos campos, ni uno más ni uno menos. No hay `z.any()`, ni campos
genéricos, ni campos de otros dominios.

**LA CREDENCIAL NO SE DEVUELVE.** El `codigo` que el operador escanea es un
secreto: viaja en la petición y NUNCA en la respuesta (`RN-P06`).
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from core.types import BaseSchema


# ── Bloque de identidad ───────────────────────────────────────────────────────


class TicketTitularOut(BaseSchema):
    """La persona que sostiene el derecho."""

    persona_id: UUID = Field(..., description="Identificador de la persona.")
    nombre: str = Field(..., description="Nombre de la persona.")


class TicketActorOut(BaseSchema):
    """La cuenta que opera la validación."""

    usuario_id: UUID | None = Field(
        default=None, description="Cuenta que operó la validación."
    )
    persona_id: UUID | None = Field(
        default=None, description="Persona de la cuenta que operó."
    )


class TicketIdentidadOut(BaseSchema):
    """El bloque de identidad de un canje confirmado."""

    validacion_id: UUID = Field(
        ..., description="Identificador del acta de validación."
    )
    consumido_en: datetime = Field(..., description="Momento del consumo.")


# ── Bloque general ───────────────────────────────────────────────────────────


class TicketGeneralOut(BaseSchema):
    """El bloque general: la edición a la que pertenece el derecho."""

    edicion_id: UUID = Field(..., description="Edición del alcance.")


# ── Bloque específico ────────────────────────────────────────────────────────


class TicketEspecificoOut(BaseSchema):
    """El bloque específico: el estado del derecho."""

    tipo_derecho: str = Field(
        ...,
        description="El discriminante del módulo dueño: `PASE`, `ENTRADA_CORTESIA` o `PRODUCTO`.",
    )
    codigo: str = Field(
        ...,
        description="El código del CONCEPTO de derecho. Nunca un identificador interno.",
    )
    estado: str = Field(..., description="El estado del derecho, según su módulo dueño.")
    cantidad_total: int = Field(..., ge=0, description="Unidades que concede el derecho.")
    cantidad_disponible: int = Field(
        ..., ge=0, description="Unidades todavía canjeables."
    )
    cantidad_consumida: int = Field(..., ge=0, description="Unidades ya canjeadas.")
    puede_canjear: bool = Field(
        ..., description="Si el derecho se puede canjear. Lo calcula el módulo dueño."
    )
    motivo_codigo: str | None = Field(
        default=None, description="Código estable del motivo. Presente si NO se puede canjear."
    )
    motivo_mensaje: str | None = Field(
        default=None, description="Motivo público y seguro. Presente si NO se puede canjear."
    )


# ── Wrappers ─────────────────────────────────────────────────────────────────


class TicketPreviewOut(TicketGeneralOut, TicketEspecificoOut):
    """La vista previa de una credencial (`RT-RT-01`).

    Es la forma congelada de `FR-05` §3.1: la comprobación NO consume y NO
    escribe nada (`RN-P06`).
    """

    titular: TicketTitularOut = Field(..., description="La persona del derecho.")


class TicketConfirmadoOut(BaseSchema):
    """El canje confirmado de una credencial (`RT-RT-02`).

    Es la forma congelada de `FR-05` §3.2.
    """

    validacion_id: UUID = Field(..., description="Identificador del acta de validación.")
    tipo_derecho: str = Field(
        ..., description="El discriminante del módulo dueño del derecho."
    )
    cantidad_consumida: int = Field(..., ge=1, description="Unidades consumidas.")
    cantidad_restante: int = Field(..., ge=0, description="Unidades que quedan.")
    estado: str = Field(..., description="El estado del canje.")
    consumido_en: datetime = Field(..., description="Momento del consumo.")
    actor: TicketActorOut = Field(..., description="Quien operó la validación.")
    repetido: bool = Field(
        ...,
        description=(
            "Si la operación es la REPETICIÓN idempotente de una ejecución "
            "previa. No es un error: la repetición devuelve el mismo dato."
        ),
    )


# ── Entradas ─────────────────────────────────────────────────────────────────


class PreviewTicketIn(BaseSchema):
    """La petición de una vista previa.

    La credencial viaja en el cuerpo: es un secreto y no se registra.
    """

    codigo: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="La credencial que se escanea o se teclea.",
    )


class ConfirmarTicketIn(BaseSchema):
    """La petición de una confirmación.

    `idempotency_key` es OBLIGATORIA: identifica UNA intención (`FR-04`
    §2.2). `cantidad` es la cantidad que el operador pide consumir; si no se
    declara, se consume todo lo disponible.
    """

    codigo: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="La credencial que se escanea o se teclea.",
    )
    idempotency_key: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Clave de idempotencia de la operación.",
    )
    cantidad: int | None = Field(
        default=None,
        ge=1,
        description="Unidades a consumir. Vacío significa todo lo disponible.",
    )


__all__ = [
    "ConfirmarTicketIn",
    "PreviewTicketIn",
    "TicketActorOut",
    "TicketConfirmadoOut",
    "TicketEspecificoOut",
    "TicketGeneralOut",
    "TicketIdentidadOut",
    "TicketPreviewOut",
    "TicketTitularOut",
]
