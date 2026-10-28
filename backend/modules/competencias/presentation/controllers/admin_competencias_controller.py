"""
AdminCompetenciasController — the administrative surface of the bracket.

Thin async controller: payload → orchestrator → presenter →
`success_response` (`contract/django-app-architecture-contract.md` §4.8).
No `if`, no ORM, no manual error response: the errors are raised by the
domain and translated by the global handlers of `core/exceptions.py`.

Authorization: the whole controller is gated by `RequireCompetenciasEscribir`
(the capability `admin.competencias.escribir`, held by the operational staff
and by the break-glass tier, evaluated SERVER-SIDE on every request):

- anonymous caller → 401 `AUTHENTICATION_REQUIRED` (the JWT runs first),
- authenticated non-admin → 403 `ACTION_NOT_ALLOWED`,
- admin → 200/201/204.

The gate is declared once at the controller level: the read capability
(`admin.ver`) and the write capability (`admin.competencias.escribir`) are
held by the SAME tier today, so splitting them route by route would repeat
the same decision twenty times.

Routes:
  GET    /administracion/competencias                     — the competitions.
  POST   /administracion/competencias                     — create one.
  GET    /administracion/competencias/agenda              — the agenda of one day.
  GET    /administracion/competencias/{id}                 — the detail.
  PATCH  /administracion/competencias/{id}                 — update it.
  PATCH  /administracion/competencias/{id}/estado          — move its lifecycle.
  DELETE /administracion/competencias/{id}                 — delete a draft.
  GET    /administracion/competencias/{id}/cuadro          — its bracket.
  GET    /administracion/competencias/{id}/equipos         — its teams.
  POST   /administracion/competencias/{id}/equipos         — register a team.
  GET    /administracion/competencias/{id}/rondas          — its rounds.
  POST   /administracion/competencias/{id}/rondas          — create a round.
  GET    /administracion/competencias/{id}/encuentros      — its encounters.
  POST   /administracion/competencias/{id}/encuentros      — create an encounter.
"""
from datetime import date

from injector import inject
from ninja import Query
from ninja_extra import api_controller, route

from core.permissions import RequireCompetenciasEscribir
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.competencias.domain.schemas.competencias_schemas import (
    CompetenciaCreateData,
    CompetenciaEquipoUpdateData,
    CompetenciaFiltrosData,
    CompetenciaUpdateData,
    EncuentroCreateData,
    EncuentroFiltrosData,
    RondaCreateData,
    RondaUpdateData,
)
from modules.competencias.domain.services.orchestrators.competencia_lectura_orchestrator import (  # noqa: E501
    CompetenciaLecturaOrchestrator,
)
from modules.competencias.domain.services.orchestrators.competencia_equipo_orchestrator import (  # noqa: E501
    CompetenciaEquipoOrchestrator,
)
from modules.competencias.domain.services.orchestrators.competencia_orchestrator import (
    CompetenciaOrchestrator,
)
from modules.competencias.domain.services.orchestrators.encuentro_orchestrator import (
    EncuentroOrchestrator,
)
from modules.competencias.domain.services.orchestrators.ronda_orchestrator import (
    RondaOrchestrator,
)
from modules.competencias.presentation.presenters.competencias_presenter import (
    CompetenciasPresenter,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    AgendaOut,
    CompetenciaCreateIn,
    CompetenciaDetalleOut,
    CompetenciaEquipoCreateIn,
    CompetenciaEquipoOut,
    CompetenciaEquipoUpdateIn,
    CompetenciaEstadoIn,
    CompetenciaListOut,
    CompetenciaUpdateIn,
    CuadroOut,
    EncuentroCreateIn,
    EncuentroOut,
    RondaCreateIn,
    RondaEstadoIn,
    RondaOut,
    RondaUpdateIn,
)


