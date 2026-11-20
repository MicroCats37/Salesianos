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


def make_item_pedido(producto_id, cantidad: int = 1, tipo: str = "PRODUCTO") -> dict:
    """Un artículo declarado en el payload del pedido.

    El payload NO admite un importe: el precio lo resuelve y congela el
    servidor (`RN-C02`). `tipo` es el discriminante del ORIGEN del artículo
    (`PRODUCTO`, `PASE`, `INSCRIPCION`).
    """
    return {
        "tipo": tipo,
        "producto_id": str(producto_id),
        "cantidad": cantidad,
    }


def make_pedido_payload(*items, **overrides) -> dict:
    """Payload de alta de un pedido de marketplace.

    Acepta artículos ya construidos con `make_item_pedido` o la forma
    `(producto_id, cantidad)`.
    """
    articulos = []
    for item in items:
        if isinstance(item, dict):
            articulos.append(item)
        else:
            producto_id, cantidad = item
            articulos.append(make_item_pedido(producto_id, cantidad))
    payload = {"items": articulos}
    payload.update(overrides)
    return payload


def make_movimiento_payload(
    producto_id,
    tipo: str,
    cantidad: int,
    motivo: str,
    **overrides,
) -> dict:
    """Payload de registro de un movimiento manual de inventario (`DOM-06`).

    La cantidad es **CON SIGNO**: positiva entra, negativa sale. La
    naturaleza del movimiento (`tipo`) es la que valida el servidor.
    """
    payload = {
        "producto_id": str(producto_id),
        "tipo": tipo,
        "cantidad": cantidad,
        "motivo": motivo,
    }
    payload.update(overrides)
    return payload


def make_reversion_payload(motivo: str, **overrides) -> dict:
    """Payload de la reversa compensatoria de un movimiento (`DOM-06`)."""
    payload = {"motivo": motivo}
    payload.update(overrides)
    return payload


__all__ = [
    "make_categoria_payload",
    "make_imagen_payload",
    "make_item_pedido",
    "make_movimiento_payload",
    "make_pedido_payload",
    "make_producto_payload",
    "make_reversion_payload",
    "precio",
]
