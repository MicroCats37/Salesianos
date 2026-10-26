"""
PublicCompetenciasController — the PUBLIC surface of the bracket.

READ-ONLY: it exposes NO write at all. Every route is a `GET` and the whole
surface is limited to the events the reader is authorized for.

The scope is resolved SERVER-SIDE by
`CompetenciaPublicaLecturaOrchestrator` (the ACTIVE editions): the client
never chooses the scope, it only asks for a competition. A competition
outside of the scope is answered with 404 `COMPETENCIA_NOT_FOUND` — the
surface never confirms the existence of a resource the reader cannot see.

Routes:
  GET /api/competencias                 — the competitions of the scope.
  GET /api/competencias/encuentros      — the encounters of the scope.
  GET /api/competencias/{id}            — the detail of one competition.
  GET /api/competencias/{id}/cuadro     — its bracket.
"""
from datetime import date

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny

from core.responses import ApiResponse, success_response
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaFiltrosData,
    EncuentroFiltrosData,
)
from modules.competencias.domain.services.orchestrators.competencia_lectura_orchestrator import (  # noqa: E501
    CompetenciaPublicaLecturaOrchestrator,
)
from modules.competencias.presentation.presenters.competencias_presenter import (
    CompetenciasPresenter,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    CompetenciaDetalleOut,
    CompetenciaListOut,
    CuadroOut,
    EncuentroOut,
)


@api_controller(
    "/competencias",
    tags=["Competencias públicas"],
    permissions=[AllowAny],
)
class PublicCompetenciasController:
    """Public and READ-ONLY surface of the bracket."""

    @inject
    def __init__(self, lectura: CompetenciaPublicaLecturaOrchestrator):
        self._lectura = lectura

    @route.get(
        "",
        response={200: ApiResponse[list[CompetenciaListOut]]},
        auth=None,
    )
    async def listar_competencias(
        self,
        request,
        disciplina_id: str | None = Query(None, description="Disciplina (UUID)."),
        categoria_id: str | None = Query(None, description="Categoría (UUID)."),
        estado: str | None = Query(None, description="Estado de la competencia."),
        fecha_desde: date | None = Query(None, description="Fecha inicial."),
        fecha_hasta: date | None = Query(None, description="Fecha final."),
    ):
        """
        List of the competitions of the authorized scope.

        Route: GET /api/competencias

        Auth: public.

        The endpoint is READ-ONLY. The filters combine with AND. An EMPTY or
        PARTIAL bracket is part of the answer: nothing is invented and no
        participant is completed automatically.

        Returns:
            ApiResponse[list[CompetenciaListOut]].
        """
        filtros = CompetenciaFiltrosData(
            disciplina_id=disciplina_id,
            categoria_id=categoria_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        result = await self._lectura.listar_competencias(filtros)
        return success_response(CompetenciasPresenter.present_listado(result))

    @route.get(
        "/encuentros",
        response={200: ApiResponse[list[EncuentroOut]]},
        auth=None,
    )
    async def listar_encuentros(
        self,
        request,
        competencia_id: str | None = Query(None, description="Competencia (UUID)."),
        ronda_id: str | None = Query(None, description="Ronda (UUID)."),
        disciplina_id: str | None = Query(None, description="Disciplina (UUID)."),
        categoria_id: str | None = Query(None, description="Categoría (UUID)."),
        estado: str | None = Query(None, description="Estado del encuentro."),
        fecha: date | None = Query(None, description="Día del horario."),
    ):
        """
        Encounters of the authorized scope.

        Route: GET /api/competencias/encuentros

        Auth: public.

        The endpoint is READ-ONLY. The encounters without a schedule and the
        partial ones are part of the answer.

        Returns:
            ApiResponse[list[EncuentroOut]].
        """
        filtros = EncuentroFiltrosData(
            competencia_id=competencia_id,
            ronda_id=ronda_id,
            disciplina_id=disciplina_id,
            categoria_id=categoria_id,
            estado=estado,
            fecha=fecha,
        )
        result = await self._lectura.listar_encuentros(filtros)
        return success_response(CompetenciasPresenter.present_encuentros(result))

    @route.get(
        "/{competencia_id}",
        response={200: ApiResponse[CompetenciaDetalleOut]},
        auth=None,
    )
    async def obtener_competencia(self, request, competencia_id: str):
        """
        Detail of one competition of the authorized scope.

        Route: GET /api/competencias/{id}

        Auth: public.

        The endpoint is READ-ONLY. A competition outside of the authorized
        scope is answered with 404 `COMPETENCIA_NOT_FOUND`, exactly like an
        unknown id: the surface never confirms the existence of a resource
        the reader cannot see.

        Returns:
            ApiResponse[CompetenciaDetalleOut].
        """
        result = await self._lectura.obtener_competencia(competencia_id)
        return success_response(CompetenciasPresenter.present_detalle(result))

    @route.get(
        "/{competencia_id}/cuadro",
        response={200: ApiResponse[CuadroOut]},
        auth=None,
    )
    async def obtener_cuadro(self, request, competencia_id: str):
        """
        Bracket of one competition of the authorized scope.

        Route: GET /api/competencias/{id}/cuadro

        Auth: public.

        The endpoint is READ-ONLY. An EMPTY or PARTIAL bracket is a valid
        answer: the rounds and the encounters that exist are returned as they
        are and NOTHING is invented.

        Returns:
            ApiResponse[CuadroOut].
        """
        result = await self._lectura.obtener_cuadro(competencia_id)
        return success_response(CompetenciasPresenter.present_cuadro(result))


__all__ = ["PublicCompetenciasController"]
