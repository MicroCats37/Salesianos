"""
CatalogoController — HTTP endpoints for public catalog (read-only).
"""
from asgiref.sync import sync_to_async

from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny

from core.responses import ApiResponse, success_response
from modules.salesianos_fest.domain.selectors import (
    DisciplinaSelector,
    PromocionSelector,
    CategoriaSelector,
    PaqueteSelector,
)
from modules.salesianos_fest.presentation.schemas.catalogo_schemas import (
    DisciplinaOut,
    PromocionOut,
    CategoriaOut,
    PaqueteListOut,
    PaqueteDetailOut,
)
from modules.salesianos_fest.presentation.presenters.catalogo_presenter import CatalogoPresenter


@api_controller("/catalogo", tags=["Catálogo FEST"], permissions=[AllowAny])
class CatalogoController:
    """
    Endpoints públicos de solo lectura para el catálogo del evento.

    Auth: AllowAny (catálogo público).
    No hay endpoints de escritura en Fase 2.
    """

    @route.get("/disciplinas/", response={200: ApiResponse[list[DisciplinaOut]]}, auth=None)
    async def listar_disciplinas(self):
        """
        Lista todas las disciplinas activas del evento.

        Route: GET /api/catalogo/disciplinas/
        Auth: público.
        Returns: Lista de disciplinas con su modalidad y jugadores por equipo.
        """
        resultados = await sync_to_async(DisciplinaSelector.get_activas)()
        disciplinas = CatalogoPresenter.present_disciplinas(resultados)
        return success_response(disciplinas, message="Disciplinas listadas correctamente.")

    @route.get("/promociones/", response={200: ApiResponse[list[PromocionOut]]}, auth=None)
    async def listar_promociones(self):
        """
        Lista todas las promociones activas (rangos etarios).

        Route: GET /api/catalogo/promociones/
        Auth: público.
        Returns: Lista de promociones con año y nombre.
        """
        resultados = await sync_to_async(PromocionSelector.get_activas)()
        promociones = CatalogoPresenter.present_promociones(resultados)
        return success_response(promociones, message="Promociones listadas correctamente.")

    @route.get("/categorias/", response={200: ApiResponse[list[CategoriaOut]]}, auth=None)
    async def listar_categorias(self):
        """
        Lista todas las categorías activas.

        Route: GET /api/catalogo/categorias/
        Auth: público.
        Returns: Lista de categorías con evento y rango etario.
        """
        resultados = await sync_to_async(CategoriaSelector.get_activas)()
        categorias = CatalogoPresenter.present_categorias(resultados)
        return success_response(categorias, message="Categorías listadas correctamente.")

    @route.get("/paquetes/", response={200: ApiResponse[list[PaqueteListOut]]}, auth=None)
    async def listar_paquetes(self):
        """
        Lista todos los paquetes activos con precios de preventa y regular.

        Route: GET /api/catalogo/paquetes/
        Auth: público.
        Returns: Lista de paquetes con precios vigentes.
        """
        resultados = await sync_to_async(PaqueteSelector.get_activos)()
        paquetes = CatalogoPresenter.present_paquetes(resultados)
        return success_response(paquetes, message="Paquetes listados correctamente.")

    @route.get(
        "/paquetes/{paquete_id}/",
        response={200: ApiResponse[PaqueteDetailOut]},
        auth=None,
    )
    async def detalle_paquete(self, paquete_id: str):
        """
        Detalle de un paquete con todos sus precios, beneficios y disciplinas.

        Route: GET /api/catalogo/paquetes/{id}/
        Auth: público.
        Returns: Detalle completo del paquete.
        """
        resultado = await sync_to_async(PaqueteSelector.get_by_id)(paquete_id)
        if resultado is None:
            from modules.salesianos_fest.domain.exceptions import PaqueteNotFoundError

            raise PaqueteNotFoundError()
        paquete = CatalogoPresenter.present_paquete_detail(resultado)
        return success_response(paquete, message="Paquete obtenido correctamente.")
