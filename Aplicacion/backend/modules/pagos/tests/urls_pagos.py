"""URLconf de prueba del módulo `pagos` (sólo tests).

**Por qué existe.** `config/api.py` es de A0 y este paquete (A2) NO lo edita:
el registro permanente del controller lo pide A0 (petición A0-03 del evidence
de FND-04). Para poder probar la superficie HTTP sin tocar la configuración
compartida, este URLconf monta una instancia propia de `NinjaExtraAPI` con el
controller `PagosController` registrado, la autenticación JWT y los handlers
de error globales.

El test usa el marcador `pytest.mark.urls("modules.pagos.tests.urls_pagos")`
para apuntar el `ROOT_URLCONF` a este módulo durante el test.

**Retiro.** A0 registra el controller en `config/api.py` y este archivo se
elimina.
"""

import uuid

from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth

from core.exceptions import register_exception_handlers
from modules.pagos.presentation.controllers.pagos_controller import PagosController

api = NinjaExtraAPI(
    title="Pagos (test)",
    version="2.0.0",
    urls_namespace=f"api-pagos-{uuid.uuid4().hex[:6]}",
    auth=JWTAuth(),
)
register_exception_handlers(api)
api.register_controllers(PagosController)

urlpatterns = [
    path("api/", api.urls),
]
