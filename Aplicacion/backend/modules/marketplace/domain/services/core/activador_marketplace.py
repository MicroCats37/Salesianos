"""`ActivadorMarketplace` — el efecto de stock de un pago confirmado.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.3
Freeze: `FREEZE-CM-1.0.0` (FR-04 §2.3)

**QUÉ HACE.** Cuando `commerce` confirma el pago de una compra de
marketplace, el coordinador despacha a este activador por el origen
`MARKETPLACE` (`FR-04` §2.3: "ActivarDominio(compra_id, origen)"). Aquí se
confirma la venta: las unidades reservadas SALEN del stock físico y queda el
movimiento de venta en la bitácora (`RN-M04` · `RN-M06`).

**LO QUE NO HACE.** No habilita derechos de acceso ni toca la entrega: la
entrega es un hecho POSTERIOR y separado (`RN-M07` · `QA-M04`). El pago
habilita el stock; la entrega la registra el operador.

**IDEMPOTENTE POR DISEÑO (`FR-04` I-2 · I-3).** La reserva es la autoridad
del "una vez": pasar de `ACTIVA` a `CONFIRMADA` es CONDICIONAL y el
movimiento de venta tiene una REFERENCIA ÚNICA. Un webhook repetido NO
descuenta dos veces ni genera un segundo movimiento.

**LA FRONTERA.** Este activador implementa el puerto CONGELADO de
`commerce` (`IActivadorDominioCompra`): el módulo consume el puerto y NO
edita los interiores de `commerce` ni de `pagos`. Se registra en
`apps.py::ready()`, igual que los activadores de pases e inscripciones.
"""

import logging

from django.db import IntegrityError, transaction
from injector import inject

from modules.commerce.domain.ports import IActivadorDominioCompra
from modules.commerce.domain.schemas.compra_schemas import (
    ContextoActivacionCompra,
    ResultadoActivacionDominio,
)

from modules.marketplace.domain.models import Pedido
from modules.marketplace.domain.services.core.inventario_core_service import (
    InventarioCoreService,
)

logger = logging.getLogger(__name__)

#: Códigos de máquina del resultado. Son públicos y estables.
CODIGO_STOCK_CONFIRMADO = "STOCK_CONFIRMADO"
CODIGO_STOCK_YA_CONFIRMADO = "STOCK_YA_CONFIRMADO"
CODIGO_PEDIDO_NO_ENCONTRADO = "PEDIDO_NO_ENCONTRADO"


class ActivadorMarketplace(IActivadorDominioCompra):
    """El activador de stock del dominio de marketplace."""

    @inject
    def __init__(self, inventario_core: InventarioCoreService | None = None):
        # Los colaboradores son colaboradores sin estado: el activador puede
        # construirse a mano (lo registra el proceso al arrancar) o por DI.
        self.inventario_core = inventario_core or InventarioCoreService()

    def activar(self, contexto: ContextoActivacionCompra) -> ResultadoActivacionDominio:
        """Confirma el stock de la compra pagada.

        Es IDEMPOTENTE: la misma clave nunca confirma el stock dos veces.

        Args:
            contexto: los hechos congelados de la compra y la clave estable.

        Returns:
            El resultado del dominio. `exito=False` significa "no se aplicó":
            el stock sigue sin confirmar y la activación queda pendiente y
            reintentable (`RN-C08`).
        """
        pedido = Pedido.objects.filter(compra_id=contexto.compra_id).first()
        if pedido is None:
            return ResultadoActivacionDominio(
                exito=False,
                codigo=CODIGO_PEDIDO_NO_ENCONTRADO,
                detalle={"estado": "PEDIDO_NO_ENCONTRADO"},
            )

        try:
            with transaction.atomic():
                return self._activar_sync(pedido)
        except IntegrityError:
            # Carrera: otra activación del MISMO derecho ganó y ya aplicó el
            # descuento. La fila ganadora es la buena: NO se vuelve a
            # descontar ni a registrar un segundo movimiento (FR-04 I-3).
            logger.warning(
                "El stock de la compra %s ya había sido confirmado por otra "
                "activación.",
                contexto.compra_id,
            )
            return ResultadoActivacionDominio(
                exito=True,
                codigo=CODIGO_STOCK_YA_CONFIRMADO,
                detalle={"cantidad": 0, "estado": "YA_CONFIRMADO"},
            )

    # ── Internos sync ───────────────────────────────────────────────────────

    def _activar_sync(self, pedido) -> ResultadoActivacionDominio:
        """Confirma la venta del pedido, dentro de una transacción."""
        movimientos = self.inventario_core.confirmar_venta_de_pedido(pedido)
        if not movimientos:
            # Ya estaba confirmada: no se vuelve a descontar nada.
            return ResultadoActivacionDominio(
                exito=True,
                codigo=CODIGO_STOCK_YA_CONFIRMADO,
                detalle={"cantidad": 0, "estado": "YA_CONFIRMADO"},
            )
        cantidad = sum(abs(movimiento.cantidad) for movimiento in movimientos)
        return ResultadoActivacionDominio(
            exito=True,
            codigo=CODIGO_STOCK_CONFIRMADO,
            detalle={"cantidad": cantidad, "estado": "CONFIRMADO"},
        )


__all__ = ["ActivadorMarketplace"]
