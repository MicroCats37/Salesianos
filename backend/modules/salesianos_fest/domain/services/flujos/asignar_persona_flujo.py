"""
AsignarPersonaFlujo — async flow for assigning a person to an inscripcion after payment.

Called when:
- User wants to add a new person to an inscripcion that already has paid quota
- The new person needs an AsignacionCupo if saldo disponible > 0

Flow:
1. Check saldo disponible for inscripcion
2. If disponible > 0: create InscripcionPersona + AsignacionCupo
3. If disponible == 0: return error (user must buy more quota first)
4. Sync AcreditacionEvento for the new person

SPEC F3: Agregar 3 personas luego de T02
"""
import logging

from asgiref.sync import sync_to_async
from django.db import transaction

from injector import inject

from modules.salesianos_fest.domain.exceptions import CupoAgotadoError, PersonaYaAsignadaError, FechaLimiteExcedidaError
from modules.salesianos_fest.domain.constants import EstadoAsignacionCupoChoices, EstadoInscripcionPersonaChoices
from modules.salesianos_fest.domain.services.core.asignacion_service import AsignacionCoreService
from modules.salesianos_fest.domain.services.core.acreditacion_service import AcreditacionCoreService
from modules.salesianos_fest.domain.models import InscripcionPersona, Inscripcion

logger = logging.getLogger(__name__)


class AsignarPersonaFlujo:
    """
    Async flow for assigning a new person to an inscripcion after payment.
    """

    @inject
    def __init__(
        self,
        asignacion_core: AsignacionCoreService,
        acreditacion_core: AcreditacionCoreService,
    ):
        self.asignacion_core = asignacion_core
        self.acreditacion_core = acreditacion_core

    def _verificar_fecha_limite(self, inscripcion_id: str) -> None:
        """Verify that modifications are still allowed for this evento."""
        inscripcion = Inscripcion.objects.select_related("evento").get(id=inscripcion_id)
        if not inscripcion.evento.puede_modificar():
            raise FechaLimiteExcedidaError()

    async def _asignar_persona(
        self,
        inscripcion_id: str,
        persona_id: str,
    ) -> dict:
        """
        Assign a person to an inscripcion if saldo disponible > 0.

        Steps:
        1. Check if person is already assigned (active AsignacionCupo)
        2. Calculate saldo disponible
        3. If disponible > 0: create InscripcionPersona + AsignacionCupo
        4. If disponible == 0: raise CupoAgotadoError
        5. Sync AcreditacionEvento
        """
        return await sync_to_async(self._asignar_persona_sync)(inscripcion_id, persona_id)

    @transaction.atomic()
    def _asignar_persona_sync(self, inscripcion_id: str, persona_id: str) -> dict:
        """
        Sync version with transaction.atomic.

        Idempotent: if person already has LIBERADA asignacion, reactivate it.
        """
        from modules.salesianos_fest.domain.models import AsignacionCupo

        # Verify fecha_limite has not been exceeded
        self._verificar_fecha_limite(inscripcion_id)

        # Check existing active asignacion
        existing_activa = self.asignacion_core.obtener_asignacion_activa_por_persona(
            inscripcion_id, persona_id
        )
        if existing_activa:
            raise PersonaYaAsignadaError()

        # Check for LIBERADA asignacion (can be reactivated)
        libereada = (
            AsignacionCupo.objects
            .filter(
                inscripcion_id=inscripcion_id,
                inscripcion_persona__persona_id=persona_id,
                estado=EstadoAsignacionCupoChoices.LIBERADA,
            )
            .select_related("inscripcion_persona")
            .first()
        )

        # Get a compra with available saldo
        compra = self.asignacion_core.obtener_compra_con_saldo_disponible(inscripcion_id)
        if compra is None:
            raise CupoAgotadoError()

        # Get or create InscripcionPersona
        inscripcion_persona = InscripcionPersona.objects.filter(
            inscripcion_id=inscripcion_id,
            persona_id=persona_id,
        ).first()

        if inscripcion_persona is None:
            inscripcion_persona = InscripcionPersona.objects.create(
                inscripcion_id=inscripcion_id,
                persona_id=persona_id,
                estado=EstadoInscripcionPersonaChoices.ACTIVO,
            )
        elif inscripcion_persona.estado != EstadoInscripcionPersonaChoices.ACTIVO:
            inscripcion_persona.estado = EstadoInscripcionPersonaChoices.ACTIVO
            inscripcion_persona.save(update_fields=["estado", "updated_at"])

        # If reactivating LIBERADA asignacion
        if libereada:
            libereada.estado = EstadoAsignacionCupoChoices.ACTIVA
            libereada.compra = compra
            libereada.motivo = None
            libereada.liberada_en = None
            libereada.save(update_fields=["estado", "compra", "motivo", "liberada_en", "updated_at"])
            asignacion = libereada
        else:
            # Create new asignacion
            asignacion = self.asignacion_core.crear_asignacion(
                inscripcion_id=inscripcion_id,
                inscripcion_persona_id=str(inscripcion_persona.id),
                compra=compra,
            )

        # Get evento_id for acreditacion sync
        evento_id = str(Inscripcion.objects.get(id=inscripcion_id).evento_id)

        # Sync AcreditacionEvento
        self.acreditacion_core.sync_acreditacion_desde_compras(
            evento_id=evento_id,
            persona_id=persona_id,
        )

        return {
            "asignacion_id": str(asignacion.id),
            "inscripcion_id": inscripcion_id,
            "persona_id": persona_id,
            "compra_origen_id": str(compra.id),
            "estado": str(asignacion.estado),
        }
