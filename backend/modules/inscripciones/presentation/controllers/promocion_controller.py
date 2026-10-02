"""PromocionController — catalog endpoints for promociones."""

from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny

from core.responses import ApiResponse, success_response
from modules.inscripciones.domain.models import Promocion
from modules.inscripciones.presentation.schemas.promocion_schemas import PromocionOut


@api_controller("/inscripciones/promociones", tags=["Catálogos"], permissions=[AllowAny])
class PromocionController:
    """
    Controller for active promotion catalog.

    Public read-only endpoint used by the inscription wizard.

    Rutas:
      GET /inscripciones/promociones/ -> listar_promociones
    """

    @route.get("/", response={200: ApiResponse[list[PromocionOut]]}, auth=None)
    def listar_promociones(self):
        """
        List active promociones ordered by year descending.

        Route: GET /api/inscripciones/promociones/
        Auth: public (no JWT).
        Returns: lista de promociones activas (colegio + nombre + año) usadas en el wizard.
        """
        promociones = Promocion.objects.filter(activa=True).order_by("-anio")
        data = [
            PromocionOut(
                id=str(p.id),
                anio=p.anio,
                colegio=p.colegio,
                nombre=p.nombre,
                activa=p.activa,
            )
            for p in promociones
        ]
        return success_response(data)
