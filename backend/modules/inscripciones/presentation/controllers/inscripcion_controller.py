"""InscripcionController — endpoints para ciclo de vida de inscripciones."""

from ninja_extra import api_controller, route
from ninja_extra.permissions import AllowAny, IsAuthenticated
from injector import inject

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from core.exceptions import BusinessError, NotFoundError
from modules.inscripciones.presentation.schemas.inscripcion_schemas import (
    AgregarParticipanteOut,
    AgregarParticipantesOut,
    InscripcionCreateIn,
    InscripcionOut,
    InscripcionDetalleOut,
    CambiarEstadoIn,
    AsignarDelegadoIn,
    ParticipantesPatchIn,
    ParticipanteCreateIn,
    ParticipanteEditIn,
    ParticipanteMoveIn,
    ParticipanteOut,
)
from modules.inscripciones.presentation.presenters.inscripcion_presenter import InscripcionPresenter


def _present_participante_full(participante):
    """
    Build a `ParticipanteOut` (canonical, with `persona`) for a single
    ParticipanteInscripcion. Used by edit/move endpoints so the response
    shape is identical to the one inside `InscripcionDetalleOut`.

    Centralizing this here keeps `persona`, `acepto_*` and `notas` consistent
    across all endpoints. The frontend cache relies on this homogeneity to
    do optimistic updates without desincronizing the
    `equipos[].participantes[]` array shape.
    """
    persona = participante.participacion.persona
    return ParticipanteOut(
        id=str(participante.id),
        participacion_id=str(participante.participacion_id),
        equipo_id=str(participante.equipo_id),
        rol=participante.rol,
        talle_camiseta=participante.talle_camiseta,
        notas=getattr(participante, "notas", None),
        persona=InscripcionPresenter._present_persona(persona),
        acepto_bases=getattr(persona, "acepto_bases", False),
        acepto_aptitud_fisica=getattr(persona, "acepto_aptitud_fisica", False),
        acepto_imagen=getattr(persona, "acepto_imagen", False),
    )
from modules.inscripciones.domain.services.orchestrators.inscripcion_orchestrator import (
    InscripcionOrchestrator,
)
from modules.inscripciones.domain.selectors.inscripcion_selector import InscripcionSelector


def _get_authenticated_persona_id(request) -> str:
    """
    Extract persona_id from the authenticated request.

    The request must have a valid JWT with an authenticated Usuario.
    Uses request.user.persona_fk_id (Usuario -> Persona FK).

    Raises BusinessError if user has no Persona linked.
    """
    user = request.user
    persona_id = getattr(user, "persona_fk_id", None)
    if not persona_id:
        raise BusinessError("Usuario sin persona vinculada. Complete su registro.")
    return str(persona_id)


