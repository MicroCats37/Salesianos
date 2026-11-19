"""`ActivacionCompraAdapter` — el coordinador de activación para `pagos`.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

`pagos` declara el puerto `IActivacionCompraService` y `commerce` lo
implementa: el módulo de pago nunca importa este módulo, pregunta por la
interfaz. Así la dirección de dependencias queda `commerce -> pagos` y el
grafo de módulos es acíclico.

Este adaptador sólo **traduce** el resultado del coordinador al vocabulario
del puerto. No decide nada: no sabe qué es un cupo, un pase o una salida de
stock, y no toca el estado del pago.
"""

import logging

from modules.commerce.domain.schemas.compra_schemas import (
    ResultadoActivacionCompra as ResultadoActivacionCompraInterno,
)
from modules.commerce.domain.services.core.activacion_compra_core_service import (
    ActivacionCompraCoreService,
)
from modules.commerce.domain.services.core.coordinador_activacion_compra import (
    CoordinadorActivacionCompra,
)
from modules.commerce.domain.services.core.registro_activadores_compra import (
    obtener_registro,
)
from modules.pagos.domain.schemas.pago_schemas import ResultadoActivacionCompra

logger = logging.getLogger(__name__)


class ActivacionCompraAdapter:
    """Implementa el puerto `IActivacionCompraService` de `pagos`."""

    def __init__(self) -> None:
        self.coordinador = CoordinadorActivacionCompra(
            core=ActivacionCompraCoreService(),
            registro=obtener_registro(),
        )

    def activar_por_orden(self, orden_pago_id: str) -> ResultadoActivacionCompra:
        """Activa los derechos de la compra que financia la orden.

        Args:
            orden_pago_id: UUID de la `OrdenPago` confirmada.

        Returns:
            El resultado de la activación en vocabulario de pago.
        """
        resultado: ResultadoActivacionCompraInterno = (
            self.coordinador.activar_por_orden(orden_pago_id)
        )
        return ResultadoActivacionCompra(
            existe=resultado.existe,
            activada=resultado.activada,
            ya_activada=resultado.ya_activada,
            en_curso=resultado.en_curso,
            recuperable=resultado.recuperable,
            intentos=resultado.intentos,
            codigo=resultado.codigo,
            proxima_accion=resultado.proxima_accion,
        )


__all__ = ["ActivacionCompraAdapter"]
