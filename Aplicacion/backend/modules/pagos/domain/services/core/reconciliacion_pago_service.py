"""`ReconciliacionPagoService` — concilia pagos verificados sin derecho.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3, §4, §6)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/cross-cutting/XCT-03-payment-media-notifications.md`

**Qué resuelve.** El pago confirmado y la entrega del derecho son hechos
SEPARADOS (RN-C08). Puede haber un pago verificado cuya activación quedó
`PENDIENTE` o `FALLIDA`: el dominio de origen todavía no registró su
activador, el intento falló, o el proceso murió con el intento reservado. Ese
pago está **cobrado y sin derecho**, y sin una conciliación nadie lo
encuentra.

**Qué NO hace.** No toca el estado de la orden ni el de la compra. No
revierte un cobro. No vuelve a invocar al dominio si el derecho ya está
habilitado: el reintento es el del coordinador, y el coordinador converge
(FR-04 I-2).

**Quién dispara.** Este paquete resuelve `D-FND-05-07`: el disparador del
reintento es un **comando de operación** (`reconciliar_activaciones`), no una
cola ni una tarea programada. Es idempotente, auditable y no corre solo.

**Dónde vive la verdad.** El estado de la activación lo publica `commerce`
(coordinador) a través del puerto `IActivacionCompraService`; este servicio
sólo lo lee y pide el reintento. No recalcula el veredicto del pago: ése lo
calcula `EstadoOperativoPagoService`, su único dueño (FR-01 §5).
"""

import logging

from injector import inject

from modules.pagos.domain.constants import EstadoActivacionPago
from modules.pagos.domain.ports import IActivacionCompraService
from modules.pagos.domain.results.pago_result import (
    ItemReconciliacion,
    ResultadoReconciliacion,
)
from modules.pagos.domain.selectors.pago_selector import OrdenPagoSelector
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)

logger = logging.getLogger(__name__)

#: Límite por defecto de órdenes revisadas en una pasada.
LIMITE_POR_DEFECTO = 100


class ReconciliacionPagoService:
    """Concilia los pagos verificados cuya activación no está resuelta."""

    @inject
    def __init__(
        self,
        orden_selector: OrdenPagoSelector,
        estado_operativo_service: EstadoOperativoPagoService,
        activacion_service: IActivacionCompraService,
    ) -> None:
        self.orden_selector = orden_selector
        self.estado_operativo_service = estado_operativo_service
        self.activacion_service = activacion_service

    # ── Lectura ─────────────────────────────────────────────────────────────

    def conciliar(
        self,
        *,
        limite: int = LIMITE_POR_DEFECTO,
        aplicar: bool = False,
    ) -> ResultadoReconciliacion:
        """Revisa las órdenes confirmadas y reintenta las activaciones pendientes.

        Args:
            limite: cuántas órdenes confirmadas se revisan como máximo.
            aplicar: `False` (por defecto) sólo **informa**; `True` pide al
                coordinador el reintento de la activación.

        Returns:
            El informe de la pasada. Nunca lanza por un fallo esperado: una
            incidencia de activación es un dato del informe, no una excepción.
        """
        ordenes = self.orden_selector.listar_confirmadas(limite)

        items: list[ItemReconciliacion] = []
        con_incidencia = 0
        recuperadas = 0
        pendientes = 0

        for orden in ordenes:
            veredicto = self.estado_operativo_service.calcular_activacion_para_orden(
                orden
            )
            codigo_antes = veredicto.codigo if veredicto is not None else ""
            if codigo_antes == EstadoActivacionPago.ACTIVADA:
                # El derecho ya está habilitado: no se toca nada.
                continue

            con_incidencia += 1
            item = self._conciliar_orden(orden, codigo_antes, aplicar=aplicar)
            items.append(item)
            if item.estado_activacion == EstadoActivacionPago.ACTIVADA:
                recuperadas += 1
            else:
                pendientes += 1

        return ResultadoReconciliacion(
            revisadas=len(ordenes),
            con_incidencia=con_incidencia,
            recuperadas=recuperadas,
            pendientes=pendientes,
            items=items,
        )

    # ── Internos ────────────────────────────────────────────────────────────

    def _conciliar_orden(self, orden, codigo_antes: str, *, aplicar: bool):
        """Reintenta la activación de UNA orden y describe el resultado."""
        if not aplicar:
            return ItemReconciliacion(
                orden_pago_id=str(orden.id),
                referencia=orden.referencia,
                estado_orden=orden.estado,
                estado_activacion=codigo_antes,
                codigo="RECONCILIACION_SIN_APLICAR",
                proxima_accion="REINTENTAR_ACTIVACION",
                recuperable=True,
                aplicada=False,
            )

        try:
            resultado = self.activacion_service.activar_por_orden(str(orden.id))
        except Exception:
            # Un fallo del coordinador NO revierte el cobro: la incidencia se
            # registra en el informe y el pago confirmado se conserva.
            logger.exception(
                "La conciliación no pudo reintentar la activación de la orden %s. "
                "El pago confirmado se conserva.",
                orden.id,
            )
            return ItemReconciliacion(
                orden_pago_id=str(orden.id),
                referencia=orden.referencia,
                estado_orden=orden.estado,
                estado_activacion=codigo_antes,
                codigo="RECONCILIACION_FALLIDA",
                proxima_accion="REINTENTAR_ACTIVACION",
                recuperable=True,
                aplicada=True,
            )

        codigo_despues = self._codigo_tras_reintento(orden, resultado)
        return ItemReconciliacion(
            orden_pago_id=str(orden.id),
            referencia=orden.referencia,
            estado_orden=orden.estado,
            estado_activacion=codigo_despues,
            codigo=resultado.codigo,
            proxima_accion=resultado.proxima_accion,
            recuperable=bool(resultado.recuperable),
            aplicada=True,
        )

    def _codigo_tras_reintento(self, orden, resultado) -> str:
        """El veredicto de activación DESPUÉS del reintento.

        Se relee del puerto en vez de deducirse del resultado del coordinador:
        la fuente de verdad es el registro de activación, no el valor de
        retorno del intento.
        """
        veredicto = self.estado_operativo_service.calcular_activacion_para_orden(orden)
        if veredicto is not None:
            return veredicto.codigo
        if resultado.activada or resultado.ya_activada:
            return EstadoActivacionPago.ACTIVADA
        if resultado.en_curso:
            return EstadoActivacionPago.EN_CURSO
        return EstadoActivacionPago.FALLIDA


__all__ = ["LIMITE_POR_DEFECTO", "ReconciliacionPagoService"]