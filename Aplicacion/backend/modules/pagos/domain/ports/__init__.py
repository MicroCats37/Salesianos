"""Puertos (interfaces) del módulo `pagos`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Un puerto lo declara el módulo **consumidor** y lo implementa el módulo
**proveedor**. La implementación vive en el `infrastructure/services.py` del
proveedor y se liga en un módulo de DI registrado.

Esto mantiene el grafo de módulos ACÍCLICO: `pagos` nunca importa `commerce`.
El puerto se expresa en **vocabulario de pago** (`orden_pago_id`,
`persona_id`), de modo que ningún tipo de `commerce` cruza la frontera.

| Puerto | Consume | Provee | Implementación |
|---|---|---|---|
| `IEstadoCompraOrdenPagoService` | `pagos` | `commerce` | `commerce/infrastructure/services/` |
| `IPropietarioOrdenPagoService` | `pagos` | `commerce` | `commerce/infrastructure/services/` |
| `IActivacionCompraService` | `pagos` | `commerce` (coordinador) | `commerce/infrastructure/services/` |
| `IProveedorPagoService` | `pagos` | el proveedor de pago | `pagos/infrastructure/services.py` |
"""

from abc import ABC, abstractmethod

from modules.pagos.domain.schemas.pago_schemas import (
    EstadoCompraOrdenPago,
    MarcaCompraPagadaResult,
    ResultadoActivacionCompra,
)


class IEstadoCompraOrdenPagoService(ABC):
    """Estado comercial de la compra que financia una orden.

    `pagos` necesita dos cosas del agregado comercial, y ninguna puede
    resolverse sin salir del módulo de pago:

    1. Saber si la compra está pagada o cancelada — para el veredicto
       operativo y para no confirmar el pago de una compra cancelada.
    2. Marcar la compra como pagada cuando el pago queda confirmado — un
       hecho comercial, idempotente, que NO habilita derechos (RN-C08).

    La relación entre compra y orden la posee `commerce.Compra.orden_pago`, así
    que la dirección de dependencias queda `commerce -> pagos` y el puerto la
    invierte sólo para la consulta y la escritura de un hecho.
    """

    @abstractmethod
    def obtener_estado_compra(self, orden_pago_id: str) -> EstadoCompraOrdenPago:
        """Devuelve el estado comercial de la compra que financia la orden.

        Args:
            orden_pago_id: UUID de la `OrdenPago`.

        Returns:
            `EstadoCompraOrdenPago` con `existe=False` cuando ninguna compra
            financia la orden, o con el estado comercial de esa compra.
        """
        ...

    @abstractmethod
    def marcar_compra_pagada(self, orden_pago_id: str) -> MarcaCompraPagadaResult:
        """Marca la compra que financia la orden como `PAGADA`.

        Es **idempotente**: llamarla sobre una compra ya pagada no la vuelve a
        escribir ni altera su fecha de pago.

        No habilita ningún derecho: la entrega del derecho es un hecho
        posterior y separado (RN-C08, FR-04 §4).

        Args:
            orden_pago_id: UUID de la `OrdenPago`.

        Returns:
            `MarcaCompraPagadaResult` con `existe=False` cuando ninguna compra
            financia la orden.
        """
        ...


class IPropietarioOrdenPagoService(ABC):
    """Titularidad de una orden de pago.

    `pagos` la consulta antes de aceptar un reenvío desde el navegador, de modo
    que el módulo de pago nunca importa el módulo que posee la compra.

    El documento de identidad NO es una credencial (RN-U04): la titularidad se
    comprueba contra la persona compradora de la compra que financia la orden.
    """

    @abstractmethod
    def es_propietario(self, orden_pago_id: str, persona_id: str) -> bool:
        """Devuelve `True` si la persona puede operar sobre esa orden.

        Args:
            orden_pago_id: UUID de la `OrdenPago`.
            persona_id: UUID de la persona autenticada.

        Returns:
            `True` cuando la persona es la compradora de la orden.
        """
        ...


class IActivacionCompraService(ABC):
    """Activación de los derechos de una compra ya pagada.

    `pagos` confirma el pago y **NO habilita** ningún derecho: el cobro
    confirmado y la entrega del derecho son hechos **separados** (RN-C08,
    FR-04 §4). Lo que `pagos` hace, al terminar la secuencia congelada
    §2.3, es pedir al coordinador que active el derecho.

    El puerto está expresado en **vocabulario de pago** (`orden_pago_id`), de
    modo que ningún tipo de `commerce` cruza la frontera: el coordinador
    resuelve la compra y su origen por su cuenta.

    Contrato para quien implemente el puerto (el coordinador de `commerce`):

    1. **Es idempotente**: una llamada repetida sobre la misma orden no
       habilita el derecho dos veces (FR-04 I-2).
    2. **No revierte el pago**: si la activación falla, el pago confirmado se
       conserva y el resultado lo dice con `recuperable=True` y una
       `proxima_accion` segura.
    3. **No lanza por un fallo esperado**: un fallo del dominio es una
       incidencia, no una excepción.
    """

    @abstractmethod
    def activar_por_orden(self, orden_pago_id: str) -> ResultadoActivacionCompra:
        """Activa los derechos de la compra que financia la orden.

        Args:
            orden_pago_id: UUID de la `OrdenPago` confirmada.

        Returns:
            `ResultadoActivacionCompra` con el estado de la activación y la
            acción segura que sigue.
        """
        ...


class IProveedorPagoService(ABC):
    """Frontera tipada con el proveedor de pago.

    El módulo de pago NUNCA habla con el proveedor directamente: habla con
    este puerto. La implementación real (`infrastructure/services.py`) verifica
    la firma del proveedor con la clave del comercio **en servidor**.

    La apertura de una sesión de pago en el proveedor **no** forma parte de
    este paquete: requiere credenciales de despliegue y una integración viva,
    que están fuera del alcance de FND-04. Este paquete no inventa ni declara
    ninguna credencial.
    """

    @property
    @abstractmethod
    def disponible(self) -> bool:
        """Si el proveedor puede autenticarse (hay clave del comercio)."""
        ...

    @abstractmethod
    def verificar_firma(self, payload_http: str, signature: str) -> bool:
        """Verifica la firma del proveedor sobre el payload crudo.

        Args:
            payload_http: el payload **crudo** tal como llegó. Re-serializar el
                JSON cambia los bytes y rompe la firma.
            signature: la firma entregada junto al payload.

        Returns:
            `True` sólo cuando la firma verifica. Sin clave configurada el
            resultado es siempre `False`: no hay fallback que convierta un
            payload no verificable en verificado.
        """
        ...


__all__ = [
    "IActivacionCompraService",
    "IEstadoCompraOrdenPagoService",
    "IPropietarioOrdenPagoService",
    "IProveedorPagoService",
]
