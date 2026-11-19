"""`CatalogoCoreService` — operaciones de bajo nivel del catálogo.

Packet: `DOM-01` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.3 — servicios
core SYNC, sin `transaction.atomic()` propio.

Este servicio sólo RESUELVE hechos del catálogo: qué disciplina está
permitida por un paquete, qué beneficios ofrece. Las DECISIONES (qué
paquete se compra, con qué precio) viven en el flujo.
"""

from modules.salesianos_fest.domain.constants import EstadoDisciplina
from modules.salesianos_fest.domain.models import Disciplina


class CatalogoCoreService:
    """Resoluciones de catálogo reutilizables."""

    def disciplina_permitida(self, paquete, disciplina_id) -> Disciplina | None:
        """La disciplina ACTIVA del EDICIÓN del paquete que el paquete permite.

        Devuelve `None` cuando la disciplina no existe en la edición, no
        está activa o no forma parte del paquete: el flujo convierte ese
        `None` en el error de dominio que corresponda.
        """
        disciplina = (
            Disciplina.objects.filter(
                id=disciplina_id,
                edicion_id=paquete.edicion_id,
                estado=EstadoDisciplina.ACTIVA,
                paquetes_vinculados__paquete=paquete,
            )
            .first()
        )
        return disciplina

    def disciplinas_permitidas(self, paquete) -> list[Disciplina]:
        """Las disciplinas activas que el paquete permite."""
        return list(
            Disciplina.objects.filter(
                edicion_id=paquete.edicion_id,
                estado=EstadoDisciplina.ACTIVA,
                paquetes_vinculados__paquete=paquete,
            ).order_by("nombre")
        )


__all__ = ["CatalogoCoreService"]
