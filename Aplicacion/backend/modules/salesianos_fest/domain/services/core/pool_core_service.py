"""`PoolCoreService` — la escritura de las participaciones del pool.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio.

Retirar una participación NO la borra: la pasa a `RETIRADA` y conserva su
historia. Retirar libera el cupo de esa inscripción, pero NO toca la compra,
NO devuelve dinero y NO altera el inventario (`RN-I04`, `DEC-06`).
"""

from django.utils import timezone

from modules.salesianos_fest.domain.constants import EstadoParticipacion
from modules.salesianos_fest.domain.models import Participacion


class PoolCoreService:
    """Operaciones de persistencia de las participaciones."""

    def crear_participacion(
        self,
        *,
        inscripcion,
        persona,
        equipo,
        rol: str,
    ) -> Participacion:
        """Crea la participación ACTIVA de una persona en un equipo.

        Los campos `edicion` y `disciplina` se COPIAN de la inscripción y
        del equipo: son los que hacen posible la restricción de
        solapamiento sin JOIN.

        Args:
            inscripcion: la inscripción que aporta la edición.
            persona: la persona que participa.
            equipo: el equipo dentro de la inscripción.
            rol: el rol de la persona en el equipo.

        Returns:
            La participación creada.
        """
        return Participacion.objects.create(
            inscripcion=inscripcion,
            persona=persona,
            equipo=equipo,
            edicion_id=inscripcion.edicion_id,
            disciplina_id=equipo.disciplina_id,
            rol=rol,
            estado=EstadoParticipacion.ACTIVA,
        )

    def retirar_participacion(
        self,
        participacion: Participacion,
        *,
        motivo: str = "",
    ) -> Participacion:
        """Retira la participación: deja de ocupar cupo, sin borrar nada.

        Args:
            participacion: la participación a retirar.
            motivo: motivo técnico de la retirada. No sale al cliente.

        Returns:
            La participación retirada.
        """
        participacion.estado = EstadoParticipacion.RETIRADA
        participacion.motivo = motivo or ""
        participacion.retirada_en = timezone.now()
        participacion.save(
            update_fields=["estado", "motivo", "retirada_en", "updated_at"]
        )
        return participacion


__all__ = ["PoolCoreService"]
