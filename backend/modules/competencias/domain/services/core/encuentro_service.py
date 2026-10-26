"""
Core sync service of the encounters of the bracket.

An encounter belongs to a round and holds two participant slots (nullable:
the bracket may be empty or partial), an optional schedule and the manual
bye flag.

The lifecycle is:

    BORRADOR → PROGRAMADO → EN_CURSO → FINALIZADO
                  ↕            ↕
             SUSPENDIDO ──────┘  (it resumes to the previous state)
    any → CANCELADO (terminal)

The result of a normal encounter (winner + score) belongs to the result flow
of Phase 2: Phase 1 only finalizes an encounter through a MANUAL BYE, which
is final by definition.
"""
from django.utils import timezone

from ...constants import (
    CAMPOS_DE_SLOT,
    EstadoEncuentroChoices,
    EstadoPreSuspensionChoices,
    SlotDestinoChoices,
)
from ...exceptions import (
    CompetenciaDuplicadaError,
    CompetenciaEquipoNotFoundError,
    DeleteNotAllowedError,
    EncuentroNotFoundError,
    InvalidLinkError,
    InvalidScheduleError,
    InvalidStateTransitionError,
    InvalidWinnerError,
)
from ...models import CompetenciaEquipo, Encuentro, Ronda
from ...schemas.competencias_schemas import (
    EncuentroCreateData,
    EncuentroProgramacionData,
)
from .base_service import BaseCoreService
from .competencia_service import ESTADOS_TERMINALES_COMPETENCIA

#: Legal transitions of an encounter.
TRANSICIONES_ENCUENTRO: dict[str, set[str]] = {
    EstadoEncuentroChoices.BORRADOR: {
        EstadoEncuentroChoices.PROGRAMADO,
        EstadoEncuentroChoices.CANCELADO,
    },
    EstadoEncuentroChoices.PROGRAMADO: {
        EstadoEncuentroChoices.BORRADOR,
        EstadoEncuentroChoices.EN_CURSO,
        EstadoEncuentroChoices.SUSPENDIDO,
        EstadoEncuentroChoices.CANCELADO,
    },
    EstadoEncuentroChoices.EN_CURSO: {
        EstadoEncuentroChoices.SUSPENDIDO,
        EstadoEncuentroChoices.FINALIZADO,
        EstadoEncuentroChoices.CANCELADO,
    },
    EstadoEncuentroChoices.SUSPENDIDO: {
        EstadoEncuentroChoices.BORRADOR,
        EstadoEncuentroChoices.PROGRAMADO,
        EstadoEncuentroChoices.EN_CURSO,
        EstadoEncuentroChoices.CANCELADO,
    },
    EstadoEncuentroChoices.FINALIZADO: set(),
    EstadoEncuentroChoices.CANCELADO: set(),
}

#: States after which the encounter no longer accepts changes.
ESTADOS_TERMINALES_ENCUENTRO = {
    EstadoEncuentroChoices.FINALIZADO,
    EstadoEncuentroChoices.CANCELADO,
}


