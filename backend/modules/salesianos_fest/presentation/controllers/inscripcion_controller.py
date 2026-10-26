"""
InscripcionController — HTTP endpoints for inscripcion, equipo and participacion.

Scope: Fase 3 sports registration (inscripcion, equipo, roster, participacion).
PROHIBIDO: compra, orden, Izipay, cupos, acreditación, QR, consentimiento,
PAGADA state, dict HTTP, flat Router.
"""
from ninja_extra import api_controller, route
from ninja_extra.permissions import IsAuthenticated
from injector import inject

from core.responses import ApiResponse, success_response
from core.security import JWTAuth
from modules.salesianos_fest.domain.services.orchestrators.inscripcion_orchestrator import (
    InscripcionOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.equipo_orchestrator import (
    EquipoOrchestrator,
)
from modules.salesianos_fest.domain.services.orchestrators.participacion_orchestrator import (
    ParticipacionOrchestrator,
)
from modules.salesianos_fest.presentation.schemas.inscripcion_schemas import (
    CrearInscripcionIn,
    CrearInscripcionCompletaIn,
    InscripcionCompletaOut,
    InscripcionOut,
    InscripcionDetailOut,
    ActualizarInscripcionIn,
    CrearEquipoIn,
    EquipoOut,
    AgregarPersonaIn,
    InscripcionPersonaOut,
    CrearParticipacionIn,
    ParticipacionOut,
    ActualizarParticipacionIn,
    MoverParticipacionIn,
    PoolOut,
    AsignarAEquipoIn,
    ElegiblesEquipoOut,
)
from modules.salesianos_fest.presentation.presenters.inscripcion_presenter import InscripcionPresenter
from modules.salesianos_fest.presentation.ownership import (
    check_ownership_or_admin,
    check_ownership_or_admin_for_equipo,
    check_ownership_or_admin_for_participacion,
)
from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
    InscripcionCreateData,
    InscripcionCompletaCreateData,
    EquipoCreateData,
    EquipoCreateSinInscripcionData,
    InscripcionPersonaCreateData,
    ParticipacionCreateData,
    ParticipacionUpdateData,
)


def _get_authenticated_persona_id(request) -> str:
    """Extract persona_id from the authenticated request (request.user.persona_fk_id)."""
    user = request.user
    persona_id = getattr(user, "persona_fk_id", None)
    if not persona_id:
        from core.exceptions import BusinessError
        raise BusinessError("Usuario sin persona vinculada. Complete su registro.")
    return str(persona_id)


