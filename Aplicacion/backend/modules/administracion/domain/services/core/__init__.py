"""Servicios sync (core) del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Un servicio core NO abre `transaction.atomic()`: la transacción la abre el
flujo que la necesita (`contract/django-app-architecture-contract.md` §4.3).
"""
