"""`CortesiaSelector` — consultas de SOLO LECTURA de las actas de cortesía.

Change: `administracion-pases-alta-directa` · Apply C

Contract: `contract/django-app-architecture-contract.md` §8 (selectors)

El selector NO decide: sólo consulta. La decisión de revocar (y su efecto
sobre el acta y sus derechos) vive en `CortesiaCoreService`; la validación del
motivo y la orquestación viven en `CortesiaFlujo`.

Existe como selector PROPIO —y no como un método más de `PaseSelector`—
porque las actas de cortesía son un recurso con su propia identidad, su
propio estado y su propio ciclo de revocación.
"""

from modules.salesianos_fest.domain.models import CortesiaPase


class CortesiaSelector:
    """Consultas de solo lectura sobre las actas de cortesía."""

    @staticmethod
    def obtener_cortesia(cortesia_id) -> CortesiaPase | None:
        """El acta de cortesía indicada, o `None`.

        Carga las relaciones que el presenter necesita (edición, pase,
        persona y actores) para que la proyección no dispare una consulta por
        campo.

        No filtra por estado: la revocación se consulta sobre el MISMO acta
        para poder informar del estado final (`FR-05` §2.3 — la revocación es
        idempotente).
        """
        return (
            CortesiaPase.objects.filter(id=cortesia_id)
            .select_related(
                "edicion",
                "pase",
                "persona",
                "actor_usuario",
                "actor_persona",
            )
            .first()
        )


__all__ = ["CortesiaSelector"]