@api_controller("/inscripciones", tags=["Inscripciones FEST"], permissions=[IsAuthenticated])
class InscripcionController:
    """Endpoints for sports inscription — no commercial rights."""

    @inject
    def __init__(self, inscripcion_orch: InscripcionOrchestrator):
        self._orch = inscripcion_orch

    @route.post("/", response={201: ApiResponse[InscripcionOut]}, auth=JWTAuth())
    async def crear_inscripcion(self, request, payload: CrearInscripcionIn):
        """
        Crear una nueva inscripción deportiva.

        Route: POST /api/inscripciones/
        Auth: JWT required. responsable_id is derived server-side from authenticated user.
        Returns: Inscripción creada.
        """
        responsable_id = _get_authenticated_persona_id(request)
        data = InscripcionCreateData(
            evento_id=payload.evento_id,
            responsable_id=responsable_id,
            paquete_id=payload.paquete_id,
            promocion_id=payload.promocion_id,
            fusion_promocion_id=payload.fusion_promocion_id,
            delegado_id=payload.delegado_id,
            estado=payload.estado,
            observacion=payload.observacion,
        )
        result = await self._orch.crear_inscripcion_proceso(data)
        return success_response(
            InscripcionPresenter.present_inscripcion(result),
            message="La inscripción se registró correctamente.",
        )

    @route.post("/completa/", response={201: ApiResponse[InscripcionCompletaOut]}, auth=JWTAuth())
    async def crear_inscripcion_completa(self, request, payload: CrearInscripcionCompletaIn):
        """
        Crear atómicamente una inscripción con compra inicial y equipos.

        Route: POST /api/inscripciones/completa/
        Auth: JWT required. responsable_id derived server-side from authenticated user.
        Creates: Inscripcion (BORRADOR) + Compra (INICIAL, PENDIENTE) + Equipos + OrdenPago.
        cantidad must be >= paquete.minimo_compra_inicial.
        Participant roster is NOT created at this stage.
        """
        responsable_id = _get_authenticated_persona_id(request)
        data = InscripcionCompletaCreateData(
            evento_id=payload.evento_id,
            paquete_id=payload.paquete_id,
            promocion_id=payload.promocion_id,
            fusion_promocion_id=payload.fusion_promocion_id,
            delegado_id=payload.delegado_id,
            cantidad=payload.cantidad,
            equipos=[
                EquipoCreateSinInscripcionData(
                    disciplina_id=eq.disciplina_id,
                    categoria_id=eq.categoria_id,
                    nombre=eq.nombre,
                    estado=eq.estado,
                )
                for eq in payload.equipos
            ],
            estado=payload.estado,
            observacion=payload.observacion,
            precio_unitario_cotizado=payload.precio_unitario_cotizado,
            cotizacion_version=payload.cotizacion_version,
        )
        result = await self._orch.crear_inscripcion_completa_proceso(data, responsable_id)
        return success_response(
            InscripcionCompletaOut(
                inscripcion_id=result.inscripcion_id,
                inscripcion_estado=result.inscripcion_estado,
                compra_id=result.compra_id,
                orden_pago_id=result.orden_pago_id,
                compra_estado=result.compra_estado,
                cantidad=result.cantidad,
                precio_unitario=result.precio_unitario,
                total=result.total,
                equipos=[
                    InscripcionPresenter.present_equipo(eq) for eq in result.equipos
                ],
            ),
            message="La inscripción con compra inicial se registró correctamente.",
        )

    @route.get("/", response={200: ApiResponse[list[InscripcionOut]]}, auth=JWTAuth())
    async def listar_mis_inscripciones(self, request):
        """
        Listar las inscripciones del usuario autenticado.

        Route: GET /api/inscripciones/
        Auth: JWT required.
        Returns: Lista de inscripciones del responsable.
        """
        responsable_id = _get_authenticated_persona_id(request)
        results = await self._orch.listar_por_responsable_proceso(responsable_id)
        return success_response(
            [InscripcionPresenter.present_inscripcion(r) for r in results],
            message="Inscripciones encontradas.",
        )

    @route.get("/{inscripcion_id}", response={200: ApiResponse[InscripcionOut]}, auth=JWTAuth())
    async def obtener_inscripcion(self, request, inscripcion_id: str):
        """
        Obtener detalle de una inscripción.

        Route: GET /api/inscripciones/{id}
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).
        Returns: Datos de la inscripción.
        """
        await check_ownership_or_admin(request, inscripcion_id)
        result = await self._orch.obtener_inscripcion_proceso(inscripcion_id)
        if result is None:
            from modules.salesianos_fest.domain.exceptions import InscripcionNotFoundError
            raise InscripcionNotFoundError()
        return success_response(
            InscripcionPresenter.present_inscripcion(result),
            message="Inscripción obtenida correctamente.",
        )

    @route.get("/{inscripcion_id}/detalle", response={200: ApiResponse[InscripcionDetailOut]}, auth=JWTAuth())
    async def obtener_inscripcion_detalle(self, request, inscripcion_id: str):
        """
        Obtener inscripción con equipos y personas (roster).

        Route: GET /api/inscripciones/{id}/detalle
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).
        Returns: Detalle completo con equipos y roster.
        """
        await check_ownership_or_admin(request, inscripcion_id)
        result = await self._orch.obtener_inscripcion_detalle_proceso(inscripcion_id)
        if result is None:
            from modules.salesianos_fest.domain.exceptions import InscripcionNotFoundError
            raise InscripcionNotFoundError()
        return success_response(
            InscripcionPresenter.present_inscripcion_detail(result),
            message="Detalle de inscripción obtenido correctamente.",
        )

    @route.patch("/{inscripcion_id}", response={200: ApiResponse[InscripcionOut]}, auth=JWTAuth())
    async def actualizar_inscripcion(self, request, inscripcion_id: str, payload: ActualizarInscripcionIn):
        """
        Actualizar estado u observación de una inscripción.

        Route: PATCH /api/inscripciones/{id}
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser). La denegación no muta nada.
        Returns: Inscripción actualizada.
        """
        await check_ownership_or_admin(request, inscripcion_id)

        from modules.salesianos_fest.domain.schemas.inscripcion_schemas import InscripcionUpdateData

        result = await self._orch.actualizar_inscripcion_proceso(
            inscripcion_id,
            InscripcionUpdateData(
                estado=payload.estado,
                observacion=payload.observacion,
                delegado_id=payload.delegado_id,
            ),
        )
        return success_response(
            InscripcionPresenter.present_inscripcion(result),
            message="Inscripción actualizada correctamente.",
        )

    @route.post("/{inscripcion_id}/personas", response={201: ApiResponse}, auth=JWTAuth())
    async def agregar_persona(self, request, inscripcion_id: str, payload: AgregarPersonaIn):
        """Add a person to an inscription roster with optional consent acceptances.

        Accepts either `persona_id` (existing persona lookup) or `persona_data`
        (inline upsert by documento — server reuses the existing Persona if the
        document matches, otherwise creates a new one). Exactly one must be sent;
        the InscripcionPersonaCreateData schema enforces XOR and raises
        `PersonaDataRequiredError` (422, `PERSONA_REQUIRED`) otherwise.

        POOL FIRST — this endpoint is the preregistration:
        without `equipo_id` it creates only the `InscripcionPersona` (the person
        waits in the pool), applies the contracted-capacity gate and claims the
        paid cup automatically when the inscription still has free paid
        capacity. It returns InscripcionPersonaOut wrapped as
        {participante: InscripcionPersonaOut}.

        With `equipo_id` it places an ALREADY registered participant in the team
        atomically and returns ParticipacionOut wrapped as
        {participante: ParticipacionOut}. A NEW person (`persona_data`) combined
        with `equipo_id` is rejected with 422
        `PARTICIPANTE_DEBE_PREREGISTRARSE`: the pool is the only entry point of
        the participant lifecycle.

        Authorization: responsible of the inscripcion OR Django admin (is_staff/is_superuser).
        """
        from modules.salesianos_fest.domain.results.inscripcion_results import ParticipacionResult
        from modules.salesianos_fest.domain.schemas.inscripcion_schemas import (
            InscripcionPersonaCreateData,
            PersonaInlineData,
        )

        # Roster mutation — restricted to the responsible of the inscripcion or
        # a Django admin. Same rule as every other participant mutation.
        await check_ownership_or_admin(request, inscripcion_id)

        # Construir DTO tipado para cruzar la frontera HTTP → dominio.
        # La validación XOR (persona_id XOR persona_data) la hace el schema.
        # Convertir PersonaInlineIn (HTTP) → PersonaInlineData (domain) explícitamente:
        # son schemas distintos (uno en presentation, otro en domain) con los mismos
        # campos. Pydantic 2 no autoconvierte entre tipos de modelos distintos.
        persona_data_domain: PersonaInlineData | None = None
        if payload.persona_data is not None:
            pd = payload.persona_data
            persona_data_domain = PersonaInlineData(
                tipo_documento=pd.tipo_documento,
                numero_documento=pd.numero_documento,
                nombres=pd.nombres,
                apellidos=pd.apellidos,
                genero=pd.genero,
                telefono=pd.telefono,
                whatsapp=pd.whatsapp,
            )
        create_data = InscripcionPersonaCreateData(
            inscripcion_id=inscripcion_id,
            persona_id=payload.persona_id,
            persona_data=persona_data_domain,
            equipo_id=payload.equipo_id,
            aceptaciones=payload.aceptaciones,
        )
        result = await self._orch.agregar_persona_proceso(create_data)
        if isinstance(result, ParticipacionResult):
            participacion_out = InscripcionPresenter.present_participacion(result)
            return success_response(
                {"participante": participacion_out},
                message="La persona se agregó al equipo correctamente.",
            )
        inscripcion_persona_out = InscripcionPresenter.present_inscripcion_persona(result)
        return success_response(
            {"participante": inscripcion_persona_out},
            message="La persona se agregó correctamente.",
        )

    @route.patch("/{inscripcion_id}/personas/{persona_id}/retirar", response={200: ApiResponse[InscripcionPersonaOut]}, auth=JWTAuth())
    async def retirar_persona(self, request, inscripcion_id: str, persona_id: str):
        """Retire a roster member and their active participations.

        Authorization: responsible of the inscripcion OR Django admin (is_staff/is_superuser).
        """
        await check_ownership_or_admin(request, inscripcion_id)
        persona = await self._orch.retirar_persona_proceso(inscripcion_id, persona_id)
        return success_response(
            InscripcionPresenter.present_inscripcion_persona(persona),
            message="La persona se retiró correctamente.",
        )

    @route.get("/{inscripcion_id}/pool", response={200: ApiResponse[PoolOut]}, auth=JWTAuth())
    async def obtener_pool(self, request, inscripcion_id: str):
        """Get the participant pool for an inscripcion.

        Returns pre-registered participants (InscripcionPersona without active Participacion)
        with their cup eligibility and a UI-safe blocked reason.

        Authorization: responsible of the inscripcion OR Django admin (is_staff/is_superuser).

        Route: GET /api/inscripciones/{id}/pool
        """
        await check_ownership_or_admin(request, inscripcion_id)
        pool_results = await self._orch.obtener_pool_proceso(inscripcion_id)
        pool_entries = InscripcionPresenter.present_pool(pool_results)
        return success_response(
            PoolOut(inscripcion_id=inscripcion_id, pool=pool_entries),
            message="Pool de participantes obtenido correctamente.",
        )

    @route.get(
        "/{inscripcion_id}/equipos/{equipo_id}/elegibles",
        response={200: ApiResponse[ElegiblesEquipoOut]},
        auth=JWTAuth(),
    )
    async def obtener_elegibles_equipo(
        self, request, inscripcion_id: str, equipo_id: str
    ):
        """Get the participant-selector candidates of one team.

        Team-scoped read used by the selector modal. For every active
        participant of the inscripcion it reports the paid-cup eligibility, the
        disciplines where the person already plays and the verdict for THIS
        team (`asignable` + `motivo_no_asignable`).

        One paid cup authorises the person in every contracted discipline, so a
        person that already plays in another discipline is still a candidate
        here; R11 only forbids playing twice in the SAME discipline.

        Authorization: responsible of the inscripcion OR Django admin (is_staff/is_superuser).

        Route: GET /api/inscripciones/{id}/equipos/{equipo_id}/elegibles
        """
        await check_ownership_or_admin(request, inscripcion_id)
        result = await self._orch.obtener_elegibles_equipo_proceso(
            inscripcion_id=inscripcion_id,
            equipo_id=equipo_id,
        )
        return success_response(
            InscripcionPresenter.present_elegibles_equipo(result),
            message="Participantes elegibles obtenidos correctamente.",
        )

    @route.post("/{inscripcion_id}/pool/asignar", response={200: ApiResponse}, auth=JWTAuth())
    async def asignar_a_equipo(self, request, inscripcion_id: str, payload: AsignarAEquipoIn):
        """Atomic assignment of a participant to an equipo (sole assignment authority).

        Enforces Phase 2 gates: cup, R11, roster, deadline.
        Only the responsible of the inscripcion or a Django admin can call this.

        One paid cup authorises the person in every contracted discipline: this
        endpoint creates one Participacion per (person, discipline), and R11
        rejects a second participation in the SAME discipline.

        Route: POST /api/inscripciones/{id}/pool/asignar
        """
        await check_ownership_or_admin(request, inscripcion_id)
        result = await self._orch.asignar_a_equipo_proceso(
            inscripcion_id=inscripcion_id,
            inscripcion_persona_id=payload.inscripcion_persona_id,
            equipo_id=payload.equipo_id,
            rol=payload.rol,
            talla_camiseta=payload.talla_camiseta,
            notas=payload.notas,
        )
        participacion_out = InscripcionPresenter.present_participacion(result)
        return success_response(
            {"participante": participacion_out},
            message="La persona se agregó al equipo correctamente.",
        )

