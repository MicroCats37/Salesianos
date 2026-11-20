"""Typed wrappers for the account's unified purchase history."""

from ninja import Schema


class EstadoCompraCuentaOut(Schema):
    codigo: str
    etiqueta: str
    descripcion: str


class CompraCuentaOut(Schema):
    id: str
    origen: str
    concepto: str
    monto: str
    moneda: str
    fecha: str
    estado: EstadoCompraCuentaOut


__all__ = ["CompraCuentaOut", "EstadoCompraCuentaOut"]
