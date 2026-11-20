"""AppConfig del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El módulo es de AGREGACIÓN: no define un dominio de negocio propio, sino la
capa de lectura transversal del panel de administración y el ACTA de auditoría
de las acciones sensibles.

El registro en `INSTALLED_APPS` es de **A0** (`config/settings/base.py`). A0 lo
registró en la reconciliación A0 de XCT-02 (2026-11-20 · lote D2): el módulo
está vivo, con su migración `0001_initial` y su DI detrás de los módulos que
consume. El `settings_overlay` de `tests/` replica ese registro para poder
verificar el módulo sin tocar la configuración de A0.
"""

from django.apps import AppConfig


class AdministracionConfig(AppConfig):
    """Configuración de la aplicación de administración operativa."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.administracion"
    label = "administracion"
    verbose_name = "Administración operativa"
