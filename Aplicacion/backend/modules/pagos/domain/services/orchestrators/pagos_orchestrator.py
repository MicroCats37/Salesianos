"""`PagosOrchestrator` — fachada async del módulo `pagos`.

Freeze: `FREEZE-CM-1.0.0` · `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Fachada MUY DELGADA: un método público por endpoint y nada más. No contiene
lógica de negocio; delega en los flujos (escrituras) o en los selectores
(lecturas). Devuelve result objects, nunca schemas HTTP.

Rutas (ledger FR-07 §3.3):

| Ruta | Método | Presenter | Wrapper | Permiso |
|---|---|---|---|---|
| `/pagos/ordenes/{orden_id}/confirmar` | POST | `PagoConfirmadoPresenter` | `PagoConfirmadoOut` | `TITULARIDAD_COMPRADOR` |
| `/pagos/izipay/notificacion` | POST | `PagoNotificacionPresenter` | `PagoConfirmadoOut` | servidor a servidor (firma) |
| `/pagos/ordenes/{orden_id}` | GET | `OrdenPagoPresenter` | `OrdenPagoOut` | `TITULARIDAD_COMPRADOR` |
"""

from asgiref.sync import sync_to_async
from injector import inject

from modules.pagos.domain.exceptions import (
    OrdenPagoNoEncontradaError,
    PagoNoAutorizadoError,
)
from modules.pagos.domain.ports import IPropietarioOrdenPagoService
from modules.pagos.domain.results.pago_result import (
    IntentoPagoResult,
    OrdenPagoResult,
    PagoConfirmadoResult,
)
from modules.pagos.domain.selectors.pago_selector import (
    OrdenPagoSelector,
    TransaccionPagoSelector,
)
from modules.pagos.infrastructure.izipay_session_service import IzipaySessionService
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)
from modules.pagos.domain.services.flujos.pago_confirmacion_flujo import (
    PagoConfirmacionFlujo,
)
from modules.pagos.domain.services.flujos.pago_intento_flujo import PagoIntentoFlujo


