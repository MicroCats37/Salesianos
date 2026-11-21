"""Generate the deployable JSON fixture from the authoritative workbook.

This module is a development utility. The management command only reads the
generated JSON and never imports openpyxl or the repository's ``mit`` tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from modules.competencias.data.fixture import SCHEMA_VERSION, SOURCE_SHA256


SOURCE_RELATIVE_PATH = "mit/SALESIANOS/Fixture_Salesianos_2026_Estructurado.xlsx"
SPORTS = {
    "Fútbol": {
        "code": "F7M",
        "slug": "futbol-7-masculino",
        "name": "Fútbol 7 Masculino Interpromociones",
        "team_prefix": "",
        "duration": 30,
        "groups": {
            "Senior A": "A",
            "Super Master": "B",
            "Master A": "C",
            "Junior A": "D",
            "Senior B": "E",
            "Junior B": "F",
            "Master B": "G",
            "Senior C": "H",
            "Junior C": "I",
        },
    },
    "Vóley": {
        "code": "VOL",
        "slug": "voley-mixto",
        "name": "Vóley Mixto Interpromociones",
        "team_prefix": "VOL-",
        "duration": 30,
        "groups": {
            "Master A": "VOL-A",
            "Junior A": "VOL-B",
            "Senior A": "VOL-C",
            "Junior B": "VOL-D",
        },
    },
    "Básquet": {
        "code": "BAS",
        "slug": "basquet-masculino",
        "name": "Básquet Masculino Interpromociones",
        "team_prefix": "BAS-",
        "duration": 20,
        "groups": {
            "Senior A": "BAS-A",
            "Senior B": "BAS-B",
            "Junior B": "BAS-C",
            "Master A": "BAS-D",
            "Master B": "BAS-E",
            "Junior A": "BAS-F",
        },
    },
}
STAGES = {
    "Fase regular": "group",
    "Cruce": "cross",
    "Final": "final",
    "3er puesto": "third_place",
}


def _canonical_label(label: str) -> str:
    return "2011A" if label == "2001A" else label


def _clock(value: object) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M")
    return str(value)[:5]


def _duration(start: str, end: str) -> int:
    first = datetime.strptime(start, "%H:%M")
    last = datetime.strptime(end, "%H:%M")
    return int((last - first).total_seconds() // 60)


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_fixture(source: Path) -> dict:
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash != SOURCE_SHA256:
        raise ValueError(
            f"Workbook hash mismatch: expected {SOURCE_SHA256}, got {source_hash}."
        )

    workbook = load_workbook(source, data_only=True, read_only=True)
    categories_sheet = workbook["Categorías"]
    groups = []
    group_by_key = {}
    for row in categories_sheet.iter_rows(min_row=5, values_only=True):
        discipline, category, _count, labels, _page = row
        if not discipline:
            continue
        sport = SPORTS[discipline]
        canonical_labels = [
            _canonical_label(label.strip()) for label in str(labels).split(",")
        ]
        group = {
            "id": sport["groups"][category],
            "competition_code": sport["code"],
            "label": category,
            "teams": [
                {
                    "id": f"{sport['team_prefix']}{label}",
                    "label": label,
                    "promotion_year": int(label[:4]),
                }
                for label in canonical_labels
            ],
        }
        groups.append(group)
        group_by_key[(discipline, category)] = group

    positions = defaultdict(int)
    matches = []
    for row in workbook["Partidos"].iter_rows(min_row=5, values_only=True):
        (
            match_id,
            discipline,
            source_stage,
            category,
            start_raw,
            end_raw,
            court,
            home_raw,
            away_raw,
            title,
            observation,
            _page,
        ) = row
        if not match_id:
            continue
        sport = SPORTS[discipline]
        stage = STAGES[source_stage]
        start = _clock(start_raw)
        end = _clock(end_raw)
        home_label = _canonical_label(str(home_raw)) if home_raw else None
        away_label = _canonical_label(str(away_raw)) if away_raw else None
        group = group_by_key.get((discipline, category)) if stage == "group" else None
        position_key = (sport["code"], group["id"] if group else stage)
        position = positions[position_key]
        positions[position_key] += 1
        duration = _duration(start, end)
        if duration != sport["duration"]:
            raise ValueError(
                f"Unexpected duration for {match_id}: {duration}, expected {sport['duration']}."
            )
        matches.append(
            {
                "id": match_id,
                "competition_code": sport["code"],
                "group_id": group["id"] if group else None,
                "stage": stage,
                "category": category,
                "position": position,
                "home_id": (
                    f"{sport['team_prefix']}{home_label}" if group and home_label else None
                ),
                "away_id": (
                    f"{sport['team_prefix']}{away_label}" if group and away_label else None
                ),
                "home_label": home_label,
                "away_label": away_label,
                "title": title,
                "start": start,
                "end": end,
                "court": court,
                "duration_minutes": duration,
                "source_observation": observation,
            }
        )

    competitions = [
        {
            "code": sport["code"],
            "slug": sport["slug"],
            "name": sport["name"],
            "source_discipline": discipline,
            "duration_minutes": sport["duration"],
        }
        for discipline, sport in SPORTS.items()
    ]
    content = {"competitions": competitions, "groups": groups, "matches": matches}
    counts = {
        "categories": len(groups),
        "teams": sum(len(group["teams"]) for group in groups),
        "regular_matches": sum(match["stage"] == "group" for match in matches),
        "postseason_matches": sum(match["stage"] != "group" for match in matches),
        "matches": len(matches),
    }
    return {
        "manifest": {
            "schema_version": SCHEMA_VERSION,
            "source": {"path": SOURCE_RELATIVE_PATH, "sha256": source_hash},
            "content_sha256": _canonical_hash(content),
            "counts": counts,
            "warnings": [
                {
                    "code": "CANONICALIZED_TEAM_2001A_TO_2011A",
                    "message": (
                        "The team list says 2001A, while all three matches and the "
                        "previous seed say 2011A. The normalized fixture uses 2011A."
                    ),
                    "source_references": ["V-01", "V-02", "V-03"],
                },
                {
                    "code": "SOURCE_TYPO_PRESERVED",
                    "message": "The source label '1° Seniro C' is preserved verbatim.",
                    "source_references": ["V-04"],
                },
                {
                    "code": "EVENT_DATE_NOT_DOCUMENTED",
                    "message": (
                        "The workbook does not state a calendar date; the command must "
                        "reuse existing competition dates or receive --event-date."
                    ),
                    "source_references": ["V-05"],
                },
            ],
        },
        **content,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    repository_root = Path(__file__).resolve().parents[5]
    parser.add_argument(
        "--source",
        type=Path,
        default=repository_root / SOURCE_RELATIVE_PATH,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("fixture_salesianos_2026.v1.json"),
    )
    arguments = parser.parse_args()
    fixture = build_fixture(arguments.source.resolve())
    arguments.output.write_text(
        json.dumps(fixture, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {arguments.output} ({fixture['manifest']['counts']})")


if __name__ == "__main__":
    main()
