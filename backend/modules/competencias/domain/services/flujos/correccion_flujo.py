"""
CorreccionFlujo — async flow of the correction of the winner.

The correction NEVER cascades silently: the flow locks the origin AND every
descendant reached through the links of the bracket (in the deterministic
ascending UUID order) and it recomputes the chain from the locked rows
before writing anything.

When a descendant already started, finished or was cancelled the whole
correction is rejected unless the administrator sends an explicit override,
accepts the impact and writes a motive: without them NOTHING changes.
"""
from asgiref.sync import sync_to_async
from django.db import transaction

from ...results.competencias_results import (
    CorreccionPreviewResult,
    CorreccionResult,
)
from ...schemas.competencias_schemas import CorreccionGanadorData
from ..core.correccion_service import CorreccionCoreService
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService


class CorreccionFlujo:
    """Async flow of the correction of the winner of an encounter."""

    def __init__(
        self,
        correccion_core: CorreccionCoreService,
        encuentro_core: EncuentroCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = correccion_core
        self._encuentros = encuentro_core
        self._programacion = programacion_core

    @sync_to_async
    def _previsualizar(
        self,
        encuentro_id,
        ganador_nuevo_id,
    ) -> CorreccionPreviewResult:
        """Return the impact of the correction (it never writes)."""
        encuentro = self._encuentros.obtener_por_id(encuentro_id)
        return self._core.previsualizar(encuentro, ganador_nuevo_id)

    @sync_to_async
    def _corregir_atomico(
        self,
        encuentro_id,
        data: CorreccionGanadorData,
        actor=None,
        expected_version=None,
    ) -> CorreccionResult:
        """Correct the winner in a transaction."""
        with transaction.atomic():
            encuentro = self._encuentros.obtener_por_id(encuentro_id)
            competencia = encuentro.ronda.competencia

            # The chain tells which rows must be locked with the origin.
            cadena = self._core.cadena_de(encuentro)
            ids = [encuentro.id] + [destino.id for destino, _ in cadena]

            self._programacion.bloquear_competencia(competencia.id)
            bloqueados = self._programacion.bloquear_encuentros(ids)
            por_id = {bloqueado.id: bloqueado for bloqueado in bloqueados}
            origen = por_id.get(encuentro.id, encuentro)

            return self._core.corregir(
                origen,
                data.ganador_id,
                actor=actor,
                motivo=data.motivo,
                override=data.override,
                acepta_impacto=data.acepta_impacto,
                expected_version=expected_version,
                por_id=por_id,
            )

    async def previsualizar(
        self,
        encuentro_id,
        ganador_nuevo_id,
    ) -> CorreccionPreviewResult:
        """Return the impact of the correction before applying it."""
        return await self._previsualizar(encuentro_id, ganador_nuevo_id)

    async def corregir(
        self,
        encuentro_id,
        data: CorreccionGanadorData,
        actor=None,
        expected_version=None,
    ) -> CorreccionResult:
        """Correct the authoritative winner of the encounter."""
        return await self._corregir_atomico(
            encuentro_id,
            data,
            actor,
            expected_version,
        )
