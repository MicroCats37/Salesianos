"""`InventarioCoreService` — las escrituras del inventario de marketplace.

Packet: `DOM-06` · Change: `salesianos-fest-rebuild`
Contract: `contract/django-app-architecture-contract.md` §4.3

Es un servicio **sync** y **NO abre `transaction.atomic()`**: el flujo es el
dueño de la atomicidad (P5). Todo lo que hace son ESCRITURAS CONDICIONALES:
la base de datos decide, no la aplicación.

**LA REGLA DE ORO (F-55 · F-64):** cuando hay que restar o apartar unidades,
la condición viaja DENTRO de la sentencia.

    UPDATE producto SET reservado = reservado + N
      WHERE id = ? AND stock >= reservado + N

Dos pedidos simultáneos por las mismas unidades NO pueden ganar los dos: el
segundo actualiza cero filas y recibe `STOCK_INSUFICIENTE` (409). No se usa
`select_for_update`: SQLite no lo soporta y el bloqueo sería un callejón
sin salida.

**TRES HECHOS SEPARADOS (RN-M06 · RN-M07):**

| # | Hecho | Dónde vive | Quién lo mueve |
|---|---|---|---|
| 1 | `stock` | el producto | este servicio |
| 2 | `reservado` | el producto | este servicio |
| 3 | `estado_entrega` | el pedido | `PedidoFlujo` (DOM-06) |

**LA VENTA NO SE DESCUENTA DOS VECES (FR-04 I-3).** La reserva es la
autoridad del "una vez" (`ACTIVA` → `CONFIRMADA` es condicional) y el
MOVIMIENTO tiene una referencia ÚNICA: un webhook repetido no genera un
segundo movimiento ni un segundo descuento.
"""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import F
from django.utils import timezone

from modules.marketplace.domain.constants import (
    SIGNO_MOVIMIENTO_MANUAL,
    EstadoReservaInventario,
    TipoItemPedido,
    TipoMovimientoInventario,
)
from modules.marketplace.domain.exceptions import (
    MovimientoInventarioInvalidoError,
    PedidoSinReservaError,
    ProductoNoEncontradoError,
    ReservaNoConfirmableError,
    StockInsuficienteError,
)
from modules.marketplace.domain.models import (
    MovimientoInventario,
    Producto,
    ReservaInventario,
)
from modules.marketplace.domain.results.inventario_result import (
    InventarioProductoResult,
    MovimientoInventarioResult,
)
from modules.marketplace.domain.selectors.inventario_selector import InventarioSelector


