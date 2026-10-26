"""
AdminEncuentrosController — the commands of the encounters of the bracket.

Thin async controller: payload → orchestrator → presenter →
`success_response` (`contract/django-app-architecture-contract.md` §4.8).
No `if`, no ORM, no manual error response.

Authorization: the whole controller is gated by `RequireAdmin`
(admin = `is_staff OR is_superuser`): anonymous → 401, authenticated
non-admin → 403, admin → 200/201/204.

Every protected mutation (moving a team, scheduling, changing the state,
linking, the result, the advance and the correction) demands an audited
motive and the optimistic lock (`expected_version`): a stale version fails
with 409 `RESOURCE_CHANGED` and NOTHING is written.

Routes:
  PATCH  .../encuentros/{id}/participantes  — move the teams of the slots.
  PATCH  .../encuentros/{id}/programacion   — schedule the encounter.
  PATCH  .../encuentros/{id}/estado        — move its lifecycle.
  POST   .../encuentros/{id}/bye            — configure a MANUAL bye.
  POST   .../encuentros/{id}/enlace        — link it to the next one.
  POST   .../encuentros/{id}/desenlace     — remove the link.
  POST   .../encuentros/{id}/resultado     — register the winner.
  POST   .../encuentros/{id}/avance/preview  — propose the propagation.
  POST   .../encuentros/{id}/avance/confirm  — propagate the winner.
  POST   .../encuentros/{id}/correccion/preview — analyse the correction.
  POST   .../encuentros/{id}/correccion/confirm — correct the winner.
  DELETE .../encuentros/{id}                — delete a draft.
"""
from injector import inject
from ninja_extra import api_controller, route

from core.permissions import RequireAdmin
from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.competencias.domain.schemas.competencias_schemas import (
    CorreccionGanadorData,
    EncuentroEnlaceData,
    EncuentroProgramacionData,
    ResultadoEncuentroData,
)
from modules.competencias.domain.services.orchestrators.avance_orchestrator import (
    AvanceOrchestrator,
)
from modules.competencias.domain.services.orchestrators.correccion_orchestrator import (
    CorreccionOrchestrator,
)
from modules.competencias.domain.services.orchestrators.encuentro_orchestrator import (
    EncuentroOrchestrator,
)
from modules.competencias.domain.services.orchestrators.resultado_orchestrator import (
    ResultadoOrchestrator,
)
from modules.competencias.presentation.presenters.competencias_presenter import (
    CompetenciasPresenter,
)
from modules.competencias.presentation.schemas.competencias_schemas import (
    AvanceConfirmarIn,
    AvanceOut,
    AvancePreviewOut,
    CorreccionConfirmarIn,
    CorreccionOut,
    CorreccionPreviewIn,
    CorreccionPreviewOut,
    EncuentroDesenlaceIn,
    EncuentroEnlaceIn,
    EncuentroEstadoIn,
    EncuentroOut,
    EncuentroParticipantesIn,
    EncuentroProgramacionIn,
    ResultadoEncuentroIn,
)


