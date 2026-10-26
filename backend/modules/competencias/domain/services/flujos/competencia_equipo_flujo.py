"""CompetenciaEquipoFlujo — async flow of the teams registered in the bracket."""
from asgiref.sync import sync_to_async
from django.db import transaction

from ...results.competencias_results import CompetenciaEquipoResult
from ...schemas.competencias_schemas import CompetenciaEquipoUpdateData
from ..core.competencia_equipo_service import CompetenciaEquipoCoreService
from ..core.competencia_service import CompetenciaCoreService


class CompetenciaEquipoFlujo:
    """Async flow of the participation of a team inside the bracket."""

    def __init__(
        self,
        competencia_equipo_core: CompetenciaEquipoCoreService,
        competencia_core: CompetenciaCoreService,
    ):
        self._core = competencia_equipo_core
        self._competencia_core = competencia_core

    @sync_to_async
    def _incorporar_atomico(
        self,
        competencia_id,
        equipo_id,
        orden,
        actor=None,
    ) -> CompetenciaEquipoResult:
        """Register the team in the bracket in a transaction."""
        with transaction.atomic():
            competencia = self._competencia_core.obtener_por_id(competencia_id)
            entrada = self._core.incorporar(
                competencia,
                equipo_id,
                orden,
                actor=actor,
            )
            return CompetenciaEquipoResult.desde(entrada)

    @sync_to_async
    def _actualizar_atomico(
        self,
        competencia_equipo_id,
        data: CompetenciaEquipoUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Update the participation of the team in a transaction."""
        with transaction.atomic():
            entrada = self._core.obtener_por_id(competencia_equipo_id)
            actualizada = self._core.actualizar(
                entrada,
                data,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return CompetenciaEquipoResult.desde(actualizada)

    @sync_to_async
    def _retirar_atomico(
        self,
        competencia_equipo_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Withdraw the team from the bracket in a transaction."""
        with transaction.atomic():
            entrada = self._core.obtener_por_id(competencia_equipo_id)
            actualizada = self._core.retirar(
                entrada,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return CompetenciaEquipoResult.desde(actualizada)

    @sync_to_async
    def _reactivar_atomico(
        self,
        competencia_equipo_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Bring the withdrawn team back into the bracket in a transaction."""
        with transaction.atomic():
            entrada = self._core.obtener_por_id(competencia_equipo_id)
            actualizada = self._core.reactivar(
                entrada,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return CompetenciaEquipoResult.desde(actualizada)

    # ── public API ────────────────────────────────────────────────────────

    async def incorporar(
        self,
        competencia_id,
        equipo_id,
        orden,
        actor=None,
    ) -> CompetenciaEquipoResult:
        """Register the team in the bracket with its manual order."""
        return await self._incorporar_atomico(
            competencia_id,
            equipo_id,
            orden,
            actor,
        )

    async def actualizar(
        self,
        competencia_equipo_id,
        data: CompetenciaEquipoUpdateData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Update the manual order or the state of the participation."""
        return await self._actualizar_atomico(
            competencia_equipo_id,
            data,
            actor,
            motivo,
            expected_version,
        )

    async def retirar(
        self,
        competencia_equipo_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Withdraw the team from the bracket (the history is preserved)."""
        return await self._retirar_atomico(
            competencia_equipo_id,
            actor,
            motivo,
            expected_version,
        )

    async def reactivar(
        self,
        competencia_equipo_id,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> CompetenciaEquipoResult:
        """Bring the withdrawn team back into the bracket."""
        return await self._reactivar_atomico(
            competencia_equipo_id,
            actor,
            motivo,
            expected_version,
        )
