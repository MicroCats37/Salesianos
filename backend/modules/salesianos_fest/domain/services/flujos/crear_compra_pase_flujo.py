"""
CrearCompraPaseFlujo — async flow for buying a batch of party passes.

Async flow with ONE `transaction.atomic`. Creates, atomically:

1. commerce.Compra (PENDIENTE) — the generic commercial root, owned by the buyer
2. OrdenPago (PENDIENTE) — the payment order that funds that purchase
3. CompraPase — the commercial line of the pass batch (frozen price snapshot)

It NEVER creates or mutates a sports object: no `Inscripcion`, no
`CompraInscripcion`, no `AsignacionCupo`, no `Participacion`, no `Equipo` and
no sports balance. A pass purchase is a commercial batch, not a sports
purchase.

Rules, in order:

1. the rollout flag `settings.PASES_FIESTA_ENABLED` gates the whole surface;
2. the buyer must be an authenticated user with a `Persona` — the owner of the
   purchase is `Compra.responsable`;
3. the purchase belongs to the ACTIVE edition, resolved server-side (the
   client never sends an `evento_id`);
4. the pass must exist, be ACTIVE and belong to that edition;
5. the quantity must be a positive integer within the commercial cap;
6. the unit price is the CURRENTLY VIGENT `PasePrecio` and the total is
   computed server-side — the client never controls price or total;
7. the inventory cap (`Pase.cantidad_maxima`, 0 = unlimited) is recalculated
   inside the transaction against the not cancelled purchases.
"""
import logging
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
from injector import inject

from modules.commerce.domain.constants import EstadoCompraChoices
from modules.commerce.domain.models import Compra
from modules.pagos.domain.services.core.izipay_core_service import (
    IzipayCoreService,
    sanitize_metadata,
)
from modules.salesianos_fest.domain.constants import (
    CANTIDAD_MAXIMA_POR_COMPRA,
    CANTIDAD_MAXIMA_SIN_LIMITE,
)
from modules.salesianos_fest.domain.exceptions import (
    PaseCantidadInvalidaError,
    PaseCompradorSinPersonaError,
    PaseInventarioAgotadoError,
    PaseNoDisponibleError,
    PaseNoEncontradoError,
    PasePrecioNoVigenteError,
    PasesFiestaDeshabilitadoError,
)
from modules.salesianos_fest.domain.models import CompraPase
from modules.salesianos_fest.domain.results.pase_results import PaseCompraCreadaResult
from modules.salesianos_fest.domain.selectors.pase_selector import PaseSelector
from modules.salesianos_fest.domain.services.core.pase_service import PaseCoreService

logger = logging.getLogger(__name__)


