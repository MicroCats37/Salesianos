"""URLconf de prueba del módulo `patrocinadores` (sólo tests).

**Por qué existe.** `config/api.py` es de A0 y este paquete (A8) NO lo edita:
el registro permanente del controller lo pide A0 (petición A0-02 de la
evidencia de DOM-08). Para poder probar las rutas HTTP sin tocar la
configuración compartida, este URLconf monta una instancia propia de
`NinjaExtraAPI` con los controllers de `patrocinadores` registrados y los
handlers de error globales.

El test usa el marcador
`pytest.mark.urls("modules.patrocinadores.tests.urls_patrocinadores")` para
apuntar el `ROOT_URLCONF` a este módulo durante el test.

**Controllers registrados:**

- `PatrocinadorController` (DOM-08) — la ficha, el logo y la galería.

**Retiro.** A0 registra los controllers en `config/api.py` y este archivo se
elimina.
"""

import uuid

from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth

from core.exceptions import register_exception_handlers
from modules.patrocinadores.presentation.controllers.patrocinadores_controller import (
    PatrocinadorController,
)

api = NinjaExtraAPI(
    title="Patrocinadores (test)",
    version="2.0.0",
    urls_namespace=f"api-patrocinadores-{uuid.uuid4().hex[:6]}",
    auth=JWTAuth(),
)
register_exception_handlers(api)
api.register_controllers(PatrocinadorController)

urlpatterns = [
    path("api/", api.urls),
]
