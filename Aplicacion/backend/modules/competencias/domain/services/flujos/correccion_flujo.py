"""`CorreccionFlujo` — la VISTA PREVIA y la APLICACIÓN de la corrección.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4

`QA-K03`: "Preview de impacto y confirmación sin cascada oculta".

**La previa es una SIMULACIÓN**: calcula el plan de la corrección y publica
el impacto sobre cada descendiente. NO escribe nada.

**La aplicación** escribe el ganador nuevo, limpia el marcador que lo
contradecía y propaga el cambio por la cadena. Si un descendiente YA
transcurrió, la cascada está BLOQUEADA: sin `override` explícito Y la
aceptación del impacto calculado, NO se escribe NADA (`DESTINO_BLOQUEADO`).

**El motivo es obligatorio** (`MOTIVO_REQUERIDO`): una corrección es una
decisión administrativa y queda auditada (`RN-K02`).
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.competencias.domain.models.auditoria import AccionAuditada
from modules.competencias.domain.results.competencias_results import (
    CorreccionPreviewResult,
    CorreccionResult,
)
from modules.competencias.domain.schemas.competencias_schemas import CorreccionData
from modules.competencias.domain.services.core.auditoria_core_service import (
    AuditoriaCoreService,
)
from modules.competencias.domain.services.core.correccion_core_service import (
    CorreccionCoreService,
)
from modules.competencias.domain.services.flujos.encuentro_flujo import (
    EncuentroFlujo,
)


class CorreccionFlujo:
    """Casos de uso de la corrección del resultado de un encuentro."""

    @inject
    def __init__(
        self,
        correccion_core: CorreccionCoreService,
        auditoria_core: AuditoriaCoreService,
        encuentro_flujo: EncuentroFlujo,
    ):
        self.correccion_core = correccion_core
        self.auditoria_core = auditoria_core
        self.encuentro_flujo = encuentro_flujo

    async def previsualizar(
        self,
        competencia_id,
        encuentro_id,
        ganador_nuevo_id,
    ) -> CorreccionPreviewResult:
        """El IMPACTO de la corrección. NO escribe NADA."""
        encuentro = await sync_to_async(self.encuentro_flujo._obtener_encuentro)(
            competencia_id,
            encuentro_id,
        )
        return await sync_to_async(self.correccion_core.previsualizar)(
            encuentro,
            ganador_nuevo_id,
        )

    async def corregir(
        self,
        competencia_id,
        encuentro_id,
        data: CorreccionData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> CorreccionResult:
        """Aplica la corrección con su impacto explícito."""
        encuentro = await sync_to_async(self.encuentro_flujo._obtener_encuentro)(
            competencia_id,
            encuentro_id,
        )
        return await sync_to_async(self._corregir_sync)(
            encuentro,
            data,
            expected_version,
            actor,
        )

    @transaction.atomic()
    def _corregir_sync(self, encuentro, data, expected_version, actor):
        """Corrección atómica y su acta."""
        ganador_antes = (
            str(encuentro.ganador_id) if encuentro.ganador_id else None
        )
        version_antes = encuentro.version
        resultado = self.correccion_core.corregir(
            encuentro,
            data.ganador_id,
            expected_version=expected_version,
            motivo=data.motivo,
            override=bool(data.override),
            acepta_impacto=bool(data.acepta_impacto),
        )
        ganador_despues = (
            str(encuentro.ganador_id) if encuentro.ganador_id else None
        )
        if ganador_antes == ganador_despues and encuentro.version == version_antes:
            # Reintento idempotente: el ganador ya era el indicado.
            return resultado

        self.auditoria_core.registrar(
            accion=AccionAuditada.CORRECCION,
            motivo=data.motivo or "Corrección del resultado",
            competencia=encuentro.ronda.competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={
                "ganador_antes": ganador_antes,
                "ganador_despues": ganador_despues,
                "descendientes_afectados": resultado.descendientes_afectados,
                "override": bool(data.override),
            },
        )
        return resultado


__all__ = ["CorreccionFlujo"]
