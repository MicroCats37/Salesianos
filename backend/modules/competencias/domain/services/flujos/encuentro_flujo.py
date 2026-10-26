"""
EncuentroFlujo — async flow of the commands of the encounters.

The scheduling is the only command that needs the whole locking protocol, so
it lives here: the flow opens the transaction, locks the competition, the
affected encounters and the underlying teams (in ascending UUID order) and
only then writes.

The overlap check is portable: a team cannot play two matches at the same
time even when the two encounters belong to different competitions.
"""
from asgiref.sync import sync_to_async
from django.db import transaction

from ...constants import EstadoEncuentroChoices
from ...exceptions import EquipoSolapadoError, InvalidStateTransitionError
from ...results.competencias_results import EncuentroResult
from ...schemas.competencias_schemas import (
    EncuentroCreateData,
    EncuentroProgramacionData,
)
from ..core.base_service import BaseCoreService
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService
from ..core.ronda_service import RondaCoreService


class EncuentroFlujo:
    """Async flow of the encounters: it owns the atomicity of the commands."""

    def __init__(
        self,
        encuentro_core: EncuentroCoreService,
        ronda_core: RondaCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = encuentro_core
        self._ronda_core = ronda_core
        self._programacion = programacion_core

    # ── creation ──────────────────────────────────────────────────────────

    @sync_to_async
    def _crear_atomico(
        self,
        ronda_id,
        data: EncuentroCreateData,
        actor=None,
    ) -> EncuentroResult:
        """Create the encounter in a transaction."""
        with transaction.atomic():
            ronda = self._ronda_core.obtener_por_id(ronda_id)
            encuentro = self._core.crear(ronda, data, actor=actor)
            return EncuentroResult.desde(encuentro)

    # ── participants ──────────────────────────────────────────────────────

    @sync_to_async
    def _asignar_participantes_atomico(
        self,
        encuentro_id,
        participante_1_id=None,
        participante_2_id=None,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Move the teams of the slots in a transaction."""
        with transaction.atomic():
            encuentro = self._core.obtener_por_id(encuentro_id)
            actualizado = self._core.asignar_participantes(
                encuentro,
                participante_1_id=participante_1_id,
                participante_2_id=participante_2_id,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return EncuentroResult.desde(actualizado)

    # ── manual bye ────────────────────────────────────────────────────────

    @sync_to_async
    def _configurar_bye_atomico(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Configure the manual bye in a transaction."""
        with transaction.atomic():
            encuentro = self._core.obtener_por_id(encuentro_id)
            actualizado = self._core.configurar_bye(
                encuentro,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return EncuentroResult.desde(actualizado)

    # ── scheduling ────────────────────────────────────────────────────────

    @sync_to_async
    def _programar_atomico(
        self,
        encuentro_id,
        data: EncuentroProgramacionData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Schedule the encounter under the locking protocol.

        The order of the steps is the one of the design:

        1. the requested interval must be valid,
        2. the competition, the encounter and the underlying teams are locked
           (the teams in ascending UUID order),
        3. the intent already applied → the command is a no-op,
        4. otherwise the version of the caller must be the current one,
        5. the state must allow the schedule,
        6. the teams must not overlap with another encounter,
        7. the schedule is written.
        """
        with transaction.atomic():
            encuentro = self._core.obtener_por_id(encuentro_id)
            competencia = encuentro.ronda.competencia

            self._programacion.validar_horario(
                competencia,
                data.inicio_programado,
                data.fin_programado,
            )

            self._programacion.bloquear_competencia(competencia.id)
            bloqueados = self._programacion.bloquear_encuentros([encuentro.id])
            encuentro = bloqueados[0] if bloqueados else encuentro

            ya_aplicado = (
                encuentro.inicio_programado == data.inicio_programado
                and encuentro.fin_programado == data.fin_programado
                and encuentro.estado == EstadoEncuentroChoices.PROGRAMADO
            )
            if ya_aplicado:
                # The intention is already applied: the command is a no-op
                # and it does not write anything.
                return EncuentroResult.desde(encuentro)

            BaseCoreService.aplicar_cas(encuentro, expected_version)
            if encuentro.estado not in (
                EstadoEncuentroChoices.BORRADOR,
                EstadoEncuentroChoices.PROGRAMADO,
            ):
                raise InvalidStateTransitionError()

            equipo_ids = self._programacion.equipos_de_encuentro(encuentro)
            self._programacion.bloquear_equipos(equipo_ids)
            solapes = self._programacion.detectar_solape(
                equipo_ids,
                data.inicio_programado,
                data.fin_programado,
                excluir_encuentro_id=encuentro.id,
            )
            if solapes:
                raise EquipoSolapadoError()

            actualizado = self._core.programar(
                encuentro,
                data,
                actor=actor,
                motivo=motivo,
            )
            return EncuentroResult.desde(actualizado)

    # ── bracket link ──────────────────────────────────────────────────────

    @sync_to_async
    def _enlazar_atomico(
        self,
        encuentro_id,
        siguiente_encuentro_id,
        slot_destino,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Link the encounter to the next one of the bracket.

        The link and its destination slot are written TOGETHER inside the
        transaction: the model constraint forbids one without the other.
        """
        with transaction.atomic():
            encuentro = self._core.obtener_por_id(encuentro_id)
            competencia = encuentro.ronda.competencia
            siguiente = self._core.obtener_por_id(siguiente_encuentro_id)

            self._programacion.bloquear_competencia(competencia.id)
            bloqueados = self._programacion.bloquear_encuentros(
                [encuentro.id, siguiente.id]
            )
            por_id = {bloqueado.id: bloqueado for bloqueado in bloqueados}
            origen = por_id.get(encuentro.id, encuentro)

            actualizado = self._core.enlazar_siguiente(
                origen,
                siguiente.id,
                slot_destino,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return EncuentroResult.desde(actualizado)

    @sync_to_async
    def _desenlazar_atomico(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Remove the link of the encounter in a transaction."""
        with transaction.atomic():
            encuentro = self._core.obtener_por_id(encuentro_id)
            bloqueados = self._programacion.bloquear_encuentros([encuentro.id])
            origen = bloqueados[0] if bloqueados else encuentro

            actualizado = self._core.desenlazar_siguiente(
                origen,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return EncuentroResult.desde(actualizado)

    # ── lifecycle ─────────────────────────────────────────────────────────

    @sync_to_async
    def _cambiar_estado_atomico(
        self,
        encuentro_id,
        nuevo_estado,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Move the encounter through its lifecycle in a transaction."""
        with transaction.atomic():
            encuentro = self._core.obtener_por_id(encuentro_id)
            actualizado = self._core.cambiar_estado(
                encuentro,
                nuevo_estado,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return EncuentroResult.desde(actualizado)

    @sync_to_async
    def _eliminar_atomico(self, encuentro_id, actor=None) -> None:
        """Delete the draft when it was never used."""
        with transaction.atomic():
            encuentro = self._core.obtener_por_id(encuentro_id)
            self._core.eliminar(encuentro, actor=actor)

    # ── public API ────────────────────────────────────────────────────────

    async def crear(
        self,
        ronda_id,
        data: EncuentroCreateData,
        actor=None,
    ) -> EncuentroResult:
        """Create the encounter."""
        return await self._crear_atomico(ronda_id, data, actor)

    async def asignar_participantes(
        self,
        encuentro_id,
        participante_1_id=None,
        participante_2_id=None,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Move the teams of the slots."""
        return await self._asignar_participantes_atomico(
            encuentro_id,
            participante_1_id,
            participante_2_id,
            actor,
            motivo,
            expected_version,
        )

    async def configurar_bye(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Configure the manual bye."""
        return await self._configurar_bye_atomico(
            encuentro_id,
            actor,
            motivo,
            expected_version,
        )

    async def programar(
        self,
        encuentro_id,
        data: EncuentroProgramacionData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Schedule the encounter."""
        return await self._programar_atomico(
            encuentro_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def cambiar_estado(
        self,
        encuentro_id,
        nuevo_estado,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Move the encounter through its lifecycle."""
        return await self._cambiar_estado_atomico(
            encuentro_id,
            nuevo_estado,
            actor,
            motivo,
            expected_version,
        )

    async def eliminar(self, encuentro_id, actor=None) -> None:
        """Delete the draft when it was never used."""
        return await self._eliminar_atomico(encuentro_id, actor)

    async def enlazar_siguiente(
        self,
        encuentro_id,
        siguiente_encuentro_id,
        slot_destino,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Link the encounter to the next encounter of the bracket."""
        return await self._enlazar_atomico(
            encuentro_id,
            siguiente_encuentro_id,
            slot_destino,
            actor,
            motivo,
            expected_version,
        )

    async def desenlazar_siguiente(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Remove the link of the encounter."""
        return await self._desenlazar_atomico(
            encuentro_id,
            actor,
            motivo,
            expected_version,
        )