class InventarioCoreService:
    """Operaciones de escritura y proyección del inventario."""

    def __init__(
        self,
        selector: InventarioSelector = None,
    ):
        self.selector = selector or InventarioSelector()

    # ── Reservas (RN-M06 · QA-M01) ───────────────────────────────────────────

    def reservar_para_pedido(self, pedido, detalles) -> list[ReservaInventario]:
        """Aparta el stock de las líneas del pedido.

        Las líneas del MISMO producto se AGREGAN: un pedido reserva cada
        producto una sola vez, con la cantidad total.

        Args:
            pedido: el pedido que reserva.
            detalles: las líneas congeladas del pedido.

        Returns:
            Las reservas creadas, en estado `ACTIVA`.

        Raises:
            `StockInsuficienteError`: no hay disponibilidad para alguna línea.
            `ProductoNoEncontradoError`: una línea apunta a un producto que no
                existe.
        """
        cantidades: dict[str, int] = {}
        for detalle in detalles:
            if detalle.tipo_concepto != TipoItemPedido.PRODUCTO:
                continue
            clave = str(detalle.concepto_id)
            cantidades[clave] = cantidades.get(clave, 0) + detalle.cantidad

        reservas: list[ReservaInventario] = []
        for concepto_id, cantidad in cantidades.items():
            producto = self._producto_por_concepto(concepto_id)
            if not self._reservar_unidades(producto.id, cantidad):
                raise StockInsuficienteError()
            reservas.append(
                ReservaInventario.objects.create(
                    producto=producto,
                    pedido=pedido,
                    cantidad=cantidad,
                    estado=EstadoReservaInventario.ACTIVA,
                    referencia=self._referencia_reserva(pedido, producto),
                )
            )
        return reservas

    def liberar_de_pedido(self, pedido) -> int:
        """Devuelve al catálogo las unidades reservadas por un pedido.

        Se llama cuando el pedido se CANCELA: las unidades vuelven a estar
        disponibles y no se pierde la traza (la reserva queda `LIBERADA`).

        Returns:
            Cuántas reservas se liberaron.
        """
        liberadas = 0
        reservas = ReservaInventario.objects.filter(
            pedido=pedido,
            estado=EstadoReservaInventario.ACTIVA,
        ).order_by("id")
        for reserva in reservas:
            actualizado = ReservaInventario.objects.filter(
                id=reserva.id,
                estado=EstadoReservaInventario.ACTIVA,
            ).update(
                estado=EstadoReservaInventario.LIBERADA,
                updated_at=timezone.now(),
            )
            if not actualizado:
                continue
            Producto.objects.filter(id=reserva.producto_id).update(
                reservado=F("reservado") - reserva.cantidad
            )
            liberadas += 1
        return liberadas

    def confirmar_venta_de_pedido(self, pedido) -> list[MovimientoInventario]:
        """Confirma la venta: el stock FÍSICO sale del producto.

        Es **IDEMPOTENTE**: si las reservas ya están `CONFIRMADA` no se
        vuelve a descontar nada y no se crea un segundo movimiento. Ésa es la
        garantía de "no descontar dos veces por webhook" (`RN-M06` ·
        `FR-04` I-3).

        Returns:
            Los movimientos de venta creados (vacío si ya estaba confirmada).

        Raises:
            `PedidoSinReservaError`: el pedido no tiene reservas.
            `ReservaNoConfirmableError`: la reserva fue liberada (el pedido
                se canceló antes del pago).
            `StockInsuficienteError`: el stock físico no alcanza (no debería
                ocurrir: las unidades estaban reservadas).
        """
        reservas = ReservaInventario.objects.filter(pedido=pedido).order_by("id")
        if not reservas.exists():
            raise PedidoSinReservaError()

        movimientos: list[MovimientoInventario] = []
        for reserva in reservas:
            if reserva.estado == EstadoReservaInventario.CONFIRMADA:
                # Ya aplicada: no se vuelve a descontar (FR-04 I-3).
                continue
            if reserva.estado == EstadoReservaInventario.LIBERADA:
                # El pedido se canceló antes del pago: la venta ya no se
                # puede cerrar (RN-C08 conserva el pago y deja incidencia).
                raise ReservaNoConfirmableError()

            actualizado = ReservaInventario.objects.filter(
                id=reserva.id,
                estado=EstadoReservaInventario.ACTIVA,
            ).update(
                estado=EstadoReservaInventario.CONFIRMADA,
                updated_at=timezone.now(),
            )
            if not actualizado:
                continue

            if not self._ajustar_stock(reserva.producto_id, -reserva.cantidad):
                raise StockInsuficienteError()
            Producto.objects.filter(id=reserva.producto_id).update(
                reservado=F("reservado") - reserva.cantidad
            )
            movimientos.append(
                MovimientoInventario.objects.create(
                    producto_id=reserva.producto_id,
                    cantidad=-reserva.cantidad,
                    tipo=TipoMovimientoInventario.VENTA,
                    motivo="Venta confirmada",
                    referencia=reserva.referencia,
                    actor=None,
                )
            )
        return movimientos

    # ── Movimientos manuales (FL-09 · RN-M04 · RN-M05) ───────────────────────

    def registrar_movimiento(
        self,
        producto,
        tipo: str,
        cantidad: int,
        motivo: str,
        actor,
    ) -> MovimientoInventario:
        """Registra un movimiento MANUAL y ajusta el stock.

        **NO crea compra ni pago** (`RN-M05` · `QA-M02`): una salida sin
        venta es una salida, no una compra ficticia.

        Args:
            producto: el producto afectado.
            tipo: la naturaleza del movimiento.
            cantidad: la cantidad CON signo.
            motivo: el motivo, obligatorio.
            actor: la cuenta que lo registra, obligatoria en los manuales.

        Returns:
            El movimiento registrado.
        """
        self._validar_movimiento_manual(tipo, cantidad, motivo)
        if actor is None:
            raise MovimientoInventarioInvalidoError()
        if not self._ajustar_stock(producto.id, cantidad):
            raise StockInsuficienteError()

        movimiento = MovimientoInventario(
            producto=producto,
            cantidad=cantidad,
            tipo=tipo,
            motivo=motivo.strip(),
            referencia="",
            actor=actor,
        )
        movimiento.referencia = f"MANUAL:{movimiento.id}"
        movimiento.save()
        return movimiento

    def revertir_movimiento(self, movimiento, actor, motivo: str) -> MovimientoInventario:
        """Compensa un movimiento con otro de signo contrario.

        Un movimiento NO se edita ni se borra: se compensa (`RN-M04`).
        """
        if movimiento.tipo == TipoMovimientoInventario.REVERSION:
            raise MovimientoInventarioInvalidoError()
        if not motivo or not motivo.strip():
            raise MovimientoInventarioInvalidoError()
        if not self._ajustar_stock(movimiento.producto_id, -movimiento.cantidad):
            raise StockInsuficienteError()

        reversa = MovimientoInventario(
            producto_id=movimiento.producto_id,
            cantidad=-movimiento.cantidad,
            tipo=TipoMovimientoInventario.REVERSION,
            motivo=motivo.strip(),
            referencia="",
            actor=actor,
            compensatorio=movimiento,
        )
        reversa.referencia = f"REVERSION:{movimiento.id}"
        reversa.save()
        return reversa

    # ── Sentencias condicionales (la autoridad) ──────────────────────────────

    @staticmethod
    def _reservar_unidades(producto_id, cantidad: int) -> bool:
        """Aparta `cantidad` unidades SI hay disponibilidad (RN-M06).

        La condición viaja dentro de la sentencia: la base de datos decide
        quién entra y sólo uno puede ganar las mismas unidades.
        """
        actualizados = Producto.objects.filter(
            id=producto_id,
            stock__gte=F("reservado") + cantidad,
        ).update(reservado=F("reservado") + cantidad)
        return actualizados == 1

    @staticmethod
    def _ajustar_stock(producto_id, cantidad: int) -> bool:
        """Ajusta el stock físico de forma CONDICIONAL.

        Una salida sólo se aplica si hay stock suficiente; una entrada siempre
        se aplica (y si el producto no existe, no se aplica nada).
        """
        if cantidad > 0:
            return Producto.objects.filter(id=producto_id).update(
                stock=F("stock") + cantidad
            ) == 1
        return Producto.objects.filter(
            id=producto_id,
            stock__gte=-cantidad,
        ).update(stock=F("stock") + cantidad) == 1

    # ── Internos ─────────────────────────────────────────────────────────────

    @staticmethod
    def _validar_movimiento_manual(tipo: str, cantidad: int, motivo: str) -> None:
        """Valida la coherencia entre naturaleza, signo y motivo (RN-M04)."""
        if tipo not in SIGNO_MOVIMIENTO_MANUAL and tipo != TipoMovimientoInventario.AJUSTE:
            raise MovimientoInventarioInvalidoError()
        if not cantidad:
            raise MovimientoInventarioInvalidoError()
        if not motivo or not motivo.strip():
            raise MovimientoInventarioInvalidoError()
        signo = SIGNO_MOVIMIENTO_MANUAL.get(tipo)
        if signo is not None and (cantidad > 0) != (signo > 0):
            raise MovimientoInventarioInvalidoError()

    @staticmethod
    def _producto_por_concepto(concepto_id: str) -> Producto:
        """El producto de una línea del pedido, o el rechazo explícito."""
        try:
            producto = Producto.objects.filter(id=concepto_id).first()
        except (ValueError, TypeError, DjangoValidationError):
            producto = None
        if producto is None:
            raise ProductoNoEncontradoError()
        return producto

    @staticmethod
    def _referencia_reserva(pedido, producto) -> str:
        """La referencia estable de la reserva (y del movimiento de venta)."""
        return f"PEDIDO:{pedido.id}:{producto.id}"

    # ── Proyección ───────────────────────────────────────────────────────────

    def listar_inventario(self, edicion_id) -> list[InventarioProductoResult]:
        """El inventario de los productos de una edición, con su bitácora."""
        return [
            self.result_inventario(
                producto,
                self.selector.listar_movimientos(producto.id),
            )
            for producto in self.selector.listar_productos(edicion_id)
        ]

    @staticmethod
    def result_movimiento(movimiento) -> MovimientoInventarioResult:
        """Proyecta un movimiento a su result."""
        return MovimientoInventarioResult(
            id=movimiento.id,
            producto_id=movimiento.producto_id,
            cantidad=movimiento.cantidad,
            tipo=movimiento.tipo,
            motivo=movimiento.motivo,
            referencia=movimiento.referencia,
            actor_id=movimiento.actor_id,
            created_at=movimiento.created_at,
        )

    def result_inventario(self, producto, movimientos) -> InventarioProductoResult:
        """Proyecta el inventario de un producto a su result."""
        return InventarioProductoResult(
            producto_id=producto.id,
            nombre=producto.nombre,
            slug=producto.slug,
            stock=producto.stock,
            reservado=producto.reservado,
            disponible=producto.disponible,
            movimientos=[self.result_movimiento(movimiento) for movimiento in movimientos],
        )


__all__ = ["InventarioCoreService"]
