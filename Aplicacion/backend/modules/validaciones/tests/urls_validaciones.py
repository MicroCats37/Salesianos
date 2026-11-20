"""URLconf de prueba del módulo `validaciones` (sólo tests).

**Por qué existe.** `config/api.py` es de A0 y este paquete (A8) NO lo edita:
el registro permanente de los controllers lo pide A0 (petición A0-02 de este
paquete). Para poder probar las rutas HTTP sin tocar la configuración
compartida, este URLconf monta una instancia propia de `NinjaExtraAPI` con
el controller `ValidacionController` registrado, la autenticación JWT y los
handlers de error globales.

El test usa el marcador
`pytest.mark.urls("modules.validaciones.tests.urls_validaciones")` para
apuntar el `ROOT_URLCONF` a este módulo durante el test.

**Retiro.** A0 registra el controller en `config/api.py` y este archivo se
elimina.
"""

import uuid

from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth

from core.exceptions import register_exception_handlers
from modules.validaciones.presentation.controllers.validacion_controller import (
    ValidacionController,
)

api = NinjaExtraAPI(
    title="Validaciones (test)",
    version="2.0.0",
    urls_namespace=f"api-validaciones-{uuid.uuid4().hex[:6]}",
    auth=JWTAuth(),
)
register_exception_handlers(api)
api.register_controllers(ValidacionController)

urlpatterns = [
    path("api/", api.urls),
]
