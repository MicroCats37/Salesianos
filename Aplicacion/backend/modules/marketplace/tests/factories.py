"""Payload factories del módulo `marketplace`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §4

Funciones PURAS que devuelven `dict`. NO son fixtures, NO usan `factory_boy` y
NO tocan la base de datos.

El payload de alta es el JSON del campo `data` del protocolo multipart
(FR-06 §2.4): los archivos viajan como TOKENS (`file_<uuid>`), no como
binarios.
"""

from decimal import Decimal


def make_imagen_payload(token: str, **overrides) -> dict:
    """Una imagen declarada en el payload de alta."""
    payload = {
        "token": token,
        "es_principal": False,
        "texto_alternativo": "",
    }
    payload.update(overrides)
    return payload


def make_producto_payload(**overrides) -> dict:
    """Payload de alta de un producto."""
    payload = {
        "nombre": "Agua mineral",
        "slug": "agua-mineral",
        "descripcion": "Botella de 500 ml.",
        "precio": "3.50",
        "estado": "ACTIVO",
        "imagenes": [],
    }
    payload.update(overrides)
    return payload


def make_categoria_payload(**overrides) -> dict:
    """Payload de alta de una categoría de producto."""
    payload = {
        "nombre": "Bebidas",
        "slug": "bebidas",
        "orden": 1,
    }
    payload.update(overrides)
    return payload


def precio(valor) -> Decimal:
    """Un `Decimal` con dos decimales, como el que viaja en el dominio."""
    return Decimal(str(valor)).quantize(Decimal("0.01"))


__all__ = [
    "make_categoria_payload",
    "make_imagen_payload",
    "make_producto_payload",
    "precio",
]
