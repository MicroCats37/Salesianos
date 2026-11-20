"""`ResultadoFlujo` — el REGISTRO del resultado autoritativo.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4

El resultado es un HECHO: fija el ganador de un encuentro y lo finaliza. El
ganador lo declara el administrador y NUNCA se deduce del marcador
(`frontend/05` §6).

El comando es idempotente: repetir exactamente el mismo resultado NO escribe
nada. Y es versionado: si el cliente viaja una versión obsoleta, el comando se
rechaza con `RESOURCE_CHANGED` y NO se escribe nada.
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.competencias.domain.models.auditoria import AccionAuditada
from modules.competencias.domain.results.competencias_results import (
    ResultadoRegistradoResult,
)
from modules.competencias.domain.schemas.competencias_schemas import (
    ResultadoEncuentroData,
)
from modules.competencias.domain.services.core.auditoria_core_service import (
    AuditoriaCoreService,
)
from modules.competencias.domain.services.core.resultado_core_service import (
    ResultadoCoreService,
)
from modules.competencias.domain.services.flujos.encuentro_flujo import (
    EncuentroFlujo,
)


class ResultadoFlujo:
    """Caso de uso del registro del resultado de un encuentro."""

    @inject
    def __init__(
        self,
        resultado_core: ResultadoCoreService,
        auditoria_core: AuditoriaCoreService,
        encuentro_flujo: EncuentroFlujo,
    ):
        self.resultado_core = resultado_core
        self.auditoria_core = auditoria_core
        self.encuentro_flujo = encuentro_flujo

    async def registrar(
        self,
        competencia_id,
        encuentro_id,
        data: ResultadoEncuentroData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> ResultadoRegistradoResult:
        """Registra el ganador del encuentro y lo finaliza."""
        encuentro = await sync_to_async(self.encuentro_flujo._obtener_encuentro)(
            competencia_id,
            encuentro_id,
        )
        return await sync_to_async(self._registrar_sync)(
            encuentro,
            data,
            expected_version,
            actor,
        )

    @transaction.atomic()
    def _registrar_sync(self, encuentro, data, expected_version, actor):
        """Registro atómico del resultado y de su acta."""
        estado_antes = encuentro.estado
        version_antes = encuentro.version
        actualizado = self.resultado_core.registrar(
            encuentro,
            data,
            expected_version=expected_version,
            motivo=data.motivo,
        )
        if (
            actualizado.estado == estado_antes
            and actualizado.version == version_antes
        ):
            # Reintento idempotente: no hubo escritura y no hay acta nueva.
            return self._resultado(actualizado)

        ganador = actualizado.ganador
        equipo = getattr(ganador, "equipo", None)
        self.auditoria_core.registrar(
            accion=AccionAuditada.RESULTADO,
            motivo=data.motivo or "Registro del resultado",
            competencia=actualizado.ronda.competencia,
            encuentro=actualizado,
            actor=actor,
            detalle={
                "ganador_equipo_id": str(ganador.equipo_id) if ganador else None,
                "puntaje_1": actualizado.puntaje_1,
                "puntaje_2": actualizado.puntaje_2,
            },
        )
        return self._resultado(actualizado, equipo)

    @staticmethod
    def _resultado(encuentro, equipo=None) -> ResultadoRegistradoResult:
        from modules.competencias.domain.selectors.proyeccion import proyectar_encuentro

        ganador = getattr(encuentro, "ganador", None)
        if equipo is None and ganador is not None:
            equipo = getattr(ganador, "equipo", None)
        return ResultadoRegistradoResult(
            encuentro=proyectar_encuentro(encuentro),
            ganador_equipo_id=str(ganador.equipo_id) if ganador is not None else "",
            ganador_equipo_nombre=equipo.nombre if equipo is not None else "",
        )


__all__ = ["ResultadoFlujo"]
