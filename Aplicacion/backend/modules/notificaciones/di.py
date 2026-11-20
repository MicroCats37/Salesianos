"""Wiring de dependencias (DI) del módulo `notificaciones`.

Contract: `contract/django-app-architecture-contract.md` §4.15

A0 registra este módulo en `NINJA_EXTRA["INJECTOR_MODULES"]`
(`config/settings/base.py`). Ese registro es de A0; este archivo sólo declara
las liaisons del módulo.

`notificaciones` es una **hoja** del grafo: no depende de ningún módulo de
dominio. El puerto `INotificadorCompraService` lo declara `pagos` (el
consumidor) y lo implementa este módulo (el proveedor), así que la dirección
de dependencias es `notificaciones -> pagos`.
"""

from injector import Binder, Module, singleton

from modules.notificaciones.domain.services.core.notificacion_envio_core_service import (
    NotificacionEnvioCoreService,
)
from modules.notificaciones.infrastructure.services.notificador_comprador import (
    NotificadorCompradorAdapter,
)


class NotificacionesModule(Module):
    """Bindings de dependencias del módulo `notificaciones`."""

    def configure(self, binder: Binder) -> None:
        binder.bind(
            NotificacionEnvioCoreService,
            to=NotificacionEnvioCoreService,
            scope=singleton,
        )
        binder.bind(
            NotificadorCompradorAdapter,
            to=NotificadorCompradorAdapter,
            scope=singleton,
        )


__all__ = ["NotificacionesModule"]
