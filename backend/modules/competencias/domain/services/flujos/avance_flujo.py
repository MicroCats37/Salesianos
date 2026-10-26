"""
AvanceFlujo — async flow of the advance (propagation of the winner).

The advance writes on TWO encounters: the origin (the one that owns the
winner) and the destination (the linked one that receives it). Both are
locked inside the transaction, in the deterministic ascending UUID order of
the locking protocol, and the destination is checked before writing:

- a destination that already started, finished or was cancelled is BLOCKED,
- a destination slot that already holds another team is OCCUPIED,
- an exact replay writes NOTHING at all.
"""
from asgiref.sync import sync_to_async
from django.db import transaction

from ...results.competencias_results import AvancePreviewResult, AvanceResult
from ..core.avance_service import AvanceCoreService
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService


class AvanceFlujo:
    """Async flow of the advance of the bracket."""

    def __init__(
        self,
        avance_core: AvanceCoreService,
        encuentro_core: EncuentroCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = avance_core
        self._encuentros = encuentro_core
        self._programacion = programacion_core

    @sync_to_async
    def _previsualizar(self, encuentro_id) -> AvancePreviewResult:
        """Build the proposal of the propagation (it never writes)."""
        encuentro = self._encuentros.obtener_por_id(encuentro_id)
        return self._core.previsualizar(encuentro)

    @sync_to_async
    def _confirmar_atomico(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> AvanceResult:
        """Propagate the winner in a transaction."""
        with transaction.atomic():
            encuentro = self._encuentros.obtener_por_id(encuentro_id)
            competencia = encuentro.ronda.competencia
            destino = self._core.destino_de(encuentro)

            self._programacion.bloquear_competencia(competencia.id)
            bloqueados = self._programacion.bloquear_encuentros(
                [encuentro.id, destino.id]
            )
            por_id = {bloqueado.id: bloqueado for bloqueado in bloqueados}
            origen = por_id.get(encuentro.id, encuentro)
            destino_bloqueado = por_id.get(destino.id, destino)

            return self._core.confirmar(
                origen,
                destino_bloqueado,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )

    async def previsualizar(self, encuentro_id) -> AvancePreviewResult:
        """Propose the placement of the winner in the linked slot."""
        return await self._previsualizar(encuentro_id)

    async def confirmar(
        self,
        encuentro_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> AvanceResult:
        """Place the winner in the linked slot and record the propagation."""
        return await self._confirmar_atomico(
            encuentro_id,
            actor,
            motivo,
            expected_version,
        )
