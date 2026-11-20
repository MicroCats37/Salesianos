"""Payload factories del módulo `patrocinadores`.

Contract: `contract/TEST_ARCHITECTURE_CONTRACT.md` §4

Funciones PURAS que devuelven `dict`. NO son fixtures, NO usan `factory_boy` y
NO tocan la base de datos.

El payload de alta es el JSON del campo `data` del protocolo multipart
(FR-06 §2.4): los archivos viajan como TOKENS (`file_<uuid>`), no como
binarios.
"""


def make_imagen_payload(token: str, **overrides) -> dict:
    """Una imagen declarada en el payload de alta de la galería."""
    payload = {
        "token": token,
        "texto_alternativo": "",
    }
    payload.update(overrides)
    return payload


def make_patrocinador_payload(**overrides) -> dict:
    """Payload de alta de un patrocinador."""
    payload = {
        "nombre": "Colegio San Juan Bosco",
        "slug": "colegio-san-juan-bosco",
        "descripcion": "Patrocinador de la edición 2026.",
        "visible": True,
        "imagenes": [],
    }
    payload.update(overrides)
    return payload


def make_orden_imagen(imagen_id, orden: int) -> dict:
    """El orden explícito de una imagen de la galería."""
    return {
        "imagen_id": str(imagen_id),
        "orden": orden,
    }


__all__ = [
    "make_imagen_payload",
    "make_orden_imagen",
    "make_patrocinador_payload",
]