@api_controller(
    "/administracion/competencias",
    tags=["Competencias"],
    permissions=[RequireCompetenciasEscribir],
)
class AdminCompetenciasController:
    """Controller of the competitions and of their bracket."""

    @inject
    def __init__(
        self,
        lectura: CompetenciaLecturaOrchestrator,
        comandos: CompetenciaOrchestrator,
        comandos_equipos: CompetenciaEquipoOrchestrator,
        comandos_rondas: RondaOrchestrator,
        comandos_encuentros: EncuentroOrchestrator,
    ):
        self._lectura = lectura
        self._comandos = comandos
        self._comandos_equipos = comandos_equipos
        self._comandos_rondas = comandos_rondas
        self._comandos_encuentros = comandos_encuentros

    # ── lecturas ───────────────────────────────────────────────────────────

    @route.get(
        "",
        response={200: ApiResponse[list[CompetenciaListOut]]},
        auth=JWTAuth(),
    )
    async def listar_competencias(
        self,
        request,
        evento_id: str | None = Query(None, description="Evento (UUID)."),
        disciplina_id: str | None = Query(None, description="Disciplina (UUID)."),
        categoria_id: str | None = Query(None, description="Categoría (UUID)."),
        estado: str | None = Query(None, description="Estado de la competencia."),
        fecha_desde: date | None = Query(None, description="Fecha inicial."),
        fecha_hasta: date | None = Query(None, description="Fecha final."),
    ):
        """
        List of the competitions of the scope of the administrator.

        Route: GET /api/administracion/competencias

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. The filters combine with AND and the
        counters (teams, encounters, finished encounters) are computed on the
        server.

        Returns:
            ApiResponse[list[CompetenciaListOut]].
        """
        filtros = CompetenciaFiltrosData(
            evento_id=evento_id,
            disciplina_id=disciplina_id,
            categoria_id=categoria_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )
        result = await self._lectura.listar_competencias(filtros)
        return success_response(CompetenciasPresenter.present_listado(result))

    @route.get(
        "/agenda",
        response={200: ApiResponse[AgendaOut]},
        auth=JWTAuth(),
    )
    async def obtener_agenda(
        self,
        request,
        fecha: date | None = Query(None, description="Día de la agenda."),
        evento_id: str | None = Query(None, description="Evento (UUID)."),
        disciplina_id: str | None = Query(None, description="Disciplina (UUID)."),
        categoria_id: str | None = Query(None, description="Categoría (UUID)."),
        estado: str | None = Query(None, description="Estado del encuentro."),
    ):
        """
        Agenda of ONE day.

        Route: GET /api/administracion/competencias/agenda

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. The agenda is TEMPORAL: it lists the
        encounters whose schedule starts that day (today when the client does
        not say). A day without encounters is an empty agenda, never an
        error.

        Returns:
            ApiResponse[AgendaOut].
        """
        filtros = EncuentroFiltrosData(
            evento_id=evento_id,
            disciplina_id=disciplina_id,
            categoria_id=categoria_id,
            estado=estado,
        )
        result = await self._lectura.obtener_agenda(fecha, filtros)
        return success_response(CompetenciasPresenter.present_agenda(result))

    @route.get(
        "/{competencia_id}",
        response={200: ApiResponse[CompetenciaDetalleOut]},
        auth=JWTAuth(),
    )
    async def obtener_competencia(self, request, competencia_id: str):
        """
        Detail of one competition with its teams and its rounds.

        Route: GET /api/administracion/competencias/{id}

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. An unknown id is answered with 404
        `COMPETENCIA_NOT_FOUND`.

        Returns:
            ApiResponse[CompetenciaDetalleOut].
        """
        result = await self._lectura.obtener_competencia(competencia_id)
        return success_response(CompetenciasPresenter.present_detalle(result))

    @route.get(
        "/{competencia_id}/cuadro",
        response={200: ApiResponse[CuadroOut]},
        auth=JWTAuth(),
    )
    async def obtener_cuadro(self, request, competencia_id: str):
        """
        Bracket of one competition.

        Route: GET /api/administracion/competencias/{id}/cuadro

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. An EMPTY or PARTIAL bracket is a valid
        answer: the rounds and the encounters that exist are returned as they
        are and NOTHING is invented.

        Returns:
            ApiResponse[CuadroOut].
        """
        result = await self._lectura.obtener_cuadro(competencia_id)
        return success_response(CompetenciasPresenter.present_cuadro(result))

    @route.get(
        "/{competencia_id}/equipos",
        response={200: ApiResponse[list[CompetenciaEquipoOut]]},
        auth=JWTAuth(),
    )
    async def listar_equipos(self, request, competencia_id: str):
        """
        Teams registered in the bracket.

        Route: GET /api/administracion/competencias/{id}/equipos

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. The order is the MANUAL one of the
        administrator, never an automatic seed.

        Returns:
            ApiResponse[list[CompetenciaEquipoOut]].
        """
        result = await self._lectura.listar_equipos(competencia_id)
        return success_response(CompetenciasPresenter.present_equipos(result))

    @route.get(
        "/{competencia_id}/rondas",
        response={200: ApiResponse[list[RondaOut]]},
        auth=JWTAuth(),
    )
    async def listar_rondas(self, request, competencia_id: str):
        """
        Rounds of the bracket.

        Route: GET /api/administracion/competencias/{id}/rondas

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY.

        Returns:
            ApiResponse[list[RondaOut]].
        """
        result = await self._lectura.listar_rondas(competencia_id)
        return success_response(CompetenciasPresenter.present_rondas(result))

    @route.get(
        "/{competencia_id}/encuentros",
        response={200: ApiResponse[list[EncuentroOut]]},
        auth=JWTAuth(),
    )
    async def listar_encuentros(
        self,
        request,
        competencia_id: str,
        ronda_id: str | None = Query(None, description="Ronda (UUID)."),
        estado: str | None = Query(None, description="Estado del encuentro."),
        fecha: date | None = Query(None, description="Día del horario."),
    ):
        """
        Encounters of the bracket.

        Route: GET /api/administracion/competencias/{id}/encuentros

        Authorization: Django admin only (is_staff OR is_superuser).

        The endpoint is READ-ONLY. The encounters without a schedule and the
        partial ones are part of the answer: the bracket must stay legible.

        Returns:
            ApiResponse[list[EncuentroOut]].
        """
        filtros = EncuentroFiltrosData(
            competencia_id=competencia_id,
            ronda_id=ronda_id,
            estado=estado,
            fecha=fecha,
        )
        result = await self._lectura.listar_encuentros(filtros)
        return success_response(CompetenciasPresenter.present_encuentros(result))

    # ── escrituras ─────────────────────────────────────────────────────────

    @route.post(
        "",
        response={201: ApiResponse[CompetenciaListOut]},
        auth=JWTAuth(),
    )
    async def crear_competencia(self, request, payload: CompetenciaCreateIn):
        """
        Create a competition.

        Route: POST /api/administracion/competencias

        Authorization: Django admin only (is_staff OR is_superuser).

        The identity (event + discipline + category + name) is unique and the
        date must be inside the event: the domain rejects the duplicate with
        409 `COMPETENCIA_DUPLICADA` and the invalid date with 422
        `INVALID_SCHEDULE`.

        Returns:
            ApiResponse[CompetenciaListOut] — 201.
        """
        data = CompetenciaCreateData(
            evento_id=str(payload.evento_id),
            disciplina_id=str(payload.disciplina_id),
            categoria_id=str(payload.categoria_id),
            nombre=payload.nombre,
            fecha=payload.fecha,
        )
        result = await self._comandos.crear_competencia_proceso(data, request.auth)
        return success_response(
            CompetenciasPresenter.present_competencia(result),
            message="La competencia se registró correctamente.",
        )

    @route.patch(
        "/{competencia_id}",
        response={200: ApiResponse[CompetenciaListOut]},
        auth=JWTAuth(),
    )
    async def actualizar_competencia(
        self,
        request,
        competencia_id: str,
        payload: CompetenciaUpdateIn,
    ):
        """
        Update the name or the date of a competition.

        Route: PATCH /api/administracion/competencias/{id}

        Authorization: Django admin only (is_staff OR is_superuser).

        The edit is optimistic: a stale `expected_version` fails with 409
        `RESOURCE_CHANGED` and NOTHING is written.

        Returns:
            ApiResponse[CompetenciaListOut].
        """
        data = CompetenciaUpdateData(
            nombre=payload.nombre,
            fecha=payload.fecha,
        )
        result = await self._comandos.actualizar_competencia_proceso(
            competencia_id,
            data,
            request.auth,
            None,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_competencia(result),
            message="La competencia se actualizó correctamente.",
        )

    @route.patch(
        "/{competencia_id}/estado",
        response={200: ApiResponse[CompetenciaListOut]},
        auth=JWTAuth(),
    )
    async def cambiar_estado_competencia(
        self,
        request,
        competencia_id: str,
        payload: CompetenciaEstadoIn,
    ):
        """
        Move a competition through its lifecycle.

        Route: PATCH /api/administracion/competencias/{id}/estado

        Authorization: Django admin only (is_staff OR is_superuser).

        An illegal transition fails with 409 `INVALID_STATE_TRANSITION` and
        a stale `expected_version` with 409 `RESOURCE_CHANGED`.

        Returns:
            ApiResponse[CompetenciaListOut].
        """
        result = await self._comandos.cambiar_estado_competencia_proceso(
            competencia_id,
            payload.estado,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_competencia(result),
            message="El estado de la competencia se actualizó correctamente.",
        )

    @route.delete(
        "/{competencia_id}",
        response={204: None},
        auth=JWTAuth(),
    )
    async def eliminar_competencia(self, request, competencia_id: str):
        """
        Delete a competition that was never used.

        Route: DELETE /api/administracion/competencias/{id}

        Authorization: Django admin only (is_staff OR is_superuser).

        Only a planned competition without teams, without rounds and without
        history after its creation may be deleted: everything else is
        cancelled and keeps its history (409 `DELETE_NOT_ALLOWED`).

        Returns:
            204 with an empty body.
        """
        await self._comandos.eliminar_competencia_proceso(competencia_id, request.auth)
        return None

    @route.post(
        "/{competencia_id}/equipos",
        response={201: ApiResponse[CompetenciaEquipoOut]},
        auth=JWTAuth(),
    )
    async def incorporar_equipo(
        self,
        request,
        competencia_id: str,
        payload: CompetenciaEquipoCreateIn,
    ):
        """
        Register a team in the bracket with its MANUAL order.

        Route: POST /api/administracion/competencias/{id}/equipos

        Authorization: Django admin only (is_staff OR is_superuser).

        The team MUST be active and belong to the same event, discipline and
        category of the competition: otherwise the domain answers 409
        `EQUIPO_NO_ELEGIBLE`. The order is NEVER chosen by the system.

        Returns:
            ApiResponse[CompetenciaEquipoOut] — 201.
        """
        result = await self._comandos_equipos.incorporar_equipo_proceso(
            competencia_id,
            str(payload.equipo_id),
            payload.orden,
            request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_equipos([result])[0],
            message="El equipo se incorporó a la competencia correctamente.",
        )

    @route.patch(
        "/{competencia_id}/equipos/{competencia_equipo_id}",
        response={200: ApiResponse[CompetenciaEquipoOut]},
        auth=JWTAuth(),
    )
    async def actualizar_equipo(
        self,
        request,
        competencia_id: str,
        competencia_equipo_id: str,
        payload: CompetenciaEquipoUpdateIn,
    ):
        """
        Update the manual order or the state of a participation.

        Route: PATCH /api/administracion/competencias/{id}/equipos/{equipo_id}

        Authorization: Django admin only (is_staff OR is_superuser).

        Returns:
            ApiResponse[CompetenciaEquipoOut].
        """
        data = CompetenciaEquipoUpdateData(
            orden=payload.orden,
            estado=payload.estado,
        )
        result = await self._comandos_equipos.actualizar_equipo_proceso(
            competencia_equipo_id,
            data,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_equipos([result])[0],
            message="La participación del equipo se actualizó correctamente.",
        )

    @route.post(
        "/{competencia_id}/rondas",
        response={201: ApiResponse[RondaOut]},
        auth=JWTAuth(),
    )
    async def crear_ronda(
        self,
        request,
        competencia_id: str,
        payload: RondaCreateIn,
    ):
        """
        Create a round of the bracket.

        Route: POST /api/administracion/competencias/{id}/rondas

        Authorization: Django admin only (is_staff OR is_superuser).

        The label and the order are unique inside the bracket: a duplicate
        fails with 409 `COMPETENCIA_DUPLICADA`.

        Returns:
            ApiResponse[RondaOut] — 201.
        """
        data = RondaCreateData(
            etiqueta=payload.etiqueta,
            orden=payload.orden,
        )
        result = await self._comandos_rondas.crear_ronda_proceso(
            competencia_id,
            data,
            request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_rondas([result])[0],
            message="La ronda se registró correctamente.",
        )

    @route.patch(
        "/{competencia_id}/rondas/{ronda_id}",
        response={200: ApiResponse[RondaOut]},
        auth=JWTAuth(),
    )
    async def actualizar_ronda(
        self,
        request,
        competencia_id: str,
        ronda_id: str,
        payload: RondaUpdateIn,
    ):
        """
        Update the label or the order of a round.

        Route: PATCH /api/administracion/competencias/{id}/rondas/{ronda_id}

        Authorization: Django admin only (is_staff OR is_superuser).

        Returns:
            ApiResponse[RondaOut].
        """
        data = RondaUpdateData(
            etiqueta=payload.etiqueta,
            orden=payload.orden,
        )
        result = await self._comandos_rondas.actualizar_ronda_proceso(
            ronda_id,
            data,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_rondas([result])[0],
            message="La ronda se actualizó correctamente.",
        )

    @route.patch(
        "/{competencia_id}/rondas/{ronda_id}/estado",
        response={200: ApiResponse[RondaOut]},
        auth=JWTAuth(),
    )
    async def invalidar_ronda(
        self,
        request,
        competencia_id: str,
        ronda_id: str,
        payload: RondaEstadoIn,
    ):
        """
        Invalidate a round (it is never deleted: its history is kept).

        Route: PATCH /api/administracion/competencias/{id}/rondas/{ronda_id}/estado

        Authorization: Django admin only (is_staff OR is_superuser).

        Returns:
            ApiResponse[RondaOut].
        """
        result = await self._comandos_rondas.invalidar_ronda_proceso(
            ronda_id,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_rondas([result])[0],
            message="La ronda se invalidó correctamente.",
        )

    @route.post(
        "/{competencia_id}/encuentros",
        response={201: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def crear_encuentro(
        self,
        request,
        competencia_id: str,
        payload: EncuentroCreateIn,
    ):
        """
        Create an encounter in a round of the bracket.

        Route: POST /api/administracion/competencias/{id}/encuentros

        Authorization: Django admin only (is_staff OR is_superuser).

        Both participants are optional ON PURPOSE: an empty or partial
        bracket must be readable and editable without inventing participants.

        Returns:
            ApiResponse[EncuentroOut] — 201.
        """
        data = EncuentroCreateData(
            orden=payload.orden,
            participante_1_id=(
                str(payload.participante_1_id)
                if payload.participante_1_id
                else None
            ),
            participante_2_id=(
                str(payload.participante_2_id)
                if payload.participante_2_id
                else None
            ),
        )
        result = await self._comandos_encuentros.crear_encuentro_proceso(
            str(payload.ronda_id),
            data,
            request.auth,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="El encuentro se registró correctamente.",
        )


__all__ = ["AdminCompetenciasController"]
