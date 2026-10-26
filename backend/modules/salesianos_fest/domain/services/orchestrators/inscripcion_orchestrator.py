"""InscripcionOrchestrator — thin async facade for inscripcion operations."""
from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from ..flujos.crear_inscripcion_flujo import CrearInscripcionFlujo
from ..flujos.crear_inscripcion_completa_flujo import CrearInscripcionCompletaFlujo
from ..flujos.agregar_persona_flujo import AgregarPersonaFlujo
from ..flujos.retirar_persona_flujo import RetirarPersonaFlujo
from ..core.inscripcion_service import InscripcionCoreService
from ..core.equipo_service import EquipoCoreService
from ..core.acreditacion_service import AcreditacionCoreService
from modules.pagos.domain.services.core.izipay_core_service import IzipayCoreService
from ...selectors.inscripcion_selector import InscripcionSelector
from ...selectors.equipo_selector import EquipoSelector
from ...results.inscripcion_results import (
    InscripcionResult,
    InscripcionDetailResult,
    InscripcionPersonaResult,
    ParticipacionResult,
    InscripcionCompletaResult,
    PoolEntryResult,
    ElegiblesEquipoResult,
)


class InscripcionOrchestrator:
    """Thin async orchestrator — delegates to flujos, no business logic."""

    @inject
    def __init__(
        self,
        inscripcion_core: InscripcionCoreService,
        acreditacion_core: AcreditacionCoreService,
        equipo_core: EquipoCoreService,
        izipay_core: IzipayCoreService,
    ):
        self._inscripcion_core = inscripcion_core
        self._acreditacion_core = acreditacion_core
        self._crear_flujo = CrearInscripcionFlujo(inscripcion_core)
        self._crear_completa_flujo = CrearInscripcionCompletaFlujo(
            inscripcion_core=inscripcion_core,
            equipo_core=equipo_core,
            izipay_core=izipay_core,
        )
        self._agregar_persona_flujo = AgregarPersonaFlujo()
        self._retirar_persona_flujo = RetirarPersonaFlujo(acreditacion_core=acreditacion_core)

    async def crear_inscripcion_proceso(
        self, data,
    ) -> InscripcionResult:
        """Create a new inscripcion."""
        return await self._crear_flujo.ejecutar(data)

    async def crear_inscripcion_completa_proceso(
        self, data, responsable_id: str,
    ) -> InscripcionCompletaResult:
        """Create atomically: inscripcion + compra + equipos."""
        return await self._crear_completa_flujo.ejecutar(data, responsable_id)

    async def actualizar_inscripcion_proceso(self, inscripcion_id: str, data) -> InscripcionResult:
        """Update administrative inscription data atomically."""
        return await sync_to_async(self._actualizar_inscripcion_atomico)(inscripcion_id, data)

    def _actualizar_inscripcion_atomico(self, inscripcion_id: str, data) -> InscripcionResult:
        from django.db import transaction

        with transaction.atomic():
            inscripcion = self._inscripcion_core.obtener_por_id(inscripcion_id)
            inscripcion = self._inscripcion_core.actualizar(inscripcion, data)
            return InscripcionResult(
                id=str(inscripcion.id),
                evento_id=str(inscripcion.evento_id),
                evento_nombre=inscripcion.evento.nombre,
                responsable_id=str(inscripcion.responsable_id),
                responsable_nombre=f"{inscripcion.responsable.nombres} {inscripcion.responsable.apellidos}",
                paquete_id=str(inscripcion.paquete_id),
                paquete_nombre=inscripcion.paquete.nombre,
                promocion_id=str(inscripcion.promocion_id),
                promocion_nombre=inscripcion.promocion.nombre,
                fusion_promocion_id=str(inscripcion.fusion_promocion_id) if inscripcion.fusion_promocion_id else None,
                delegado_id=str(inscripcion.delegado_id) if inscripcion.delegado_id else None,
                estado=inscripcion.estado,
                observacion=inscripcion.observacion,
                created_at=inscripcion.created_at,
            )

    async def obtener_inscripcion_proceso(
        self, inscripcion_id: str,
    ) -> InscripcionResult | None:
        """Get inscripcion by ID."""
        return await sync_to_async(InscripcionSelector.get_by_id)(inscripcion_id)

    async def obtener_inscripcion_detalle_proceso(
        self, inscripcion_id: str,
    ) -> InscripcionDetailResult | None:
        """Get inscripcion with equipos and personas."""
        return await sync_to_async(InscripcionSelector.get_by_id_with_details)(inscripcion_id)

    async def agregar_persona_proceso(
        self,
        data,
    ) -> InscripcionPersonaResult | ParticipacionResult:
        """Add a persona to an inscripcion with optional aceptaciones and optional Participacion creation.

        Receives a typed `InscripcionPersonaCreateData` (NOT a dict).
        The controller is responsible for mapping the HTTP payload into
        this domain DTO before calling this method. XOR validation
        (persona_id XOR persona_data) is enforced by the schema.
        """
        from ...schemas.inscripcion_schemas import InscripcionPersonaCreateData

        if not isinstance(data, InscripcionPersonaCreateData):
            raise TypeError(
                f"agregar_persona_proceso requires InscripcionPersonaCreateData, "
                f"got {type(data).__name__}"
            )

        ip, participacion = await self._agregar_persona_flujo.ejecutar(data=data)
        if participacion is not None:
            return await sync_to_async(self._presentar_participacion)(participacion)
        return await sync_to_async(self._presentar_inscripcion_persona)(ip.id)

    @staticmethod
    def _presentar_participacion(participacion) -> ParticipacionResult:
        """Present a Participacion model as ParticipacionResult (sync)."""
        return ParticipacionResult(
            id=str(participacion.id),
            inscripcion_persona_id=str(participacion.inscripcion_persona_id),
            equipo_id=str(participacion.equipo_id),
            equipo_nombre=participacion.equipo.nombre,
            evento_id=str(participacion.evento_id),
            disciplina_id=str(participacion.disciplina_id),
            disciplina_nombre=participacion.disciplina.nombre,
            disciplina_sigla=participacion.disciplina.sigla,
            persona_id=str(participacion.persona_id),
            persona_nombre=f"{participacion.inscripcion_persona.persona.nombres} {participacion.inscripcion_persona.persona.apellidos}",
            persona_numero_documento=participacion.inscripcion_persona.persona.numero_documento,
            rol=participacion.rol,
            talla_camiseta=participacion.talla_camiseta,
            notas=participacion.notas,
            estado=participacion.estado,
            created_at=participacion.created_at,
        )

    async def retirar_persona_proceso(
        self, inscripcion_id: str, persona_id: str,
    ) -> InscripcionPersonaResult:
        """Retire a persona from an inscripcion (retires all active participaciones)."""
        persona = await self._retirar_persona_flujo.ejecutar(inscripcion_id, persona_id)
        return await sync_to_async(self._presentar_inscripcion_persona)(persona.id)

    @staticmethod
    def _presentar_inscripcion_persona(inscripcion_persona_id) -> InscripcionPersonaResult:
        from ...models import InscripcionPersona

        persona = InscripcionPersona.objects.select_related("persona").get(id=inscripcion_persona_id)
        return InscripcionPersonaResult(
            id=str(persona.id),
            inscripcion_id=str(persona.inscripcion_id),
            persona_id=str(persona.persona_id),
            persona_nombre=f"{persona.persona.nombres} {persona.persona.apellidos}",
            persona_numero_documento=persona.persona.numero_documento,
            estado=persona.estado,
            created_at=persona.created_at,
        )

    async def listar_por_evento_proceso(self, evento_id: str) -> list[InscripcionResult]:
        """List inscripciones by evento."""
        return await sync_to_async(InscripcionSelector.get_by_evento)(evento_id)

    async def listar_por_responsable_proceso(self, responsable_id: str) -> list[InscripcionResult]:
        """List inscripciones by responsable (authenticated user)."""
        return await sync_to_async(InscripcionSelector.get_by_responsable)(responsable_id)

    async def obtener_pool_proceso(self, inscripcion_id: str) -> list[PoolEntryResult]:
        """Get the participant pool for an inscripcion.

        Returns InscripcionPersona records without active Participacion.
        Each entry includes cup eligibility and a UI-safe blocked reason.
        """
        return await sync_to_async(InscripcionSelector.get_pool)(inscripcion_id)

    async def obtener_elegibles_equipo_proceso(
        self,
        inscripcion_id: str,
        equipo_id: str,
    ) -> ElegiblesEquipoResult:
        """Get the participant-selector candidates of ONE team.

        Team-scoped read: it reports, for every active participant of the
        inscripcion, the commercial eligibility, the disciplines where the
        person already plays and the verdict for this team (`asignable`).

        The selector owns the whole verdict — the UI never re-derives it.
        """
        return await sync_to_async(InscripcionSelector.get_elegibles_equipo)(
            inscripcion_id,
            equipo_id,
        )

    async def asignar_a_equipo_proceso(
        self,
        inscripcion_id: str,
        inscripcion_persona_id: str,
        equipo_id: str,
        rol: str,
        talla_camiseta: str,
        notas: str,
    ) -> ParticipacionResult:
        """Atomic assignment of a participant to an equipo (sole assignment authority).

        Validates that the InscripcionPersona belongs to the given inscripcion
        before deleging to ParticipacionOrchestrator (which enforces Phase 2
        gates: cup, R11, roster, deadline).

        Authorization (inscripcion ownership) is enforced at the controller layer
        before calling this method.
        """
        return await self._asignar_persona_a_equipo_atomico(
            inscripcion_id=inscripcion_id,
            inscripcion_persona_id=inscripcion_persona_id,
            equipo_id=equipo_id,
            rol=rol,
            talla_camiseta=talla_camiseta,
            notas=notas,
        )

    @sync_to_async
    def _asignar_persona_a_equipo_atomico(
        self,
        inscripcion_id: str,
        inscripcion_persona_id: str,
        equipo_id: str,
        rol: str,
        talla_camiseta: str,
        notas: str,
    ) -> ParticipacionResult:
        """Atomic assign an existing InscripcionPersona to an equipo.

        Uses the existing ParticipacionCoreService which enforces Phase 2 gates
        (cup, R11, roster) inside a transaction.
        """
        from ...models import InscripcionPersona
        from ...exceptions import InscripcionNotFoundError, ParticipanteRetiradoError
        from ...constants import EstadoInscripcionPersonaChoices
        from ...services.core.participacion_service import ParticipacionCoreService
        from ...schemas.inscripcion_schemas import ParticipacionCreateData

        # Validate InscripcionPersona belongs to this inscripcion
        try:
            ip = InscripcionPersona.objects.only("inscripcion_id", "estado").get(
                id=inscripcion_persona_id
            )
        except InscripcionPersona.DoesNotExist:
            raise InscripcionNotFoundError()

        if str(ip.inscripcion_id) != str(inscripcion_id):
            raise InscripcionNotFoundError()

        # A retired participant cannot be placed in a team again — the
        # preregistration must be restored first.
        if ip.estado != EstadoInscripcionPersonaChoices.ACTIVO:
            raise ParticipanteRetiradoError()

        with transaction.atomic():
            participacion_core = ParticipacionCoreService()
            data = ParticipacionCreateData(
                inscripcion_persona_id=inscripcion_persona_id,
                equipo_id=equipo_id,
                rol=rol,
                talla_camiseta=talla_camiseta,
                notas=notas,
            )
            p = participacion_core.crear(data)
            return ParticipacionResult(
                id=str(p.id),
                inscripcion_persona_id=str(p.inscripcion_persona_id),
                equipo_id=str(p.equipo_id),
                equipo_nombre=p.equipo.nombre,
                evento_id=str(p.evento_id),
                disciplina_id=str(p.disciplina_id),
                disciplina_nombre=p.disciplina.nombre,
                disciplina_sigla=p.disciplina.sigla,
                persona_id=str(p.persona_id),
                persona_nombre=f"{p.inscripcion_persona.persona.nombres} {p.inscripcion_persona.persona.apellidos}",
                persona_numero_documento=p.inscripcion_persona.persona.numero_documento,
                rol=p.rol,
                talla_camiseta=p.talla_camiseta,
                notas=p.notas,
                estado=p.estado,
                created_at=p.created_at,
            )
