"""El adaptador de `VerificarDerecho` del módulo de MARKETPLACE.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §5 · `RN-M07`

Este adaptador es el PRODUCTOR de la interfaz `VerificarDerecho` para los
derechos de ENTREGA: un pedido PAGADO que todavía no se recogió.

**LA REGLA ES DE AQUÍ.** `validaciones` NO reimplanta estas reglas: este
archivo vive en el módulo DUEÑO y por eso es el único que puede decir si un
pedido se puede entregar y por qué (`FR-05` §1).

Las reglas que aplica, todas CONGELADAS:

- **Pagado y entregado son estados DISTINTOS** (`RN-M07`): entregar exige
  pagado, pero un pedido pagado NO está entregado.
- un pedido CANCELADO no se entrega;
- la entrega es IDEMPOTENTE: el reintento del operador devuelve el MISMO
  acta, no la duplica (`DOM-06`).

**LA ENTREGA PARCIAL NO ESTÁ RATIFICADA** (`PD-03` sigue ABIERTO): el dueño
confirma el pedido COMPLETO. Pedir una parte es una operación que el módulo
dueño todavía no sabe hacer, y por eso la rechaza.

La escritura del estado y del acta la hacen los servicios core del PROPIO
`marketplace` (`PedidoCoreService`): este adaptador no reimplementa la
escritura, la usa.
"""

from django.db import transaction

from modules.marketplace.domain.constants import (
    EstadoEntregaPedido,
    EstadoPedido,
    TipoItemPedido,
)
from modules.marketplace.domain.models import EntregaPedido, Pedido, Producto
from modules.marketplace.domain.services.core.pedido_core_service import (
    PedidoCoreService,
)
from modules.marketplace.domain.selectors.pedido_selector import PedidoSelector
from modules.validaciones.domain.constants import TipoDerechoChoices
from modules.validaciones.domain.exceptions import (
    CantidadExcedidaError,
    DerechoRevocadoError,
    TicketNoEncontradoError,
    TicketYaConsumidoError,
)
from modules.validaciones.domain.ports.verificador_derecho import (
    IVerificadorDerecho,
    TitularDerecho,
    VerificacionDerecho,
)

#: Los motivos públicos y SEGUROS por los que un pedido no se entrega.
MOTIVO_PEDIDO_CANCELADO = "El pedido está cancelado."
MOTIVO_PEDIDO_NO_PAGADO = "El pedido todavía no está pagado."
MOTIVO_YA_ENTREGADO = "El pedido ya fue entregado."


