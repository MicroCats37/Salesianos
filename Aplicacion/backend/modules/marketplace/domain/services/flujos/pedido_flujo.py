"""`PedidoFlujo` — los casos de uso del pedido de marketplace.

Packet: `DOM-05` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.4

El flujo es ASYNC y es el ÚNICO lugar donde se abre `transaction.atomic()`.

**RN-C03 / RN-C04 — un reintento NO duplica el pedido.** La identidad de una
intención de compra es la HUELLA de sus artículos. Antes de crear, el flujo
consulta si ya existe un pedido para esa intención; si existe, lo RECUPERA
(con su snapshot congelado y su compra pendiente) en vez de crear otro.

**RN-C08 / RN-M07 — pago, pedido y entrega son hechos separados.** La
reconciliación mueve el estado del PEDIDO según el hecho del PAGO y NUNCA
toca el estado de la ENTREGA: un pedido pagado sigue con la entrega
`PENDIENTE` (`QA-M04`).
"""

from asgiref.sync import sync_to_async
from django.db import IntegrityError, transaction
from injector import inject

from modules.marketplace.domain.constants import (
    MONEDA_PEDIDO,
    EstadoPagoPedido,
    EstadoPedido,
)
from modules.marketplace.domain.exceptions import (
    PedidoNoAutorizadoError,
    PedidoNoEncontradoError,
)
from modules.marketplace.domain.ports.alcance_edicion import IAlcanceEdicion
from modules.marketplace.domain.ports.comercio import ICommerceMarketplaceService
from modules.marketplace.domain.results.pedido_result import (
    PedidoCreadoResult,
    PedidoSeguimientoResult,
)
from modules.marketplace.domain.schemas.pedido_schemas import (
    CompraMarketplaceData,
    LineaCompraMarketplace,
    PedidoCreateData,
)
from modules.marketplace.domain.selectors.pedido_selector import PedidoSelector
from modules.marketplace.domain.services.core.pedido_core_service import (
    PedidoCoreService,
)


