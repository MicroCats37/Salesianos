"""Contratos del snapshot canónico y los comandos del torneo integrado."""

from types import SimpleNamespace

import pytest
from django.test import Client

from modules.competencias.management.commands.seed_torneo_referencia import (
    BASKETBALL_GROUPS,
    FOOTBALL_GROUPS,
    VOLLEY_GROUPS,
)
from modules.competencias.domain.models import (
    EquipoTorneo,
    GrupoTorneo,
    PartidoTorneo,
)
from modules.competencias.domain.services.flujos.torneo_flujo import TorneoFlujo


pytestmark = [
    pytest.mark.urls("modules.competencias.tests.urls_competencias"),
    pytest.mark.django_db,
]


def _equipo(competencia, grupo, equipo_id):
    return EquipoTorneo.objects.create(
        id=equipo_id,
        competencia=competencia,
        grupo=grupo,
    )


@pytest.mark.parametrize(
    ("groups", "expected_groups", "expected_teams", "expected_matches", "courts"),
    [
        (FOOTBALL_GROUPS, 9, 33, 45, {"A", "B", "C", "D"}),
        (VOLLEY_GROUPS, 4, 13, 15, {"E", "F"}),
        (BASKETBALL_GROUPS, 6, 18, 20, {"G"}),
    ],
)
def test_el_fixture_total_separa_las_disciplinas_por_cancha(
    groups,
    expected_groups,
    expected_teams,
    expected_matches,
    courts,
):
    labels = {
        label for group_labels, _matches in groups.values() for label in group_labels
    }
    matches = [
        match for _labels, group_matches in groups.values() for match in group_matches
    ]

    assert len(groups) == expected_groups
    assert len(labels) == expected_teams
    assert len(matches) == expected_matches
    assert {match[4] for match in matches} == courts


def test_el_snapshot_del_torneo_resuelve_la_competencia_seleccionada(
    edicion_publicada,
    competencia,
    competencia_categoria_2,
):
    """La consulta seleccionada no mezcla grupos ni metadatos de otra llave."""
    GrupoTorneo.objects.create(id="A", competencia=competencia)
    GrupoTorneo.objects.create(id="B", competencia=competencia_categoria_2)

    respuesta = Client().get(
        "/api/publico/competencias/estado",
        {"competition_id": str(competencia_categoria_2.id)},
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["ready"] is True
    assert datos["competition_id"] == str(competencia_categoria_2.id)
    assert datos["competition_name"] == competencia_categoria_2.nombre
    assert [grupo["id"] for grupo in datos["groups"]] == ["B"]
    assert {opcion["id"] for opcion in datos["competitions"]} == {
        str(competencia.id),
        str(competencia_categoria_2.id),
    }


def test_el_snapshot_con_competencia_desconocida_conserva_el_catalogo(
    competencia,
):
    """Una selección inválida es un estado vacío, no una respuesta ambigua."""
    GrupoTorneo.objects.create(id="A", competencia=competencia)

    respuesta = Client().get(
        "/api/publico/competencias/estado",
        {"competition_id": "no-existe"},
    )

    assert respuesta.status_code == 200
    datos = respuesta.json()["data"]
    assert datos["ready"] is False
    assert datos["groups"] == []
    assert datos["knockout"] == []
    assert datos["competitions"] == [
        {
            "id": str(competencia.id),
            "name": competencia.nombre,
            "discipline": competencia.disciplina.nombre,
            "category": competencia.categoria.nombre,
            "date": competencia.fecha.isoformat(),
        }
    ]


def test_finalizar_llave_propagado_y_publica_despues_del_commit(
    competencia,
    monkeypatch,
    django_capture_on_commit_callbacks,
):
    """El ganador se propaga y la señal realtime sólo se emite al confirmar."""
    grupo = GrupoTorneo.objects.create(id="A", competencia=competencia)
    local = _equipo(competencia, grupo, "local")
    visitante = _equipo(competencia, grupo, "visitante")
    origen = PartidoTorneo.objects.create(
        id="quarter-0",
        competencia=competencia,
        etapa="quarter",
        posicion=0,
        local=local,
        visitante=visitante,
        puntaje_local=2,
        puntaje_visitante=1,
    )
    destino = PartidoTorneo.objects.create(
        id="semi-0",
        competencia=competencia,
        etapa="semi",
        posicion=0,
    )
    publicados = []
    monkeypatch.setattr(
        "modules.competencias.domain.services.flujos.torneo_flujo.publicar_encuentro_actualizado",
        publicados.append,
    )

    with django_capture_on_commit_callbacks(execute=True):
        resultado = TorneoFlujo().controlar_partido(
            origen.id,
            SimpleNamespace(action="finish", decision=None, winner_id=None),
        )

    origen.refresh_from_db()
    destino.refresh_from_db()
    assert resultado == {"saved": True, "status": "final"}
    assert origen.ganador_id == local.id
    assert destino.local_id == local.id
    assert publicados == [origen.id]
