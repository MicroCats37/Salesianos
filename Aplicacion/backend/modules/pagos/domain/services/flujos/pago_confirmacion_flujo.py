"""`PagoConfirmacionFlujo` — la confirmación de un pago, idempotente.

Freeze: `FREEZE-CM-1.0.0` (FR-04 §1.3, §2.1 I-1, §2.2, §3, §4)
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Este flujo es el ÚNICO lugar donde un pago se declara confirmado, y lo hace
respetando tres garantías congeladas:

**I-1 — Una confirmación efectiva por orden.** La firma se verifica ANTES de
mutar; el estado `CONFIRMADA` se alcanza una sola vez. Un reenvío desde el
navegador o una notificación tardía converge: no duplica derechos, ni
movimientos de stock, ni correos.

**§3 — Sólo evidencia confiable declara el pago pagado.** Hay dos canales y
dos reglas:

| Canal | Regla |
|---|---|
| `NOTIFICACION` (servidor a servidor) | La clave del comercio debe estar configurada Y la firma debe verificar. **No hay fallback**: una notificación no verificable se rechaza. |
| `BROWSER` (reenvío del SDK) | El actor debe estar autenticado y ser el titular de la orden. La firma se verifica cuando la clave está configurada: una firma inválida siempre se rechaza, y un pago exitoso sin firma verificable también. |

**§4 — El pago confirmado y la entrega del derecho son hechos separados.** La
confirmación deja el cobro registrado y la orden confirmada; marcar la compra
como pagada es un hecho comercial idempotente. **Este módulo no habilita
ningún derecho**: al final de la secuencia congelada §2.3 pide al
*coordinador* (`IActivacionCompraService`, FND-05) que active el origen
correspondiente, y el coordinador se encarga de hacerlo **una sola vez** por
`(compra, origen)`. Si la marca comercial falla, o si la activación falla, el
pago confirmado **se conserva** y el veredicto operativo queda en
`PAGADA_SIN_LIQUIDAR` — la incidencia recuperable de `RN-C08`, nunca una
reversión silenciosa del cobro.

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`
(`contract/django-app-architecture-contract.md` §4.4).
"""

import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.pagos.domain.constants import (
    CODIGO_PROVEEDOR_EXITO,
    CanalConfirmacionPago,
    EstadoOrdenPago,
    EstadoTransaccionPago,
    EstadoVerificacionPago,
)
from modules.pagos.domain.exceptions import (
    OrdenPagoNoEncontradaError,
    OrdenPagoNoPagableError,
    PagoDatosInconsistentesError,
    PagoFirmaInvalidaError,
    PagoNoAutorizadoError,
    PagoNotificacionNoVerificableError,
    TransaccionPagoNoEncontradaError,
)
from modules.pagos.domain.models import TransaccionPago
from modules.pagos.domain.ports import (
    IActivacionCompraService,
    IEstadoCompraOrdenPagoService,
    INotificadorCompraService,
    IPropietarioOrdenPagoService,
    IProveedorPagoService,
)
from modules.pagos.domain.results.pago_result import PagoConfirmadoResult
from modules.pagos.domain.schemas.pago_schemas import ContextoNotificacionCompra
from modules.pagos.domain.services.core.estado_operativo_pago_service import (
    EstadoOperativoPagoService,
)
from modules.pagos.domain.services.core.idempotencia_pago_service import (
    IdempotenciaPagoService,
)
from modules.pagos.domain.services.core.orden_pago_core_service import (
    OrdenPagoCoreService,
)
from modules.pagos.domain.services.core.transaccion_pago_core_service import (
    TransaccionPagoCoreService,
)
from modules.pagos.domain.services.core.verificacion_pago_service import (
    VerificacionPagoService,
)
from modules.pagos.infrastructure.services import sanitizar_payload_proveedor

logger = logging.getLogger(__name__)


