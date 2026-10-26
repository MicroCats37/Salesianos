"""
Core sync service of the ADVANCE (propagation of the winner).

The system NEVER invents the placement of the winner: it PROPOSES it and
the administrator confirms it (spec: "Al registrarlo, el sistema MUST
proponer su colocación en un slot enlazado del siguiente encuentro y
requerir confirmación administrativa idempotente").

The advance writes ONCE into the configured destination slot and records the
propagated winner (`ganador_propagado`) so a later correction can tell a
propagated participant from a manual one (design).

Idempotency comes first: when the destination already holds the winner and
the propagation was already recorded, the command writes NOTHING.
"""
from ...constants import CAMPOS_DE_SLOT, EstadoEncuentroChoices
from ...exceptions import (
    DestinoBloqueadoError,
    InvalidLinkError,
    InvalidWinnerError,
    SlotOcupadoError,
)
from ...models import Encuentro
from ...results.competencias_results import (
    AvancePreviewResult,
    AvanceResult,
    EncuentroResult,
)
from .base_service import BaseCoreService


class AvanceCoreService(BaseCoreService):
    """Proposal and application of the propagation of the winner."""

    # ── reads ──────────────────────────────────────────────────────────────

    def destino_de(self, encuentro: Encuentro) -> Encuentro:
        """Return the linked encounter or reject the command."""
        if not encuentro.siguiente_encuentro_id or not encuentro.slot_destino:
            raise InvalidLinkError()
        return encuentro.siguiente_encuentro

    def previsualizar(self, encuentro: Encuentro) -> AvancePreviewResult:
        """Build the proposal of the propagation. It never writes."""
        destino = self.destino_de(encuentro)
        ganador = self._ganador(encuentro)
        ocupante = self._ocupante(destino, encuentro.slot_destino)
        bloqueado, motivo_bloqueo = self._bloqueo(destino)
        ya_propagado = self._ya_propagado(destino, encuentro.slot_destino, ganador)
        return AvancePreviewResult(
            encuentro_id=str(encuentro.id),
            siguiente_encuentro_id=str(destino.id),
            slot_destino=encuentro.slot_destino,
            ganador_id=str(ganador.id),
            ocupante_actual_id=str(ocupante.id) if ocupante is not None else None,
            ya_propagado=ya_propagado,
            bloqueado=bloqueado,
            motivo_bloqueo=motivo_bloqueo,
        )

    # ── commands ───────────────────────────────────────────────────────────

    def confirmar(
        self,
        encuentro: Encuentro,
        destino: Encuentro,
        actor=None,
        motivo: str | None = None,
        expected_version: int | None = None,
    ) -> AvanceResult:
        """Place the winner in the destination slot and record the propagation."""
        ganador = self._ganador(encuentro)
        ocupante = self._ocupante(destino, encuentro.slot_destino)

        # Idempotency first: an exact replay writes nothing at all.
        if self._ya_propagado(destino, encuentro.slot_destino, ganador):
            return self._resultado(encuentro, destino, ganador, ya_aplicado=True)

        bloqueado, _ = self._bloqueo(destino)
        if bloqueado:
            raise DestinoBloqueadoError()

        if ocupante is not None and ocupante.id != ganador.id:
            raise SlotOcupadoError()

        self.aplicar_cas(encuentro, expected_version)
        motivo = self.exigir_motivo(motivo)

        campo = CAMPOS_DE_SLOT[encuentro.slot_destino]
        setattr(destino, campo, ganador)
        destino.ganador_propagado = ganador
        self.persistir_cambio(destino, actor, motivo)

        return self._resultado(encuentro, destino, ganador, ya_aplicado=False)

    # ── validations ───────────────────────────────────────────────────────

    @staticmethod
    def _ganador(encuentro: Encuentro):
        """The winner of the encounter — it is required to advance."""
        if encuentro.ganador_id is None:
            raise InvalidWinnerError()
        return encuentro.ganador

    @staticmethod
    def _ocupante(destino: Encuentro, slot_destino: str):
        """The team that currently occupies the destination slot."""
        campo = CAMPOS_DE_SLOT.get(slot_destino or "")
        if campo is None:
            raise InvalidLinkError()
        return getattr(destino, campo)

    @staticmethod
    def _bloqueo(destino: Encuentro) -> tuple[bool, str | None]:
        """A destination that started, finished or was cancelled is blocked."""
        if destino.estado in (
            EstadoEncuentroChoices.FINALIZADO,
            EstadoEncuentroChoices.CANCELADO,
        ):
            return True, "El encuentro de destino ya finalizó o fue cancelado."
        if destino.iniciado_en is not None:
            return True, "El encuentro de destino ya había comenzado."
        return False, None

    @staticmethod
    def _ya_propagado(
        destino: Encuentro,
        slot_destino: str,
        ganador,
    ) -> bool:
        """True when the propagation was already applied (exact replay)."""
        campo = CAMPOS_DE_SLOT.get(slot_destino or "")
        if campo is None:
            return False
        ocupante = getattr(destino, campo)
        if ocupante is None or ocupante.id != ganador.id:
            return False
        return destino.ganador_propagado_id == ganador.id

    @staticmethod
    def _resultado(
        encuentro: Encuentro,
        destino: Encuentro,
        ganador,
        ya_aplicado: bool,
    ) -> AvanceResult:
        """Build the result of the advance."""
        return AvanceResult(
            encuentro_origen_id=str(encuentro.id),
            siguiente_encuentro_id=str(destino.id),
            slot_destino=encuentro.slot_destino,
            ganador_id=str(ganador.id),
            ya_aplicado=ya_aplicado,
            destino=EncuentroResult.desde(destino),
        )