@api_controller("/inscripciones", tags=["Inscripciones"], permissions=[AllowAny])
class InscripcionController:
    """
    Controlador para operaciones de inscripción.

    Endpoints para crear, listar y gestionar inscripciones.
    Catalogos (disciplinas, paquetes, eventos) son publicos (auth=None).
    Ciclo de vida requiere autenticacion JWT con persona vinculada.

    Rutas:
      POST   /                                                  -> crear_inscripcion
      GET    /                                                  -> listar_inscripciones
      GET    /{inscripcion_id}                                  -> obtener_inscripcion
      PATCH  /{inscripcion_id}/estado                           -> cambiar_estado
      POST   /{inscripcion_id}/delegado                         -> asignar_delegado
      POST   /{inscripcion_id}/participantes                    -> agregar_participante
      PATCH  /{inscripcion_id}/equipos/{equipo_id}/participantes -> agregar_participantes_a_equipo
      PATCH  /{inscripcion_id}/participantes/{participante_id}  -> editar_participante
      DELETE /{inscripcion_id}/participantes/{participante_id}  -> remover_participante
      PATCH  /{inscripcion_id}/participantes/{participante_id}/mover -> mover_participante
    """

    @inject
    def __init__(
        self,
        orchestrator: InscripcionOrchestrator,
        selector: InscripcionSelector,
    ):
        self.orchestrator = orchestrator
        self.selector = selector

    @route.post("/", response={200: ApiResponse[InscripcionOut]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def crear_inscripcion(self, request, payload: InscripcionCreateIn):
        """
        Crear una nueva inscripción (wizard completo).

        Route: POST /api/inscripciones/
        Auth: JWT required. El responsable se toma del JWT (persona vinculada).
        Side effects: crea Inscripcion + Equipos + Participaciones + ParticipanteInscripcion
                      en una sola transaccion (orchestrator.crear_inscripcion_completa).
        Errors: BusinessError si usuario sin persona vinculada, ConflictError si ya existe
                inscripcion para el responsable en el evento activo.
        """
        from asgiref.sync import sync_to_async

        responsable_id = _get_authenticated_persona_id(request)

        # Build equipos_data from payload
        equipos_data = [
            {
                "disciplina_id": eq.disciplina_id,
                "categoria_id": eq.categoria_id,
                "nombre": eq.nombre,
                "participantes": [
                    {
                        **{k: v for k, v in {
                            "persona_id": p.persona_id,
                            "tipoDocumento": p.tipoDocumento,
                            "numeroDocumento": p.numeroDocumento,
                            "nombres": p.nombres,
                            "apellidos": p.apellidos,
                            "genero": p.genero,
                            "telefono": p.telefono,
                            "whatsapp": p.whatsapp,
                            "notas": p.notas,
                        }.items() if v is not None},
                        "rol": p.rol,
                        "talle_camiseta": p.talle_camiseta,
                        "acepto_bases": p.acepto_bases,
                        "acepto_aptitud_fisica": p.acepto_aptitud_fisica,
                        "acepto_imagen": p.acepto_imagen,
                    }
                    for p in eq.participantes
                ],
            }
            for eq in payload.equipos
        ]

        inscripcion = await self.orchestrator.crear_inscripcion_completa(
            responsable_id=responsable_id,
            paquete_id=payload.paquete_id,
            promocion_id=payload.promocion_id,
            observacion=payload.observacion,
            equipos_data=equipos_data,
            fusion_promocion_id=payload.fusion_promocion_id,
            accepted_bases=payload.accepted_bases,
            fitness_declaration=payload.fitness_declaration,
            image_consent=payload.image_consent,
        )
        # Wrap presenter call in sync_to_async because present_inscripcion uses
        # sync ORM calls (.count() on querysets) which are not allowed in async context
        presenter_result = await sync_to_async(InscripcionPresenter.present_inscripcion)(inscripcion)
        return success_response(presenter_result, message="Inscripción creada correctamente.")

    @route.get("/", response={200: ApiResponse[list[InscripcionOut]]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def listar_inscripciones(self, request):
        """
        Listar las inscripciones del responsable autenticado.

        Route: GET /api/inscripciones/
        Auth: JWT required. Devuelve solo las inscripciones cuyo responsable
              es el usuario autenticado.
        Errors: BusinessError si usuario sin persona vinculada.
        """
        from asgiref.sync import sync_to_async

        responsable_id = _get_authenticated_persona_id(request)
        _listar = sync_to_async(self.selector.listar_inscripciones_por_responsable)
        inscripciones = await _listar(responsable_id)
        data = await sync_to_async(lambda: [InscripcionPresenter.present_inscripcion(i) for i in inscripciones])()
        return success_response(data)

    @route.get("/{inscripcion_id}", response={200: ApiResponse[InscripcionDetalleOut]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def obtener_inscripcion(self, request, inscripcion_id: str):
        """
        Obtener el detalle completo de una inscripción (incluye equipos + participantes).

        Route: GET /api/inscripciones/{inscripcion_id}
        Auth: JWT required. Solo el responsable puede ver su propia inscripción.
        Errors: NotFoundError si la inscripción no existe,
                BusinessError si el usuario no es el responsable.
        """
        from asgiref.sync import sync_to_async

        responsable_id = _get_authenticated_persona_id(request)
        _obtener = sync_to_async(self.selector.obtener_inscripcion)
        inscripcion = await _obtener(inscripcion_id)

        if not inscripcion:
            raise NotFoundError(f"Inscripción {inscripcion_id} no encontrada.")

        # Check ownership
        if str(inscripcion.responsable_id) != responsable_id:
            raise BusinessError("No tienes permiso para ver esta inscripción.")

        presenter_result = await sync_to_async(InscripcionPresenter.present_inscripcion_detalle)(inscripcion)
        return success_response(presenter_result)

    @route.patch("/{inscripcion_id}/estado", response={200: ApiResponse[InscripcionOut]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def cambiar_estado(self, request, inscripcion_id: str, payload: CambiarEstadoIn):
        """
        Cambiar el estado de una inscripción.

        Route: PATCH /api/inscripciones/{inscripcion_id}/estado
        Auth: JWT required. Uso interno del Comité.
        Errors: NotFoundError si la inscripción no existe,
                BusinessError si la transición de estado no es válida.
        """
        _get_authenticated_persona_id(request)  # Verify user has persona
        inscripcion = await self.orchestrator.cambiar_estado(
            inscripcion_id=inscripcion_id,
            nuevo_estado=payload.nuevo_estado,
            observacion=payload.observacion,
        )
        presenter_result = await sync_to_async(InscripcionPresenter.present_inscripcion)(inscripcion)
        nuevo_estado_label = getattr(payload.nuevo_estado, "value", str(payload.nuevo_estado))
        return success_response(
            presenter_result,
            message=f"Estado de la inscripción actualizado a '{nuevo_estado_label}'.",
        )

    @route.post("/{inscripcion_id}/delegado", response={200: ApiResponse[dict]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def asignar_delegado(self, request, inscripcion_id: str, payload: AsignarDelegadoIn):
        """
        Asignar un delegado a la inscripción.

        Route: POST /api/inscripciones/{inscripcion_id}/delegado
        Auth: JWT required. El delegado debe ser el responsable o un participante
              de la inscripción.
        Errors: NotFoundError si la inscripción o la persona no existen,
                BusinessError si la persona no pertenece a la inscripción.
        """
        _get_authenticated_persona_id(request)  # Verify user has persona
        await self.orchestrator.asignar_delegado(
            inscripcion_id=inscripcion_id,
            persona_id=payload.persona_id,
        )
        return success_response(
            {"delegado_persona_id": payload.persona_id},
            message="Delegado asignado correctamente.",
        )

    @route.post(
        "/{inscripcion_id}/participantes",
        response={200: ApiResponse[AgregarParticipanteOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def agregar_participante(
        self,
        request,
        inscripcion_id: str,
        payload: ParticipanteCreateIn,
    ):
        """
        Agregar un participante existente a un equipo existente dentro de una inscripción.

        Route: POST /api/inscripciones/{inscripcion_id}/participantes
        Auth: JWT required. Toma el primer equipo de la inscripción (MVP).
              Soporta aseguradora y acceptances booleanas por participante.

        Returns the canonical `ParticipanteOut` (incl. `persona`, `acepto_*`,
        `notas`) so the frontend can append it to its TanStack Query cache
        without a refetch — same shape as `InscripcionDetalleOut`.
        """
        from asgiref.sync import sync_to_async

        _get_authenticated_persona_id(request)  # Verify user has persona

        # Get the equipo from the inscription
        equipo = None
        equipos = self.selector.obtener_equipos_de_inscripcion(inscripcion_id)
        if equipos:
            equipo = equipos[0]  # For MVP, use first team

        if not equipo:
            raise NotFoundError(f"No se encontró equipo en la inscripción {inscripcion_id}.")

        resultado = await self.orchestrator.agregar_participante(
            equipo_id=str(equipo.id),
            persona_id=payload.persona_id,
            rol=payload.rol,
            talle_camiseta=payload.talle_camiseta,
            notas=payload.notas,
            acepto_bases=payload.acepto_bases,
            acepto_aptitud_fisica=payload.acepto_aptitud_fisica,
            acepto_imagen=payload.acepto_imagen,
        )

        # Build canonical response (same shape as InscripcionDetalleOut entries).
        participante_out = await sync_to_async(_present_participante_full)(resultado)
        return success_response(
            AgregarParticipanteOut(
                mensaje="Participante agregado correctamente.",
                participante=participante_out,
            )
        )

    @route.patch(
        "/{inscripcion_id}/equipos/{equipo_id}/participantes",
        response={200: ApiResponse[AgregarParticipantesOut]},
        auth=JWTAuth(),
        permissions=[IsAuthenticated],
    )
    async def agregar_participantes_a_equipo(
        self,
        request,
        inscripcion_id: str,
        equipo_id: str,
        payload: ParticipantesPatchIn,
    ):
        """
        Agregar uno o más participantes a un equipo existente dentro de una inscripción.

        Route: PATCH /api/inscripciones/{inscripcion_id}/equipos/{equipo_id}/participantes
        Auth: JWT required. El equipo debe pertenecer a la inscripción del usuario.
        Soporta dos modos por participante:
          - Legacy: persona_id existente
          - Inline: datos de persona (tipoDocumento, numeroDocumento, nombres, apellidos, genero)
        Errors: NotFoundError si la inscripción no existe,
                BusinessError si el usuario no es el responsable de la inscripción.

        Returns each created entity as the canonical `ParticipanteOut` (incl.
        `persona`, `acepto_*`, `notas`) so the frontend can append them to its
        TanStack Query cache without a full refetch. Array stays homogeneous
        with `InscripcionDetalleOut.equipos[].participantes[]`.
        """
        _get_authenticated_persona_id(request)  # Verify user has persona

        # Verify inscription exists and belongs to the authenticated user
        from asgiref.sync import sync_to_async
        _obtener = sync_to_async(self.selector.obtener_inscripcion)
        inscripcion = await _obtener(inscripcion_id)
        if not inscripcion:
            raise NotFoundError(f"Inscripción {inscripcion_id} no encontrada.")
        if str(inscripcion.responsable_id) != _get_authenticated_persona_id(request):
            raise BusinessError("No tienes permiso para modificar esta inscripción.")

        # Build participantes_data list from payload
        participantes_data = [
            {
                **{k: v for k, v in {
                    "persona_id": p.persona_id,
                    "tipoDocumento": p.tipoDocumento,
                    "numeroDocumento": p.numeroDocumento,
                    "nombres": p.nombres,
                    "apellidos": p.apellidos,
                    "genero": p.genero,
                    "telefono": p.telefono,
                    "whatsapp": p.whatsapp,
                    "aseguradora_nombre": p.aseguradora_nombre,
                    "aseguradora_numero_poliza": p.aseguradora_numero_poliza,
                    "notas": p.notas,
                    "acepto_bases": p.acepto_bases,
                    "acepto_aptitud_fisica": p.acepto_aptitud_fisica,
                    "acepto_imagen": p.acepto_imagen,
                }.items() if v is not None},
                "rol": p.rol,
                "talle_camiseta": p.talle_camiseta,
            }
            for p in payload.participantes
        ]

        # Capture the created entities (orchestrator already returns them).
        created = await self.orchestrator.agregar_participantes_a_equipo(
            inscripcion_id=inscripcion_id,
            equipo_id=equipo_id,
            participantes_data=participantes_data,
        )

        # Map every created ParticipanteInscripcion through the canonical
        # presenter so the array shape is IDENTICAL to InscripcionDetalleOut.
        def _build_response():
            return [
                _present_participante_full(p) for p in created
            ]

        participantes_out = await sync_to_async(_build_response)()
        return success_response(
            AgregarParticipantesOut(participantes=participantes_out),
            message=f"{len(payload.participantes)} participante(s) agregado(s) correctamente.",
        )

    @route.patch("/{inscripcion_id}/participantes/{participante_id}", response={200: ApiResponse[ParticipanteOut]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def editar_participante(
        self,
        request,
        inscripcion_id: str,
        participante_id: str,
        payload: ParticipanteEditIn,
    ):
        """
        Editar un participante: rol, talle_camiseta, aseguradora y notas.

        Route: PATCH /api/inscripciones/{inscripcion_id}/participantes/{participante_id}
        Auth: JWT required. La inscripción debe pertenecer al usuario autenticado.
        Errors: NotFoundError si la inscripción no existe,
                BusinessError si el usuario no es el responsable.
        """
        from asgiref.sync import sync_to_async

        responsable_id = _get_authenticated_persona_id(request)

        # Verify inscription ownership
        _obtener = sync_to_async(self.selector.obtener_inscripcion)
        inscripcion = await _obtener(inscripcion_id)
        if not inscripcion:
            raise NotFoundError(f"Inscripción {inscripcion_id} no encontrada.")
        if str(inscripcion.responsable_id) != responsable_id:
            raise BusinessError("No tienes permiso para modificar esta inscripción.")

        participante = await self.orchestrator.editar_participante(
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
            rol=payload.rol,
            talle_camiseta=payload.talle_camiseta,
            aseguradora_nombre=payload.aseguradora_nombre,
            aseguradora_numero_poliza=payload.aseguradora_numero_poliza,
            notas=payload.notas,
        )

        # Build response with the canonical presenter (incl. persona + acepto_*).
        response_data = await sync_to_async(_present_participante_full)(participante)
        return success_response(
            response_data,
            message="Participante actualizado correctamente.",
        )

    @route.delete("/{inscripcion_id}/participantes/{participante_id}", response={200: ApiResponse[dict]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def remover_participante(
        self,
        request,
        inscripcion_id: str,
        participante_id: str,
    ):
        """
        Remover un participante del equipo dentro de una inscripción.

        Route: DELETE /api/inscripciones/{inscripcion_id}/participantes/{participante_id}
        Auth: JWT required. La inscripción debe pertenecer al usuario autenticado.
        Errors: NotFoundError si la inscripción no existe,
                BusinessError si el usuario no es el responsable.
        """
        from asgiref.sync import sync_to_async

        responsable_id = _get_authenticated_persona_id(request)

        # Verify inscription ownership
        _obtener = sync_to_async(self.selector.obtener_inscripcion)
        inscripcion = await _obtener(inscripcion_id)
        if not inscripcion:
            raise NotFoundError(f"Inscripción {inscripcion_id} no encontrada.")
        if str(inscripcion.responsable_id) != responsable_id:
            raise BusinessError("No tienes permiso para modificar esta inscripción.")

        await self.orchestrator.remover_participante(
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
        )
        return success_response(
            {"participante_id": participante_id},
            message="Participante removido correctamente.",
        )

    @route.patch("/{inscripcion_id}/participantes/{participante_id}/mover", response={200: ApiResponse[ParticipanteOut]}, auth=JWTAuth(), permissions=[IsAuthenticated])
    async def mover_participante(
        self,
        request,
        inscripcion_id: str,
        participante_id: str,
        payload: ParticipanteMoveIn,
    ):
        """
        Mover un participante a otro equipo dentro de la misma inscripción.

        Route: PATCH /api/inscripciones/{inscripcion_id}/participantes/{participante_id}/mover
        Auth: JWT required. La inscripción debe pertenecer al usuario autenticado.
              - Misma disciplina: actualiza equipo_id de la ParticipanteInscripcion.
              - Disciplina distinta: crea nueva ParticipacionDisciplina y actualiza el link.
        Errors: NotFoundError si la inscripción no existe,
                BusinessError si el usuario no es el responsable.
        """
        from asgiref.sync import sync_to_async

        responsable_id = _get_authenticated_persona_id(request)

        # Verify inscription ownership
        _obtener = sync_to_async(self.selector.obtener_inscripcion)
        inscripcion = await _obtener(inscripcion_id)
        if not inscripcion:
            raise NotFoundError(f"Inscripción {inscripcion_id} no encontrada.")
        if str(inscripcion.responsable_id) != responsable_id:
            raise BusinessError("No tienes permiso para modificar esta inscripción.")

        participante = await self.orchestrator.mover_participante(
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
            equipo_destino_id=payload.equipo_destino_id,
        )
        return success_response(
            _present_participante_full(participante),
            message="Participante movido correctamente.",
        )