class PagosOrchestrator:
    """Fachada async del módulo de pagos."""

    @inject
    def __init__(
        self,
        confirmacion_flujo: PagoConfirmacionFlujo,
        intento_flujo: PagoIntentoFlujo,
        orden_selector: OrdenPagoSelector,
        transaccion_selector: TransaccionPagoSelector,
        estado_operativo_service: EstadoOperativoPagoService,
        propietario_service: IPropietarioOrdenPagoService,
        izipay_session: IzipaySessionService,
    ):
        self.confirmacion_flujo = confirmacion_flujo
        self.intento_flujo = intento_flujo
        self.orden_selector = orden_selector
        self.transaccion_selector = transaccion_selector
        self.estado_operativo_service = estado_operativo_service
        self.propietario_service = propietario_service
        self.izipay_session = izipay_session

    # ── RT-PG-01 · Confirmación desde el navegador ───────────────────────────

    async def confirmar_pago(
        self,
        *,
        orden_pago_id: str,
        payload: dict,
        persona_id: str | None,
        ambito_idempotencia: str = "",
        clave_idempotencia: str | None = None,
    ) -> PagoConfirmadoResult:
        """Confirma el pago de una orden a partir del reenvío del navegador."""
        return await self.confirmacion_flujo.confirmar_desde_navegador(
            orden_pago_id=orden_pago_id,
            payload=payload,
            persona_id=persona_id,
            ambito_idempotencia=ambito_idempotencia,
            clave_idempotencia=clave_idempotencia,
        )

    # ── RT-PG-02 · Notificación del proveedor ────────────────────────────────

    async def confirmar_notificacion(
        self,
        *,
        payload_http: str,
        signature: str,
    ) -> PagoConfirmadoResult:
        """Confirma el pago a partir de la notificación servidor a servidor."""
        return await self.confirmacion_flujo.confirmar_desde_notificacion(
            payload_http=payload_http,
            signature=signature,
        )

    # ── RT-PG-03 · Lectura del estado de una orden ───────────────────────────

    async def obtener_orden(
        self,
        *,
        orden_pago_id: str,
        persona_id: str | None,
    ) -> OrdenPagoResult:
        """Devuelve el estado de la orden con su veredicto y sus intentos.

        El veredicto lo calcula `EstadoOperativoPagoService`: el cliente nunca
        cruza los tres hechos por su cuenta (`RN-C07`).
        """
        orden = await sync_to_async(self.orden_selector.obtener_por_id)(
            orden_pago_id
        )
        if orden is None:
            raise OrdenPagoNoEncontradaError()

        await self._verificar_propiedad(orden_pago_id, persona_id)

        estado_operativo = await sync_to_async(
            self.estado_operativo_service.calcular_para_orden
        )(orden)

        estado_activacion = await sync_to_async(
            self.estado_operativo_service.calcular_activacion_para_orden
        )(orden)

        intentos = await self._intentos_publicos(orden_pago_id)
        origen_pago = await sync_to_async(self._origen)(orden)

        return OrdenPagoResult(
            id=str(orden.id),
            referencia=orden.referencia,
            estado=orden.estado,
            monto=orden.monto,
            moneda=orden.moneda,
            pagada_en=orden.pagada_en,
            creada_en=orden.created_at,
            estado_operativo=estado_operativo,
            estado_activacion=estado_activacion,
            intentos=intentos,
            origen_pago=origen_pago,
        )

    # ── Capacidad de módulo: reabrir el checkout ────────────────────────────

    async def abrir_intento(self, orden_pago_id: str) -> IntentoPagoResult:
        """Abre un intento nuevo sobre la orden existente.

        Reabrir el checkout **no** crea otra compra ni otra orden: crea un
        intento nuevo y retira el anterior, que queda en el historial
        (FR-04 I-4, RN-C04).
        """
        return await self.intento_flujo.abrir_intento(orden_pago_id)

    async def preparar_marketplace(self, token: str) -> dict:
        """Abre un intento Izipay para el único pedido que autoriza ``token``."""
        pedido = await sync_to_async(self._pedido_por_token)(token)
        if pedido is None or not pedido.compra_id or not pedido.compra.orden_pago_id:
            raise PagoNoAutorizadoError()

        orden = await sync_to_async(self.orden_selector.obtener_por_id)(
            pedido.compra.orden_pago_id
        )
        if orden is None:
            raise OrdenPagoNoEncontradaError()

        intento = await self.abrir_intento(str(orden.id))
        order_number = intento.referencia_proveedor[:10]
        comprador = pedido.comprador
        token_sesion = await self.izipay_session.abrir(
            transaction_id=intento.referencia_proveedor,
            order_number=order_number,
            amount=orden.monto,
            currency=orden.moneda,
            buyer_email=pedido.contacto_email or "cliente@marketplace.local",
            buyer_name=getattr(comprador, "nombres", "") or "CLIENTE",
            buyer_surname=getattr(comprador, "apellidos", "") or "VENTA",
        )
        return {
            "transaction_id": intento.referencia_proveedor,
            "order_number": order_number,
            "token": token_sesion,
            "merchant_code": self.izipay_session.shop_id,
            "amount": orden.monto,
            "currency": orden.moneda,
            "buyer_email": pedido.contacto_email or "cliente@marketplace.local",
            "buyer_name": getattr(comprador, "nombres", "") or "CLIENTE",
            "buyer_surname": getattr(comprador, "apellidos", "") or "VENTA",
        }

    async def confirmar_marketplace(
        self, token: str, payload: dict, clave_idempotencia: str | None = None
    ):
        """Confirma mediante el mismo coordinador una transacción del pedido privado."""
        pedido = await sync_to_async(self._pedido_por_token)(token)
        transaction_id = payload.get("transactionId")
        intento = await sync_to_async(
            self.transaccion_selector.obtener_por_referencia_proveedor
        )(transaction_id)
        if (
            pedido is None
            or intento is None
            or not pedido.compra_id
            or str(pedido.compra.orden_pago_id) != str(intento.orden_pago_id)
        ):
            raise PagoNoAutorizadoError()
        return await self.confirmar_pago(
            orden_pago_id=str(intento.orden_pago_id),
            payload=payload,
            persona_id=str(pedido.comprador_id),
            ambito_idempotencia=f"pagos:marketplace:{pedido.id}",
            clave_idempotencia=clave_idempotencia,
        )

    async def estado_transaccion_marketplace(self, token: str, transaction_id: str):
        """Lee sólo el intento que pertenece al pedido autorizado por el token."""
        pedido = await sync_to_async(self._pedido_por_token)(token)
        intento = await sync_to_async(
            self.transaccion_selector.obtener_por_referencia_proveedor
        )(transaction_id)
        if (
            pedido is None
            or intento is None
            or not pedido.compra_id
            or str(pedido.compra.orden_pago_id) != str(intento.orden_pago_id)
        ):
            raise PagoNoAutorizadoError()
        return intento

    @staticmethod
    def _pedido_por_token(token: str):
        from modules.marketplace.domain.models import Pedido

        if not token:
            return None
        return Pedido.objects.filter(token=token).select_related(
            "compra", "comprador"
        ).first()

    # ── Internos ────────────────────────────────────────────────────────────

    async def _verificar_propiedad(self, orden_pago_id: str, persona_id: str | None):
        """Exige que el actor sea el titular de la orden.

        El documento de identidad no es una credencial (RN-U04): la
        titularidad se comprueba contra la persona compradora.
        """
        if not persona_id:
            raise PagoNoAutorizadoError()
        es_propietario = await sync_to_async(self.propietario_service.es_propietario)(
            orden_pago_id, persona_id
        )
        if not es_propietario:
            raise PagoNoAutorizadoError()

    async def _intentos_publicos(self, orden_pago_id: str) -> list:
        """Los intentos de la orden proyectados a su forma pública.

        `referencia_proveedor` NO viaja: es dato técnico y sólo se expone en
        detalle técnico autorizado (FR-04 §1.3).
        """
        from modules.pagos.domain.schemas.pago_schemas import LineaIntentoData

        intentos = await sync_to_async(self.transaccion_selector.listar_por_orden)(
            orden_pago_id
        )
        return [
            LineaIntentoData(
                id=str(intento.id),
                intento=intento.intento,
                estado=intento.estado,
                verificada=intento.verificada,
                codigo_respuesta=intento.codigo_respuesta,
                metodo_pago=intento.metodo_pago,
                creada_en=intento.created_at,
            )
            for intento in intentos
        ]

    def _origen(self, orden) -> str:
        """Procedencia de la evidencia de la orden."""
        from modules.pagos.domain.constants import OrigenPago
        from modules.pagos.domain.models import TransaccionPago
        from modules.pagos.domain.constants import EstadoTransaccionPago

        existe = TransaccionPago.objects.filter(
            orden_pago_id=orden.id,
            estado=EstadoTransaccionPago.EXITO,
            verificada=True,
        ).exists()
        return OrigenPago.IZIPAY if existe else OrigenPago.SIN_PAGO


__all__ = ["PagosOrchestrator"]
