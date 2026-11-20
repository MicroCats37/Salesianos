"""`NotificadorCompradorAdapter` — el notificador del comprador.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

Implementa el puerto `INotificadorCompraService` que declara `pagos`: la
dirección de dependencias queda `notificaciones -> pagos` y el grafo de
módulos sigue acíclico (`pagos` nunca importa este módulo en tiempo de
importación; el enlace es perezoso, en `modules/pagos/di.py`).

**El proveedor NO existe.** `PD-08` (proveedor, plantillas, límites,
reintentos y entrega) sigue **ABIERTO** y diferido por `DEC-21`. Este
adaptador, por tanto:

- **NO envía nada**. No hay cliente SMTP, ni destinatario, ni plantilla, ni
  credencial, ni nombre de variable de entorno de correo.
- Registra el intento como `OMITIDA` con el código
  `PROVEEDOR_NO_APROBADO`: el intento queda **auditable** y el bloqueo es
  **explícito**, no un fallo silencioso.
- **Nunca revierte la compra.** Un fallo aquí no propaga al flujo de pago: el
  llamador lo captura y el cobro confirmado se conserva (RN-C08).

El día que `PD-08` se ratifique, este adaptador se sustituye por uno que
implemente el proveedor aprobado. El puerto y la trazabilidad no cambian.
"""

import logging

from modules.notificaciones.domain.constants import (
    CODIGO_ENVIO_FALLIDO,
    CODIGO_PROVEEDOR_NO_APROBADO,
    EstadoNotificacion,
    TipoNotificacion,
)
from modules.notificaciones.domain.services.core.notificacion_envio_core_service import (
    NotificacionEnvioCoreService,
)
from modules.pagos.domain.schemas.pago_schemas import (
    ContextoNotificacionCompra,
    ResultadoNotificacion,
)

logger = logging.getLogger(__name__)


class NotificadorCompradorAdapter:
    """Implementa el puerto `INotificadorCompraService` de `pagos`."""

    def __init__(self, core: NotificacionEnvioCoreService | None = None) -> None:
        self.core = core or NotificacionEnvioCoreService()

    def notificar_compra_confirmada(
        self, contexto: ContextoNotificacionCompra
    ) -> ResultadoNotificacion:
        """Registra el intento de notificar al comprador.

        Mientras `PD-08` no se ratifique, **no se envía nada**: el intento se
        registra como `OMITIDA` con el código `PROVEEDOR_NO_APROBADO`.

        Args:
            contexto: los hechos congelados de la compra.

        Returns:
            `ResultadoNotificacion` con `omitida=True`.
        """
        registro = self.core.registrar_intento(
            orden_pago_id=contexto.orden_pago_id,
            persona_id=contexto.persona_id,
            tipo=TipoNotificacion.COMPRA_CONFIRMADA,
            estado=EstadoNotificacion.OMITIDA,
            codigo=CODIGO_PROVEEDOR_NO_APROBADO,
        )

        logger.info(
            "Notificación de compra OMITIDA: el proveedor de correo no está "
            "aprobado (PD-08 abierto). El pago confirmado se conserva."
        )

        return ResultadoNotificacion(
            enviada=False,
            omitida=True,
            recuperable=True,
            codigo=CODIGO_PROVEEDOR_NO_APROBADO,
            intentos=registro.intentos if registro is not None else 0,
        )

    def registrar_fallo(self, contexto: ContextoNotificacionCompra) -> ResultadoNotificacion:
        """Registra un fallo de envío como incidencia recuperable.

        Lo usa el llamador cuando un proveedor futuro falla. El texto de la
        excepción **nunca** se persiste ni se devuelve: sólo un código.
        """
        registro = self.core.registrar_intento(
            orden_pago_id=contexto.orden_pago_id,
            persona_id=contexto.persona_id,
            tipo=TipoNotificacion.COMPRA_CONFIRMADA,
            estado=EstadoNotificacion.FALLIDA,
            codigo=CODIGO_ENVIO_FALLIDO,
        )
        return ResultadoNotificacion(
            enviada=False,
            omitida=False,
            recuperable=True,
            codigo=CODIGO_ENVIO_FALLIDO,
            intentos=registro.intentos if registro is not None else 0,
        )


__all__ = ["NotificadorCompradorAdapter"]