@api_controller(
    "/administracion/competencias/encuentros",
    tags=["Competencias"],
    permissions=[RequireAdmin],
)
class AdminEncuentrosController:
    """Controller of the commands of the encounters."""

    @inject
    def __init__(
        self,
        comandos: EncuentroOrchestrator,
        comandos_resultado: ResultadoOrchestrator,
        comandos_avance: AvanceOrchestrator,
        comandos_correccion: CorreccionOrchestrator,
    ):
        self._comandos = comandos
        self._comandos_resultado = comandos_resultado
        self._comandos_avance = comandos_avance
        self._comandos_correccion = comandos_correccion

    # ── participantes, horario y estado ────────────────────────────────────

    @route.patch(
        "/{encuentro_id}/participantes",
        response={200: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def asignar_participantes(
        self,
        request,
        encuentro_id: str,
        payload: EncuentroParticipantesIn,
    ):
        """
        Move the teams of the two slots of an encounter.

        Route: PATCH /api/administracion/competencias/encuentros/{id}/participantes

        Authorization: Django admin only (is_staff OR is_superuser).

        Moving a slot ALWAYS demands an audited motive (422
        `REASON_REQUIRED` without it). A repeated command with the same
        intention writes NOTHING (it is idempotent).

        Returns:
            ApiResponse[EncuentroOut].
        """
        result = await self._comandos.asignar_participantes_proceso(
            encuentro_id,
            (
                str(payload.participante_1_id)
                if payload.participante_1_id
                else None
            ),
            (
                str(payload.participante_2_id)
                if payload.participante_2_id
                else None
            ),
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="Los participantes del encuentro se actualizaron correctamente.",
        )

    @route.patch(
        "/{encuentro_id}/programacion",
        response={200: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def programar_encuentro(
        self,
        request,
        encuentro_id: str,
        payload: EncuentroProgramacionIn,
    ):
        """
        Schedule an encounter.

        Route: PATCH /api/administracion/competencias/encuentros/{id}/programacion

        Authorization: Django admin only (is_staff OR is_superuser).

        The schedule must be a positive interval of the competition day
        (422 `INVALID_SCHEDULE`) and a team MUST NOT play two encounters at
        the same time (409 `EQUIPO_SOLAPADO`). The check is portable: it
        spans every competition of the event.

        Returns:
            ApiResponse[EncuentroOut].
        """
        data = EncuentroProgramacionData(
            inicio_programado=payload.inicio_programado,
            fin_programado=payload.fin_programado,
        )
        result = await self._comandos.programar_encuentro_proceso(
            encuentro_id,
            data,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="El encuentro se programó correctamente.",
        )

    @route.patch(
        "/{encuentro_id}/estado",
        response={200: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def cambiar_estado_encuentro(
        self,
        request,
        encuentro_id: str,
        payload: EncuentroEstadoIn,
    ):
        """
        Move an encounter through its lifecycle.

        Route: PATCH /api/administracion/competencias/encuentros/{id}/estado

        Authorization: Django admin only (is_staff OR is_superuser).

        An illegal transition fails with 409 `INVALID_STATE_TRANSITION` and
        a stale `expected_version` with 409 `RESOURCE_CHANGED`.

        Returns:
            ApiResponse[EncuentroOut].
        """
        result = await self._comandos.cambiar_estado_encuentro_proceso(
            encuentro_id,
            payload.estado,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="El estado del encuentro se actualizó correctamente.",
        )

    @route.post(
        "/{encuentro_id}/bye",
        response={200: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def configurar_bye(
        self,
        request,
        encuentro_id: str,
        payload: EncuentroParticipantesIn,
    ):
        """
        Configure a MANUAL bye.

        Route: POST /api/administracion/competencias/encuentros/{id}/bye

        Authorization: Django admin only (is_staff OR is_superuser).

        A bye has exactly one participant, no schedule and no score, and it
        is final. The system NEVER chooses a bye by itself: the administrator
        does (spec).

        Returns:
            ApiResponse[EncuentroOut].
        """
        result = await self._comandos.configurar_bye_proceso(
            encuentro_id,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="El bye se configuró correctamente.",
        )

    # ── enlaces del cuadro ─────────────────────────────────────────────────

    @route.post(
        "/{encuentro_id}/enlace",
        response={200: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def enlazar_siguiente(
        self,
        request,
        encuentro_id: str,
        payload: EncuentroEnlaceIn,
    ):
        """
        Link an encounter to the next encounter of the bracket.

        Route: POST /api/administracion/competencias/encuentros/{id}/enlace

        Authorization: Django admin only (is_staff OR is_superuser).

        The link and its destination slot are written TOGETHER and the link
        ALWAYS points forward (to a LATER round of the same competition), so
        a cycle can never be built. An invalid link fails with 422
        `INVALID_LINK`.

        Returns:
            ApiResponse[EncuentroOut].
        """
        data = EncuentroEnlaceData(
            siguiente_encuentro_id=str(payload.siguiente_encuentro_id),
            slot_destino=payload.slot_destino,
        )
        result = await self._comandos.enlazar_siguiente_encuentro_proceso(
            encuentro_id,
            data.siguiente_encuentro_id,
            data.slot_destino,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="El encuentro se enlazó correctamente.",
        )

    @route.post(
        "/{encuentro_id}/desenlace",
        response={200: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def desenlazar_siguiente(
        self,
        request,
        encuentro_id: str,
        payload: EncuentroDesenlaceIn,
    ):
        """
        Remove the link of an encounter (both fields travel together).

        Route: POST /api/administracion/competencias/encuentros/{id}/desenlace

        Authorization: Django admin only (is_staff OR is_superuser).

        A propagation that was already applied cannot be orphaned: the
        correction owns that rewrite (409 `INVALID_STATE_TRANSITION`).

        Returns:
            ApiResponse[EncuentroOut].
        """
        result = await self._comandos.desenlazar_siguiente_encuentro_proceso(
            encuentro_id,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="El enlace del encuentro se eliminó correctamente.",
        )

    # ── resultado, avance y corrección ─────────────────────────────────────

    @route.post(
        "/{encuentro_id}/resultado",
        response={200: ApiResponse[EncuentroOut]},
        auth=JWTAuth(),
    )
    async def registrar_resultado(
        self,
        request,
        encuentro_id: str,
        payload: ResultadoEncuentroIn,
    ):
        """
        Register the authoritative result of an encounter.

        Route: POST /api/administracion/competencias/encuentros/{id}/resultado

        Authorization: Django admin only (is_staff OR is_superuser).

        The winner is AUTHORITATIVE and it MUST occupy one of the two slots
        (422 `INVALID_WINNER` otherwise). The scores are optional and purely
        informative: they never determine nor contradict the winner. A
        repeated command with the same intention writes NOTHING.

        Returns:
            ApiResponse[EncuentroOut].
        """
        data = ResultadoEncuentroData(
            ganador_id=str(payload.ganador_id),
            puntaje_1=payload.puntaje_1,
            puntaje_2=payload.puntaje_2,
            marcador_detalle=payload.marcador_detalle or "",
        )
        result = await self._comandos_resultado.registrar_resultado_proceso(
            encuentro_id,
            data,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_encuentros([result])[0],
            message="El resultado del encuentro se registró correctamente.",
        )

    @route.post(
        "/{encuentro_id}/avance/preview",
        response={200: ApiResponse[AvancePreviewOut]},
        auth=JWTAuth(),
    )
    async def previsualizar_avance(self, request, encuentro_id: str):
        """
        Proposal of the propagation of the winner to the next encounter.

        Route: POST /api/administracion/competencias/encuentros/{id}/avance/preview

        Authorization: Django admin only (is_staff OR is_superuser).

        The preview NEVER writes: it is the proposal the administrator
        confirms. A blocked destination is reported in the answer (it is not
        an error of the request).

        Returns:
            ApiResponse[AvancePreviewOut].
        """
        result = await self._comandos_avance.previsualizar_avance_proceso(
            encuentro_id
        )
        return success_response(
            CompetenciasPresenter.present_avance_preview(result),
            message="La propuesta de avance se generó correctamente.",
        )

    @route.post(
        "/{encuentro_id}/avance/confirm",
        response={200: ApiResponse[AvanceOut]},
        auth=JWTAuth(),
    )
    async def confirmar_avance(
        self,
        request,
        encuentro_id: str,
        payload: AvanceConfirmarIn,
    ):
        """
        Place the winner in the linked slot of the next encounter.

        Route: POST /api/administracion/competencias/encuentros/{id}/avance/confirm

        Authorization: Django admin only (is_staff OR is_superuser).

        The winner is placed ONCE and the propagation is recorded. A blocked
        destination fails with 409 `DESTINO_BLOQUEADO` and an occupied slot
        with 409 `SLOT_OCUPADO`. A repeated command writes NOTHING.

        Returns:
            ApiResponse[AvanceOut].
        """
        result = await self._comandos_avance.confirmar_avance_proceso(
            encuentro_id,
            request.auth,
            payload.motivo,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_avance(result),
            message="El avance del cuadro se aplicó correctamente.",
        )

    @route.post(
        "/{encuentro_id}/correccion/preview",
        response={200: ApiResponse[CorreccionPreviewOut]},
        auth=JWTAuth(),
    )
    async def previsualizar_correccion(
        self,
        request,
        encuentro_id: str,
        payload: CorreccionPreviewIn,
    ):
        """
        Impact analysis of the correction of the winner.

        Route: POST /api/administracion/competencias/encuentros/{id}/correccion/preview

        Authorization: Django admin only (is_staff OR is_superuser).

        The preview NEVER writes: it reports the impact over every
        descendant of the link and whether the correction would need an
        explicit override.

        Returns:
            ApiResponse[CorreccionPreviewOut].
        """
        result = await self._comandos_correccion.previsualizar_correccion_proceso(
            encuentro_id,
            str(payload.ganador_id),
        )
        return success_response(
            CompetenciasPresenter.present_correccion_preview(result),
            message="El impacto de la corrección se calculó correctamente.",
        )

    @route.post(
        "/{encuentro_id}/correccion/confirm",
        response={200: ApiResponse[CorreccionOut]},
        auth=JWTAuth(),
    )
    async def corregir_ganador(
        self,
        request,
        encuentro_id: str,
        payload: CorreccionConfirmarIn,
    ):
        """
        Correct the authoritative winner of an encounter.

        Route: POST /api/administracion/competencias/encuentros/{id}/correccion/confirm

        Authorization: Django admin only (is_staff OR is_superuser).

        When a descendant of the link already started, finished or was
        cancelled, the correction changes NOTHING unless the administrator
        sends `override=true` AND `acepta_impacto=true` AND a motive: there
        is never a silent cascade (409 `DESTINO_BLOQUEADO`).

        Returns:
            ApiResponse[CorreccionOut].
        """
        data = CorreccionGanadorData(
            ganador_id=str(payload.ganador_id),
            motivo=payload.motivo,
            override=payload.override,
            acepta_impacto=payload.acepta_impacto,
        )
        result = await self._comandos_correccion.corregir_ganador_proceso(
            encuentro_id,
            data,
            request.auth,
            payload.expected_version,
        )
        return success_response(
            CompetenciasPresenter.present_correccion(result),
            message="La corrección del ganador se aplicó correctamente.",
        )

    @route.delete(
        "/{encuentro_id}",
        response={204: None},
        auth=JWTAuth(),
    )
    async def eliminar_encuentro(self, request, encuentro_id: str):
        """
        Delete a draft that was never used.

        Route: DELETE /api/administracion/competencias/encuentros/{id}

        Authorization: Django admin only (is_staff OR is_superuser).

        Only a draft without participants, without schedule, without links or
        dependencies and without history after its creation may be deleted:
        everything else is cancelled and keeps its history (409
        `DELETE_NOT_ALLOWED`).

        Returns:
            204 with an empty body.
        """
        await self._comandos.eliminar_encuentro_proceso(encuentro_id, request.auth)
        return None


__all__ = ["AdminEncuentrosController"]
