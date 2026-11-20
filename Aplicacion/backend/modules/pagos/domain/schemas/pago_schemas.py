"""DTOs internos del módulo `pagos`.

Contract: `contract/django-app-architecture-contract.md` §4.6

Son DTOs de Pydantic **puros** (no schemas HTTP): viajan entre el dominio, los
puertos y la capa de presentación. Los schemas HTTP viven en
`presentation/schemas/`.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class EstadoCompraOrdenPago(BaseModel):
    """Estado comercial de la compra que financia una orden de pago.

    Lo devuelve el puerto `IEstadoCompraOrdenPagoService`. `existe=False`
    significa que ninguna compra financia la orden: el consumidor decide qué
    significa eso para su propia regla.

    El puerto expone **banderas**, no el vocabulario crudo del estado de la
    compra: `pagos` no necesita conocer los valores de `commerce` y el
    grafo de módulos queda desacoplado también en los datos.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    existe: bool = Field(..., description="Si hay una compra que financia la orden.")
    pagada: bool = Field(
        default=False,
        description="Si la compra consta como pagada.",
    )
    cancelada: bool = Field(
        default=False,
        description="Si la compra está cancelada.",
    )


class MarcaCompraPagadaResult(BaseModel):
    """Resultado de marcar la compra de una orden como pagada."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    existe: bool = Field(..., description="Si había una compra que marcar.")
    pagada: bool = Field(
        default=False,
        description="Si la compra consta como pagada tras la marca.",
    )
    ya_pagada: bool = Field(
        default=False,
        description="Si la compra ya estaba pagada (marca idempotente).",
    )


class EvidenciaPagoData(BaseModel):
    """Evidencia pública de un pago confirmado.

    Deliberadamente **no** contiene el payload firmado, la firma, el token de
    sesión ni ninguna credencial: sólo los hechos que el operador necesita
    para auditar (canal, código de respuesta, fecha y método de pago).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    canal: str = Field(..., description="Canal por el que llegó la confirmación.")
    verificada: bool = Field(
        default=False,
        description="Si la firma del proveedor fue verificada en servidor.",
    )
    codigo_respuesta: str = Field(
        default="",
        description="Código de respuesta del proveedor.",
    )
    mensaje_respuesta: str = Field(
        default="",
        description="Mensaje de respuesta del proveedor (texto público).",
    )
    metodo_pago: str = Field(default="", description="Método de pago informado.")
    fecha: datetime | None = Field(
        default=None,
        description="Instante en que se registró la evidencia.",
    )


class LineaIntentoData(BaseModel):
    """Datos de un intento de pago tal como se exponen al lector.

    `referencia_proveedor` **no** viaja aquí: es dato técnico y sólo se
    expone en detalle técnico autorizado (FR-04 §1.3).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: str = Field(..., description="Identificador del intento.")
    intento: int = Field(..., description="Posición del intento dentro de su orden.")
    estado: str = Field(..., description="Estado del intento.")
    verificada: bool = Field(
        default=False,
        description="Si la confirmación fue firmada y verificada en servidor.",
    )
    codigo_respuesta: str = Field(default="", description="Código de respuesta.")
    metodo_pago: str = Field(default="", description="Método de pago informado.")
    creada_en: datetime = Field(..., description="Instante de creación del intento.")


class TotalOrdenData(BaseModel):
    """Total monetario de una orden, en forma segura de comparar."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    monto: Decimal = Field(..., description="Monto congelado de la orden.")
    moneda: str = Field(..., description="Código ISO-4217 del monto.")


