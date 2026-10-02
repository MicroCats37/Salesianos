"""
InscripcionOrchestrator — async thin facade for inscription use cases.

Orchestrator — async thin facade that delegates to flujos.
No business logic here — only delegation.
"""

from injector import inject

from modules.inscripciones.domain.services.flujos.crear_inscripcion_flujo import CrearInscripcionFlujo
from modules.inscripciones.domain.services.flujos.agregar_participante_flujo import AgregarParticipanteFlujo
from modules.inscripciones.domain.services.flujos.agregar_participantes_flujo import AgregarParticipantesFlujo
from modules.inscripciones.domain.services.flujos.cambiar_estado_inscripcion_flujo import (
    CambiarEstadoInscripcionFlujo,
)
from modules.inscripciones.domain.services.flujos.asignar_delegado_flujo import AsignarDelegadoFlujo
from modules.inscripciones.domain.services.flujos.participante_accion_flujo import ParticipanteAccionFlujo


class InscripcionOrchestrator:
    """
    Thin async facade for inscription operations.

    All methods delegate to their respective flujos.
    """

    @inject
    def __init__(
        self,
        crear_flujo: CrearInscripcionFlujo,
        agregar_participante_flujo: AgregarParticipanteFlujo,
        agregar_participantes_flujo: AgregarParticipantesFlujo,
        cambiar_estado_flujo: CambiarEstadoInscripcionFlujo,
        asignar_delegado_flujo: AsignarDelegadoFlujo,
        participante_accion_flujo: ParticipanteAccionFlujo,
    ):
        self.crear_flujo = crear_flujo
        self.agregar_participante_flujo = agregar_participante_flujo
        self.agregar_participantes_flujo = agregar_participantes_flujo
        self.cambiar_estado_flujo = cambiar_estado_flujo
        self.asignar_delegado_flujo = asignar_delegado_flujo
        self.participante_accion_flujo = participante_accion_flujo

    # ── Inscripcion ──────────────────────────────────────────────────────────

    async def crear_inscripcion_completa(
        self,
        responsable_id: str,
        paquete_id: str,
        promocion_id: str,
        observacion: str | None,
        equipos_data: list[dict],
        fusion_promocion_id: str | None = None,
        accepted_bases: bool | None = None,
        fitness_declaration: bool | None = None,
        image_consent: bool | None = None,
    ):
        """
        Create a complete inscription with teams and participants.

        The active event is resolved internally by the flujo from
        `settings.EVENTO_ACTIVO_NOMBRE` — it is not an input parameter.

        See CrearInscripcionFlujo._crear_inscripcion_completa for params/docs.
        """
        return await self.crear_flujo._crear_inscripcion_completa(
            responsable_id=responsable_id,
            paquete_id=paquete_id,
            promocion_id=promocion_id,
            observacion=observacion,
            equipos_data=equipos_data,
            fusion_promocion_id=fusion_promocion_id,
            accepted_bases=accepted_bases,
            fitness_declaration=fitness_declaration,
            image_consent=image_consent,
        )

    async def cambiar_estado(
        self,
        inscripcion_id: str,
        nuevo_estado: str,
        observacion: str | None = None,
    ):
        """
        Change the state of an inscription.

        See CambiarEstadoInscripcionFlujo._cambiar_estado for params/docs.
        """
        return await self.cambiar_estado_flujo._cambiar_estado(
            inscripcion_id=inscripcion_id,
            nuevo_estado=nuevo_estado,
            observacion=observacion,
        )

    # ── Participante ────────────────────────────────────────────────────────

    async def agregar_participante(
        self,
        equipo_id: str,
        persona_id: str,
        rol: str = "JUGADOR",
        talle_camiseta: str | None = None,
        notas: str | None = None,
        acepto_bases: bool | None = None,
        acepto_aptitud_fisica: bool | None = None,
        acepto_imagen: bool | None = None,
    ):
        """
        Add a participant to an existing equipo.

        See AgregarParticipanteFlujo._agregar_participante for params/docs.
        """
        return await self.agregar_participante_flujo._agregar_participante(
            equipo_id=equipo_id,
            persona_id=persona_id,
            rol=rol,
            talle_camiseta=talle_camiseta,
            notas=notas,
            acepto_bases=acepto_bases,
            acepto_aptitud_fisica=acepto_aptitud_fisica,
            acepto_imagen=acepto_imagen,
        )

    async def agregar_participantes_a_equipo(
        self,
        inscripcion_id: str,
        equipo_id: str,
        participantes_data: list[dict],
    ):
        """
        Add multiple participants to an existing equipo.

        See AgregarParticipantesFlujo._agregar_participantes for params/docs.
        """
        return await self.agregar_participantes_flujo._agregar_participantes(
            inscripcion_id=inscripcion_id,
            equipo_id=equipo_id,
            participantes_data=participantes_data,
        )

    # ── Delegado ────────────────────────────────────────────────────────────

    async def asignar_delegado(self, inscripcion_id: str, persona_id: str):
        """
        Assign a delegate to an inscription.

        See AsignarDelegadoFlujo._asignar_delegado for params/docs.
        """
        return await self.asignar_delegado_flujo._asignar_delegado(
            inscripcion_id=inscripcion_id,
            persona_id=persona_id,
        )

    async def remover_delegado(self, inscripcion_id: str):
        """
        Remove the delegate from an inscription.

        See AsignarDelegadoFlujo._remover_delegado for params/docs.
        """
        return await self.asignar_delegado_flujo._remover_delegado(inscripcion_id)

    # ── Participante Actions ─────────────────────────────────────────────────

    async def editar_participante(
        self,
        inscripcion_id: str,
        participante_id: str,
        rol: str | None = None,
        talle_camiseta: str | None = None,
        aseguradora_nombre: str | None = None,
        aseguradora_numero_poliza: str | None = None,
        notas: str | None = None,
    ):
        """
        Edit a participant's rol, talle_camiseta, insurance, and/or notes.

        See ParticipanteAccionFlujo._editar_participante for params/docs.
        """
        return await self.participante_accion_flujo._editar_participante(
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
            rol=rol,
            talle_camiseta=talle_camiseta,
            aseguradora_nombre=aseguradora_nombre,
            aseguradora_numero_poliza=aseguradora_numero_poliza,
            notas=notas,
        )

    async def remover_participante(
        self,
        inscripcion_id: str,
        participante_id: str,
    ):
        """
        Remove a participant from a team.

        See ParticipanteAccionFlujo._remover_participante for params/docs.
        """
        return await self.participante_accion_flujo._remover_participante(
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
        )

    async def mover_participante(
        self,
        inscripcion_id: str,
        participante_id: str,
        equipo_destino_id: str,
    ):
        """
        Move a participant to another equipo within the same inscription.

        See ParticipanteAccionFlujo._mover_participante for params/docs.
        """
        return await self.participante_accion_flujo._mover_participante(
            inscripcion_id=inscripcion_id,
            participante_id=participante_id,
            equipo_destino_id=equipo_destino_id,
        )
