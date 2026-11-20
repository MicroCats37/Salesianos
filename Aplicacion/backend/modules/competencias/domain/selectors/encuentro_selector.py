"""Selectores de `Encuentro`: el cuadro, la agenda y el detalle.

Packet: `DOM-07` · Change: `salesianos-fest-rebuild`

Contract: `contract/django-app-architecture-contract.md` §4.12

**Una sola fuente operativa.** `FL-11` paso 6 exige que la lista, la agenda
y el bracket compartan una sola fuente de datos. Este selector es esa fuente:
el cuadro, la agenda y el detalle salen de aquí, y los tres proyectan con
`proyeccion.py`. No hay una consulta de agenda y una consulta de cuadro que
puedan discrepar.

**La agenda es TRANSVERSAL** (`frontend/05` §2): reúne los encuentros del día
de TODAS las competencias de la edición, ordenados por hora de inicio.
"""

from datetime import date

from modules.competencias.domain.exceptions import EncuentroNoEncontradoError
from modules.competencias.domain.models import Encuentro, Ronda
from modules.competencias.domain.results.competencias_results import (
    AgendaResult,
    RondaResult,
)
from modules.competencias.domain.selectors.proyeccion import proyectar_ronda


class EncuentroSelector:
    """Lecturas de los encuentros: cuadro, agenda y detalle."""

    # ── consultas ───────────────────────────────────────────────────────────

    def obtener_por_id(self, encuentro_id) -> Encuentro:
        """El encuentro, o el error de no encontrado (404)."""
        try:
            return (
                Encuentro.objects.select_related(
                    "ronda",
                    "ronda__competencia",
                    "participante_1",
                    "participante_1__equipo",
                    "participante_2",
                    "participante_2__equipo",
                    "ganador",
                    "ganador__equipo",
                ).get(id=encuentro_id)
            )
        except (Encuentro.DoesNotExist, ValueError, TypeError):
            raise EncuentroNoEncontradoError()

    def rondas(self, competencia_id) -> list[RondaResult]:
        """El cuadro completo de una competencia: rondas y encuentros.

        Las rondas invalidadas se conservan y se devuelven: el cuadro que se
        trazó con ellas sigue en la historia (`RN-K02`).
        """
        rondas = list(
            Ronda.objects.filter(competencia_id=competencia_id)
            .prefetch_related(
                "encuentros__participante_1__equipo",
                "encuentros__participante_2__equipo",
                "encuentros__ganador__equipo",
            )
            .order_by("orden")
        )
        return [
            proyectar_ronda(ronda, sorted(ronda.encuentros.all(), key=lambda e: e.orden))
            for ronda in rondas
        ]

    def agenda(self, edicion_id, dia: date, edicion_nombre: str = "") -> AgendaResult:
        """Los encuentros programados del día, en el alcance de la edición.

        Un encuentro sin horario NO aparece en la agenda: la agenda es el
        horario, y un encuentro sin horario no tiene lugar en él. Los
        encuentros CANCELADOS se excluyen: no reservan la franja.
        """
        encuentros = list(
            Encuentro.objects.filter(
                ronda__competencia__edicion_id=edicion_id,
                inicio_programado__isnull=False,
                fin_programado__isnull=False,
                inicio_programado__date=dia,
            )
            .exclude(estado="CANCELADO")
            .select_related(
                "ronda",
                "ronda__competencia",
                "participante_1",
                "participante_1__equipo",
                "participante_2",
                "participante_2__equipo",
                "ganador",
                "ganador__equipo",
            )
            .order_by("inicio_programado", "ronda__orden", "orden")
        )
        from modules.competencias.domain.selectors.proyeccion import proyectar_encuentro

        return AgendaResult(
            edicion_id=str(edicion_id),
            edicion_nombre=edicion_nombre,
            fecha=dia,
            total=len(encuentros),
            encuentros=[proyectar_encuentro(encuentro) for encuentro in encuentros],
        )


__all__ = ["EncuentroSelector"]
