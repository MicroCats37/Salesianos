"""
Payloads de prueba del módulo `usuarios`.

`contract/TEST_ARCHITECTURE_CONTRACT.md` §4: `factories.py` NO es un archivo
de fixtures — contiene funciones puras que devuelven `dict`. Sin base de
datos, sin pytest.
"""

from typing import Any


def make_persona_payload(
    numero_documento: str = "12345678",
    tipo_documento: str = "DNI",
    nombres: str = "ANA",
    apellidos: str = "PEREZ",
    genero: str = "F",
) -> dict[str, Any]:
    """Payload de alta de una `Persona`."""
    return {
        "tipo_documento": tipo_documento,
        "numero_documento": numero_documento,
        "nombres": nombres,
        "apellidos": apellidos,
        "genero": genero,
    }


def make_usuario_payload(
    username: str = "ana.prueba",
    email: str = "ana.prueba@example.com",
    password: str = "Prueba-12345",
) -> dict[str, Any]:
    """Payload de alta de una cuenta."""
    return {
        "username": username,
        "email": email,
        "password": password,
    }


def make_resolver_payload(
    numero_documento: str = "12345678",
    tipo_documento: str = "DNI",
) -> dict[str, Any]:
    """Payload del resolver (`RT-ID-02`)."""
    return {
        "tipo_documento": tipo_documento,
        "numero_documento": numero_documento,
    }


def make_confirmar_payload(
    numero_documento: str = "12345678",
    tipo_documento: str = "DNI",
    nombres: str = "ANA",
    apellidos: str = "PEREZ",
    genero: str = "F",
) -> dict[str, Any]:
    """Payload de la confirmación (`RT-ID-03`)."""
    return {
        "tipo_documento": tipo_documento,
        "numero_documento": numero_documento,
        "nombres": nombres,
        "apellidos": apellidos,
        "genero": genero,
    }


__all__ = [
    "make_confirmar_payload",
    "make_persona_payload",
    "make_resolver_payload",
    "make_usuario_payload",
]