@api_controller("/equipos", tags=["Equipos FEST"], permissions=[IsAuthenticated])
class EquipoController:
    """Endpoints for equipo management."""

    @inject
    def __init__(self, equipo_orch: EquipoOrchestrator):
        self._orch = equipo_orch

    @route.post("/", response={201: ApiResponse[EquipoOut]}, auth=JWTAuth())
    async def crear_equipo(self, request, payload: CrearEquipoIn):
        """
        Crear un equipo dentro de una inscripción.

        Route: POST /api/equipos/
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser). La denegación no crea ningún equipo.
        Returns: Equipo creado.
        """
        await check_ownership_or_admin(request, str(payload.inscripcion_id))

        data = EquipoCreateData(
            inscripcion_id=payload.inscripcion_id,
            disciplina_id=payload.disciplina_id,
            categoria_id=payload.categoria_id,
            nombre=payload.nombre,
            estado=payload.estado,
        )
        result = await self._orch.crear_equipo_proceso(data)
        return success_response(
            InscripcionPresenter.present_equipo(result),
            message="Equipo creado correctamente.",
        )

    @route.get("/{equipo_id}", response={200: ApiResponse[EquipoOut]}, auth=JWTAuth())
    async def obtener_equipo(self, request, equipo_id: str):
        """
        Obtener un equipo por ID.

        Route: GET /api/equipos/{id}
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).
        Returns: Datos del equipo.
        """
        await check_ownership_or_admin_for_equipo(request, equipo_id)
        result = await self._orch.obtener_equipo_proceso(equipo_id)
        if result is None:
            from modules.salesianos_fest.domain.exceptions import EquipoNotFoundError
            raise EquipoNotFoundError()
        return success_response(
            InscripcionPresenter.present_equipo(result),
            message="Equipo obtenido correctamente.",
        )

    @route.get("/inscripcion/{inscripcion_id}", response={200: ApiResponse[list[EquipoOut]]}, auth=JWTAuth())
    async def listar_por_inscripcion(self, request, inscripcion_id: str):
        """
        Listar equipos de una inscripción.

        Route: GET /api/equipos/inscripcion/{inscripcion_id}
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).
        Returns: Lista de equipos.
        """
        await check_ownership_or_admin(request, inscripcion_id)
        results = await self._orch.listar_por_inscripcion_proceso(inscripcion_id)
        return success_response(
            InscripcionPresenter.present_equipos(results),
            message="Equipos listados correctamente.",
        )


