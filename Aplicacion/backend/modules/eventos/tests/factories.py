"""Payload factories del módulo `eventos`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §4

Funciones PURAS que devuelven `dict`. NO son fixtures, NO usan `factory_boy` y
NO tocan la base de datos.
"""

from datetime import date


def make_evento_payload(**overrides) -> dict:
    """Payload de alta de un evento."""
    payload = {
        "nombre": "Salesianos FEST",
        "slug": "salesianos-fest",
    }
    payload.update(overrides)
    return payload


def make_edicion_payload(**overrides) -> dict:
    """Payload de alta de una edición."""
    payload = {
        "nombre": "Salesianos FEST 2026",
        "slug": "2026",
        "anio": 2026,
        "estado": "BORRADOR",
        "modulos_habilitados": [],
        "fecha_inicio": date(2026, 11, 15),
        "fecha_fin": date(2026, 11, 20),
    }
    payload.update(overrides)
    return payload


__all__ = [
    "make_edicion_payload",
    "make_evento_payload",
]