class EncuentroCoreService(BaseCoreService):
    """Sync operations over `Encuentro` — the caller owns the transaction."""

    # ── reads ──────────────────────────────────────────────────────────────

    def obtener_por_id(self, encuentro_id) -> Encuentro:
        """Return the encounter or raise `EncuentroNotFoundError`."""
        try:
            return Encuentro.objects.select_related(
                "ronda__competencia",
                "participante_1__equipo",
                "participante_2__equipo",
            ).get(id=encuentro_id)
        except (Encuentro.DoesNotExist, ValueError, TypeError):
            raise EncuentroNotFoundError()

    # ── commands ───────────────────────────────────────────────────────────

    def crear(
        self,
        ronda: Ronda,
        data: EncuentroCreateData,
        actor=None,
    ) -> Encuentro:
        """Create an encounter of the round (participants may be empty)."""
        self.exigir_no_terminal(ronda.competencia, ESTADOS_TERMINALES_COMPETENCIA)
        if ronda.encuentros.filter(orden=data.orden).exists():
            raise CompetenciaDuplicadaError()
        participante_1, participante_2 = self._validar_participantes(
            ronda,
            data.participante_1_id,
            data.participante_2_id,
        )
        encuentro = Encuentro(
            ronda=ronda,
            orden=data.orden,
            participante_1=participante_1,
            participante_2=participante_2,
            estado=EstadoEncuentroChoices.BORRADOR,
        )
        return self.persistir_nuevo(encuentro, actor, "Alta de encuentro en el cuadro")

    def asignar_participantes(
        self,
        encuentro: Encuentro,
        participante_1_id=None,
        participante_2_id=None,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Encuentro:
        """Move the teams of the slots (moving a slot always needs a motive)."""
        self.exigir_no_terminal(encuentro, ESTADOS_TERMINALES_ENCUENTRO)
        ya_aplicado = (
            self._mismo_participante(encuentro.participante_1_id, participante_1_id)
            and self._mismo_participante(encuentro.participante_2_id, participante_2_id)
        )
        self.aplicar_cas(encuentro, expected_version, ya_aplicado)
        if ya_aplicado:
            return encuentro

        motivo = self.exigir_motivo(motivo)
        participante_1, participante_2 = self._validar_participantes(
            encuentro.ronda,
            participante_1_id,
            participante_2_id,
        )
        encuentro.participante_1 = participante_1
        encuentro.participante_2 = participante_2
        return self.persistir_cambio(
            encuentro, actor, motivo
        )

    def programar(
        self,
        encuentro: Encuentro,
        data: EncuentroProgramacionData,
        actor=None,
        motivo: str | None = None,
    ) -> Encuentro:
        """Store the schedule of the encounter and publish it.

        The overlap check and the locks are NOT done here: the flow owns them
        because they need the transaction (design).
        """
        if encuentro.estado not in (
            EstadoEncuentroChoices.BORRADOR,
            EstadoEncuentroChoices.PROGRAMADO,
        ):
            raise InvalidStateTransitionError()
        motivo = self.exigir_motivo(motivo)
        encuentro.inicio_programado = data.inicio_programado
        encuentro.fin_programado = data.fin_programado
        if encuentro.estado == EstadoEncuentroChoices.BORRADOR:
            encuentro.estado = EstadoEncuentroChoices.PROGRAMADO
        return self.persistir_cambio(encuentro, actor, motivo)

    def configurar_bye(
        self,
        encuentro: Encuentro,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Encuentro:
        """Configure a MANUAL bye.

        A bye has exactly one participant, no schedule, no score and it is
        final: the participant is the winner. The bye is NEVER chosen
        automatically by the system (spec).
        """
        # Idempotency: the encounter already IS a manual bye.
        if (
            encuentro.es_bye
            and encuentro.estado == EstadoEncuentroChoices.FINALIZADO
        ):
            return encuentro
        # A bye is never played: it cannot have a schedule.
        if (
            encuentro.inicio_programado is not None
            or encuentro.fin_programado is not None
        ):
            raise InvalidScheduleError()
        if (encuentro.participante_1 is None) == (encuentro.participante_2 is None):
            raise InvalidWinnerError()
        if (
            encuentro.puntaje_1 is not None
            or encuentro.puntaje_2 is not None
            or encuentro.marcador_detalle
        ):
            raise InvalidWinnerError()
        if encuentro.estado != EstadoEncuentroChoices.BORRADOR:
            raise InvalidStateTransitionError()

        self.aplicar_cas(encuentro, expected_version)
        motivo = self.exigir_motivo(motivo)
        participante = encuentro.participante_1 or encuentro.participante_2
        encuentro.es_bye = True
        encuentro.ganador = participante
        encuentro.estado = EstadoEncuentroChoices.FINALIZADO
        encuentro.finalizado_en = timezone.now()
        return self.persistir_cambio(encuentro, actor, motivo)

    def cambiar_estado(
        self,
        encuentro: Encuentro,
        nuevo_estado: str,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Encuentro:
        """Move the encounter through its lifecycle."""
        if encuentro.estado == nuevo_estado:
            return encuentro

        if encuentro.estado == EstadoEncuentroChoices.SUSPENDIDO:
            # A suspended encounter resumes to the state it had before.
            if nuevo_estado != EstadoEncuentroChoices.CANCELADO:
                if nuevo_estado != encuentro.estado_pre_suspension:
                    raise InvalidStateTransitionError()
        else:
            permitidos = TRANSICIONES_ENCUENTRO.get(encuentro.estado, set())
            if nuevo_estado not in permitidos:
                raise InvalidStateTransitionError()
            if nuevo_estado == EstadoEncuentroChoices.FINALIZADO:
                # The result of a normal encounter is owned by the result flow
                # of Phase 2: only a bye (which already has its winner) may
                # reach the final state through this command.
                if encuentro.ganador_id is None:
                    raise InvalidWinnerError()

        self.aplicar_cas(encuentro, expected_version)

        if nuevo_estado == EstadoEncuentroChoices.SUSPENDIDO:
            # Only a non terminal state may be resumed later.
            if encuentro.estado not in EstadoPreSuspensionChoices.values:
                raise InvalidStateTransitionError()
            encuentro.estado_pre_suspension = encuentro.estado
        elif encuentro.estado == EstadoEncuentroChoices.SUSPENDIDO:
            encuentro.estado_pre_suspension = None

        if nuevo_estado == EstadoEncuentroChoices.EN_CURSO and not encuentro.iniciado_en:
            encuentro.iniciado_en = timezone.now()
        if nuevo_estado == EstadoEncuentroChoices.FINALIZADO:
            encuentro.finalizado_en = timezone.now()
        if nuevo_estado == EstadoEncuentroChoices.BORRADOR:
            # Going back to the draft removes the published schedule.
            encuentro.inicio_programado = None
            encuentro.fin_programado = None

        encuentro.estado = nuevo_estado
        return self.persistir_cambio(
            encuentro, actor, motivo or f"Cambio de estado a {nuevo_estado}"
        )

    # ── bracket link ───────────────────────────────────────────────────────

    def enlazar_siguiente(
        self,
        encuentro: Encuentro,
        siguiente_encuentro_id,
        slot_destino,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Encuentro:
        """Link the encounter to the NEXT encounter of the bracket.

        The link and its destination slot are written TOGETHER (the model
        constraint `ck_encuento_enlace_slot` forbids one without the other)
        and the change is always audited (design: "enlaces ... exige motivo").

        Integrity rules of the link:

        - the destination must exist and must NOT be the encounter itself,
        - the destination must belong to the SAME competition,
        - the destination must be in a LATER round: the link always points
          forward, so a cycle can never be built,
        - no other encounter may already feed the same destination slot,
        - a propagation that was already applied cannot be orphaned: it must
          be corrected first (the correction flow owns that).
        """
        if not siguiente_encuentro_id or not slot_destino:
            raise InvalidLinkError()
        if slot_destino not in SlotDestinoChoices.values:
            raise InvalidLinkError()

        ya_aplicado = (
            str(encuentro.siguiente_encuentro_id) == str(siguiente_encuentro_id)
            and encuentro.slot_destino == slot_destino
        )
        self.aplicar_cas(encuentro, expected_version, ya_aplicado)
        if ya_aplicado:
            return encuentro

        motivo = self.exigir_motivo(motivo)
        siguiente = self.obtener_por_id(siguiente_encuentro_id)
        self._validar_enlace(encuentro, siguiente, slot_destino)

        if self._propagacion_aplicada(encuentro):
            raise InvalidStateTransitionError()

        encuentro.siguiente_encuentro = siguiente
        encuentro.slot_destino = slot_destino
        return self.persistir_cambio(encuentro, actor, motivo)

    def desenlazar_siguiente(
        self,
        encuentro: Encuentro,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> Encuentro:
        """Remove the link of the encounter (both fields travel together)."""
        if not encuentro.siguiente_encuentro_id:
            # Nothing linked: the intention is already applied.
            return encuentro

        self.aplicar_cas(encuentro, expected_version)
        if self._propagacion_aplicada(encuentro):
            raise InvalidStateTransitionError()

        motivo = self.exigir_motivo(motivo)
        encuentro.siguiente_encuentro = None
        encuentro.slot_destino = None
        return self.persistir_cambio(encuentro, actor, motivo)

    def eliminar(self, encuentro: Encuentro, actor=None) -> None:
        """Physically delete a draft that was never used.

        Only a draft without participants, without schedule, without links or
        dependencies and without any change after its creation may be deleted.
        """
        if encuentro.estado != EstadoEncuentroChoices.BORRADOR:
            raise DeleteNotAllowedError()
        if encuentro.participante_1_id or encuentro.participante_2_id:
            raise DeleteNotAllowedError()
        if (
            encuentro.inicio_programado is not None
            or encuentro.fin_programado is not None
        ):
            raise DeleteNotAllowedError()
        if (
            encuentro.siguiente_encuentro_id
            or encuentro.ganador_id
            or encuentro.ganador_propagado_id
        ):
            raise DeleteNotAllowedError()
        if Encuentro.objects.filter(siguiente_encuentro=encuentro).exists():
            raise DeleteNotAllowedError()
        if encuentro.history.count() > 1:
            raise DeleteNotAllowedError()
        encuentro.delete()

    # ── validations ───────────────────────────────────────────────────────

    @staticmethod
    def _validar_enlace(
        encuentro: Encuentro,
        siguiente: Encuentro,
        slot_destino: str,
    ) -> None:
        """The link must point forward, inside the same bracket and alone."""
        if siguiente.id == encuentro.id:
            raise InvalidLinkError()
        if siguiente.ronda.competencia_id != encuentro.ronda.competencia_id:
            raise InvalidLinkError()
        if siguiente.ronda.orden <= encuentro.ronda.orden:
            # The link always points to a LATER round: a cycle can never be
            # built and the winner always flows forward.
            raise InvalidLinkError()
        ya_usado = (
            Encuentro.objects.filter(
                siguiente_encuentro=siguiente,
                slot_destino=slot_destino,
            )
            .exclude(id=encuentro.id)
            .exists()
        )
        if ya_usado:
            raise InvalidLinkError()

    @staticmethod
    def _propagacion_aplicada(encuentro: Encuentro) -> bool:
        """True when the winner of the encounter is already in its destination."""
        if not encuentro.siguiente_encuentro_id or not encuentro.ganador_id:
            return False
        campo = CAMPOS_DE_SLOT.get(encuentro.slot_destino or "")
        if campo is None:
            return False
        destino = encuentro.siguiente_encuentro
        ocupante = getattr(destino, campo)
        return ocupante is not None and ocupante.id == encuentro.ganador_id

    @staticmethod
    def _mismo_participante(actual, solicitado) -> bool:
        actual_id = str(actual) if actual else None
        solicitado_id = str(solicitado) if solicitado else None
        return actual_id == solicitado_id

    @staticmethod
    def _obtener_participante(participante_id) -> CompetenciaEquipo:
        try:
            return CompetenciaEquipo.objects.select_related(
                "equipo",
            ).get(id=participante_id)
        except (CompetenciaEquipo.DoesNotExist, ValueError, TypeError):
            raise CompetenciaEquipoNotFoundError()

    @classmethod
    def _validar_participantes(
        cls,
        ronda: Ronda,
        participante_1_id,
        participante_2_id,
    ) -> tuple:
        """Both slots must belong to the competition of the round."""
        participante_1 = (
            cls._obtener_participante(participante_1_id)
            if participante_1_id
            else None
        )
        participante_2 = (
            cls._obtener_participante(participante_2_id)
            if participante_2_id
            else None
        )
        for participante in (participante_1, participante_2):
            if (
                participante is not None
                and participante.competencia_id != ronda.competencia_id
            ):
                raise InvalidLinkError()
        if (
            participante_1 is not None
            and participante_2 is not None
            and participante_1.id == participante_2.id
        ):
            raise InvalidLinkError()
        return participante_1, participante_2
