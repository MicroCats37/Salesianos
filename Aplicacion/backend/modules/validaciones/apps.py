"""Configuración de la app Django `validaciones`.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

El `label` es ÚNICO en el proyecto (`validaciones`): no colisiona con
`django.contrib.*` ni con ninguna otra app del objetivo.

**Registro.** `config/settings/base.py` y `config/api.py` son de A0 y este
paquete NO los edita (`00-contrato-global-de-apply.md`, "Shared Files"). El
registro permanente se PIDE como evidencia (peticiones A0 de este paquete) y
mientras tanto la verificación local usa
`modules/validaciones/tests/settings_overlay.py`, que replica exactamente el
registro que A0 debe hacer.
"""

from django.apps import AppConfig


class ValidacionesConfig(AppConfig):
    """La app de validaciones del FEST."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "modules.validaciones"
    label = "validaciones"
    verbose_name = "Validaciones"