@api_controller("/participaciones", tags=["Participaciones FEST"], permissions=[IsAuthenticated])
class ParticipacionController:
    """Endpoints for participacion (roster entry) management."""

    @inject
    def __init__(self, participacion_orch: ParticipacionOrchestrator):
        self._orch = participacion_orch

    async def _check_participacion_ownership(self, request, participacion_id: str) -> None:
        """Check if the authenticated user can mutate this participacion.

        Allowed: responsible of the parent inscripcion OR Django admin.
        """
        from core.exceptions import ForbiddenError

        user = request.user
        if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
            return

        persona_id = getattr(user, "persona_fk_id", None)
        if not persona_id:
            raise ForbiddenError()

        # Use sync_to_async since we are in an async controller
        from asgiref.sync import sync_to_async

        def _check():
            from modules.salesianos_fest.domain.models import Participacion
            try:
                p = Participacion.objects.select_related(
                    "inscripcion_persona__inscripcion"
                ).only("inscripcion_persona__inscripcion__responsable_id").get(id=participacion_id)
            except Participacion.DoesNotExist:
                return  # Let the endpoint handle it
            if str(p.inscripcion_persona.inscripcion.responsable_id) != str(persona_id):
                raise ForbiddenError()

        await sync_to_async(_check, thread_sensitive=True)()

    @route.post("/", response={201: ApiResponse[ParticipacionOut]}, auth=JWTAuth())
    async def crear_participacion(self, request, payload: CrearParticipacionIn):
        """
        Crear una participación (registrar persona en equipo).

        Aplica R11 y validación de roster máximo.
        Authorization: responsible of the inscripcion OR Django admin.

        Route: POST /api/participaciones/
        Returns: Participación creada.
        """
        # Find the inscripcion for auth check - use sync_to_async
        from asgiref.sync import sync_to_async

        def _get_inscripcion_id_sync():
            from modules.salesianos_fest.domain.models import InscripcionPersona
            try:
                ip = InscripcionPersona.objects.only("inscripcion_id").get(id=payload.inscripcion_persona_id)
                return str(ip.inscripcion_id)
            except InscripcionPersona.DoesNotExist:
                from modules.salesianos_fest.domain.exceptions import InscripcionNotFoundError
                raise InscripcionNotFoundError()

        inscripcion_id = await sync_to_async(_get_inscripcion_id_sync, thread_sensitive=True)()
        await check_ownership_or_admin(request, inscripcion_id)

        data = ParticipacionCreateData(
            inscripcion_persona_id=payload.inscripcion_persona_id,
            equipo_id=payload.equipo_id,
            rol=payload.rol,
            talla_camiseta=payload.talla_camiseta,
            notas=payload.notas,
        )
        result = await self._orch.crear_participacion_proceso(data)
        return success_response(
            InscripcionPresenter.present_participacion(result),
            message="Participación registrada correctamente.",
        )

    @route.get("/{participacion_id}", response={200: ApiResponse[ParticipacionOut]}, auth=JWTAuth())
    async def obtener_participacion(self, request, participacion_id: str):
        """
        Obtener una participación por ID.

        Route: GET /api/participaciones/{id}
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).
        Returns: Datos de la participación.
        """
        await check_ownership_or_admin_for_participacion(request, participacion_id)
        result = await self._orch.obter_participacion_proceso(participacion_id)
        if result is None:
            from modules.salesianos_fest.domain.exceptions import ParticipacionNotFoundError
            raise ParticipacionNotFoundError()
        return success_response(
            InscripcionPresenter.present_participacion(result),
            message="Participación obtenida correctamente.",
        )

    @route.get("/equipo/{equipo_id}", response={200: ApiResponse[list[ParticipacionOut]]}, auth=JWTAuth())
    async def listar_por_equipo(self, request, equipo_id: str):
        """
        Listar participantes de un equipo (roster).

        Route: GET /api/participaciones/equipo/{equipo_id}
        Auth: JWT required.
        Authorization: responsable of the inscripcion OR Django admin
        (is_staff/is_superuser).
        Returns: Lista de participantes.
        """
        await check_ownership_or_admin_for_equipo(request, equipo_id)
        results = await self._orch.listar_por_equipo_proceso(equipo_id)
        return success_response(
            InscripcionPresenter.present_participaciones(results),
            message="Participaciones listadas correctamente.",
        )

    @route.patch("/{participacion_id}/retirar", response={200: ApiResponse[ParticipacionOut]}, auth=JWTAuth())
    async def retirar_participacion(self, request, participacion_id: str):
        """
        Retirar una participación (estado -> R).

        Authorization: responsible of the inscripcion OR Django admin.

        Route: PATCH /api/participaciones/{id}/retirar
        Returns: Participación retirada.
        """
        await self._check_participacion_ownership(request, participacion_id)
        result = await self._orch.retirer_participacion_proceso(participacion_id)
        return success_response(
            InscripcionPresenter.present_participacion(result),
            message="Participación retirada correctamente.",
        )

    @route.patch("/{participacion_id}/mover", response={200: ApiResponse[ParticipacionOut]}, auth=JWTAuth())
    async def mover_participacion(
        self, request, participacion_id: str, payload: MoverParticipacionIn
    ):
        """
        Mover una participación a otro equipo.

        Authorization: responsible of the inscripcion OR Django admin.

        Route: PATCH /api/participaciones/{id}/mover
        Returns: Participación con nuevo equipo.
        """
        await self._check_participacion_ownership(request, participacion_id)
        result = await self._orch.mover_participacion_proceso(
            participacion_id, payload.equipo_destino_id
        )
        return success_response(
            InscripcionPresenter.present_participacion(result),
            message="Participación movida correctamente.",
        )

    @route.patch("/{participacion_id}", response={200: ApiResponse[ParticipacionOut]}, auth=JWTAuth())
    async def actualizar_participacion(
        self, request, participacion_id: str, payload: ActualizarParticipacionIn
    ):
        """
        Actualizar una participación (rol, talla_camiseta, notas, estado).

        Authorization: responsible of the inscripcion OR Django admin.

        Route: PATCH /api/participaciones/{id}
        Returns: Participación actualizada.
        """
        await self._check_participacion_ownership(request, participacion_id)
        data = ParticipacionUpdateData(
            rol=payload.rol,
            talla_camiseta=payload.talla_camiseta,
            notas=payload.notas,
            estado=payload.estado,
        )
        result = await self._orch.actualizar_participacion_proceso(participacion_id, data)
        return success_response(
            InscripcionPresenter.present_participacion(result),
            message="Participación actualizada correctamente.",
        )
