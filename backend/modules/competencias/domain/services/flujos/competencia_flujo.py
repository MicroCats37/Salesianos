"""CompetenciaFlujo — async flow of the commands of the competition."""
from asgiref.sync import sync_to_async
from django.db import transaction

from ...results.competencias_results import CompetenciaResult
from ...schemas.competencias_schemas import (
    CompetenciaCreateData,
    CompetenciaUpdateData,
)
from ..core.competencia_service import CompetenciaCoreService


class CompetenciaFlujo:
    """Async flow of the competition: it owns the atomicity of the commands."""

    def __init__(self, competencia_core: CompetenciaCoreService):
        self._core = competencia_core

    @sync_to_async
    def _crear_atomico(
        self,
        data: CompetenciaCreateData,
        actor=None,
    ) -> CompetenciaResult:
        """Create the competition in a transaction."""
        with transaction.atomic():
            competencia = self._core.crear(data, actor=actor)
            return CompetenciaResult.desde(competencia)

    @sync_to_async
    def _actualizar_atomico(
        self,
        competencia_id,
        data: CompetenciaUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaResult:
        """Update the competition in a transaction."""
        with transaction.atomic():
            competencia = self._core.obtener_por_id(competencia_id)
            actualizado = self._core.actualizar(
                competencia,
                data,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return CompetenciaResult.desde(actualizado)

    @sync_to_async
    def _cambiar_estado_atomico(
        self,
        competencia_id,
        nuevo_estado,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaResult:
        """Move the competition through its lifecycle in a transaction."""
        with transaction.atomic():
            competencia = self._core.obtener_por_id(competencia_id)
            actualizado = self._core.cambiar_estado(
                competencia,
                nuevo_estado,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return CompetenciaResult.desde(actualizado)

    @sync_to_async
    def _eliminar_atomico(self, competencia_id, actor=None) -> None:
        """Delete the competition (only when it was never used)."""
        with transaction.atomic():
            competencia = self._core.obtener_por_id(competencia_id)
            self._core.eliminar(competencia, actor=actor)

    # ── public API ────────────────────────────────────────────────────────

    async def crear(
        self,
        data: CompetenciaCreateData,
        actor=None,
    ) -> CompetenciaResult:
        """Create the competition."""
        return await self._crear_atomico(data, actor)

    async def actualizar(
        self,
        competencia_id,
        data: CompetenciaUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaResult:
        """Update the editable fields of the competition."""
        return await self._actualizar_atomico(
            competencia_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def cambiar_estado(
        self,
        competencia_id,
        nuevo_estado,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaResult:
        """Move the competition through its lifecycle."""
        return await self._cambiar_estado_atomico(
            competencia_id,
            nuevo_estado,
            actor,
            motivo,
            expected_version,
        )

    async def eliminar(self, competencia_id, actor=None) -> None:
        """Delete the competition when it was never used."""
        return await self._eliminar_atomico(competencia_id, actor)
