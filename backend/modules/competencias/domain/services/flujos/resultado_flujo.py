"""
ResultadoFlujo — async flow of the authoritative result of an encounter.

The flow owns the atomicity of the command (contract §4.4) and it locks the
encounter before writing it. The core service owns the rules: the winner is
authoritative, the scores are optional and informative, and the complete
intention is compared BEFORE the version so an exact replay writes nothing.
"""
from asgiref.sync import sync_to_async
from django.db import transaction

from ...results.competencias_results import EncuentroResult
from ...schemas.competencias_schemas import ResultadoEncuentroData
from ..core.encuentro_service import EncuentroCoreService
from ..core.programacion_service import ProgramacionCoreService
from ..core.resultado_service import ResultadoCoreService


class ResultadoFlujo:
    """Async flow of the result of the encounters."""

    def __init__(
        self,
        resultado_core: ResultadoCoreService,
        encuentro_core: EncuentroCoreService,
        programacion_core: ProgramacionCoreService,
    ):
        self._core = resultado_core
        self._encuentros = encuentro_core
        self._programacion = programacion_core

    @sync_to_async
    def _registrar_atomico(
        self,
        encuentro_id,
        data: ResultadoEncuentroData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Register the winner in a transaction."""
        with transaction.atomic():
            bloqueados = self._programacion.bloquear_encuentros([encuentro_id])
            encuentro = bloqueados[0] if bloqueados else None
            if encuentro is None:
                encuentro = self._encuentros.obtener_por_id(encuentro_id)
            actualizado = self._core.registrar_resultado(
                encuentro,
                data,
                actor=actor,
                motivo=motivo,
                expected_version=expected_version,
            )
            return EncuentroResult.desde(actualizado)

    async def registrar_resultado(
        self,
        encuentro_id,
        data: ResultadoEncuentroData,
        actor=None,
        motivo=None,
        expected_version=None,
    ) -> EncuentroResult:
        """Register the authoritative winner of the encounter."""
        return await self._registrar_atomico(
            encuentro_id,
            data,
            actor,
            motivo,
            expected_version,
        )
