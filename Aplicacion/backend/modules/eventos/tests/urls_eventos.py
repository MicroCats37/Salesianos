"""URLconf de prueba del módulo `eventos` (sólo tests).

**Por qué existe.** `config/api.py` es de A0 y este paquete (A1) NO lo edita:
el registro permanente del controller lo pide A0 (petición A0-03 del evidence
de FND-02). Para poder probar la ruta HTTP sin tocar la configuración
compartida, este URLconf monta una instancia propia de `NinjaExtraAPI` con el
controller `EdicionController` registrado y los handlers de error globales.

El test usa el marcador `pytest.mark.urls("modules.eventos.tests.urls_eventos")`
para apuntar el `ROOT_URLCONF` a este módulo durante el test.

**Retiro.** A0 registra el controller en `config/api.py` y este archivo se
elimina.
"""

import uuid

from django.urls import path
from ninja_extra import NinjaExtraAPI

from core.exceptions import register_exception_handlers
from modules.eventos.presentation.controllers.edicion_controller import EdicionController

api = NinjaExtraAPI(
    title="Ediciones (test)",
    version="2.0.0",
    urls_namespace=f"api-eventos-{uuid.uuid4().hex[:6]}",
    auth=None,
)
register_exception_handlers(api)
api.register_controllers(EdicionController)

urlpatterns = [
    path("api/", api.urls),
]
