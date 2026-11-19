"""`EstadoOperativoPagoService` — el ÚNICO dueño del veredicto del pago.

Freeze: `FREEZE-ENV-1.0.0` (FR-01 §5) · `FREEZE-CM-1.0.0` (FR-04 §1.3)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-01-envelope-error-pagination.md`

`Compra.estado` (hecho comercial), `OrdenPago.estado` (hecho de orden) y
`TransaccionPago.estado` (hecho del proveedor) son **tres hechos distintos**.
Este servicio los cruza **una sola vez**, en un solo lugar, y publica un
veredicto comprensible. Ninguna otra superficie —ni el frontend— recalcula el
veredicto comparando hechos hermanos (`RN-C07`, `contratos/01` §1.4).

El vocabulario `EstadoOperativoPago` (8 valores) está CONGELADO sin renumerar
(FR-01 §5.2): este paquete lo reproduce tal cual.

Precedencia (la primera regla que se cumple gana):

1. `SIN_ORDEN` — no hay orden de pago.
2. `PAGADA_SIN_LIQUIDAR` — la orden está confirmada pero la compra no consta
   pagada (el dinero entró; el hecho comercial todavía no).
3. `PAGADA_SIN_EVIDENCIA` — la orden está confirmada pero no hay evidencia
   verificable asociada.
4. `PAGADA_SIN_FECHA` — la orden está confirmada y evidenciada, pero sin fecha
   de pago.
5. `PAGADA` — la orden está confirmada, la compra consta pagada, hay evidencia
   y hay fecha.
6. `VENCIDA` — la orden venció.
7. `CANCELADA` — la orden o la compra fueron canceladas.
8. `PENDIENTE` — el pago todavía no ocurrió.

Una orden confirmada NUNCA devuelve `CANCELADA` ni `VENCIDA`: el estado de la
orden gana primero, para que nadie lea que un pago cobrado fue cancelado.

Este módulo NO conoce el vocabulario de estados de `commerce`: recibe
**banderas** del puerto (`compra_pagada`, `compra_cancelada`), de modo que el
acoplamiento entre módulos queda cerrado también en los datos.
"""

from datetime import datetime

from injector import inject

from modules.pagos.domain.constants import (
    DESCRIPCIONES_ESTADO_OPERATIVO,
    EstadoOperativoPago,
    EstadoOrdenPago,
    EstadoTransaccionPago,
    OrigenPago,
)
from modules.pagos.domain.models import TransaccionPago
from modules.pagos.domain.ports import IEstadoCompraOrdenPagoService
from modules.pagos.domain.results.pago_result import EstadoOperativoResult


class EstadoOperativoPagoService:
    """Calcula el veredicto operativo de una orden de pago."""

    @inject
    def __init__(self, estado_compra_service: IEstadoCompraOrdenPagoService):
        self.estado_compra_service = estado_compra_service

    # ── Cálculo puro ─────────────────────────────────────────────────────────

    @staticmethod
    def calcular(
        *,
        estado_orden: str | None,
        compra_pagada: bool,
        compra_cancelada: bool,
        origen_pago: str,
        pagada_en: datetime | None,
    ) -> str:
        """Devuelve el código del veredicto a partir de los hechos.

        Es una función PURA: recibe los hechos y devuelve el veredicto. No
        consulta la base de datos y no escribe nada.

        Args:
            estado_orden: estado de la orden (`None` si no hay orden).
            compra_pagada: si la compra que financia la orden consta pagada.
            compra_cancelada: si esa compra está cancelada.
            origen_pago: procedencia de la evidencia (`IZIPAY`, `MANUAL` o
                `SIN_PAGO`).
            pagada_en: fecha del pago (`None` si nunca se pagó).

        Returns:
            Un código de `EstadoOperativoPago`.
        """
        if not estado_orden:
            return EstadoOperativoPago.SIN_ORDEN

        if estado_orden == EstadoOrdenPago.CONFIRMADA:
            if not compra_pagada:
                return EstadoOperativoPago.PAGADA_SIN_LIQUIDAR
            if origen_pago == OrigenPago.SIN_PAGO:
                return EstadoOperativoPago.PAGADA_SIN_EVIDENCIA
            if pagada_en is None:
                return EstadoOperativoPago.PAGADA_SIN_FECHA
            return EstadoOperativoPago.PAGADA

        if estado_orden == EstadoOrdenPago.VENCIDA:
            return EstadoOperativoPago.VENCIDA

        if estado_orden == EstadoOrdenPago.FALLIDA:
            # El intento falló: el pago NO se completó. La compra sigue
            # pendiente y el comprador puede reintentar sobre la MISMA orden
            # (RN-C03, RN-C04). Es el estado "pago no completado" de RN-C07.
            return EstadoOperativoPago.CANCELADA

        if compra_cancelada:
            return EstadoOperativoPago.CANCELADA

        return EstadoOperativoPago.PENDIENTE

    # ── Resultado con etiqueta y descripción ────────────────────────────────

    @staticmethod
    def construir_result(codigo: str) -> EstadoOperativoResult:
        """Envuelve el código del veredicto en su wrapper HTTP-ready."""
        return EstadoOperativoResult(
            codigo=codigo,
            etiqueta=EstadoOperativoPago(codigo).label,
            descripcion=DESCRIPCIONES_ESTADO_OPERATIVO.get(codigo, ""),
        )

    # ── Cálculo sobre una orden concreta ────────────────────────────────────

    def calcular_para_orden(self, orden) -> EstadoOperativoResult:
        """Calcula el veredicto de una orden real.

        Reúne los hechos — el estado de la orden, el estado comercial de la
        compra (a través del puerto), la procedencia de la evidencia y la fecha
        del pago — y devuelve el veredicto.

        Args:
            orden: la `OrdenPago`.

        Returns:
            El `EstadoOperativoResult` de la orden.
        """
        compra_pagada = False
        compra_cancelada = False
        if orden is not None:
            estado = self.estado_compra_service.obtener_estado_compra(str(orden.id))
            compra_pagada = estado.pagada
            compra_cancelada = estado.cancelada

        codigo = self.calcular(
            estado_orden=orden.estado if orden is not None else None,
            compra_pagada=compra_pagada,
            compra_cancelada=compra_cancelada,
            origen_pago=self._origen_pago(orden),
            pagada_en=orden.pagada_en if orden is not None else None,
        )
        return self.construir_result(codigo)

    def _origen_pago(self, orden) -> str:
        """Procedencia de la evidencia de una orden.

        `IZIPAY` cuando existe un intento `EXITO` **verificado**; `SIN_PAGO`
        en cualquier otro caso. La aprobación manual (`MANUAL`) la decide un
        administrador y la incorpora la ruta administrativa (A0).
        """
        if orden is None:
            return OrigenPago.SIN_PAGO
        existe = TransaccionPago.objects.filter(
            orden_pago_id=orden.id,
            estado=EstadoTransaccionPago.EXITO,
            verificada=True,
        ).exists()
        return OrigenPago.IZIPAY if existe else OrigenPago.SIN_PAGO


__all__ = ["EstadoOperativoPagoService"]
