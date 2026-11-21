"""URLconf de prueba del CAMINO ADMINISTRATIVO de la credencial de puerta.

**Por qué existe.** La credencial se emite en el módulo `validaciones` y el
`derecho_id` que la habilita lo publica el módulo `salesianos_fest`. Para
probar el CAMINO COMPLETO —otorgar, listar y emitir— hace falta UNA API que
monte los DOS controllers.

Este archivo monta una instancia propia de `NinjaExtraAPI` con
`AdminPaseController` y `ValidacionController` registrados, la autenticación
JWT y los handlers de error globales.

Es un URLconf de PRUEBAS: no registra nada en `config/api.py` (que es de A0) y
se elimina cuando A0 registre los controllers de forma permanente.

El test usa el marcador
`pytest.mark.urls("modules.salesianos_fest.tests.urls_cortesia_credencial")`
para apuntar el `ROOT_URLCONF` a este módulo durante el test.
"""

import uuid

from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth

from core.exceptions import register_exception_handlers
from modules.salesianos_fest.presentation.controllers.pase_controller import (
    AdminPaseController,
)
from modules.validaciones.presentation.controllers.validacion_controller import (
    ValidacionController,
)

api = NinjaExtraAPI(
    title="Cortesías y credenciales (test)",
    version="2.0.0",
    urls_namespace=f"api-cortesia-credencial-{uuid.uuid4().hex[:6]}",
    auth=JWTAuth(),
)
register_exception_handlers(api)
api.register_controllers(
    AdminPaseController,
    ValidacionController,
)

urlpatterns = [
    path("api/", api.urls),
]
