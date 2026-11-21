"""Load and validate the normalized reference fixture without Excel dependencies."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).with_name("fixture_salesianos_2026.v1.json")
SOURCE_SHA256 = "3ebbaa770a9a8ae86283982b7224ac0baf982dc5efccb9d3cb091b099b7d9691"
SCHEMA_VERSION = 1


class FixtureDataError(RuntimeError):
    """The deployable fixture is missing, corrupt, or internally inconsistent."""


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_reference_fixture(path: Path = FIXTURE_PATH) -> dict:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FixtureDataError(f"No se pudo leer el fixture normalizado: {exc}") from exc

    manifest = fixture.get("manifest", {})
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise FixtureDataError("La versión del fixture normalizado no es compatible.")
    if manifest.get("source", {}).get("sha256") != SOURCE_SHA256:
        raise FixtureDataError("El hash de la fuente del fixture no coincide.")

    content = {
        "competitions": fixture.get("competitions"),
        "groups": fixture.get("groups"),
        "matches": fixture.get("matches"),
    }
    if manifest.get("content_sha256") != _canonical_hash(content):
        raise FixtureDataError("El contenido del fixture normalizado fue alterado.")

    groups = fixture["groups"]
    matches = fixture["matches"]
    counts = manifest.get("counts", {})
    actual = {
        "categories": len(groups),
        "teams": sum(len(group["teams"]) for group in groups),
        "regular_matches": sum(match["stage"] == "group" for match in matches),
        "postseason_matches": sum(match["stage"] != "group" for match in matches),
        "matches": len(matches),
    }
    if counts != actual:
        raise FixtureDataError(
            f"Los conteos del manifest no coinciden: declarados={counts}, reales={actual}."
        )

    expected_duration = {"F7M": 30, "VOL": 30, "BAS": 20}
    for match in matches:
        if match["duration_minutes"] != expected_duration[match["competition_code"]]:
            raise FixtureDataError(
                f"Duración inválida en {match['id']}: {match['duration_minutes']}."
            )
    return fixture


__all__ = [
    "FIXTURE_PATH",
    "SOURCE_SHA256",
    "FixtureDataError",
    "load_reference_fixture",
]
