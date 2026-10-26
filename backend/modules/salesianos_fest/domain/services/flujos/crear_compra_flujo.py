"""
CrearCompraFlujo — async flow for creating a Compra and its OrdenPago.

Async flow with transaction.atomic — creates commerce.Compra + OrdenPago + CompraInscripcion atomically:

1. Validate Inscripcion exists and is in a valid state
2. Get vigentes PaquetePrecio for the inscripcion's paquete
3. Validate minimum inicial quantity (not enforced for AMPLIACION)
4. Freeze precio_unitario from vigente tariff
5. Calculate total = cantidad * precio_unitario
6. Create commerce.Compra (PENDIENTE)
7. Create OrdenPago(PENDIENTE) with descripcion and referencia_externa, linked to commerce.Compra
8. Update commerce.Compra.orden_pago
9. Create CompraInscripcion (linked to commerce.Compra and Inscripcion)
10. Return CompraCreatedResult

Price snapshot is frozen at Compra creation time (decision D2).
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.salesianos_fest.domain.constants import TipoCompraChoices
from modules.salesianos_fest.domain.exceptions import (
    InscripcionNotFoundError,
)
from modules.salesianos_fest.domain.models import CompraInscripcion, Inscripcion
from modules.salesianos_fest.domain.schemas.compra_schemas import CompraCreateData
from modules.salesianos_fest.domain.results.compra_results import CompraCreatedResult
from modules.pagos.domain.services.core.izipay_core_service import (
    IzipayCoreService,
    sanitize_metadata,
)

logger = logging.getLogger(__name__)


class CrearCompraFlujo:
    """
    Async flow for creating a commercial purchase.

    Creates:
    - commerce.Compra (generic, agnostic)
    - OrdenPago in pagos module (with descripcion and referencia_externa snapshots)
    - CompraInscripcion in salesianos_fest (composition link)
    """

    @inject
    def __init__(
        self,
        izipay_core: IzipayCoreService,
    ):
        self.izipay_core = izipay_core

    async def _crear_compra(
        self,
        data: CompraCreateData,
    ) -> CompraCreatedResult:
        """
        Create a Compra and its associated OrdenPago atomically.

        Steps:
        1. Load Inscripcion and validate it exists
        2. Get vigentes PaquetePrecio for the paquete
        3. Validate quantity meets minimo_inicial for INICIAL tipo
        4. Freeze precio_unitario from vigente tariff
        5. Create commerce.Compra
        6. Create OrdenPago with descripcion and referencia_externa
        7. Assign OrdenPago to commerce.Compra
        8. Create CompraInscripcion
        9. Return CompraCreatedResult

        Raises:
            InscripcionNotFoundError: if inscripcion not found
            PrecioNoEncontradoError: if no active price found
            CantidadInsuficienteError: if INICIAL and quantity < minimo_inicial
        """
        return await sync_to_async(self._crear_compra_sync)(data)

    def _crear_compra_sync(self, data: CompraCreateData) -> CompraCreatedResult:
        """
        Sync wrapper with transaction.atomic for compra creation.
        """
        with transaction.atomic():
            # 1. Load Inscripcion
            inscripcion = Inscripcion.objects.filter(id=data.inscripcion_id).first()
            if inscripcion is None:
                raise InscripcionNotFoundError()

            # 2. Get vigentes price
            # Both initial and expansion purchases use the inscription package tariff.
            precio_unitario, cantidad_disciplinas = self._obtener_precio_vigente(
                inscripcion.paquete_id
            )

            # 3. Validate minimo_inicial for INICIAL tipo
            if data.tipo == TipoCompraChoices.INICIAL:
                if data.cantidad < inscripcion.paquete.minimo_compra_inicial:
                    from modules.salesianos_fest.domain.exceptions import CantidadInsuficienteError
                    raise CantidadInsuficienteError()

            # 4. Freeze price
            total = data.cantidad * precio_unitario

            # 5. Create commerce.Compra (without orden_pago yet)
            from modules.commerce.domain.models import Compra
            from modules.commerce.domain.constants import EstadoCompraChoices

            # Build description and reference for the payment order
            tipo_display = "Inicial" if data.tipo == TipoCompraChoices.INICIAL else "Ampliacion"
            descripcion = f"Compra {tipo_display} - {inscripcion.paquete.nombre}"
            referencia_externa = f"FEST-{str(inscripcion.id)[:8]}"

            # Build metadata — audit/display context only (non-authoritative snapshots)
            # METADATA_ALLOWED_KEYS enforced by sanitize_metadata
            metadata = sanitize_metadata({
                "source": "fest",
                "inscripcion_id": str(inscripcion.id),
                "paquete_id": str(inscripcion.paquete_id),
                "paquete_nombre": inscripcion.paquete.nombre,
                "evento_id": str(inscripcion.paquete.evento_id),
            })

            commerce_compra = Compra.objects.create(
                responsable=inscripcion.responsable,
                descripcion=descripcion,
                referencia_externa=referencia_externa,
                total=total,
                estado=EstadoCompraChoices.PENDIENTE,
            )

            # 6. Create OrdenPago with descripcion, referencia_externa, and metadata
            numero_orden = self.izipay_core.generar_numero_orden()
            orden_pago = self.izipay_core.crear_orden_pago(
                numero=numero_orden,
                monto_total=total,
                moneda="PEN",
                descripcion=descripcion,
                referencia_externa=referencia_externa,
                metadata=metadata,
            )

            # 7. Assign OrdenPago to commerce.Compra
            commerce_compra.orden_pago = orden_pago
            commerce_compra.save(update_fields=["orden_pago", "updated_at"])

            # 8. Create CompraInscripcion (composition link)
            compra_inscripcion = CompraInscripcion.objects.create(
                compra=commerce_compra,
                inscripcion=inscripcion,
                tipo=data.tipo,
                cantidad=data.cantidad,
                precio_unitario=precio_unitario,
                total=total,
            )

            return CompraCreatedResult(
                compra_id=str(commerce_compra.id),
                compra_inscripcion_id=str(compra_inscripcion.id),
                orden_pago_id=str(orden_pago.id),
                tipo=data.tipo,
                cantidad=data.cantidad,
                precio_unitario=precio_unitario,
                total=total,
                estado=EstadoCompraChoices.PENDIENTE,
            )

    def _obtener_precio_vigente(self, paquete_id):
        """Get vigente precio_unitario for a paquete."""
        from django.db.models import Q
        from django.utils import timezone

        hoy = timezone.now().date()
        from modules.salesianos_fest.domain.models import PaquetePrecio
        precio = (
            PaquetePrecio.objects
            .filter(
                paquete_id=paquete_id,
                activo=True,
                vigente_desde__lte=hoy,
            )
            .filter(
                Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy)
            )
            .order_by("-vigente_desde")
            .first()
        )
        if precio is None:
            from modules.salesianos_fest.domain.exceptions import PrecioNoEncontradoError
            raise PrecioNoEncontradoError()

        from modules.salesianos_fest.domain.models import Paquete
        paquete = precio.paquete
        return precio.precio_unitario, paquete.cantidad_disciplinas