class CrearCompraPaseFlujo:
    """
    Async flow for creating a pass purchase (Compra + OrdenPago + CompraPase).
    """

    @inject
    def __init__(
        self,
        izipay_core: IzipayCoreService,
        pase_core: PaseCoreService,
        pase_selector: PaseSelector,
    ):
        self.izipay_core = izipay_core
        self.pase_core = pase_core
        self.pase_selector = pase_selector

    async def _crear_compra_pase(
        self,
        responsable_id: str | None,
        pase_id: str,
        cantidad: int,
    ) -> PaseCompraCreadaResult:
        """
        Create the pass purchase atomically.

        Args:
            responsable_id: Persona UUID of the buyer (`Compra.responsable`).
            pase_id: UUID of the pass to buy.
            cantidad: Number of passes requested by the buyer.

        Raises:
            PasesFiestaDeshabilitadoError: the rollout flag is off.
            PaseCompradorSinPersonaError: the buyer has no Persona.
            PaseNoDisponibleError: no active edition, or the pass is not
                publishable in it.
            PaseNoEncontradoError: the pass does not exist.
            PaseCantidadInvalidaError: the quantity is out of range.
            PasePrecioNoVigenteError: the pass has no vigente price.
            PaseInventarioAgotadoError: the inventory cap is exhausted.
        """
        return await sync_to_async(self._crear_compra_pase_sync)(
            responsable_id, pase_id, cantidad
        )

    @transaction.atomic()
    def _crear_compra_pase_sync(
        self,
        responsable_id: str | None,
        pase_id: str,
        cantidad: int,
    ) -> PaseCompraCreadaResult:
        """
        Sync body with the transaction that makes the purchase atomic.

        The pass row is LOCKED before the inventory is recalculated, so two
        concurrent purchases of the same pass cannot both pass the cap.
        """
        # 1. Rollout flag — the whole surface is gated.
        if not getattr(settings, "PASES_FIESTA_ENABLED", False):
            raise PasesFiestaDeshabilitadoError()

        # 2. The buyer must be a Persona: `Compra.responsable` is the owner.
        if not responsable_id:
            raise PaseCompradorSinPersonaError()

        from modules.usuarios.domain.models import Persona

        persona = Persona.objects.filter(id=responsable_id).first()
        if persona is None:
            raise PaseCompradorSinPersonaError()

        # 3. The purchase belongs to the ACTIVE edition (server-side).
        evento = self.pase_core.resolver_evento_activo()
        if evento is None:
            raise PaseNoDisponibleError()

        # 4. Locked pass — the lock serializes purchases of the same pass.
        pase = self.pase_core.obtener_pase_bloqueado(pase_id)
        if pase is None:
            raise PaseNoEncontradoError()
        if not pase.activo or pase.evento_id != evento.id:
            raise PaseNoDisponibleError()

        # 5. Quantity — a positive integer within the commercial cap.
        if cantidad <= 0 or cantidad > CANTIDAD_MAXIMA_POR_COMPRA:
            raise PaseCantidadInvalidaError()

        # 6. Freeze the CURRENTLY VIGENT price. The client never sends one.
        precio = self.pase_selector.obtener_precio_vigente(str(pase.id))
        if precio is None:
            raise PasePrecioNoVigenteError()
        precio_unitario: Decimal = precio.precio_unitario
        total: Decimal = precio_unitario * cantidad

        # 7. Inventory cap (0 = unlimited), recomputed under the pass lock.
        if pase.cantidad_maxima != CANTIDAD_MAXIMA_SIN_LIMITE:
            vendido = self.pase_selector.contar_cantidad_vendida(str(pase.id))
            if vendido + cantidad > pase.cantidad_maxima:
                raise PaseInventarioAgotadoError()

        # 8. commerce.Compra (PENDIENTE) — generic root, owner is the buyer.
        descripcion = f"Compra de pases - {pase.nombre}"
        referencia_externa = f"PASE-{str(pase.id)[:8]}"

        # Audit/display context only — never authoritative.
        metadata = sanitize_metadata({
            "source": "fest",
            "purchase_reference": referencia_externa,
            "display_context": {"label": pase.nombre, "tipo": "PASE"},
            "evento_id": str(evento.id),
            "buyer_documento": persona.numero_documento,
            "buyer_nombres": persona.nombres,
            "buyer_apellidos": persona.apellidos,
        })

        compra = Compra.objects.create(
            responsable=persona,
            descripcion=descripcion,
            referencia_externa=referencia_externa,
            total=total,
            estado=EstadoCompraChoices.PENDIENTE,
        )

        # 9. OrdenPago (PENDIENTE) — the order that funds the purchase.
        numero_orden = self.izipay_core.generar_numero_orden()
        orden_pago = self.izipay_core.crear_orden_pago(
            numero=numero_orden,
            monto_total=total,
            moneda="PEN",
            descripcion=descripcion,
            referencia_externa=referencia_externa,
            metadata=metadata,
        )
        compra.orden_pago = orden_pago
        compra.save(update_fields=["orden_pago", "updated_at"])

        # 10. CompraPase — the commercial line with the frozen snapshot.
        compra_pase = CompraPase.objects.create(
            compra=compra,
            pase=pase,
            evento=pase.evento,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            total=total,
        )

        logger.info(
            "Pass purchase created: compra=%s pase=%s cantidad=%s",
            compra.id,
            pase.id,
            cantidad,
        )

        return PaseCompraCreadaResult(
            compra_id=str(compra.id),
            compra_pase_id=str(compra_pase.id),
            orden_pago_id=str(orden_pago.id),
            numero_orden=orden_pago.numero,
            pase_id=str(pase.id),
            pase_nombre=pase.nombre,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
            total=total,
            estado_compra=compra.estado,
            estado_orden=orden_pago.estado,
        )
