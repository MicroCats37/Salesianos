"""URLconf de prueba del módulo `competencias` (sólo tests).

**Por qué existe.** `config/api.py` es de A0 y este paquete (A6) NO lo edita:
el registro permanente de los controllers lo pide A0 (petición A0-02 de este
paquete). Para poder probar las rutas HTTP sin tocar la configuración
compartida, este URLconf monta una instancia propia de `NinjaExtraAPI` con
el controller `CompetenciasController` registrado, la autenticación JWT y los
handlers de error globales.

El test usa el marcador
`pytest.mark.urls("modules.competencias.tests.urls_competencias")` para
apuntar el `ROOT_URLCONF` a este módulo durante el test.

**Retiro.** A0 registra el controller en `config/api.py` y este archivo se
elimina.
"""

import uuid

from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth

from core.exceptions import register_exception_handlers
from modules.competencias.presentation.controllers.competencias_controller import (
    CompetenciasController,
)

api = NinjaExtraAPI(
    title="Competencias (test)",
    version="2.0.0",
    urls_namespace=f"api-competencias-{uuid.uuid4().hex[:6]}",
    auth=JWTAuth(),
)
register_exception_handlers(api)
api.register_controllers(CompetenciasController)

urlpatterns = [
    path("api/", api.urls),
]
