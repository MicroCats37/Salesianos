"""RondaFlujo — async flow of the rounds of the bracket."""
from asgiref.sync import sync_to_async
from django.db import transaction

from ...results.competencias_results import RondaResult
from ...schemas.competencias_schemas import RondaCreateData, RondaUpdateData
from ..core.competencia_service import CompetenciaCoreService
from ..core.ronda_service import RondaCoreService


class RondaFlujo:
    """Async flow of the rounds: it owns the atomicity of the commands."""

    def __init__(
        self,
        ronda_core: RondaCoreService,
        competencia_core: CompetenciaCoreService,
    ):
        self._core = ronda_core
        self._competencia_core = competencia_core

    @sync_to_async
    def _crear_atomico(
        self,
        competencia_id,
        data: RondaCreateData,
        actor=None,
    ) -> RondaResult:
        """Create the round in a transaction."""
        with transaction.atomic():
            competencia = self._competencia_core.obtener_por_id(competencia_id)
            ronda = self._core.crear(competencia, data, actor=actor)
            return RondaResult.desde(ronda)

    @sync_to_async
    def _actualizar_atomico(
        self,
        ronda_id,
        data: RondaUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> RondaResult:
        """Update the round in a transaction."""
        with transaction.atomic():
            ronda = self._core.obtener_por_id(ronda_id)
            actualizada = self._core.actualizar(
                ronda,
                data,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return RondaResult.desde(actualizada)

    @sync_to_async
    def _invalidar_atomico(
        self,
        ronda_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> RondaResult:
        """Invalidate the round in a transaction (it is never deleted)."""
        with transaction.atomic():
            ronda = self._core.obtener_por_id(ronda_id)
            invalidada = self._core.invalidar(
                ronda,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return RondaResult.desde(invalidada)

    @sync_to_async
    def _eliminar_atomico(self, ronda_id, actor=None) -> None:
        """Delete the round when it was never used."""
        with transaction.atomic():
            ronda = self._core.obtener_por_id(ronda_id)
            self._core.eliminar(ronda, actor=actor)

    # ── public API ────────────────────────────────────────────────────────

    async def crear(
        self,
        competencia_id,
        data: RondaCreateData,
        actor=None,
    ) -> RondaResult:
        """Create the round."""
        return await self._crear_atomico(competencia_id, data, actor)

    async def actualizar(
        self,
        ronda_id,
        data: RondaUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> RondaResult:
        """Update the label or the order of the round."""
        return await self._actualizar_atomico(
            ronda_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def invalidar(
        self,
        ronda_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> RondaResult:
        """Invalidate the round."""
        return await self._invalidar_atomico(
            ronda_id,
            actor,
            motivo,
            expected_version,
        )

    async def eliminar(self, ronda_id, actor=None) -> None:
        """Delete the round when it was never used."""
        return await self._eliminar_atomico(ronda_id, actor)