class EstadoActivacionCompraData(BaseModel):
    """El estado de la activación de derechos de la compra que financia la orden.

    Lo devuelve el puerto `IActivacionCompraService.estado_activacion`.

    Expone **BANDERAS**, no el vocabulario crudo del dominio de activación:
    `pagos` no necesita conocer los valores de `commerce` y el grafo de
    módulos queda desacoplado también en los datos (igual que
    `EstadoCompraOrdenPago`).

    `incidencia_codigo` es un **código de máquina seguro** (`[A-Z0-9_]`), nunca
    el texto de una excepción ni un payload (FR-04 §4, RN-C08).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    existe: bool = Field(
        ...,
        description="Si hay una activación registrada para la compra.",
    )
    activada: bool = Field(
        default=False,
        description="Si el derecho quedó habilitado (terminal).",
    )
    pendiente: bool = Field(
        default=False,
        description="Si la activación está registrada y aún no se resolvió.",
    )
    fallida: bool = Field(
        default=False,
        description="Si el último intento de activación falló (recuperable).",
    )
    en_curso: bool = Field(
        default=False,
        description="Si hay un intento de activación reservado.",
    )
    recuperable: bool = Field(
        default=False,
        description="Si la incidencia admite un reintento seguro.",
    )
    intentos: int = Field(
        default=0,
        description="Número de intentos de activación Consumidos.",
    )
    incidencia_codigo: str = Field(
        default="",
        description="Código de máquina de la incidencia, si la hay.",
    )
    proxima_accion: str = Field(
        default="",
        description="La acción segura que sigue (REINTENTAR_ACTIVACION, …).",
    )


class ContextoNotificacionCompra(BaseModel):
    """Los hechos congelados que se entregan al notificador del comprador.

    No lleva reglas, plantillas, destinos ni credenciales: sólo los hechos
    públicos de la compra. El **proveedor** es un puerto sin implementación
    hasta que `PD-08` se ratifique, así que nada de esto se envía todavía.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    orden_pago_id: str = Field(..., description="Identificador de la orden pagada.")
    persona_id: str | None = Field(
        default=None,
        description="Identificador de la persona compradora, si la hay.",
    )
    referencia: str = Field(
        default="",
        description="Referencia visible de la orden. Nunca un secreto.",
    )
    total: Decimal | None = Field(
        default=None,
        description="Monto congelado de la compra.",
    )
    moneda: str = Field(default="", description="Código ISO-4217 del monto.")


class ResultadoNotificacion(BaseModel):
    """El resultado de intentar notificar al comprador.

    `omitida=True` significa que **no se intentó enviar**: el proveedor no
    está configurado (`PD-08` abierto). `enviada=False` con `omitida=False`
    significa que se intentó y falló. En los dos casos el pago confirmado se
    conserva: la notificación NUNCA revierte una compra (RN-C08).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    enviada: bool = Field(
        default=False,
        description="Si la notificación se envió.",
    )
    omitida: bool = Field(
        default=False,
        description="Si no se intentó enviar (proveedor no configurado).",
    )
    recuperable: bool = Field(
        default=False,
        description="Si el intento admite un reintento.",
    )
    codigo: str = Field(
        default="",
        description="Código de máquina del resultado.",
    )
    intentos: int = Field(
        default=0,
        description="Número de intentos de notificación consumidos.",
    )


class ResultadoActivacionCompra(BaseModel):
    """El resultado de pedir la activación de los derechos de una compra.

    Lo devuelve el puerto `IActivacionCompraService`. `pagos` lo necesita
    porque es el módulo que declara el pago confirmado: el derecho es un
    hecho POSTERIOR y separado (RN-C08), y el coordinador lo resuelve una
    sola vez por `(compra, origen)`.

    El puerto expone **banderas y códigos**, nunca identificadores internos
    ni mensajes de excepción: el resultado es un hecho público.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    existe: bool = Field(..., description="Si hay una compra que financia la orden.")
    activada: bool = Field(
        default=False,
        description="Si el derecho quedó habilitado.",
    )
    ya_activada: bool = Field(
        default=False,
        description="Si el derecho ya estaba habilitado (repetición idempotente).",
    )
    en_curso: bool = Field(
        default=False,
        description="Si otro intento tiene la activación reservada.",
    )
    recuperable: bool = Field(
        default=False,
        description=(
            "Si la activación quedó pendiente por una incidencia reintentable "
            "sin perder el pago confirmado (RN-C08)."
        ),
    )
    intentos: int = Field(
        default=0,
        description="Cuántos intentos de activación lleva la compra.",
    )
    codigo: str = Field(
        default="",
        max_length=64,
        description="Código de máquina del resultado de la activación.",
    )
    proxima_accion: str = Field(
        default="NINGUNA",
        max_length=40,
        description=(
            "La acción segura que sigue: `NINGUNA`, `REINTENTAR_ACTIVACION` "
            "o `ESPERAR_ACTIVACION`."
        ),
    )


__all__ = [
    "ContextoNotificacionCompra",
    "EvidenciaPagoData",
    "EstadoActivacionCompraData",
    "EstadoCompraOrdenPago",
    "LineaIntentoData",
    "MarcaCompraPagadaResult",
    "ResultadoActivacionCompra",
    "ResultadoNotificacion",
    "TotalOrdenData",
]
