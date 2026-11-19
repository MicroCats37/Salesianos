"""`BeneficioCoreService` — la concesión efectiva de los beneficios del paquete.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio.

`PaqueteBeneficio` DECLARA lo que el paquete ofrece (`RN-P01`); este servicio
registra lo que se CONCEDIÓ, ligado a la activación de derechos.

**Qué regla está CERRADA y cuál NO (`RN-I06`, `PD-09`):**

| Tipo | Regla | Estado |
|---|---|---|
| `FIJO_INICIAL` | se concede UNA vez por inscripción, en la activación del ALTA | **CERRADA** — la implementa este servicio |
| `POR_CUPO` | se concede por cupo comprado | **ABIERTA** (`PD-09`) — este módulo NO concede y NO inventa la regla |

La regla `POR_CUPO` sigue abierta porque ningún contrato congela cómo se
reparte (¿uno por cupo? ¿con mínimo? ¿con tope?). Conceder sin regla sería
INVENTAR un derecho con dinero detrás, así que el módulo no lo hace: la
concesión queda explícitamente PENDIENTE y el model's `BeneficioConcedido`
acepta la acumulación de `cantidad` para cuando la regla se cierre.

La no duplicación del beneficio `FIJO_INICIAL` NO depende de este servicio:
la garantiza la restricción única `(inscripcion, beneficio)` de la base de
datos. El servicio sólo se asegura de NO mandar dos veces la misma concesión.
"""

from modules.salesianos_fest.domain.constants import TipoBeneficioPaquete
from modules.salesianos_fest.domain.models import BeneficioConcedido, PaqueteBeneficio


class BeneficioCoreService:
    """Operaciones de concesión de beneficios de paquete."""

    def beneficios_fijo_inicial(self, inscripcion) -> list[PaqueteBeneficio]:
        """Los beneficios `FIJO_INICIAL` que ofrece el paquete de la inscripción.

        Los beneficios `POR_CUPO` NO entran aquí: su regla de reparto sigue
        ABIERTA (`PD-09`) y concederlos sin regla sería inventar un derecho.
        """
        return list(
            PaqueteBeneficio.objects.filter(
                paquete_id=inscripcion.paquete_id,
                tipo=TipoBeneficioPaquete.FIJO_INICIAL,
            ).order_by("codigo")
        )

    def conceder_fijo_inicial(self, inscripcion, activacion) -> list[BeneficioConcedido]:
        """Concede los beneficios `FIJO_INICIAL` del paquete, UNA vez por inscripción.

        Es idempotente: si la concesión ya existe (la restricción única de
        la base de datos lo garantiza), se conserva la fila original y no se
        crea otra. Una AMPLIACIÓN vuelve a llamar a este servicio y NO
        duplica nada (`RN-I06`).

        Args:
            inscripcion: la inscripción que recibe la concesión.
            activacion: la activación que la justifica.

        Returns:
            Las concesiones vigentes de esos beneficios.
        """
        concedidas: list[BeneficioConcedido] = []
        for beneficio in self.beneficios_fijo_inicial(inscripcion):
            concesion, _creada = BeneficioConcedido.objects.get_or_create(
                inscripcion=inscripcion,
                beneficio=beneficio,
                defaults={
                    "cantidad": beneficio.cantidad,
                    "activacion": activacion,
                },
            )
            concedidas.append(concesion)
        return concedidas


__all__ = ["BeneficioCoreService"]
