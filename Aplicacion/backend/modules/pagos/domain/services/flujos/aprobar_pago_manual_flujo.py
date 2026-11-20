"""Registro seguro de evidencia manual y liquidación comercial de una orden."""

import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone
from injector import inject

from core.exceptions import ConflictError

from modules.pagos.domain.constants import (
    EstadoAprobacionPagoManual,
    EstadoOrdenPago,
    EstadoTransaccionPago,
)
from modules.pagos.domain.exceptions import (
    CompraYaCanceladaError,
    OrdenPagoNoEncontradaError,
    OrdenPagoNoPagableError,
    OrdenYaPagadaConIzipayError,
)
from modules.pagos.domain.models import AprobacionPagoManual, OrdenPago, TransaccionPago
from modules.pagos.domain.ports import (
    IActivacionCompraService,
    IEstadoCompraOrdenPagoService,
)

logger = logging.getLogger(__name__)


class AprobarPagoManualFlujo:
    """Registra una única evidencia manual sin simular una transacción Izipay."""

    CANALES_PERMITIDOS = {
        "TRANSFERENCIA_BANCARIA",
        "EFECTIVO",
        "YAPE",
        "PLIN",
        "OTRO",
    }

    @inject
    def __init__(
        self,
        estado_compra_service: IEstadoCompraOrdenPagoService,
        activacion_service: IActivacionCompraService,
    ):
        self.estado_compra_service = estado_compra_service
        self.activacion_service = activacion_service

    async def aprobar(
        self, *, orden_pago_id: str, actor_id: str, canal: str, referencia: str, motivo: str
    ) -> AprobacionPagoManual:
        """Persiste la evidencia y luego converge los hechos comerciales."""
        estado_compra = await sync_to_async(
            self.estado_compra_service.obtener_estado_compra
        )(orden_pago_id)
        if estado_compra.cancelada:
            raise CompraYaCanceladaError()

        aprobacion = await sync_to_async(self._registrar)(
            orden_pago_id, actor_id, canal, referencia, motivo
        )

        # La prueba del pago queda durable incluso si la liquidación falla.
        try:
            await sync_to_async(self.estado_compra_service.marcar_compra_pagada)(
                orden_pago_id
            )
            await sync_to_async(self.activacion_service.activar_por_orden)(orden_pago_id)
        except Exception:
            logger.exception(
                "No se pudo completar la liquidación de la orden %s tras aprobarla manualmente.",
                orden_pago_id,
            )

        return aprobacion

    @staticmethod
    @transaction.atomic
    def _registrar(orden_pago_id, actor_id, canal, referencia, motivo):
        canal = canal.strip().upper()
        referencia = referencia.strip()
        motivo = motivo.strip()
        if (
            canal not in AprobarPagoManualFlujo.CANALES_PERMITIDOS
            or not referencia
            or not motivo
        ):
            raise ConflictError(code="PAGO_MANUAL_EVIDENCIA_INVALIDA")

        orden = OrdenPago.objects.select_for_update().filter(id=orden_pago_id).first()
        if orden is None:
            raise OrdenPagoNoEncontradaError()

        existente = AprobacionPagoManual.objects.filter(
            orden_pago=orden, estado=EstadoAprobacionPagoManual.APROBADA
        ).first()
        if existente is not None:
            return existente

        if TransaccionPago.objects.filter(
            orden_pago=orden,
            estado=EstadoTransaccionPago.EXITO,
            verificada=True,
        ).exists():
            raise OrdenYaPagadaConIzipayError()

        if orden.estado in (EstadoOrdenPago.CONFIRMADA, EstadoOrdenPago.VENCIDA):
            raise OrdenPagoNoPagableError()

        aprobacion = AprobacionPagoManual.objects.create(
            orden_pago=orden,
            actor_id=actor_id,
            canal=canal,
            referencia=referencia,
            monto=orden.monto,
            moneda=orden.moneda,
            motivo=motivo,
        )
        orden.estado = EstadoOrdenPago.CONFIRMADA
        orden.pagada_en = timezone.now()
        orden.save(update_fields=["estado", "pagada_en", "updated_at"])
        return aprobacion