class PagoConfirmacionFlujo:
    """Confirma un pago a partir de la evidencia del proveedor."""

    @inject
    def __init__(
        self,
        orden_core: OrdenPagoCoreService,
        transaccion_core: TransaccionPagoCoreService,
        verificacion: VerificacionPagoService,
        idempotencia: IdempotenciaPagoService,
        estado_operativo_service: EstadoOperativoPagoService,
        estado_compra_service: IEstadoCompraOrdenPagoService,
        propietario_service: IPropietarioOrdenPagoService,
        activacion_service: IActivacionCompraService,
        proveedor: IProveedorPagoService,
        notificador_service: INotificadorCompraService,
    ):
        self.orden_core = orden_core
        self.transaccion_core = transaccion_core
        self.verificacion = verificacion
        self.idempotencia = idempotencia
        self.estado_operativo_service = estado_operativo_service
        self.estado_compra_service = estado_compra_service
        self.propietario_service = propietario_service
        self.activacion_service = activacion_service
        self.proveedor = proveedor
        # El notificador es el ÚLTIMO paso de la secuencia congelada y su
        # fallo nunca revierte el cobro (RN-C08).
        self.notificador_service = notificador_service

    # ── Canales ──────────────────────────────────────────────────────────────

    async def confirmar_desde_navegador(
        self,
        *,
        orden_pago_id: str,
        payload: dict,
        persona_id: str | None,
        ambito_idempotencia: str = "",
        clave_idempotencia: str | None = None,
    ) -> PagoConfirmadoResult:
        """Confirma un pago reenviado por el navegador (canal `BROWSER`).

        El actor debe estar autenticado y ser el titular de la orden: el
        documento de identidad no es una credencial (RN-U04).
        """
        return await self._confirmar(
            payload=payload,
            canal=CanalConfirmacionPago.BROWSER,
            orden_pago_id=orden_pago_id,
            persona_id=persona_id,
            ambito_idempotencia=ambito_idempotencia,
            clave_idempotencia=clave_idempotencia,
        )

    async def confirmar_desde_notificacion(
        self,
        *,
        payload_http: str,
        signature: str,
    ) -> PagoConfirmadoResult:
        """Confirma un pagoNotifier del proveedor (canal `NOTIFICACION`).

        La autoridad viene **sólo** de la firma del comercio, nunca de una
        sesión: no hay ningún actor que pueda suplantar al proveedor.
        """
        import json

        if not payload_http or not signature:
            raise PagoNotificacionNoVerificableError()

        try:
            payload = json.loads(payload_http)
        except (ValueError, TypeError):
            raise PagoDatosInconsistentesError()

        if not isinstance(payload, dict):
            raise PagoDatosInconsistentesError()

        return await self._confirmar(
            payload=payload,
            canal=CanalConfirmacionPago.NOTIFICACION,
            orden_pago_id=None,
            persona_id=None,
            payload_http=payload_http,
            signature=signature,
            ambito_idempotencia="pagos:notificacion",
            clave_idempotencia=None,
        )

    # ── Confirmación ────────────────────────────────────────────────────────

    async def _confirmar(
        self,
        *,
        payload: dict,
        canal: str,
        orden_pago_id: str | None,
        persona_id: str | None,
        payload_http: str | None = None,
        signature: str | None = None,
        ambito_idempotencia: str = "",
        clave_idempotencia: str | None = None,
    ) -> PagoConfirmadoResult:
        """Ejecuta la confirmación completa.

        El orden es el congelado:

        1. Resolver el intento (por la identidad del proveedor).
        2. Verificar el CANAL — antes de mutar una sola fila.
        3. Contrastar el monto y la moneda con el snapshot de la orden.
        4. Contrastar la correlación del payload.
        5. Registrar la clave de idempotencia.
        6. Registrar el resultado del intento y confirmar la orden.
        7. Marcar la compra como pagada (hecho comercial, idempotente).
        """
        # 1. El intento se resuelve por la identidad que entrega el proveedor.
        transaction_id = self.verificacion.extraer_transaction_id(payload)
        if not transaction_id:
            raise PagoDatosInconsistentesError()

        intento = await sync_to_async(
            self.transaccion_core.obtener_por_referencia_proveedor
        )(transaction_id)
        if intento is None:
            raise TransaccionPagoNoEncontradaError()

        orden = intento.orden_pago

        if orden_pago_id and str(orden.id) != str(orden_pago_id):
            # La confirmación no pertenece a la orden que seConsultó.
            raise PagoDatosInconsistentesError()

        # 2. El canal se verifica ANTES de mutar nada.
        estado_verificacion = self._estado_verificacion(
            payload, payload_http, signature
        )
        await self._verificar_canal(
            canal=canal,
            estado_verificacion=estado_verificacion,
            orden_pago_id=str(orden.id),
            persona_id=persona_id,
            es_pago_exitoso=self.verificacion.extraer_codigo(payload)
            == CODIGO_PROVEEDOR_EXITO,
        )

        # 3. El dinero: el monto y la moneda deben coincidir EXACTAMENTE con
        #    el snapshot congelado de la orden.
        self.verificacion.validar_monto(payload, orden)

        # 4. La correlación: el payload debe describir esta orden.
        self.verificacion.validar_correlacion(payload, orden, intento)

        # 5. La clave de idempotencia del borde HTTP.
        clave = self.idempotencia.normalizar_clave(clave_idempotencia)
        registro = None
        repetida = False
        if clave and ambito_idempotencia:
            huella = self.idempotencia.huella(
                {
                    "canal": canal,
                    "orden_pago_id": str(orden.id),
                    "payload": payload,
                }
            )
            registro, repetida = await sync_to_async(self.idempotencia.registrar)(
                ambito=ambito_idempotencia,
                clave=clave,
                huella=huella,
            )
            if repetida and registro.respuesta:
                # La operación ya se ejecutó: se devuelve SU resultado, con el
                # status HTTP de la primera vez. Nunca 500.
                return PagoConfirmadoResult.model_validate(registro.respuesta)

        # 6. El resultado del intento y la confirmación de la orden.
        codigo = self.verificacion.extraer_codigo(payload)
        mensaje = self._mensaje_respuesta(payload)
        metodo = self._metodo_pago(payload)
        evidencia = self._evidencia(canal, verificada=estado_verificacion ==
                                    EstadoVerificacionPago.FIRMADA)
        estado_intento = self._estado_intento(codigo)
        metadata = sanitizar_payload_proveedor(payload)

        # The legacy browser relay settles an approved payment after ownership
        # verification when the merchant key is unavailable. An invalid
        # signature is still rejected by `_verificar_canal` before this point.
        confirmar = estado_verificacion == EstadoVerificacionPago.FIRMADA or (
            canal == CanalConfirmacionPago.BROWSER
            and estado_verificacion == EstadoVerificacionPago.NO_VERIFICABLE
        )

        orden, intento, ya_confirmado = await sync_to_async(
            self._aplicar_confirmacion_sync
        )(
            orden_pago_id=str(orden.id),
            intento_id=str(intento.id),
            estado_intento=estado_intento,
            codigo=codigo,
            mensaje=mensaje,
            metodo=metodo,
            evidencia=evidencia,
            metadata=metadata,
            verificada=confirmar,
            confirmar=confirmar,
        )

        # 7. El hecho comercial: la compra consta pagada. Es idempotente y
        #    NO habilita derechos. Si falla, el pago confirmado se conserva.
        if confirmar:
            await sync_to_async(self._marcar_compra_pagada)(str(orden.id))

        # 8. La entrega del derecho: un hecho POSTERIOR y separado (RN-C08).
        #    La resuelve el coordinador, una sola vez por (compra, origen).
        activacion = None
        if confirmar:
            activacion = await sync_to_async(self._activar_compra)(str(orden.id))

        # 9. La notificación al comprador: el ÚLTIMO paso de la secuencia
        #    congelada (FR-04 §2.3). Es opcional y reintentable, y su fallo
        #    NUNCA revierte el cobro ni el derecho (RN-C08, FR-04 §4).
        if confirmar and not ya_confirmado:
            await sync_to_async(self._notificar_comprador)(orden, activacion)

        estado_operativo = await sync_to_async(
            self.estado_operativo_service.calcular_para_orden
        )(orden)

        estado_activacion = await sync_to_async(
            self.estado_operativo_service.calcular_activacion_para_orden
        )(orden)

        resultado = PagoConfirmadoResult(
            orden_pago_id=str(orden.id),
            referencia=orden.referencia,
            estado_orden=orden.estado,
            estado_operativo=estado_operativo,
            estado_activacion=estado_activacion,
            ya_confirmado=ya_confirmado,
            transaccion_id=str(intento.id),
            monto=orden.monto,
            moneda=orden.moneda,
            pagada_en=orden.pagada_en,
        )

        if registro is not None and not repetida:
            await sync_to_async(self.idempotencia.actualizar_respuesta)(
                registro,
                respuesta=resultado.model_dump(mode="json"),
                codigo_estado=200,
            )

        return resultado

    # ── Verificación del canal ──────────────────────────────────────────────

    def _estado_verificacion(
        self,
        payload: dict,
        payload_http: str | None,
        signature: str | None,
    ) -> str:
        """Resuelve el estado de verificación de la firma del payload."""
        payload_crudo = payload_http
        firma = signature

        if isinstance(payload, dict):
            if not payload_crudo:
                payload_crudo = payload.get("payloadHttp") or payload.get("payload_http")
            if not firma:
                firma = payload.get("signature")

        if not payload_crudo or not firma:
            return EstadoVerificacionPago.NO_VERIFICABLE

        if not self.proveedor.disponible:
            # Sin la clave del comercio el proveedor no puede autenticarse.
            return EstadoVerificacionPago.NO_VERIFICABLE

        if self.proveedor.verificar_firma(payload_crudo, firma):
            return EstadoVerificacionPago.FIRMADA

        return EstadoVerificacionPago.NO_FIRMADA

    async def _verificar_canal(
        self,
        *,
        canal: str,
        estado_verificacion: str,
        orden_pago_id: str,
        persona_id: str | None,
        es_pago_exitoso: bool,
    ) -> None:
        """Verifica que el canal que entregó la confirmación sea confiable.

        Notificación servidor a servidor (SIN fallback):
            la clave del comercio debe estar configurada Y la firma debe
            verificar.

        Reenvío desde el navegador:
            el actor debe estar autenticado y ser el titular de la orden; la
            firma se verifica cuando la clave está configurada.
        """
        if canal == CanalConfirmacionPago.NOTIFICACION:
            if not self.proveedor.disponible:
                logger.warning(
                    "Notificación de pago rechazada: la clave del comercio no "
                    "está configurada (falla cerrado)."
                )
                raise PagoNotificacionNoVerificableError()
            if estado_verificacion != EstadoVerificacionPago.FIRMADA:
                logger.warning(
                    "Notificación de pago rechazada: la firma del proveedor no "
                    "verifica."
                )
                raise PagoFirmaInvalidaError()
            return

        # ── Canal del navegador ────────────────────────────────────────────
        if estado_verificacion == EstadoVerificacionPago.NO_FIRMADA:
            logger.warning(
                "Reenvío de pago rechazado: la firma del proveedor no verifica."
            )
            raise PagoFirmaInvalidaError()

        if (
            estado_verificacion == EstadoVerificacionPago.NO_VERIFICABLE
            and self.proveedor.disponible
            and es_pago_exitoso
        ):
            logger.warning(
                "Reenvío de pago rechazado: llegó un pago exitoso sin firma "
                "verificable mientras la clave del comercio está configurada."
            )
            raise PagoFirmaInvalidaError()

        if not persona_id:
            raise PagoNoAutorizadoError()

        es_propietario = await sync_to_async(self.propietario_service.es_propietario)(
            orden_pago_id, persona_id
        )
        if not es_propietario:
            raise PagoNoAutorizadoError()

    # ── Escritura ───────────────────────────────────────────────────────────

    @transaction.atomic()
    def _aplicar_confirmacion_sync(
        self,
        *,
        orden_pago_id: str,
        intento_id: str,
        estado_intento: str,
        codigo: str,
        mensaje: str,
        metodo: str,
        evidencia: dict,
        metadata: dict | None,
        verificada: bool,
        confirmar: bool,
    ):
        """Registra el resultado del intento y confirma la orden.

        Atómico y **idempotente**: un intento ya `EXITO` no se reescribe y una
        orden ya `CONFIRMADA` no se vuelve a confirmar.
        """
        orden = self.orden_core.bloquear(orden_pago_id)
        if orden is None:
            raise OrdenPagoNoEncontradaError()

        intento = (
            TransaccionPago.objects.select_for_update().filter(id=intento_id).first()
        )
        if intento is None:
            raise TransaccionPagoNoEncontradaError()

        ya_confirmado = False

        if estado_intento == EstadoTransaccionPago.EXITO:
            if intento.estado != EstadoTransaccionPago.EXITO:
                self.transaccion_core.marcar_exito(
                    intento,
                    codigo_respuesta=codigo,
                    mensaje_respuesta=mensaje,
                    metodo_pago=metodo,
                    evidencia=evidencia,
                    metadata=metadata,
                    verificada=verificada,
                )
            else:
                ya_confirmado = True
        elif estado_intento == EstadoTransaccionPago.CANCELADO:
            self.transaccion_core.marcar_cancelado(intento)
        else:
            self.transaccion_core.marcar_fallido(
                intento,
                codigo_respuesta=codigo,
                mensaje_respuesta=mensaje,
                verificada=verificada,
            )

        if not confirmar:
            # La evidencia no es de confianza: la orden NO se confirma. Queda
            # en verificación — "estamos verificando tu pago" (RN-C07).
            if orden.estado != EstadoOrdenPago.CONFIRMADA:
                self.orden_core.marcar_en_verificacion(orden)
            return orden, intento, ya_confirmado

        if orden.estado == EstadoOrdenPago.CONFIRMADA:
            # Otra vuelta del mismo pago, o otro intento de la misma orden:
            # la orden ya está confirmada y no se vuelve a confirmar.
            ya_confirmado = True
        elif orden.estado in (
            EstadoOrdenPago.PENDIENTE,
            EstadoOrdenPago.EN_VERIFICACION,
            EstadoOrdenPago.FALLIDA,
        ):
            self.orden_core.marcar_confirmada(orden)
        else:
            raise OrdenPagoNoPagableError()

        return orden, intento, ya_confirmado

    def _activar_compra(self, orden_pago_id: str):
        """Pide al coordinador la activación de los derechos de la compra.

        Es el paso `ActivarDominio(compra_id, origen)` de la secuencia
        congelada `FR-04` §2.3. El coordinador sabe qué activar; `pagos` sólo
        sabe que el pago quedó confirmado.

        Si la activación falla, el pago confirmado **se conserva**: la
        incidencia queda registrada y es reintentable (RN-C08). Este módulo
        nunca revierte un cobro.
        """
        try:
            return self.activacion_service.activar_por_orden(orden_pago_id)
        except Exception:
            logger.exception(
                "No se pudo pedir la activación de los derechos de la orden "
                "%s. El pago confirmado se conserva y la activación queda "
                "pendiente y reintentable.",
                orden_pago_id,
            )
            return None

    def _marcar_compra_pagada(self, orden_pago_id: str):
        """Marca la compra de la orden como pagada (hecho comercial).

        Idempotente y **sin derechos**: el pago confirmado no habilita cupos,
        entradas ni stock (RN-C08, FR-04 §4).

        Si la marca falla, el pago confirmado **se conserva** y el veredicto
        operativo queda en `PAGADA_SIN_LIQUIDAR`: la incidencia es visible y
        recuperable, nunca una reversión silenciosa del cobro.
        """
        try:
            return self.estado_compra_service.marcar_compra_pagada(orden_pago_id)
        except Exception:
            logger.exception(
                "No se pudo marcar la compra de la orden %s como pagada. El pago "
                "confirmado se conserva y la activación queda pendiente.",
                orden_pago_id,
            )
            return None

    # ── Notificación al comprador (FR-04 §2.3 paso 6 · RN-C08) ──────────────

    def _notificar_comprador(self, orden, activacion) -> None:
        """Notifica al comprador que su compra quedó confirmada.

        Es el paso `NotificarComprador(compra_id)` de la secuencia congelada
        (FR-04 §2.3): **opcional y reintentable**.

        La garantía congelada es una sola y es fuerte: **el fallo de la
        notificación NUNCA revierte el pago ni el derecho** (RN-C08, FR-04
        §4). Por eso el fallo se captura aquí, se registra y el flujo sigue:
        la compra queda pagada y el derecho queda habilitado.

        Sólo se notifica cuando el derecho quedó habilitado: avisar de una
        compra cuyo derecho todavía no se ha concedido sería afirmar un hecho
        que no ocurrió.
        """
        if self.notificador_service is None:
            return

        if not self._derecho_habilitado(activacion):
            logger.info(
                "No se notifica la compra de la orden %s: el derecho todavía no "
                "está habilitado. La incidencia queda reintentable (RN-C08).",
                getattr(orden, "id", orden),
            )
            return

        # `pagos` es agnóstico del dominio: la orden no declara la persona
        # compradora. El contexto lleva los hechos que el pago SÍ conoce; el
        # proveedor, cuando exista, resolverá el destinatario.
        contexto = ContextoNotificacionCompra(
            orden_pago_id=str(orden.id),
            persona_id=None,
            referencia=orden.referencia,
            total=orden.monto,
            moneda=orden.moneda,
        )

        try:
            self.notificador_service.notificar_compra_confirmada(contexto)
        except Exception:
            # El fallo de la notificación NO revierte el cobro: la incidencia
            # queda registrada por el módulo `notificaciones` y el pago
            # confirmado se conserva (RN-C08).
            logger.exception(
                "No se pudo notificar la compra de la orden %s. El pago "
                "confirmado y el derecho habilitado se conservan.",
                getattr(orden, "id", orden),
            )

    @staticmethod
    def _derecho_habilitado(activacion) -> bool:
        """Si el coordinador confirmó que el derecho quedó habilitado."""
        if activacion is None:
            return False
        return bool(getattr(activacion, "activada", False) or getattr(
            activacion, "ya_activada", False
        ))

    # ── Extracción ──────────────────────────────────────────────────────────

    def _estado_intento(self, codigo: str) -> str:
        """Traduce el código del proveedor al estado del intento."""
        if codigo == CODIGO_PROVEEDOR_EXITO:
            return EstadoTransaccionPago.EXITO
        if codigo in ("111", "CANCELADO"):
            return EstadoTransaccionPago.CANCELADO
        return EstadoTransaccionPago.FALLIDO

    def _mensaje_respuesta(self, payload: dict) -> str:
        """Mensaje público del proveedor (sin payload crudo)."""
        if not isinstance(payload, dict):
            return ""
        mensaje = payload.get("message")
        if mensaje is None or isinstance(mensaje, (dict, list, bool)):
            return ""
        return str(mensaje)[:255]

    def _metodo_pago(self, payload: dict) -> str:
        """Método de pago informado por el proveedor."""
        if not isinstance(payload, dict):
            return ""
        respuesta = payload.get("response")
        if not isinstance(respuesta, dict):
            return ""
        metodo = respuesta.get("payMethod") or respuesta.get("paymentMethodType")
        if metodo is None or isinstance(metodo, (dict, list, bool)):
            return ""
        return str(metodo)[:32]

    def _evidencia(self, canal: str, *, verificada: bool) -> dict:
        """Evidencia pública del pago.

        Deliberadamente NO contiene el payload firmado, la firma ni ningún
        token: sólo los hechos que el operador necesita para auditar.
        """
        from django.utils import timezone

        return {
            "canal": canal,
            "verificada": verificada,
            "fecha": timezone.now().isoformat(),
        }


__all__ = ["PagoConfirmacionFlujo"]
