"""The deployable JSON is an exact, validated projection of the workbook."""

import hashlib
from pathlib import Path

from modules.competencias.data.fixture import SOURCE_SHA256, load_reference_fixture
from modules.competencias.data.generate_fixture import build_fixture


def test_el_json_normalizado_coincide_con_el_excel_autoritativo():
    source = (
        Path(__file__).resolve().parents[6]
        / "mit"
        / "SALESIANOS"
        / "Fixture_Salesianos_2026_Estructurado.xlsx"
    )
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256
    assert build_fixture(source) == load_reference_fixture()


def test_el_manifest_y_los_conteos_del_fixture_son_canonicos():
    fixture = load_reference_fixture()

    assert fixture["manifest"]["counts"] == {
        "categories": 19,
        "teams": 64,
        "regular_matches": 80,
        "postseason_matches": 22,
        "matches": 102,
    }
    assert {item["duration_minutes"] for item in fixture["matches"] if item["competition_code"] == "F7M"} == {30}
    assert {item["duration_minutes"] for item in fixture["matches"] if item["competition_code"] == "VOL"} == {30}
    assert {item["duration_minutes"] for item in fixture["matches"] if item["competition_code"] == "BAS"} == {20}


def test_basquet_usa_los_horarios_corregidos_y_2011a_es_canonico():
    fixture = load_reference_fixture()
    basketball_starts = [
        item["start"]
        for item in fixture["matches"]
        if item["competition_code"] == "BAS" and item["stage"] == "group"
    ]
    assert basketball_starts == [
        "09:00",
        "09:20",
        "09:40",
        "10:00",
        "10:20",
        "10:40",
        "11:00",
        "11:20",
        "11:40",
        "12:00",
        "12:20",
        "13:00",
        "13:20",
        "13:40",
        "14:00",
        "14:20",
        "14:40",
        "15:00",
        "15:20",
        "15:40",
    ]
    labels = {
        team["label"] for group in fixture["groups"] for team in group["teams"]
    }
    warning_codes = {
        warning["code"] for warning in fixture["manifest"]["warnings"]
    }
    assert "2011A" in labels
    assert "2001A" not in labels
    assert "CANONICALIZED_TEAM_2001A_TO_2011A" in warning_codes


def test_el_fixture_modela_cruces_finales_y_terceros_puestos():
    fixture = load_reference_fixture()
    postseason = [item for item in fixture["matches"] if item["stage"] != "group"]

    assert sum(item["stage"] == "cross" for item in postseason) == 8
    assert sum(item["stage"] == "final" for item in postseason) == 10
    assert sum(item["stage"] == "third_place" for item in postseason) == 4
    assert next(item for item in postseason if item["id"] == "P-081")[
        "home_label"
    ] == "1° Master A"
