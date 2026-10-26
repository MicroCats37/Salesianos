"""CotizacionFlujo — stateless quotation calculation for a package.

This flow is read-only: it computes a quotation based on the current catalog
state without persisting anything. The client stores the result in form state
and sends it back at confirmation time for server-side revalidation.

Business rules:
- cantidad >= Paquete.minimo_compra_inicial (commercial minimum)
- precio_unitario comes from the currently active PREVENTA or REGULAR price
- precio_promocional is derived from the active price if lower than regular
- The quotation is NOT persisted; Compra snapshots the price at creation time
"""
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Q
from django.utils import timezone

from modules.salesianos_fest.domain.exceptions import (
    CantidadInsuficienteError,
    PaqueteNotFoundError,
)
from modules.salesianos_fest.domain.models import Paquete
from modules.salesianos_fest.presentation.schemas.cotizacion_schemas import CotizacionResponse


# Validity window for a quotation (24 hours)
COTIZACION_VALIDITY_HOURS = 24


def _obtener_precio_vigente(paquete_id: str) -> tuple[Decimal, str]:
    """Get vigente precio_unitario and etapa for a paquete."""
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
    return precio.precio_unitario, precio.etapa


class CotizacionFlujo:
    """Stateless quotation calculator."""

    def cotizar(
        self, paquete_id: str, cantidad: int
    ) -> CotizacionResponse:
        """
        Calculate a quotation for the given package and quantity.

        Raises:
            PaqueteNotFoundError: if paquete does not exist
            CantidadInsuficienteError: if cantidad < minimo_compra_inicial

        Returns:
            CotizacionResponse with current price, total, and validity window
        """
        try:
            paquete = Paquete.objects.select_related("evento").get(id=paquete_id)
        except Paquete.DoesNotExist:
            raise PaqueteNotFoundError()

        if cantidad < paquete.minimo_compra_inicial:
            raise CantidadInsuficienteError(
                minimo=paquete.minimo_compra_inicial,
                received=cantidad,
            )

        # Get current active price
        precio_unitario, etapa = _obtener_precio_vigente(paquete_id)

        # Get regular and preventa for reference
        precio_regular = None
        precio_preventa = None
        version = 1

        for precio in paquete.precios.filter(activo=True).order_by("etapa"):
            if precio.etapa == "REGULAR":
                precio_regular = float(precio.precio_unitario)
                version += 1
            elif precio.etapa == "PREVENTA":
                precio_preventa = float(precio.precio_unitario)

        # Use the vigente price as unitario
        precio_vigente = float(precio_unitario)
        total = round(precio_vigente * cantidad, 2)
        validez_hasta = datetime.now() + timedelta(hours=COTIZACION_VALIDITY_HOURS)

        return CotizacionResponse(
            paquete_id=str(paquete.id),
            paquete_nombre=paquete.nombre,
            modo_disciplinas=paquete.modo_disciplinas,
            minimo_cantidad=paquete.minimo_compra_inicial,
            cantidad_cotizada=cantidad,
            precio_unitario=precio_vigente,
            precio_regular=precio_regular or precio_vigente,
            precio_preventa=precio_preventa,
            total=total,
            validez_hasta=validez_hasta,
            version=version,
            estado="ACTIVA",
        )
