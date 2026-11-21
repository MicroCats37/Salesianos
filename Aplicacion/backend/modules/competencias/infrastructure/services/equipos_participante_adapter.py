"""El adaptador de los EQUIPOS de una persona.

Change: `partidos-marcadores-competencias` · Batch 3B

Contract: `contract/django-app-architecture-contract.md` §4.10

`modules.salesianos_fest` es el DUEÑO de la inscripción, del equipo y del
POOL de participantes (`RN-K01`). Este adaptador CONSUME ese hecho: pregunta
en qué equipos juega una persona y devuelve SUS identificadores.

**NO decide nada**: no filtra por edición, ni por disciplina, ni por estado
del cuadro. La lectura de "MIS PARTIDOS" es la que acota el alcance con los
equipos VIGENTES (la participación activa) y con los encuentros en los que
participan.

El cruce se hace por PUERTO (`IEquiposDeParticipante`) y NUNCA por import
directo del modelo de otro módulo en el dominio o en el presenter.
"""

from modules.competencias.domain.ports import IEquiposDeParticipante


class EquiposDeParticipanteAdapter(IEquiposDeParticipante):
    """Puente con el POOL de `modules.salesianos_fest`."""

    def __init__(self, participacion_model=None):
        if participacion_model is None:
            from modules.salesianos_fest.domain.models import Participacion

            participacion_model = Participacion

        self._participacion = participacion_model

    def equipos_de_persona(self, persona_id) -> list[str]:
        """Los equipos VIGENTES de una persona, sin duplicados.

        Una participación RETIRADA no cuenta: el equipo actual es el de la
        participación activa.
        """
        from modules.salesianos_fest.domain.constants import EstadoParticipacion

        equipos = self._participacion.objects.filter(
            persona_id=persona_id,
            estado=EstadoParticipacion.ACTIVA,
        ).values_list("equipo_id", flat=True)

        return [str(equipo_id) for equipo_id in sorted(set(equipos))]


__all__ = ["EquiposDeParticipanteAdapter"]
