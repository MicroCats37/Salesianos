"""`BeneficiarioCoreService` — la escritura de los DERECHOS de entrada.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio (la aporta el flujo).

Este servicio es el ÚNICO que escribe derechos de entrada. Las reglas que
aplica:

- **Sólo se asigna capacidad PAGADA** (`RN-P02`): el flujo comprueba el
  estado de la compra antes de llegar aquí.
- **Un derecho NO se duplica** (`RN-P07`): la restricción parcial única
  `(edicion, pase, persona) WHERE estado = 'ACTIVO'` es la autoridad. Este
  servicio traduce esa restricción a una excepción legible.
- **La revocación es PERMANENTE y auditada** (`RN-P08`, `FR-05` §2.3): el
  derecho revocado deja de ser canjeable para validaciones futuras; los
  consumos ya occurring permanecen.

**LO QUE ESTE SERVICIO NO HACE (y no debe hacer nadie en su lugar):**

- **No devuelve el cupo al comprar.** La revocación NO libera la unidad
  ocupada: el derecho revocado sigue contando como unidad consumida del
  lote. Es la lectura más CONSERVADORA de `FR-05` §2.3 ("el slot no se
  devuelve") mientras `PD-02` / `GOV-01-OPEN-08` siguen ABIERTOS: la
  política comercial de reasignación NO se inventa aquí.
- **No reasigna.** Un derecho revocado no se puede volver a otorgar a otra
  persona dentro del mismo lote: la unidad ya está comprometida.
"""

from django.db import IntegrityError
from django.utils import timezone

from modules.salesianos_fest.domain.constants import (
    EstadoDerechoPase,
    OrigenDerechoPase,
)
from modules.salesianos_fest.domain.exceptions import (
    PaseBeneficiarioNoEncontradoError,
    PaseDuplicadoError,
    PaseNoTransferibleError,
)
from modules.salesianos_fest.domain.models import PaseBeneficiario


class BeneficiarioCoreService:
    """Operaciones de persistencia de los derechos de entrada."""

    def asignar(
        self,
        *,
        compra_pase,
        pase,
        persona,
        cantidad: int = 1,
        actor_usuario_id=None,
        actor_persona_id=None,
        motivo: str = "",
    ) -> PaseBeneficiario:
        """Asigna UN pase comprado a una persona.

        Args:
            compra_pase: el lote que financia el derecho.
            pase: el tipo de pase del lote.
            persona: la persona que ASISTE (`RN-P04`).
            cantidad: unidades que concede el derecho.
            actor_usuario_id: cuenta que ejecuta la asignación.
            actor_persona_id: persona que ejecuta la asignación.
            motivo: motivo de la asignación (opcional en una compra).

        Returns:
            El derecho creado.

        Raises:
            PaseDuplicadoError: la persona ya tiene un derecho ACTIVO de ese
                pase en esa edición. La garantía real es la restricción
                única parcial de la base de datos; esta excepción es su
                traducción legible.
        """
        try:
            return PaseBeneficiario.objects.create(
                edicion_id=compra_pase.edicion_id,
                pase_id=pase.id,
                persona_id=persona.id,
                origen=OrigenDerechoPase.COMPRA,
                compra_pase=compra_pase,
                cantidad=cantidad,
                actor_usuario_id=actor_usuario_id,
                actor_persona_id=actor_persona_id,
                motivo=motivo or "",
            )
        except IntegrityError as error:
            # La restricción de la base de datos es la autoridad. Se
            # traduce a un error de dominio legible: el texto crudo de la
            # excepción NUNCA sale al cliente.
            if self._es_conflicto_de_duplicado(error):
                raise PaseDuplicadoError() from error
            raise

    def revocar(
        self,
        *,
        beneficiario: PaseBeneficiario,
        actor_usuario_id=None,
        actor_persona_id=None,
        motivo: str = "",
    ) -> tuple[PaseBeneficiario, bool]:
        """Revoca un derecho de entrada.

        Es IDEMPOTENTE (`FR-05` §2.3): revocar dos veces no es un error; la
        segunda devuelve el estado final con `ya_revocado=True`.

        La revocación es PERMANENTE: el derecho deja de ser canjeable para
        validaciones futuras y los consumos ya occurring permanecen
        (`RN-P08`).

        Args:
            beneficiario: el derecho a revocar.
            actor_usuario_id: cuenta que ejecuta la revocación.
            actor_persona_id: persona que ejecuta la revocación.
            motivo: motivo de la revocación (se conserva en la auditoría).

        Returns:
            La tupla `(derecho, ya_revocado)`.

        Raises:
            PaseNoTransferibleError: el derecho ya estaba revocado en una
                operación que exige que esté ACTIVO.
        """
        if beneficiario.estado == EstadoDerechoPase.REVOCADO:
            return beneficiario, True

        beneficiario.estado = EstadoDerechoPase.REVOCADO
        beneficiario.revocado_en = timezone.now()
        beneficiario.motivo_revocacion = motivo or ""
        if actor_usuario_id is not None:
            beneficiario.actor_usuario_id = actor_usuario_id
        if actor_persona_id is not None:
            beneficiario.actor_persona_id = actor_persona_id
        beneficiario.save(
            update_fields=[
                "estado",
                "revocado_en",
                "motivo_revocacion",
                "actor_usuario",
                "actor_persona",
                "updated_at",
            ]
        )
        return beneficiario, False

    @staticmethod
    def _es_conflicto_de_duplicado(error: IntegrityError) -> bool:
        """Si el `IntegrityError` es la restricción de no duplicar el derecho.

        La traducción es INTENCIONAL y conservadora: mira el nombre de la
        restricción, no el texto de la excepción (que puede variar entre
        motores). Si el conflicto es de otro tipo, la excepción se propaga
        sin翻译: un error de integridad que no es de duplicado NO se
        disfraza de duplicado.
        """
       约束 = "fest_pase_beneficiario"
        texto = str(error).lower()
        return (
            "unique" in texto
            and "pase_beneficiario" in texto
            and 约束 in texto
        )


__all__ = ["BeneficiarioCoreService"]
