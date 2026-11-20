"""`CortesiaCoreService` — el ACTA auditada de una cortesía.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio (la aporta el flujo).

Una cortesía es un DERECHO GRATUITO y AUDITADO (`RN-P05`, `FL-07`):

- **No hay cobro de S/ 0** (`RN-P05`): este servicio no toca `commerce` ni
  `pagos`. El modelo `CortesiaPase` no tiene ninguna columna que lo enlace
  con una compra, una orden o una transacción: la AUSENCIA del enlace es la
  garantía estructural, no una convención.
- **Hay actor, fecha y motivo** (`RN-P05`, `FL-07` paso 2): sin actor no hay
  auditoría, y sin motivo el derecho no se registra.
- **Se puede invalidar conservando el historial** (`FL-07` paso 4): la
  revocación cambia el estado del acta; el acta no se borra.
"""

from django.utils import timezone

from modules.salesianos_fest.domain.constants import (
    EstadoCortesiaPase,
    EstadoDerechoPase,
    OrigenDerechoPase,
)
from modules.salesianos_fest.domain.models import (
    CortesiaPase,
    PaseBeneficiario,
)


class CortesiaCoreService:
    """Operaciones de persistencia de las cortesías."""

    def crear(
        self,
        *,
        edicion_id,
        pase,
        persona,
        motivo: str,
        actor_usuario_id=None,
        actor_persona_id=None,
    ) -> tuple[CortesiaPase, PaseBeneficiario]:
        """Crea el acta de cortesía y su DERECHO.

        El derecho se crea en la MISMA operación atómica que el acta: un
        acta sin derecho no sirve de nada, y un derecho sin acta no es
        auditable.

        Args:
            edicion_id: edición del alcance.
            pase: tipo de pase que se otorga.
            persona: persona que recibe la cortesía.
            motivo: motivo del otorgamiento (obligatorio).
            actor_usuario_id: cuenta que otorga la cortesía.
            actor_persona_id: persona que otorga la cortesía.

        Returns:
            La tupla `(acta, derecho)`.

        Raises:
            IntegrityError: la persona ya tiene un derecho ACTIVO de ese
                pase en esa edición. La cortesía NO puede duplicar una
                compra, ni al revés. El FLUJO traduce ese `IntegrityError`
                a `PaseDuplicadoError` FUERA de la transacción.
        """
        cortesia = CortesiaPase.objects.create(
            edicion_id=edicion_id,
            pase_id=pase.id,
            persona_id=persona.id,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
            motivo=motivo,
            estado=EstadoCortesiaPase.ACTIVA,
        )
        derecho = PaseBeneficiario.objects.create(
            edicion_id=edicion_id,
            pase_id=pase.id,
            persona_id=persona.id,
            origen=OrigenDerechoPase.CORTESIA,
            cortesia=cortesia,
            cantidad=1,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
            motivo=motivo,
        )
        return cortesia, derecho

    @staticmethod
    def revocar(
        *,
        cortesia: CortesiaPase,
        actor_usuario_id=None,
        actor_persona_id=None,
        motivo: str = "",
    ) -> tuple[CortesiaPase, bool]:
        """Revoca la cortesía y su derecho.

        Deja HISTORIAL: el acta permanece con su estado `REVOCADA`, su actor
        y su motivo (`FL-07` paso 4). Los consumos ya occurring del derecho
        permanecen (`RN-P08`).

        Returns:
            La tupla `(acta, ya_revocada)`.
        """
        if cortesia.estado == EstadoCortesiaPase.REVOCADA:
            return cortesia, True

        ahora = timezone.now()
        cortesia.estado = EstadoCortesiaPase.REVOCADA
        cortesia.revocado_en = ahora
        cortesia.motivo_revocacion = motivo or ""
        cortesia.save(
            update_fields=[
                "estado",
                "revocado_en",
                "motivo_revocacion",
                "updated_at",
            ]
        )

        derechos = PaseBeneficiario.objects.filter(
            cortesia=cortesia,
            estado=EstadoDerechoPase.ACTIVO,
        )
        for derecho in derechos:
            derecho.estado = EstadoDerechoPase.REVOCADO
            derecho.revocado_en = ahora
            derecho.motivo_revocacion = motivo or ""
            if actor_usuario_id is not None:
                derecho.actor_usuario_id = actor_usuario_id
            if actor_persona_id is not None:
                derecho.actor_persona_id = actor_persona_id
            derecho.save(
                update_fields=[
                    "estado",
                    "revocado_en",
                    "motivo_revocacion",
                    "actor_usuario",
                    "actor_persona",
                    "updated_at",
                ]
            )
        return cortesia, False


__all__ = ["CortesiaCoreService"]
