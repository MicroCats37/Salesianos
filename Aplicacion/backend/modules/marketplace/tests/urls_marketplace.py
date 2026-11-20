"""URLconf de prueba del módulo `marketplace` (sólo tests).

**Por qué existe.** `config/api.py` es de A0 y este paquete (A5) NO lo edita:
el registro permanente del controller lo pide A0 (petición A0-03 del evidence
de DOM-04). Para poder probar las rutas HTTP sin tocar la configuración
compartida, este URLconf monta una instancia propia de `NinjaExtraAPI` con los
controllers de `marketplace` registrados y los handlers de error globales.

El test usa el marcador `pytest.mark.urls("modules.marketplace.tests.urls_marketplace")`
para apuntar el `ROOT_URLCONF` a este módulo durante el test.

**Controllers registrados:**

- `ProductoController` (DOM-04) — el catálogo.
- `PedidoController` (DOM-05) — el pedido y su seguimiento.
- `InventarioController` (DOM-06) — el inventario y las entregas.

**Retiro.** A0 registra los controllers en `config/api.py` y este archivo se
elimina.
"""

import uuid

from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth

from core.exceptions import register_exception_handlers
from modules.marketplace.presentation.controllers.inventario_controller import (
    InventarioController,
)
from modules.marketplace.presentation.controllers.pedido_controller import (
    PedidoController,
)
from modules.marketplace.presentation.controllers.producto_controller import (
    ProductoController,
)

api = NinjaExtraAPI(
    title="Marketplace (test)",
    version="2.0.0",
    urls_namespace=f"api-marketplace-{uuid.uuid4().hex[:6]}",
    auth=JWTAuth(),
)
register_exception_handlers(api)
api.register_controllers(ProductoController, PedidoController, InventarioController)

urlpatterns = [
    path("api/", api.urls),
]
