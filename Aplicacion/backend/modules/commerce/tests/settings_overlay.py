"""Overlay de configuración para la VERIFICACIÓN del paquete FND-04 (compartido).

El paquete FND-04 verifica `commerce` y `pagos` **juntos**, con un único
juego de settings: el registro de las tres apps (incluida `usuarios`, de la
que `Compra.persona` depende) y el cableado de DI.

El overlay vive en `modules/pagos/tests/settings_overlay.py` porque `pagos` es
el módulo dueño de las rutas del paquete; este archivo sólo lo reexporta para
que la suite de `commerce` pueda ejecutarse sola con
`--settings=modules.commerce.tests.settings_overlay`.

**Retiro.** A0 registra las apps de forma permanente en
`config/settings/base.py` y se elimina el overlay de `pagos`.
"""

from modules.pagos.tests.settings_overlay import *  # noqa: F401,F403
