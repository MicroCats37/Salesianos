"""Modelos del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El módulo es de AGREGACIÓN: el único modelo propio es el ACTA de auditoría
(`AccionAuditada`). Ningún otro dato de negocio se duplica aquí.
"""

from .accion_auditada import AccionAuditada

__all__ = ["AccionAuditada"]
