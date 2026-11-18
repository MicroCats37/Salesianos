"""
Integration test of the CAPACITY state of a team.

`CapacidadEquipoService` is the SINGLE owner of the rule: the administrative
teams table publishes its verdict and the frontend renders it as delivered. The
threshold is the same one the write path respects (`ParticipacionCoreService`
rejects a new participation when the team already holds `max_jugadores` active
players), so `AL_LIMITE` is exactly the state in which the next participant
cannot be added.

The test is TABLE-DRIVEN: every boundary of the rule is pinned, including the
degenerate `min == max` case and a discipline without cap.
"""
import pytest

from modules.salesianos_fest.domain.constants import EstadoCapacidadEquipoChoices
from modules.salesianos_fest.domain.services.core.capacidad_equipo_service import (
    CapacidadEquipoService,
)


@pytest.mark.parametrize(
    ("jugadores", "maximo", "esperado"),
    [
        # Below the cap: the team still has room.
        (0, 10, EstadoCapacidadEquipoChoices.CON_CUPOS),
        (1, 10, EstadoCapacidadEquipoChoices.CON_CUPOS),
        (9, 10, EstadoCapacidadEquipoChoices.CON_CUPOS),
        # AT the cap: the next participant cannot be added.
        (10, 10, EstadoCapacidadEquipoChoices.AL_LIMITE),
        (11, 10, EstadoCapacidadEquipoChoices.AL_LIMITE),
        # The degenerate case `min == max`: complete AND at the limit.
        (1, 1, EstadoCapacidadEquipoChoices.AL_LIMITE),
        (0, 1, EstadoCapacidadEquipoChoices.CON_CUPOS),
        # A discipline WITHOUT cap can never be full.
        (5, 0, EstadoCapacidadEquipoChoices.CON_CUPOS),
    ],
)
def test_estado_capacidad_respeta_el_tope_de_la_disciplina(
    jugadores, maximo, esperado
):
    assert (
        CapacidadEquipoService.estado_capacidad(jugadores=jugadores, maximo=maximo)
        == esperado
    )


def test_el_veredicto_pertenece_al_vocabulario_del_dominio():
    assert CapacidadEquipoService.estado_capacidad(jugadores=10, maximo=10) in {
        valor for valor, _etiqueta in EstadoCapacidadEquipoChoices.choices
    }
