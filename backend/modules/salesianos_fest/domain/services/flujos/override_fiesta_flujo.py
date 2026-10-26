"""
OverrideFiestaFlujo — async flow for admin fiesta override.

Called when:
- Admin wants to allow fiesta to someone who only bought sport
- Admin wants to block fiesta from someone who paid

Flow (SPEC R13, F6):
1. Admin sets autorizacion_fiesta = AUTORIZADA or BLOQUEADA
2. System recalculates effective acceso_fiesta:
   - If BLOQUEADA: acceso_fiesta = False regardless of other origins
   - If AUTORIZADA: acceso_fiesta = True
   - If AUTOMATICA: acceso_fiesta = derived from paid compras with FIESTA benefit
3. Audit log: autor, motivo, timestamp stored in observacion field
4. Override is NOT cleared on next sync
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.salesianos_fest.domain.constants import AutorizacionFiestaChoices
from modules.salesianos_fest.domain.exceptions import AcreditacionNotFoundError
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService

logger = logging.getLogger(__name__)


class OverrideFiestaFlujo:
    """
    Async flow for admin fiesta override.
    """

    @inject
    def __init__(self, acreditacion_core: AcreditacionCoreService):
        self.acreditacion_core = acreditacion_core

    async def _aplicar_override(
        self,
        evento_id: str,
        persona_id: str,
        autorizacion: str,
        motivo: str,
    ) -> dict:
        """
        Apply admin override for fiesta access.

        Steps:
        1. Get or create AcreditacionEvento
        2. Apply override
        3. Recalculate effective acceso_fiesta based on precedence
        """
        return await sync_to_async(self._aplicar_override_sync)(
            evento_id, persona_id, autorizacion, motivo
        )

    @transaction.atomic()
    def _aplicar_override_sync(
        self,
        evento_id: str,
        persona_id: str,
        autorizacion: str,
        motivo: str,
    ) -> dict:
        """
        Sync version with transaction.atomic.
        """
        if autorizacion not in [
            AutorizacionFiestaChoices.AUTORIZADA,
            AutorizacionFiestaChoices.BLOQUEADA,
        ]:
            raise ValueError(f"Invalid autorizacion: {autorizacion}")

        # Get or create acreditacion
        acreditacion = self.acreditacion_core.obtener_acreditacion_por_evento_persona(
            evento_id, persona_id
        )
        if acreditacion is None:
            # Create it with the override
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            acreditacion = self.acreditacion_core.obtener_o_crear_acreditacion(
                evento_id, persona_id
            )[0]
            if acreditacion.observacion:
                existing = acreditacion.observacion
            else:
                existing = ""
            acreditacion.observacion = (
                f"{existing}\n[Override {autorizacion} {timestamp}]: {motivo}"
            ).strip()

        # Apply override via core service
        acreditacion = self.acreditacion_core.aplicar_override_fiesta(
            acreditacion,
            autorizacion,
            f"[Admin Override]: {motivo}",
        )

        return {
            "persona_id": persona_id,
            "evento_id": evento_id,
            "autorizacion_fiesta": str(acreditacion.autorizacion_fiesta),
            "acceso_fiesta": acreditacion.acceso_fiesta,
            "observacion": str(acreditacion.observacion or ""),
        }
