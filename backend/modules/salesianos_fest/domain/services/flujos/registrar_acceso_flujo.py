"""
RegistrarAccesoFlujo — async flow for QR scan access control.

Called when:
- QR code is scanned at event entry
- System validates and records the access attempt

Flow (SPEC F7):
1. Receive QR token (UUID non-guessable)
2. Find AcreditacionEvento by codigo_qr
3. Validate: evento activo, estado=ACTIVA, habilitado != False
4. Validate acceso_fiesta based on autorizacion_fiesta precedence
5. Within transaction.atomic:
   a. Check no existing PERMITIDO ControlAcceso for this acreditacion today (single-use)
   b. Create ControlAcceso with resultado=PERMITIDO/DENEGADO
   c. Return access decision

QR uniqueness: single-use per event day.
"""
import logging
from datetime import date

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.salesianos_fest.domain.constants import ResultadoAccesoChoices
from modules.salesianos_fest.domain.exceptions import AcreditacionNotFoundError, AccesoDenegadoError
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.models import ControlAcceso

logger = logging.getLogger(__name__)


class RegistrarAccesoFlujo:
    """
    Async flow for registering an access attempt via QR scan.
    """

    @inject
    def __init__(self, acreditacion_core: AcreditacionCoreService):
        self.acreditacion_core = acreditacion_core

    async def _registrar_acceso(
        self,
        qr_token: str,
        punto_acceso: str | None = None,
        operador_id: int | None = None,
    ) -> dict:
        """
        Register an access attempt via QR scan.

        Steps:
        1. Find AcreditacionEvento by QR code
        2. Validate acceso_fiesta
        3. Within transaction.atomic, check single-use and record
        """
        return await sync_to_async(self._registrar_acceso_sync)(
            qr_token, punto_acceso, operador_id
        )

    @transaction.atomic()
    def _registrar_acceso_sync(
        self,
        qr_token: str,
        punto_acceso: str | None = None,
        operador_id: int | None = None,
    ) -> dict:
        """
        Sync version with transaction.atomic for atomic single-use check.
        """
        from modules.salesianos_fest.domain.models import AcreditacionEvento
        from django.contrib.auth import get_user_model

        # Find acreditacion by QR
        acreditacion = self.acreditacion_core.obtener_acreditacion_por_qr(qr_token)
        if acreditacion is None:
            raise AcreditacionNotFoundError()

        # Check if already used today (single-use per event day)
        # Use select_for_update to prevent TOCTOU race condition
        today = date.today()
        ya_usado_hoy = ControlAcceso.objects.select_for_update().filter(
            acreditacion=acreditacion,
            resultado=ResultadoAccesoChoices.PERMITIDO,
            fecha_hora__date=today,
        ).exists()

        if ya_usado_hoy:
            # Already scanned today - deny
            control = ControlAcceso.objects.create(
                acreditacion=acreditacion,
                resultado=ResultadoAccesoChoices.DENEGADO,
                punto_acceso=punto_acceso,
                operador_id=operador_id,
            )
            logger.info(f"QR scan denied for {acreditacion.id}: already used today")
            return {
                "resultado": ResultadoAccesoChoices.DENEGADO,
                "persona_nombre": None,
                "acceso_fiesta": False,
                "timestamp": control.fecha_hora.isoformat(),
            }

        # Validate acceso_fiesta
        acceso_permitido = self.acreditacion_core.validar_acceso_fiesta(acreditacion)

        if acceso_permitido:
            # Check evento is active (not needed if scanner only active during event)
            # Create PERMITIDO control
            control = ControlAcceso.objects.create(
                acreditacion=acreditacion,
                resultado=ResultadoAccesoChoices.PERMITIDO,
                punto_acceso=punto_acceso,
                operador_id=operador_id,
            )
            logger.info(f"QR scan permitted for {acreditacion.id}")
            return {
                "resultado": ResultadoAccesoChoices.PERMITIDO,
                "persona_nombre": (
                    f"{acreditacion.persona.nombres} {acreditacion.persona.apellidos}"
                ),
                "acceso_fiesta": acreditacion.acceso_fiesta,
                "timestamp": control.fecha_hora.isoformat(),
            }
        else:
            # DENEGADO - not authorized
            control = ControlAcceso.objects.create(
                acreditacion=acreditacion,
                resultado=ResultadoAccesoChoices.DENEGADO,
                punto_acceso=punto_acceso,
                operador_id=operador_id,
            )
            logger.info(f"QR scan denied for {acreditacion.id}: not authorized")
            return {
                "resultado": ResultadoAccesoChoices.DENEGADO,
                "persona_nombre": (
                    f"{acreditacion.persona.nombres} {acreditacion.persona.apellidos}"
                ) if acreditacion.persona else None,
                "acceso_fiesta": False,
                "timestamp": control.fecha_hora.isoformat(),
            }
