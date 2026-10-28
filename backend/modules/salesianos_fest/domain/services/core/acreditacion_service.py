"""
AcreditacionCoreService — sync core operations for AcreditacionEvento.

Core service — no transaction.atomic own, no async.
Operations that touch the DB are here; atomicity is provided by the caller flujo.
"""
from injector import inject

from modules.salesianos_fest.domain.models import (
    AcreditacionEvento,
    AsignacionCupo,
    Inscripcion,
)
from modules.commerce.domain.models import Compra
from modules.salesianos_fest.domain.constants import (
    EstadoAcreditacionChoices,
    AutorizacionFiestaChoices,
    EstadoAsignacionCupoChoices,
    EstadoCompraChoices,
)


class AcreditacionCoreService:
    """
    Core sync service for AcreditacionEvento operations.

    Handles:
    - AcreditacionEvento creation and sync
    - Override management
    - QR code generation
    """

    @inject
    def __init__(self):
        pass

    def obtener_o_crear_acreditacion(
        self,
        evento_id: str,
        persona_id: str,
    ) -> tuple[AcreditacionEvento, bool]:
        """
        Get or create an AcreditacionEvento for (evento, persona).

        Returns (acreditacion, created).
        """
        acreditacion, created = AcreditacionEvento.objects.get_or_create(
            evento_id=evento_id,
            persona_id=persona_id,
            defaults={
                "estado": EstadoAcreditacionChoices.PENDIENTE,
                "acceso_fiesta": False,
                "autorizacion_fiesta": AutorizacionFiestaChoices.AUTOMATICA,
            },
        )
        return acreditacion, created

    def sync_acreditacion_desde_compras(
        self,
        evento_id: str,
        persona_id: str,
    ) -> AcreditacionEvento:
        """
        Recalculate acceso_fiesta based on all paid compras across inscriptions.

        Called when:
        - A purchase is confirmed (Ampliacion)
        - A player is retired
        - An admin override changes
        - A pass beneficiary is assigned or revoked

        Override rules:
        - BLOQUEADA: acceso_fiesta = False regardless of other origins
        - AUTORIZADA: acceso_fiesta = True
        - AUTOMATICA: acceso_fiesta = derived from paid compras with FIESTA
          benefit OR from an ACTIVE pass entitlement of a PAID pass purchase

        The pass is only ONE MORE SOURCE of fiesta access: it never grants
        `acceso_box` and it never touches the administrative overrides.
        """
        from modules.salesianos_fest.domain.models import PaqueteBeneficio
        from modules.salesianos_fest.domain.constants import TipoBeneficioChoices

        acreditacion, _ = self.obtener_o_crear_acreditacion(evento_id, persona_id)

        # If admin override is BLOQUEADA, never grant access
        if acreditacion.autorizacion_fiesta == AutorizacionFiestaChoices.BLOQUEADA:
            acreditacion.acceso_fiesta = False
            acreditacion.estado = EstadoAcreditacionChoices.ACTIVA
            acreditacion.save(update_fields=["acceso_fiesta", "estado", "updated_at"])
            return acreditacion

        # If admin override is AUTORIZADA, always grant access
        if acreditacion.autorizacion_fiesta == AutorizacionFiestaChoices.AUTORIZADA:
            acreditacion.acceso_fiesta = True
            acreditacion.estado = EstadoAcreditacionChoices.ACTIVA
            acreditacion.save(update_fields=["acceso_fiesta", "estado", "updated_at"])
            return acreditacion

        # AUTOMATICA: derive from paid compras with FIESTA benefit
        # Find all inscriptions for this evento where persona has active asignaciones
        asignaciones = (
            AsignacionCupo.objects
            .filter(
                inscripcion_persona__persona_id=persona_id,
                inscripcion__evento_id=evento_id,
                estado=EstadoAsignacionCupoChoices.ACTIVA,
                compra__estado=EstadoCompraChoices.PAGADA,
            )
            .select_related("compra", "inscripcion", "inscripcion__paquete")
        )

        # Check if any active asignacion comes from a compra whose paquete has FIESTA benefit
        acceso_fiesta = False
        for asignacion in asignaciones:
            paquete = asignacion.inscripcion.paquete
            if paquete.tipo == "PACK":
                # Check if the paquete has FIESTA benefit
                tiene_fiesta = PaqueteBeneficio.objects.filter(
                    paquete=paquete,
                    tipo=TipoBeneficioChoices.FIESTA,
                ).exists()
                if tiene_fiesta:
                    acceso_fiesta = True
                    break

        # Also check if the person has any paid Ampliacion with FIESTA
        if not acceso_fiesta:
            # Check all inscripciones for this event where this persona has asignaciones
            inscripcion_ids = asignaciones.values_list("inscripcion_id", flat=True)
            for inscripcion_id in inscripcion_ids:
                paquete = Inscripcion.objects.get(id=inscripcion_id).paquete
                if paquete.tipo == "PACK":
                    tiene_fiesta = PaqueteBeneficio.objects.filter(
                        paquete=paquete,
                        tipo=TipoBeneficioChoices.FIESTA,
                    ).exists()
                    if tiene_fiesta:
                        acceso_fiesta = True
                        break

        # A PASS entitlement of a PAID pass purchase is the SECOND source of
        # fiesta access. It is additive: revoking it only removes THIS source
        # (a sports benefit or an AUTORIZADA override may keep the access).
        if not acceso_fiesta:
            acceso_fiesta = self.tiene_pase_activo(evento_id, persona_id)

        acreditacion.acceso_fiesta = acceso_fiesta
        acreditacion.estado = (
            EstadoAcreditacionChoices.ACTIVA if acceso_fiesta
            else EstadoAcreditacionChoices.PENDIENTE
        )
        acreditacion.save(update_fields=["acceso_fiesta", "estado", "updated_at"])
        return acreditacion

    def tiene_pase_activo(self, evento_id: str, persona_id: str) -> bool:
        """
        Return True when the person holds an ACTIVE pass of a PAID purchase.

        The pass is a source of FIESTA access only: it never says anything
        about `acceso_box`.
        """
        from modules.salesianos_fest.domain.constants import (
            EstadoPaseBeneficiarioChoices,
        )
        from modules.salesianos_fest.domain.models import PaseBeneficiario

        return (
            PaseBeneficiario.objects
            .filter(
                evento_id=evento_id,
                persona_id=persona_id,
                estado=EstadoPaseBeneficiarioChoices.ACTIVA,
                compra_pase__compra__estado=EstadoCompraChoices.PAGADA,
            )
            .exists()
        )

    def aplicar_override_fiesta(
        self,
        acreditacion: AcreditacionEvento,
        autorizacion: str,
        motivo: str,
    ) -> AcreditacionEvento:
        """
        Apply admin override for fiesta access.

        The override persists and takes precedence over AUTOMATICA.
        """
        acreditacion.autorizacion_fiesta = autorizacion
        if motivo:
            existing = acreditacion.observacion
            acreditacion.observacion = (
                f"{existing}\n[Override {autorizacion}]: {motivo}"
            ).strip()

        # Recalculate based on new override
        if autorizacion == AutorizacionFiestaChoices.BLOQUEADA:
            acreditacion.acceso_fiesta = False
        elif autorizacion == AutorizacionFiestaChoices.AUTORIZADA:
            acreditacion.acceso_fiesta = True

        acreditacion.save(
            update_fields=[
                "autorizacion_fiesta",
                "acceso_fiesta",
                "observacion",
                "updated_at",
            ]
        )
        return acreditacion

    def obtener_acreditacion_por_evento_persona(
        self,
        evento_id: str,
        persona_id: str,
    ) -> AcreditacionEvento | None:
        """Get AcreditacionEvento by evento and persona."""
        return (
            AcreditacionEvento.objects
            .select_related("evento", "persona")
            .filter(evento_id=evento_id, persona_id=persona_id)
            .first()
        )

    def obtener_acreditacion_por_id(
        self,
        acreditacion_id: str,
    ) -> AcreditacionEvento | None:
        """Get AcreditacionEvento by ID."""
        return (
            AcreditacionEvento.objects
            .select_related("evento", "persona")
            .filter(id=acreditacion_id)
            .first()
        )

    def obtener_acreditacion_por_qr(
        self,
        qr_token: str,
    ) -> AcreditacionEvento | None:
        """Get AcreditacionEvento by QR code."""
        import uuid
        try:
            uuid_val = uuid.UUID(qr_token)
        except (ValueError, AttributeError):
            return None
        return (
            AcreditacionEvento.objects
            .select_related("evento", "persona")
            .filter(codigo_qr=uuid_val)
            .first()
        )

    def regenarar_qr(
        self,
        acreditacion: AcreditacionEvento,
    ) -> AcreditacionEvento:
        """Regenerate the QR code for an acreditacion."""
        import uuid
        acreditacion.codigo_qr = uuid.uuid4()
        acreditacion.save(update_fields=["codigo_qr", "updated_at"])
        return acreditacion

    def validar_acceso_fiesta(
        self,
        acreditacion: AcreditacionEvento,
    ) -> bool:
        """
        Validate if acceso_fiesta is effective.

        Rules:
        - If habilitado=False, always deny
        - If estado=REVOCADA, always deny
        - Otherwise check acceso_fiesta
        """
        if acreditacion.habilitado is False:
            return False
        if acreditacion.estado == EstadoAcreditacionChoices.REVOCADA:
            return False
        return acreditacion.acceso_fiesta

    def obtener_acreditaciones_por_evento(
        self,
        evento_id: str,
    ) -> list[AcreditacionEvento]:
        """List all acreditaciones for an event."""
        return list(
            AcreditacionEvento.objects
            .select_related("persona")
            .filter(evento_id=evento_id)
            .order_by("persona__nombres", "persona__apellidos")
        )
