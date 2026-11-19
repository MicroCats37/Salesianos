"""Operaciones de escritura y proyección del pedido de marketplace.

Packet: `DOM-05` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.3

Este servicio es SYNC y NO abre `transaction.atomic()`: el flujo (el único
lugar con atomicidad, §4.4) provee la transacción.

Reglas que vive aquí:

- **RN-C01 — no hay carrito combinado.** Un pedido sólo puede contener
  artículos de la tienda.
- **RN-C02 — el servidor congela el precio.** El precio se resuelve contra
  el catálogo vigente y se congela; el cliente no impone un importe.
- **RN-M03 — el histórico no cambia.** La línea guarda el precio unitario y
  el precio aplicado del momento del pedido.
- **RN-M07 — pagado NO es entregado.** `marcar_estado` mueve el estado del
  PEDIDO y NUNCA el de la entrega.
"""

import hashlib
import secrets
from decimal import Decimal

from modules.marketplace.domain.constants import (
    BYTES_TOKEN_PEDIDO,
    MAX_CANTIDAD_ITEM_PEDIDO,
    AccionPedido,
    EstadoEntregaPedido,
    EstadoPagoPedido,
    EstadoPedido,
    EstadoProducto,
    TipoItemPedido,
)
from modules.marketplace.domain.exceptions import (
    PedidoCantidadInvalidaError,
    PedidoItemNoPermitidoError,
    PedidoItemsMixtosError,
    ProductoNoDisponibleError,
    ProductoNoEncontradoError,
)
from modules.marketplace.domain.results.pedido_result import (
    PedidoLineaResult,
    PedidoSeguimientoResult,
)
from modules.marketplace.domain.schemas.pedido_schemas import PedidoLineaResuelta
from modules.marketplace.domain.selectors.pedido_selector import PedidoSelector
from modules.marketplace.domain.selectors.producto_selector import ProductoSelector


