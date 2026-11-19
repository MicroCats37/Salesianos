"""`CompraFlujo` — la creación (o reutilización) de una compra.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §1.1, §2.1 I-4, I-5)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Este flujo implementa dos garantías congeladas y una regla de dinero.

**I-4 — Reabrir el checkout NO crea otra compra.** La compra se identifica por
`(persona, referencia)`, donde la `referencia` es la **intención de compra**
que declara el módulo de origen. Antes de crear, el flujo consulta si ya
existe una compra `PENDIENTE` para esa intención: si existe, la **reutiliza**
(con su misma orden de pago) y no crea nada. La base de datos lo garantiza con
la restricción parcial `compra_pendiente_unica_por_comprador`.

**I-5 — Cerrar el modal NO cancela.** Este paquete no expone ninguna operación
de cancelación: la compra queda `PENDIENTE` y es recuperable. La cancelación
comercial es una decisión posterior (`PD-06` sigue abierta).

**RN-C02 — El servidor congela el precio.** El total se **deriva** de las
líneas del snapshot, no de lo que declara el cliente. Si alguien declara un
total que no coincide con el derivado, la compra se rechaza: nunca se acepta
un importe arbitrario.

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`
(`contract/django-app-architecture-contract.md` §4.4).
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.commerce.domain.exceptions import (
    CompraReferenciaInvalidaError,
    CompraTotalIncoherenteError,
)
from modules.commerce.domain.schemas.compra_schemas import CompraCreateData, calcular_total
from modules.commerce.domain.selectors.compra_selector import CompraSelector
from modules.commerce.domain.services.core.compra_core_service import CompraCoreService
from modules.pagos.domain.services.core.orden_pago_core_service import (
    OrdenPagoCoreService,
)


class CompraFlujo:
    """Creación y reutilización de compras comerciales."""

    @inject
    def __init__(
        self,
        core_service: CompraCoreService,
        orden_core: OrdenPagoCoreService,
        selector: CompraSelector,
    ):
        self.core_service = core_service
        self.orden_core = orden_core
        self.selector = selector

    async def crear_o_reutilizar_compra(self, data: CompraCreateData):
        """Crea la compra de una intención o reutiliza la pendiente.

        Returns:
            La tupla `(compra, reutilizada)`.
        """
        # El total lo decide el servidor (RN-C02). Un total declarado que no
        # coincide con el derivado de las líneas es un error, no un ajuste.
        total = calcular_total(data.lineas)
        if data.total is not None and data.total != total:
            raise CompraTotalIncoherenteError()

        if not str(data.referencia or "").strip():
            raise CompraReferenciaInvalidaError()

        # 1. ¿Existe ya una compra pendiente para esta intención?
        existente = await sync_to_async(
            self.selector.obtener_pendiente_por_referencia
        )(data.persona_id, data.referencia)
        if existente is not None:
            return existente, True

        # 2. Creación atómica de la compra y su orden de pago.
        try:
            return await sync_to_async(self._crear_sync)(data, total), False
        except IntegrityError:
            # La restricción parcial de la base de datos rechaza otra compra
            # pendiente para la misma intención: la que ganó la carrera es la
            # buena y se reutiliza.
            existente = await sync_to_async(
                self.selector.obtener_pendiente_por_referencia
            )(data.persona_id, data.referencia)
            if existente is None:
                raise
            return existente, True

    @transaction.atomic()
    def _crear_sync(self, data: CompraCreateData, total):
        """Crea la compra y su orden de pago en una sola transacción."""
        compra = self.core_service.crear(
            persona_id=data.persona_id,
            origen=data.origen,
            total=total,
            moneda=data.moneda,
            lineas_snapshot=[linea.model_dump(mode="json") for linea in data.lineas],
            referencia=str(data.referencia).strip(),
        )

        orden = self.orden_core.crear(
            referencia=self._referencia_orden(compra),
            monto=total,
            moneda=data.moneda,
            metadata={
                "concepto_tipo": data.origen,
                "concepto_id": data.referencia,
                "purchase_reference": data.referencia,
            },
        )
        return self.core_service.vincular_orden_pago(compra, orden)

    def _referencia_orden(self, compra) -> str:
        """La referencia **visible** de la orden de pago.

        Deriva del identificador de la compra: es estable, no es un secreto y
        permite reconciliar con el proveedor sin guardar nada más.
        """
        return f"ORD-{str(compra.id).replace('-', '')[:12].upper()}"


__all__ = ["CompraFlujo"]
