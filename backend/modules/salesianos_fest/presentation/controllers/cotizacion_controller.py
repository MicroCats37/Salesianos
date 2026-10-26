"""CotizacionController — stateless quotation endpoint."""
from asgiref.sync import sync_to_async

from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny

from core.responses import ApiResponse, success_response
from modules.salesianos_fest.domain.services.flujos.cotizacion_flujo import CotizacionFlujo
from modules.salesianos_fest.presentation.schemas.cotizacion_schemas import (
    CotizacionRequest,
    CotizacionResponse,
)


@api_controller("/cotizaciones", tags=["Cotizaciones FEST"], permissions=[AllowAny])
class CotizacionController:
    """
    Stateless quotation endpoint.

    POST /api/cotizaciones/ — calculate a quotation for a package and quantity.
    The quotation is NOT persisted; it is returned for the client to store in
    form state and send back at confirmation time.

    Auth: AllowAny (quotation is public pricing info).
    """

    @route.post(
        "/",
        response={200: ApiResponse[CotizacionResponse]},
        auth=None,
    )
    async def cotizar(self, request, data: CotizacionRequest):
        """
        Generate a quotation for the given package and quantity.

        Route: POST /api/cotizaciones/
        Auth: público.
        Returns: CotizacionResponse with current price, total, and validity window.

        Raises:
            400: CantidadInsuficienteError | PaqueteNotFoundError
        """
        flujo = CotizacionFlujo()
        resultado = await sync_to_async(flujo.cotizar)(
            paquete_id=data.paquete_id,
            cantidad=data.cantidad,
        )
        return success_response(resultado, message="Cotización generada correctamente.")