class PedidoFlujo:
    """Casos de uso del pedido de marketplace."""

    @inject
    def __init__(
        self,
        core_service: PedidoCoreService,
        selector: PedidoSelector,
        alcance: IAlcanceEdicion,
        comercio: ICommerceMarketplaceService,
    ):
        self.core_service = core_service
        self.selector = selector
        self.alcance = alcance
        self.comercio = comercio

    # ── Alta del pedido ─────────────────────────────────────────────────────

    async def crear_pedido(
        self,
        data: PedidoCreateData,
        persona_id: str,
    ) -> PedidoCreadoResult:
        """Crea el pedido de una intención de compra, o la recupera.

        El precio lo resuelve y congela el servidor (RN-C02); la entrega
        nace `PENDIENTE` (RN-M07).
        """
        # 1. Las reglas del pedido, ANTES de tocar la base de datos.
        self.core_service.validar_tipos(data.items)
        self.core_service.validar_cantidades(data.items)

        # 2. El alcance lo resuelve el servidor: el cliente no elige la
        #    edición (RN-E01, RN-E02).
        edicion = await sync_to_async(self._resolver_edicion)()

        # 3. Los productos se resuelven contra el catálogo y sus precios se
        #    CONGELAN (RN-C02, RN-M03).
        lineas = await sync_to_async(self.core_service.resolver_lineas)(
            edicion.id,
            data.items,
        )
        total = self.core_service.calcular_total(lineas)

        # 4. La huella identifica la INTENCIÓN (artículos y cantidades), NO
        #    los precios: un cambio de oferta no abre otra intención.
        huella = self.core_service.calcular_huella(data.items)

        # 5. ¿Existe ya un pedido para esta intención? (RN-C04)
        previo = await sync_to_async(self.selector.obtener_por_huella)(
            persona_id,
            edicion.id,
            huella,
        )
        if previo is not None:
            previo = await self._sincronizar_estado(previo)
            if previo.estado == EstadoPedido.PENDIENTE:
                # Un pedido pendiente SIN compra es un alta a MEDIO CAMINO: se
                # le abre SU compra (con el snapshot ya congelado) en vez de
                # duplicar el pedido. El reintento, por tanto, es siempre
                # recuperable (RN-C03, RN-C04).
                if not previo.compra_id:
                    previo = await self._abrir_compra_de(previo)
                return await self._proyectar_creado(previo, recuperado=True)

        # 6. Alta del pedido y de su detalle.
        try:
            pedido, detalles = await sync_to_async(self._crear_pedido_sync)(
                edicion.id,
                persona_id,
                total,
                huella,
                lineas,
            )
        except IntegrityError as exc:
            # Otra vuelta de la MISMA intención ganó la carrera: la que ganó
            # es la buena y se recupera (el índice parcial lo garantiza).
            return await self._recuperar_tras_carrera(
                persona_id,
                edicion.id,
                huella,
                exc,
            )

        # 7. La compra la crea `commerce` a través de su interfaz CONGELADA:
        #    este flujo sólo entrega el snapshot ya resuelto por el servidor.
        compra = await self.comercio.crear_o_reutilizar_compra(
            CompraMarketplaceData(
                persona_id=str(persona_id),
                lineas=[
                    LineaCompraMarketplace(
                        concepto_tipo=linea.tipo_concepto,
                        concepto_id=linea.concepto_id,
                        concepto_nombre=linea.concepto_nombre,
                        cantidad=linea.cantidad,
                        precio_unitario=linea.precio_unitario,
                        precio_aplicado=linea.precio_aplicado,
                    )
                    for linea in lineas
                ],
                referencia=self.core_service.referencia_compra(pedido.id),
                moneda=MONEDA_PEDIDO,
                total=total,
            )
        )

        # 8. El pedido queda vinculado con la compra que lo financia.
        pedido = await sync_to_async(self.core_service.vincular_compra)(
            pedido,
            compra.compra_id,
        )
        return await self._proyectar_creado(
            pedido,
            recuperado=False,
            compra=compra,
            detalles=detalles,
        )

    @transaction.atomic()
    def _crear_pedido_sync(self, edicion_id, persona_id, total, huella, lineas):
        """Alta atómica del pedido y de su detalle."""
        pedido = self.core_service.crear(
            edicion_id=edicion_id,
            comprador_id=persona_id,
            total=total,
            moneda=MONEDA_PEDIDO,
            token=self.core_service.generar_token(),
            huella=huella,
        )
        detalles = self.core_service.crear_detalles(pedido, lineas)
        return pedido, detalles

    async def _recuperar_tras_carrera(self, persona_id, edicion_id, huella, exc):
        """Recupera el pedido que ganó la carrera de un alta simultánea.

        Si el pedido ganador ya NO está pendiente (se pagó entre medias), la
        carrera no se puede recuperar: el error original de integridad se
        propaga.
        """
        previo = await sync_to_async(self.selector.obtener_por_huella)(
            persona_id,
            edicion_id,
            huella,
        )
        if previo is None:
            raise exc
        previo = await self._sincronizar_estado(previo)
        if previo.estado != EstadoPedido.PENDIENTE:
            raise exc
        return await self._proyectar_creado(previo, recuperado=True)

    # ── Consulta del pedido ─────────────────────────────────────────────────

    async def obtener_pedido_por_token(
        self,
        token: str,
        persona_id_actor: str | None,
    ) -> PedidoSeguimientoResult:
        """El pedido de un enlace privado, con su estado reconciliado.

        La autorización: un token desconocido NO revela nada (404); un actor
        AUTENTICADO que no es el comprador del pedido NO puede consultarlo
        (403), aunque conozca el token (RN-U02, FR-03 §2.1). Un enlace de
        invitado (sin sesión) se abre con el token, que es la credencial.
        """
        pedido = await sync_to_async(self.selector.obtener_por_token)(token)
        if pedido is None:
            raise PedidoNoEncontradoError()
        if (
            persona_id_actor is not None
            and str(pedido.comprador_id) != str(persona_id_actor)
        ):
            raise PedidoNoAutorizadoError()

        pedido = await self._sincronizar_estado(pedido)
        detalles = await sync_to_async(self.selector.listar_detalles)(pedido.id)
        compra = await self._hechos_de_la_compra(pedido)
        return self.core_service.result_de(
            pedido,
            detalles,
            compra.estado_pago if compra else EstadoPagoPedido.PENDIENTE,
            compra.orden_pago_id if compra else None,
        )

    # ── Internos ────────────────────────────────────────────────────────────

    async def _abrir_compra_de(self, pedido):
        """Abre la compra que financia un pedido pendiente ya existente.

        El snapshot del pedido ya está CONGELADO (RN-M03): la compra se crea
        con esas MISMAS líneas, nunca con los precios vigentes del catálogo. La
        referencia de la compra es la del propio pedido (`MARKETPLACE:{id}`),
        así que un reintento posterior reutiliza la MISMA compra en vez de
        abrir otra (FR-04 I-4, RN-C04).
        """
        detalles = await sync_to_async(self.selector.listar_detalles)(pedido.id)
        compra = await self.comercio.crear_o_reutilizar_compra(
            CompraMarketplaceData(
                persona_id=str(pedido.comprador_id),
                lineas=[
                    LineaCompraMarketplace(
                        concepto_tipo=detalle.tipo_concepto,
                        concepto_id=detalle.concepto_id,
                        concepto_nombre=detalle.concepto_nombre,
                        cantidad=detalle.cantidad,
                        precio_unitario=detalle.precio_unitario,
                        precio_aplicado=detalle.precio_aplicado,
                    )
                    for detalle in detalles
                ],
                referencia=pedido.referencia,
                moneda=pedido.moneda,
                total=pedido.total,
            )
        )
        return await sync_to_async(self.core_service.vincular_compra)(
            pedido,
            compra.compra_id,
        )

    def _resolver_edicion(self):
        """La edición vigente con el módulo `marketplace` habilitado."""
        from modules.marketplace.domain.constants import MODULO_LOGICO
        from modules.marketplace.domain.exceptions import ModuloNoHabilitadoError

        edicion = self.alcance.resolver_actual()
        if not edicion.modulo_habilitado(MODULO_LOGICO):
            raise ModuloNoHabilitadoError()
        return edicion

    async def _sincronizar_estado(self, pedido):
        """Reconcilia el estado del PEDIDO con el hecho del PAGO.

        Idempotente y **sin efectos sobre la entrega**: un pedido cuyo pago
        se confirma pasa a `PAGADO`, pero su entrega sigue `PENDIENTE`
        (RN-M07, `QA-M04`).
        """
        if pedido.estado != EstadoPedido.PENDIENTE or not pedido.compra_id:
            return pedido

        compra = await self._hechos_de_la_compra(pedido)
        if compra is None:
            return pedido

        if compra.estado_pago == EstadoPagoPedido.CONFIRMADO:
            estado = EstadoPedido.PAGADO
        elif compra.estado_pago == EstadoPagoPedido.NO_COMPLETADO:
            estado = EstadoPedido.CANCELADO
        else:
            return pedido

        return await sync_to_async(self.core_service.marcar_estado)(pedido, estado)

    async def _hechos_de_la_compra(self, pedido):
        """Los hechos de la compra que financia el pedido, si existe."""
        if not pedido.compra_id:
            return None
        return await self.comercio.hechos_compra(pedido.compra_id)

    async def _proyectar_creado(
        self,
        pedido,
        *,
        recuperado: bool,
        compra=None,
        detalles=None,
    ) -> PedidoCreadoResult:
        """Proyecta el pedido como respuesta del alta."""
        if detalles is None:
            detalles = await sync_to_async(self.selector.listar_detalles)(pedido.id)
        if compra is None:
            compra = await self._hechos_de_la_compra(pedido)

        seguimiento = self.core_service.result_de(
            pedido,
            detalles,
            compra.estado_pago if compra else EstadoPagoPedido.PENDIENTE,
            compra.orden_pago_id if compra else None,
        )
        return PedidoCreadoResult(
            **seguimiento.model_dump(),
            token=pedido.token,
            recuperado=recuperado,
        )


__all__ = ["PedidoFlujo"]
