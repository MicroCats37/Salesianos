"""`AvanceFlujo` — la VISTA PREVIA y la CONFIRMACIÓN del avance.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.4

`QA-K04`: "Advance preview no escribe; confirm sí".

**La previa es una SIMULACIÓN.** No abre transacción, no escribe y no
invierte la versión de nada: sólo lee el enlace, el ganador, el slot de
destino y su ocupante actual, y dice si la cascada está bloqueada.

**La confirmación es la que escribe**, dentro de su propia atomicidad, con su
motivo auditado y con el bloqueo optimista.

**Un destino que YA transcurrió bloquea la cascada**: la confirmación falla
con `DESTINO_BLOQUEADO` y NADA se escribe. El backend no propaga en silencio
(`frontend/05` §6).
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.competencias.domain.models.auditoria import AccionAuditada
from modules.competencias.domain.results.competencias_results import (
    AvancePreviewResult,
    AvanceResult,
)
from modules.competencias.domain.schemas.competencias_schemas import AvanceData
from modules.competencias.domain.services.core.auditoria_core_service import (
    AuditoriaCoreService,
)
from modules.competencias.domain.services.core.avance_core_service import (
    AvanceCoreService,
)
from modules.competencias.domain.services.flujos.encuentro_flujo import (
    EncuentroFlujo,
)


class AvanceFlujo:
    """Casos de uso del avance del ganador a la ronda siguiente."""

    @inject
    def __init__(
        self,
        avance_core: AvanceCoreService,
        auditoria_core: AuditoriaCoreService,
        encuentro_flujo: EncuentroFlujo,
    ):
        self.avance_core = avance_core
        self.auditoria_core = auditoria_core
        self.encuentro_flujo = encuentro_flujo

    async def previsualizar(
        self,
        competencia_id,
        encuentro_id,
    ) -> AvancePreviewResult:
        """La PROPUESTA de la propagación. NO escribe NADA."""
        encuentro = await sync_to_async(self.encuentro_flujo._obtener_encuentro)(
            competencia_id,
            encuentro_id,
        )
        return await sync_to_async(self.avance_core.previsualizar)(encuentro)

    async def confirmar(
        self,
        competencia_id,
        encuentro_id,
        data: AvanceData,
        *,
        expected_version: int | None,
        actor=None,
    ) -> AvanceResult:
        """Confirma la propagación del ganador al encuentro de destino."""
        encuentro = await sync_to_async(self.encuentro_flujo._obtener_encuentro)(
            competencia_id,
            encuentro_id,
        )
        return await sync_to_async(self._confirmar_sync)(
            encuentro,
            data,
            expected_version,
            actor,
        )

    @transaction.atomic()
    def _confirmar_sync(self, encuentro, data, expected_version, actor):
        """Confirmación atómica del avance y de su acta."""
        destino = self.avance_core.destino_de(encuentro)
        resultado = self.avance_core.confirmar(
            encuentro,
            destino,
            expected_version=expected_version,
            motivo=data.motivo,
        )
        if resultado.ya_aplicado:
            # Reintento idempotente: el avance ya estaba aplicado.
            return resultado
        self.auditoria_core.registrar(
            accion=AccionAuditada.AVANCE,
            motivo=data.motivo or "Avance confirmado",
            competencia=encuentro.ronda.competencia,
            encuentro=encuentro,
            actor=actor,
            detalle={
                "siguiente_encuentro_id": str(destino.id),
                "slot_destino": encuentro.slot_destino,
                "ganador_equipo_id": resultado.ganador_equipo_id,
            },
        )
        return resultado


__all__ = ["AvanceFlujo"]
