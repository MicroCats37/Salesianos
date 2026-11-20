"""Result objects del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.6 · §3.C

Un *result* es el DTO interno que el orquestador devuelve al controlador. Los
presenters los transforman en schemas HTTP; los presenters nunca consultan la
base de datos.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from modules.pagos.domain.schemas.pago_schemas import LineaIntentoData


class EstadoOperativoResult(BaseModel):
    """Veredicto operativo del pago: la respuesta única a «¿está pagado?».

    Es el ÚNICO veredicto que publica el backend (FR-01 §5). El frontend nunca
    lo deriva cruzando `Compra.estado`, `OrdenPago.estado` y las banderas del
    proveedor.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    codigo: str = Field(..., description="Código estable del veredicto.")
    etiqueta: str = Field(..., description="Etiqueta corta en español.")
    descripcion: str = Field(
        ...,
        description="Una línea con la causa y el siguiente paso seguro.",
    )


class EstadoActivacionResult(BaseModel):
    """El veredicto de la ACTIVACIÓN de derechos de una compra pagada.

    Es un canal **SEPARADO** del veredicto operativo: el veredicto operativo
    responde «¿está pagado esto?» y este responde «¿está habilitado el
    derecho?». Los dos los publica `pagos`, su único dueño (FR-01 §5,
    FR-04 §6).

    El vocabulario de `EstadoOperativoPago` NO se amplía ni se renumera: la
    garantía de FND-04 (`PAGADA` tras una confirmación correcta) se mantiene
    intacta y la incidencia de activación viaja en su propio canal.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

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


class ItemReconciliacion(BaseModel):
    """Una orden revisada por la conciliación de activaciones."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    orden_pago_id: str = Field(..., description="Identificador de la orden.")
    referencia: str = Field(..., description="Referencia visible de la orden.")
    estado_orden: str = Field(..., description="Estado de la orden de pago.")
    estado_activacion: str = Field(
        ...,
        description="Veredicto de activación ANTES de la conciliación.",
    )
    codigo: str = Field(
        ...,
        description="Código de máquina del resultado del reintento.",
    )
    proxima_accion: str = Field(
        default="",
        description="La acción segura que sigue.",
    )
    recuperable: bool = Field(
        default=False,
        description="Si la incidencia admite un reintento seguro.",
    )
    aplicada: bool = Field(
        default=False,
        description="Si se intentó el reintento de la activación.",
    )


class ResultadoReconciliacion(BaseModel):
    """El informe de una pasada de conciliación de activaciones.

    Es un informe, no una mutación: la conciliación **no** toca el estado de
    la orden ni el de la compra. Sólo pide al coordinador que reintente la
    activación, y el reintento es seguro (converge) (FR-04 I-2, RN-C08).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    revisadas: int = Field(default=0, description="Órdenes confirmadas revisadas.")
    con_incidencia: int = Field(
        default=0,
        description="Órdenes cuya activación no estaba resuelta.",
    )
    recuperadas: int = Field(
        default=0,
        description="Órdenes cuyo derecho quedó habilitado en esta pasada.",
    )
    pendientes: int = Field(
        default=0,
        description="Órdenes que siguen con la activación sin resolver.",
    )
    items: list[ItemReconciliacion] = Field(
        default_factory=list,
        description="El detalle por orden.",
    )


class IntentoPagoResult(BaseModel):
    """Un intento de pago, con su posición y su evidencia de verificación."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(..., description="Identificador del intento.")
    intento: int = Field(..., description="Posición del intento dentro de su orden.")
    referencia_proveedor: str = Field(
        ...,
        description="Referencia técnica del intento (detalle técnico autorizado).",
    )
    estado: str = Field(..., description="Estado del intento.")
    verificada: bool = Field(
        default=False,
        description="Si la confirmación fue firmada y verificada en servidor.",
    )
    codigo_respuesta: str = Field(default="", description="Código de respuesta.")
    metodo_pago: str = Field(default="", description="Método de pago informado.")
    creada_en: datetime = Field(..., description="Instante de creación del intento.")


class OrdenPagoResult(BaseModel):
    """Estado de una orden de pago, con su veredicto y su historial de intentos."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(..., description="Identificador de la orden.")
    referencia: str = Field(..., description="Referencia visible del proveedor.")
    estado: str = Field(..., description="Estado de la orden.")
    monto: Decimal = Field(..., description="Monto congelado de la orden.")
    moneda: str = Field(..., description="Código ISO-4217 del monto.")
    pagada_en: datetime | None = Field(
        default=None,
        description="Instante del pago. Nulo = aún no se pagó.",
    )
    creada_en: datetime = Field(..., description="Instante de creación de la orden.")
    estado_operativo: EstadoOperativoResult = Field(
        ...,
        description="Veredicto operativo del pago.",
    )
    estado_activacion: EstadoActivacionResult | None = Field(
        default=None,
        description=(
            "Veredicto de la activación de derechos. Es un canal SEPARADO del "
            "veredicto operativo (FR-04 §6)."
        ),
    )
    intentos: list[LineaIntentoData] = Field(
        default_factory=list,
        description="Historial de intentos contra el proveedor.",
    )
    origen_pago: str = Field(
        ...,
        description="Procedencia de la evidencia de pago.",
    )


class PagoConfirmadoResult(BaseModel):
    """Resultado de confirmar un pago.

    `ya_confirmado` dice si esta llamada fue la que confirmó el pago o si
    encontró el pago ya confirmado (notificación duplicada o tardía). En ambos
    casos el resultado es el mismo: **una sola confirmación efectiva por
    orden** (FR-04 I-1).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    orden_pago_id: str = Field(..., description="Identificador de la orden.")
    referencia: str = Field(..., description="Referencia visible del proveedor.")
    estado_orden: str = Field(..., description="Estado de la orden tras confirmar.")
    estado_operativo: EstadoOperativoResult = Field(
        ...,
        description="Veredicto operativo del pago.",
    )
    estado_activacion: EstadoActivacionResult | None = Field(
        default=None,
        description=(
            "Veredicto de la activación de derechos. Es un canal SEPARADO del "
            "veredicto operativo (FR-04 §6)."
        ),
    )
    ya_confirmado: bool = Field(
        default=False,
        description="Si el pago ya estaba confirmado antes de esta llamada.",
    )
    transaccion_id: str | None = Field(
        default=None,
        description="Identificador del intento que sustenta la confirmación.",
    )
    monto: Decimal = Field(..., description="Monto confirmado.")
    moneda: str = Field(..., description="Código ISO-4217 del monto.")
    pagada_en: datetime | None = Field(
        default=None,
        description="Instante del pago.",
    )


__all__ = [
    "EstadoActivacionResult",
    "EstadoOperativoResult",
    "IntentoPagoResult",
    "ItemReconciliacion",
    "OrdenPagoResult",
    "PagoConfirmadoResult",
    "ResultadoReconciliacion",
]