class PedidoCoreService:
    """Operaciones de escritura y proyección del pedido."""

    def __init__(
        self,
        producto_selector: ProductoSelector = None,
        pedido_selector: PedidoSelector = None,
    ):
        self.producto_selector = producto_selector or ProductoSelector()
        self.pedido_selector = pedido_selector or PedidoSelector()

    # ── Validaciones del pedido (antes de tocar la base de datos) ───────────

    @staticmethod
    def validar_tipos(items) -> None:
        """Un pedido sólo puede contener artículos de la tienda (RN-C01).

        Se rechazan DOS situaciones, con dos códigos distintos:

        - artículos de DISTINTOS orígenes mezclados → `PEDIDO_ITEMS_MIXTOS`;
        - artículos que no son de la tienda (un pase, una inscripción) →
          `PEDIDO_ITEM_NO_PERMITIDO`.

        Un pase o una inscripción se compran por su propio endpoint y su
        propio flujo (DEC-10): nunca dentro de un pedido de marketplace.
        """
        tipos = {str(item.tipo).strip().upper() for item in items}
        if len(tipos) > 1:
            raise PedidoItemsMixtosError()
        if tipos != {TipoItemPedido.PRODUCTO}:
            raise PedidoItemNoPermitidoError()

    @staticmethod
    def validar_cantidades(items) -> None:
        """La cantidad de cada artículo tiene que ser admisible.

        La cantidad la valida el servidor: el cliente no puede pedir cero ni
        superar el máximo comercial.
        """
        for item in items:
            if item.cantidad < 1 or item.cantidad > MAX_CANTIDAD_ITEM_PEDIDO:
                raise PedidoCantidadInvalidaError()

    # ── Identidad de la intención ───────────────────────────────────────────

    @staticmethod
    def calcular_huella(items) -> str:
        """La huella de la INTENCIÓN de compra.

        Identifica QUÉ se pide (artículo y cantidad), NO el precio: una
        oferta posterior NO cambia la intención y, por tanto, un reintento
        sigue recuperando el MISMO pedido con su snapshot congelado (RN-M03).
        """
        partes = sorted(
            f"{str(item.tipo).strip().upper()}:{str(item.producto_id)}:{item.cantidad}"
            for item in items
        )
        return hashlib.sha256("|".join(partes).encode("utf-8")).hexdigest()

    @staticmethod
    def generar_token() -> str:
        """Un token privado de seguimiento, impredecible.

        Es una credencial de enlace (P-01): 32 bytes de entropía en URL-safe
        base64. Nunca se deriva del pedido ni del comprador.
        """
        return secrets.token_urlsafe(BYTES_TOKEN_PEDIDO)

    @staticmethod
    def referencia_compra(pedido_id) -> str:
        """La referencia estable de la compra que financia el pedido.

        Es ESTABLE: un reintento del pedido abre la MISMA compra pendiente en
        vez de crear otra (FR-04 I-4, RN-C03, RN-C04).
        """
        return f"MARKETPLACE:{pedido_id}:INICIAL"

    # ── Resolución de las líneas (RN-C02, RN-M03) ───────────────────────────

    def resolver_lineas(self, edicion_id, items) -> list[PedidoLineaResuelta]:
        """Resuelve los artículos contra el catálogo y CONGELA los precios.

        Tres rechazos distintos, con tres códigos distintos:

        - el producto no existe → `PRODUCTO_NO_ENCONTRADO` (404);
        - el producto es de OTRA edición → `PRODUCTO_NO_DISPONIBLE` (409);
        - el producto está `INACTIVO` → `PRODUCTO_NO_DISPONIBLE` (409).

        El precio que se congela es el PRECIO EFECTIVO del catálogo (con
        oferta vigente): es el dominio quien decide el precio, nunca el
        cliente (RN-C02).
        """
        lineas: list[PedidoLineaResuelta] = []
        for item in items:
            producto = self.producto_selector.obtener_por_id(item.producto_id)
            if producto is None:
                raise ProductoNoEncontradoError()
            if str(producto.edicion_id) != str(edicion_id):
                raise ProductoNoDisponibleError()
            if producto.estado != EstadoProducto.ACTIVO:
                raise ProductoNoDisponibleError()

            lineas.append(
                PedidoLineaResuelta(
                    tipo_concepto=TipoItemPedido.PRODUCTO,
                    concepto_id=str(producto.id),
                    concepto_nombre=producto.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio,
                    precio_aplicado=producto.precio_efectivo(),
                )
            )
        return lineas

    @staticmethod
    def calcular_total(lineas) -> Decimal:
        """El total del pedido, DERIVADO de sus líneas.

        Es la misma expresión que usa `commerce` para el total de la compra:
        `Σ (cantidad × precio aplicado)`, redondeado a dos decimales. El
        total es un hecho del servidor: el cliente no lo impone (RN-C02).
        """
        total = sum(
            (linea.subtotal for linea in lineas),
            Decimal("0.00"),
        )
        return total.quantize(Decimal("0.01"))

    # ── Escritura ───────────────────────────────────────────────────────────

    def crear(
        self,
        *,
        edicion_id,
        comprador_id,
        total: Decimal,
        moneda: str,
        token: str,
        huella: str,
    ):
        """Crea el pedido en estado `PENDIENTE` con entrega `PENDIENTE`.

        El pedido nace `PENDIENTE` en los DOS hechos: ni el pago ni la
        entrega están resueltos al crearse.

        El identificador se genera ANTES de insertar para que la referencia
        de la compra sea estable desde el primer momento: la compra se
        identifica por `(persona, referencia)` y un reintento tiene que
        abrir la MISMA compra (FR-04 I-4).
        """
        import uuid

        from modules.marketplace.domain.models import Pedido

        pedido_id = uuid.uuid4()
        return Pedido.objects.create(
            id=pedido_id,
            edicion_id=edicion_id,
            comprador_id=comprador_id,
            estado=EstadoPedido.PENDIENTE,
            estado_entrega=EstadoEntregaPedido.PENDIENTE,
            total=total,
            moneda=moneda,
            token=token,
            huella=huella,
            referencia=self.referencia_compra(pedido_id),
        )

    def crear_detalles(self, pedido, lineas) -> list:
        """Persiste el detalle del pedido con el precio CONGELADO (RN-M03)."""
        from modules.marketplace.domain.models import PedidoDetalle

        detalles = []
        for linea in lineas:
            detalles.append(
                PedidoDetalle.objects.create(
                    pedido=pedido,
                    tipo_concepto=linea.tipo_concepto,
                    concepto_id=linea.concepto_id,
                    concepto_nombre=linea.concepto_nombre,
                    cantidad=linea.cantidad,
                    precio_unitario=linea.precio_unitario,
                    precio_aplicado=linea.precio_aplicado,
                )
            )
        return detalles

    def vincular_compra(self, pedido, compra_id):
        """Vincula el pedido con la compra que lo financia."""
        pedido.compra_id = compra_id
        pedido.save(update_fields=["compra", "updated_at"])
        return pedido

    def marcar_estado(self, pedido, estado: str):
        """Mueve el estado del PEDIDO. Idempotente.

        **NUNCA** toca `estado_entrega`: el pago de un pedido no habilita la
        entrega (RN-M07, `QA-M04`). La entrega la avanza `DOM-06`.
        """
        if pedido.estado == estado:
            return pedido
        pedido.estado = estado
        pedido.save(update_fields=["estado", "updated_at"])
        return pedido

    # ── Proyección a results ────────────────────────────────────────────────

    @staticmethod
    def acciones_sugeridas(estado_pago: str, estado_entrega: str) -> list[str]:
        """La siguiente acción SEGURA del comprador.

        Son verbos del dominio, nunca operaciones del proveedor: el
        presenter no expone intentos, referencias técnicas ni evidencias
        (FR-01 §4).
        """
        if estado_pago == EstadoPagoPedido.CONFIRMADO:
            if estado_entrega == EstadoEntregaPedido.ENTREGADO:
                return [AccionPedido.VER_TICKET]
            return [AccionPedido.ESPERAR_ENTREGA]
        if estado_pago == EstadoPagoPedido.NO_COMPLETADO:
            return [AccionPedido.REINTENTAR_COMPRA]
        return [AccionPedido.REALIZAR_PAGO]

    def result_de(
        self,
        pedido,
        detalles,
        estado_pago: str,
        orden_pago_id: str | None,
    ) -> PedidoSeguimientoResult:
        """Proyecta el pedido con sus TRES estados y su acción segura."""
        lineas = [
            PedidoLineaResult(
                id=detalle.id,
                tipo_concepto=detalle.tipo_concepto,
                concepto_id=detalle.concepto_id,
                concepto_nombre=detalle.concepto_nombre,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
                precio_aplicado=detalle.precio_aplicado,
                subtotal=detalle.subtotal,
            )
            for detalle in detalles
        ]
        return PedidoSeguimientoResult(
            id=pedido.id,
            edicion_id=pedido.edicion_id,
            estado=pedido.estado,
            estado_pago=estado_pago,
            estado_entrega=pedido.estado_entrega,
            total=pedido.total,
            moneda=pedido.moneda,
            lineas=lineas,
            orden_pago_id=orden_pago_id,
            siguientes_acciones=self.acciones_sugeridas(
                estado_pago,
                pedido.estado_entrega,
            ),
            created_at=pedido.created_at,
        )


__all__ = ["PedidoCoreService"]