class PedidoVerificadorDerecho(IVerificadorDerecho):
    """El dueño de los derechos de ENTREGA."""

    tipo_derecho = TipoDerechoChoices.PRODUCTO

    def __init__(
        self,
        selector: PedidoSelector | None = None,
        core: PedidoCoreService | None = None,
    ):
        self.selector = selector or PedidoSelector()
        self.core = core or PedidoCoreService()

    # ── LECTURA ───────────────────────────────────────────────────────────────

    def resolver(self, referencia_id: str) -> VerificacionDerecho:
        """Publica el estado del pedido SIN tocarlo (`RN-P06`)."""
        pedido = self._pedido(referencia_id)
        detalles = self.selector.listar_detalles(pedido.id)
        return self._verificacion(pedido, detalles)

    # ── MUTACIÓN ──────────────────────────────────────────────────────────────

    def consumir(
        self,
        referencia_id: str,
        cantidad: int | None = None,
        actor_usuario_id: str | None = None,
    ) -> VerificacionDerecho:
        """Confirma la ENTREGA del pedido, con el acta del propio dueño.

        `cantidad=None` significa "todo lo pendiente". Una cantidad distinta
        es una entrega parcial, que `PD-03` todavía no ratifica: el dueño la
        rechaza (`FR-05` §2.2).
        """
        with transaction.atomic():
            pedido = self._pedido(referencia_id, bloquear=True)
            detalles = self.selector.listar_detalles(pedido.id)
            pendiente = self._pendiente(pedido, detalles)

            if pendiente <= 0:
                raise TicketYaConsumidoError()
            if cantidad is not None and cantidad != pendiente:
                raise CantidadExcedidaError()
            if pedido.estado == EstadoPedido.CANCELADO:
                raise DerechoRevocadoError()
            if pedido.estado != EstadoPedido.PAGADO:
                raise DerechoRevocadoError()

            actor = self._actor(actor_usuario_id)
            self.core.marcar_estado_entrega(
                pedido, EstadoEntregaPedido.ENTREGADO
            )
            if not EntregaPedido.objects.filter(pedido=pedido).exists():
                self.core.crear_entrega(pedido, actor, detalles)

        return self._verificacion(pedido, detalles)

    # ── Internos ──────────────────────────────────────────────────────────────

    def _pedido(self, referencia_id: str, bloquear: bool = False) -> Pedido:
        """El pedido del módulo dueño."""
        consulta = Pedido.objects.select_related("comprador", "edicion")
        if bloquear:
            consulta = consulta.select_for_update()
        pedido = consulta.filter(id=referencia_id).first()
        if pedido is None:
            raise TicketNoEncontradoError()
        return pedido

    @staticmethod
    def _pendiente(pedido, detalles) -> int:
        """Las unidades que todavía no se entregaron."""
        if pedido.estado_entrega == EstadoEntregaPedido.ENTREGADO:
            return 0
        return sum(detalle.cantidad for detalle in detalles)

    @staticmethod
    def _actor(actor_usuario_id: str | None):
        """La cuenta que opera, para el acta del dueño."""
        if not actor_usuario_id:
            return None
        from modules.usuarios.domain.models import Usuario

        return Usuario.objects.filter(id=actor_usuario_id).first()

    def _verificacion(self, pedido, detalles) -> VerificacionDerecho:
        """La publicación del dueño sobre su pedido."""
        total = sum(detalle.cantidad for detalle in detalles)
        pendiente = self._pendiente(pedido, detalles)
        puede_canjear, motivo_codigo, motivo_mensaje = self._motivo(
            pedido, pendiente
        )
        return VerificacionDerecho(
            tipo_derecho=TipoDerechoChoices.PRODUCTO,
            codigo=self._codigo(pedido, detalles),
            titular=TitularDerecho(
                persona_id=str(pedido.comprador_id),
                nombre=_nombre_completo(pedido.comprador),
            ),
            edicion_id=str(pedido.edicion_id),
            estado=pedido.estado_entrega,
            cantidad_total=total,
            cantidad_consumida=max(0, total - pendiente),
            cantidad_disponible=pendiente,
            puede_canjear=puede_canjear,
            motivo_codigo=motivo_codigo,
            motivo_mensaje=motivo_mensaje,
        )

    @staticmethod
    def _motivo(pedido, pendiente: int):
        """Si el pedido se puede entregar, y por qué no."""
        if pedido.estado == EstadoPedido.CANCELADO:
            return (False, "PEDIDO_CANCELADO", MOTIVO_PEDIDO_CANCELADO)
        if pedido.estado != EstadoPedido.PAGADO:
            return (False, "PEDIDO_NO_PAGADO", MOTIVO_PEDIDO_NO_PAGADO)
        if pendiente <= 0:
            return (False, "TICKET_YA_CONSUMIDO", MOTIVO_YA_ENTREGADO)
        return (True, None, None)

    @staticmethod
    def _codigo(pedido, detalles) -> str:
        """El código del CONCEPTO entregado: los productos del pedido."""
        ids = [
            detalle.concepto_id
            for detalle in detalles
            if detalle.tipo_concepto == TipoItemPedido.PRODUCTO
        ]
        if ids:
            slugs = list(
                Producto.objects.filter(id__in=ids).values_list("slug", flat=True)
            )
            if slugs:
                return ", ".join(sorted(slugs))[:200]
        return str(pedido.referencia or "")[:200]


def _nombre_completo(persona) -> str:
    """El nombre de la persona, como lo publica su módulo."""
    partes = [persona.nombres or "", persona.apellidos or ""]
    return " ".join(parte for parte in partes if parte).strip()


__all__ = [
    "MOTIVO_PEDIDO_CANCELADO",
    "MOTIVO_PEDIDO_NO_PAGADO",
    "MOTIVO_YA_ENTREGADO",
    "PedidoVerificadorDerecho",
]
