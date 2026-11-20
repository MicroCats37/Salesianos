"""Contrato HTTP del módulo `pagos`.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`
Contract: `contract/SCHEMA_DRY_INTENTION.md` (composición) ·
          `contract/api-wrapper-presenter-contract.md` §2, §7 ·
          `contract/PLAN_REFACTORIZACION.md` §C

Composición de los TRES bloques (SCHEMA_DRY_INTENTION):

| Bloque | Contenido | Clase |
|---|---|---|
| Identidad | ids + marcas de tiempo | `PagoIdentidadOut` |
| General | lo compartido por las salidas de pago | `PagoGeneralOut` |
| Específico | lo que varía por caso de uso | `PagoConfirmadoEspecificaOut` · `OrdenPagoEspecificaOut` |

Todos heredan de `core.types.BaseSchema` (`contract/PLAN_REFACTORIZACION.md`
§C). El espejo Zod 1:1 del frontend es responsabilidad de A7 (FR-07 §1.1);
este lado NO declara `z.any()` ni campos genéricos.

Reglas de seguridad que este contrato respeta:

- `referencia_proveedor` (la identidad técnica del intento) **NO** viaja en
  ninguna salida pública: es dato técnico y sólo se expone en detalle técnico
  autorizado (FR-04 §1.3, `contratos/03` §8).
- La clave de idempotencia viaja en el **header** `Idempotency-Key`, nunca en
  el cuerpo (FR-04 §2.2).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasChoices, Field

from core.types import BaseSchema


# ── Bloque de identidad ─────────────────────────────────────────────────────


class PagoIdentidadOut(BaseSchema):
    """Bloque de identidad: identificadores y marcas de tiempo."""

    orden_pago_id: UUID = Field(..., description="Identificador de la orden de pago.")
    transaccion_id: UUID | None = Field(
        default=None,
        description="Identificador del intento que sustenta la confirmación.",
    )
    pagada_en: datetime | None = Field(
        default=None,
        description="Instante del pago. Nulo = todavía no se pagó.",
    )


# ── Bloque general ──────────────────────────────────────────────────────────


class PagoGeneralOut(BaseSchema):
    """Bloque general: la referencia visible y el estado de la orden."""

    referencia: str = Field(
        ...,
        description="Referencia visible de la orden. Nunca es un secreto.",
    )
    estado_orden: str = Field(
        ...,
        description=(
            "Estado de la orden (PENDIENTE, EN_VERIFICACION, CONFIRMADA, "
            "FALLIDA, VENCIDA)."
        ),
    )


# ── Bloque específico ───────────────────────────────────────────────────────


class EstadoOperativoOut(BaseSchema):
    """Veredicto operativo del pago.

    Es el ÚNICO veredicto que publica el backend (FR-01 §5). El cliente nunca
    lo deriva cruzando por su cuenta los estados hermanos.
    """

    codigo: str = Field(..., description="Código estable del veredicto.")
    etiqueta: str = Field(..., description="Etiqueta corta en español.")
    descripcion: str = Field(
        ...,
        description="Una línea con la causa y el siguiente paso seguro.",
    )


class EstadoActivacionOut(BaseSchema):
    """Veredicto de la activación de derechos de la compra.

    Es un canal **SEPARADO** del veredicto operativo: el veredicto operativo
    responde «¿está pagado esto?» y este responde «¿está habilitado el
    derecho?». Los dos los calcula y los publica `pagos`, su único dueño
    (FR-01 §5, FR-04 §6).

    El vocabulario del veredicto operativo NO se amplía: la garantía de
    FND-04 (`PAGADA` tras una confirmación correcta) se mantiene intacta y la
    incidencia de activación viaja aquí (RN-C08).
    """

    codigo: str = Field(..., description="Código estable del veredicto.")
    etiqueta: str = Field(..., description="Etiqueta corta en español.")
    descripcion: str = Field(
        ...,
        description="Una línea con la causa y el siguiente paso seguro.",
    )
    recuperable: bool = Field(
        default=False,
        description="Si la incidencia admite un reintento seguro.",
    )
    proxima_accion: str = Field(
        default="",
        description="La acción segura que sigue (REINTENTAR_ACTIVACION, …).",
    )


class PagoConfirmadoEspecificaOut(BaseSchema):
    """Bloque específico de la confirmación de un pago."""

    estado_operativo: EstadoOperativoOut = Field(
        ...,
        description="Veredicto operativo del pago.",
    )
    estado_activacion: EstadoActivacionOut | None = Field(
        default=None,
        description=(
            "Veredicto de la activación de derechos. Es un canal SEPARADO del "
            "veredicto operativo (FR-04 §6)."
        ),
    )
    ya_confirmado: bool = Field(
        ...,
        description=(
            "Si el pago ya estaba confirmado antes de esta llamada "
            "(notificación duplicada o tardía)."
        ),
    )
    monto: Decimal = Field(..., description="Monto confirmado.")
    moneda: str = Field(..., description="Código ISO-4217 del monto.")


class IntentoPagoOut(BaseSchema):
    """Un intento de pago en su forma pública.

    `referencia_proveedor` no viaja: es detalle técnico autorizado
    (FR-04 §1.3).
    """

    id: UUID = Field(..., description="Identificador del intento.")
    intento: int = Field(..., description="Posición del intento en su orden.")
    estado: str = Field(
        ...,
        description="Estado del intento (PENDIENTE, EXITO, FALLIDO, CANCELADO).",
    )
    verificada: bool = Field(
        ...,
        description="Si la confirmación fue firmada y verificada en servidor.",
    )
    codigo_respuesta: str = Field(default="", description="Código de respuesta.")
    metodo_pago: str = Field(default="", description="Método de pago informado.")
    creada_en: datetime = Field(..., description="Instante de creación del intento.")


class OrdenPagoEspecificaOut(BaseSchema):
    """Bloque específico de la lectura de una orden."""

    estado_operativo: EstadoOperativoOut = Field(
        ...,
        description="Veredicto operativo del pago.",
    )
    estado_activacion: EstadoActivacionOut | None = Field(
        default=None,
        description=(
            "Veredicto de la activación de derechos. Es un canal SEPARADO del "
            "veredicto operativo (FR-04 §6)."
        ),
    )
    origen_pago: str = Field(
        ...,
        description="Procedencia de la evidencia (IZIPAY, MANUAL, SIN_PAGO).",
    )
    monto: Decimal = Field(..., description="Monto congelado de la orden.")
    moneda: str = Field(..., description="Código ISO-4217 del monto.")
    intentos: list[IntentoPagoOut] = Field(
        default_factory=list,
        description="Historial de intentos contra el proveedor.",
    )


# ── Wrappers compuestos ─────────────────────────────────────────────────────


class PagoConfirmadoOut(PagoIdentidadOut, PagoGeneralOut, PagoConfirmadoEspecificaOut):
    """Salida de la confirmación de un pago. Composición de los tres bloques."""


class OrdenPagoOut(BaseSchema):
    """Salida de la lectura de una orden de pago.

    Se compone del bloque IDENTIDAD (ids y marcas de tiempo), del bloque
    GENERAL (referencia y estado) y del bloque ESPECÍFICO (veredicto,
    evidencia e intentos).
    """

    id: UUID = Field(..., description="Identificador de la orden.")
    referencia: str = Field(..., description="Referencia visible de la orden.")
    estado: str = Field(..., description="Estado de la orden.")
    creada_en: datetime = Field(..., description="Instante de creación de la orden.")
    pagada_en: datetime | None = Field(
        default=None,
        description="Instante del pago. Nulo = todavía no se pagó.",
    )
    estado_operativo: EstadoOperativoOut = Field(
        ...,
        description="Veredicto operativo del pago.",
    )
    estado_activacion: EstadoActivacionOut | None = Field(
        default=None,
        description=(
            "Veredicto de la activación de derechos. Es un canal SEPARADO del "
            "veredicto operativo (FR-04 §6)."
        ),
    )
    origen_pago: str = Field(
        ...,
        description="Procedencia de la evidencia (IZIPAY, MANUAL, SIN_PAGO).",
    )
    monto: Decimal = Field(..., description="Monto congelado de la orden.")
    moneda: str = Field(..., description="Código ISO-4217 del monto.")
    intentos: list[IntentoPagoOut] = Field(
        default_factory=list,
        description="Historial de intentos contra el proveedor.",
    )


# ── Schema de entrada ───────────────────────────────────────────────────────


class ConfirmarPagoIn(BaseSchema):
    """Cuerpo de la confirmación que reenvía el SDK del navegador.

    Acepta los nombres del proveedor (`camelCase`) y los del backend
    (`snake_case`): el espejo Zod del frontend declara una forma, el proveedor
    entrega la otra.

    `payload_http` es el texto **crudo** firmado por el proveedor: es lo que
    se verifica contra la clave del comercio. No se re-serializa nunca.
    """

    model_config = {
        **BaseSchema.model_config,
        "populate_by_name": True,
    }

    kr_answer: dict | None = Field(
        default=None,
        description="Payload íntegro que entrega el SDK de Izipay.",
    )
    transaction_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("transaction_id", "transactionId"),
        max_length=100,
        description="Identificador del intento según el proveedor.",
    )
    code: str | None = Field(
        default=None,
        max_length=32,
        description="Código de respuesta del proveedor.",
    )
    message: str | None = Field(
        default=None,
        max_length=255,
        description="Mensaje de respuesta del proveedor.",
    )
    order_number: str | None = Field(
        default=None,
        validation_alias=AliasChoices("order_number", "orderNumber"),
        max_length=100,
        description="Referencia de orden según el proveedor.",
    )
    amount: str | None = Field(
        default=None,
        max_length=32,
        description="Monto según el proveedor.",
    )
    currency: str | None = Field(
        default=None,
        max_length=3,
        description="Moneda según el proveedor.",
    )
    signature: str | None = Field(
        default=None,
        max_length=512,
        description="Firma del proveedor sobre el payload crudo.",
    )
    payload_http: str | None = Field(
        default=None,
        validation_alias=AliasChoices("payload_http", "payloadHttp"),
        description="Payload crudo y firmado por el proveedor.",
    )
    response: dict | None = Field(
        default=None,
        description="Bloque `response` del proveedor, si lo entrega.",
    )


__all__ = [
    "ConfirmarPagoIn",
    "EstadoActivacionOut",
    "EstadoOperativoOut",
    "IntentoPagoOut",
    "OrdenPagoEspecificaOut",
    "OrdenPagoOut",
    "PagoConfirmadoEspecificaOut",
    "PagoConfirmadoOut",
    "PagoGeneralOut",
    "PagoIdentidadOut",
]
