"""
Instancia central de NinjaExtraAPI.
Aquí se registran todos los routers y controllers del proyecto.

Propietario del archivo: **A0** (paquete FND-01).

Reglas de registro (FREEZE-PS-1.0.0 · FR-07 §3.1.2):

- Una ruta **no existe** hasta que su controller está registrado aquí. Código
  escrito y no registrado es código muerto.
- `registrar_controladores()` es la ÚNICA puerta de entrada. Los paquetes de
  dominio (FND-02…DOM-08) la usan; nadie llama a `api.register_controllers()`
  por su cuenta.
- El **orden es significativo**: cuando dos controllers comparten prefijo de
  ruta, el último registrado es el que resuelve primero.
- Una ruta del ledger marcada `provisional = sí` NO debe registrarse hasta que
  su módulo y su presenter estén implementados y versionados.
- A0 no registra controllers de dominio INACABADOS: sólo se registran los
  controllers cuyo módulo está completado, verificado y versionado
  (reconciliación A0 de FND-01, 2026-11-19 · DOM-01 y DOM-04, 2026-11-19).
"""

from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

from core.exceptions import register_exception_handlers

from modules.eventos.presentation.controllers.edicion_controller import EdicionController
from modules.marketplace.presentation.controllers.producto_controller import ProductoController
from modules.pagos.presentation.controllers.pagos_controller import PagosController
from modules.salesianos_fest.presentation.controllers.catalogo_controller import (
    CatalogoController,
)
from modules.salesianos_fest.presentation.controllers.inscripcion_controller import (
    InscripcionController,
)
from modules.usuarios.presentation.controllers import PersonaController

import os

api_version = "2.0.0"
api_namespace = "api"

if os.environ.get("PYTEST_CURRENT_TEST"):
    import sys
    from ninja.errors import ConfigError
    import uuid

    if hasattr(sys, "_ninja_api_instance"):
        api = sys._ninja_api_instance
    else:
        try:
            api = NinjaExtraAPI(
                title="Generic API (Test)",
                version=api_version,
                urls_namespace="api-test-suite",
                description="Generic API Boilerplate",
                auth=JWTAuth(),
                docs_url="/docs",
            )
        except ConfigError:
            api = NinjaExtraAPI(
                title="Generic API (Test)",
                version=api_version,
                urls_namespace=f"api-test-{uuid.uuid4().hex[:6]}",
                description="Generic API Boilerplate",
                auth=JWTAuth(),
                docs_url="/docs",
            )
        sys._ninja_api_instance = api
else:
    api = NinjaExtraAPI(
        title="Generic API",
        version=api_version,
        urls_namespace=api_namespace,
        description="Generic API Boilerplate",
        auth=JWTAuth(),
        docs_url="/docs",
    )


# ── Extensión de registro (A0) ─────────────────────────────────────────────
#
# El registro vive EN la instancia de la API para que sobreviva a una recarga
# del módulo: recargar `config.api` no vuelve a registrar los mismos
# controllers (eso rompería el router con rutas duplicadas).
#
# La extensión es IDEMPOTENTE: registrar dos veces el mismo controller no
# lanza error ni duplica rutas.


def registrar_controladores(*controllers) -> list:
    """Registra controllers de dominio en la API. Punto de extensión de A0.

    Devuelve la lista de controllers realmente registrados en esta llamada
    (los que ya estaban registrados se omiten).
    """
    registrados = getattr(api, "_a0_controladores_registrados", None)
    if registrados is None:
        registrados = []
        api._a0_controladores_registrados = registrados

    nuevos = []
    for controller in controllers:
        if controller in registrados:
            continue
        api.register_controllers(controller)
        registrados.append(controller)
        nuevos.append(controller)
    return nuevos


def controllers_registrados() -> tuple:
    """Controllers vivos en la API, en orden de registro."""
    return tuple(getattr(api, "_a0_controladores_registrados", []) or [])


# ── Controllers JWT (token/pair, token/refresh, token/verify) ─
registrar_controladores(NinjaJWTDefaultController)

# ── Controllers de dominio COMPLETADOS (A0 · reconciliación FND-01) ─────────
# Sólo se registra lo que está TERMINADO, verificado y versionado. Un
# controller sin módulo terminado NO se registra: su ruta no existe y el
# código queda muerto por diseño (FR-07 §3.1 regla 2).
#
#   - `EdicionController` → FND-02 (`eventos`)   · RT-ED-01
#   - `PersonaController` → FND-03 (`usuarios`)  · RT-ID-01…RT-ID-03
#   - `PagosController`   → FND-04 (`pagos`)     · RT-PG-01…RT-PG-03
#   - `CatalogoController` → DOM-01 (`salesianos_fest`) · RT-IN-12, RT-IN-13
#   - `InscripcionController` → DOM-01 (`salesianos_fest`) · RT-IN-02,
#                             RT-IN-04, RT-IN-14 (provisional, ratificada)
#   - `ProductoController` → DOM-04 (`marketplace`) · RT-MD-01, RT-MK-01…03
#
# `commerce` NO aporta surface HTTP (D-FND-04-06): sus compras las crean los
# dominios in-process. Ningún dominio INACABADO (`pases`, `beneficios`,
# `validaciones`, `patrocinadores`, `competencias`, `administracion`, …) se
# registra aquí.
registrar_controladores(
    EdicionController,
    PersonaController,
    PagosController,
    CatalogoController,
    InscripcionController,
    ProductoController,
)

# ── Exception handlers globales ────────────────────────────────
register_exception_handlers(api)
