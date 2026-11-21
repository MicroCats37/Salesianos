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
  (reconciliación A0 de FND-01, 2026-11-19 · DOM-01 y DOM-04, 2026-11-19 ·
  DOM-03, 2026-11-19 · DOM-05, DOM-06, DOM-07 y DOM-08, 2026-11-19 ·
  XCT-01, 2026-11-19).
"""

from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

from core.exceptions import register_exception_handlers

from modules.administracion.presentation.controllers.admin_controller import (
    AdminController,
)
from modules.administracion.presentation.controllers.admin_asistido_controller import (
    AdminAsistidoController,
)
from modules.administracion.presentation.controllers.admin_equipo_controller import (
    AdminEquipoController,
)
from modules.administracion.presentation.controllers.admin_inscripcion_controller import (
    AdminInscripcionController,
)
from modules.administracion.presentation.controllers.admin_pago_controller import (
    AdminPagoController,
)
from modules.administracion.presentation.controllers.admin_participante_controller import (
    AdminParticipanteController,
)
from modules.administracion.presentation.controllers.admin_persona_controller import (
    AdminPersonaController,
)
from modules.competencias.presentation.controllers.competencias_controller import (
    CompetenciasController,
)
from modules.competencias.presentation.controllers.competencias_publico_controller import (
    CompetenciasPublicoController,
    TorneoAdminController,
)
from modules.competencias.presentation.controllers.mis_partidos_controller import (
    MisPartidosController,
)
from modules.commerce.presentation.controllers.cuenta_compras_controller import (
    CuentaComprasController,
)
from modules.eventos.presentation.controllers.edicion_controller import EdicionController
from modules.marketplace.presentation.controllers.inventario_controller import (
    InventarioController,
)
from modules.marketplace.presentation.controllers.pedido_controller import PedidoController
from modules.marketplace.presentation.controllers.producto_controller import ProductoController
from modules.pagos.presentation.controllers.pagos_controller import PagosController
from modules.patrocinadores.presentation.controllers.patrocinadores_controller import (
    AdminPatrocinadoresController,
    PatrocinadorController,
)
from modules.salesianos_fest.presentation.controllers.catalogo_controller import (
    CatalogoController,
)
from modules.salesianos_fest.presentation.controllers.cotizacion_controller import (
    CotizacionController,
)
from modules.salesianos_fest.presentation.controllers.inscripcion_controller import (
    InscripcionController,
)
from modules.salesianos_fest.presentation.controllers.pase_controller import (
    AdminPaseController,
    PaseController,
)
from modules.usuarios.presentation.controllers import AuthController, PersonaController
from modules.validaciones.presentation.controllers.validacion_controller import (
    ValidacionController,
)
from modules.videos.presentation.controllers.admin_videos_controller import (
    AdminVideosController,
)
from modules.videos.presentation.controllers.videos_controller import VideoController

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
#   - `AuthController`   → FND-03A (`usuarios`) · POST /auth/login/{username,
#                             dni,email} + GET /auth/me (ruta CORRECTIVA: el
#                             ledger de GOV-01 no la congeló)
#   - `PagosController`   → FND-04 (`pagos`)     · RT-PG-01…RT-PG-03
#   - `CatalogoController` → DOM-01 (`salesianos_fest`) · RT-IN-12, RT-IN-13
#   - `InscripcionController` → DOM-01 (`salesianos_fest`) · RT-IN-02,
#                             RT-IN-04, RT-IN-14 (provisional, ratificada)
#   - `ProductoController` → DOM-04 (`marketplace`) · RT-MD-01, RT-MK-01…03
#   - `PedidoController` → DOM-05 (`marketplace`) · RT-CM-03, RT-MK-04
#   - `InventarioController` → DOM-06 (`marketplace`) · RT-MK-08…RT-MK-12
#   - `PaseController` → DOM-03 (`salesianos_fest`) · RT-PS-01…RT-PS-05,
#                             RT-CM-02, RT-RT-03
#   - `AdminPaseController` → DOM-03 (`salesianos_fest`) · RT-PS-06…RT-PS-08
#   - `CompetenciasController` → DOM-07 (`competencias`) · 16 rutas
#   - `CompetenciasPublicoController` → `partidos-marcadores-competencias` ·
#                             GET /api/publico/competencias/encuentros
#                             (lectura PÚBLICA, anónimo, de solo lectura)
#   - `MisPartidosController` → `partidos-marcadores-competencias` ·
#                             GET /api/cuenta/mis-partidos (lectura de la
#                             CUENTA: sesión, sin capacidad administrativa)
#   - `PatrocinadorController` → DOM-08 (`patrocinadores`) · RT-MD-02
#   - `ValidacionController` → XCT-01 (`validaciones`) · RT-RT-01, RT-RT-02
#   - `CotizacionController` → DOM-01 (`salesianos_fest`) · POST /cotizaciones
#   - `AdminController` → XCT-02 (`administracion`) · RT-ADM-01, RT-ADM-02
#   - `AdminInscripcionController` → XCT-02 (`administracion`) · inscripciones
#   - `AdminEquipoController` → XCT-02 (`administracion`) · equipos
#   - `AdminParticipanteController` → XCT-02 (`administracion`) · participantes
#   - `AdminPagoController` → XCT-02 (`administracion`) · pagos
#   - `AdminPersonaController` → XCT-02 (`administracion`) · personas
#   - `AdminAsistidoController` → `admin-client-purchases-and-participants` ·
#                             el alta de participante por documento y las
#                             compras asistidas para un tercero
#   - `VideoController` → `public-video-streaming-crud` · GET /api/videos,
#                             GET /api/videos/{video_id}
#   - `AdminVideosController` → `public-video-streaming-crud` · la gestión de
#                             la sala de proyección
#
# `commerce` NO aporta surface HTTP (D-FND-04-06): sus compras las crean los
# dominios in-process. Ningún dominio INACABADO (`beneficios`, …) se registra
# aquí.
#
# `validaciones` (XCT-01) tiene módulo, DI, migración, controller y SUITE
# VERDE (20 de 20): se registra (reconciliación A0 de XCT-01, 2026-11-19 ·
# cierre del cableado global).
#
# `administracion` (XCT-02) tiene módulo, DI, migración, controllers y SUITE
# VERDE (15 de 15 con el overlay de registro): se registra (reconciliación A0
# de XCT-02, 2026-11-20 · cierre del cableado global; correcting
# `evidence/verification/VER-01-baseline-regression-payments.md` §7).
#
# `CotizacionController` (DOM-01) expone la ruta PROVISIONAL `POST
# /cotizaciones`: el módulo, el presenter y la suite e2e existen y están
# verdes, así que la ruta deja de ser código muerto (reconciliación A0 de
# DOM-01, 2026-11-20 · petición `A0-API02-09`).
registrar_controladores(
    EdicionController,
    PersonaController,
    AuthController,
    CuentaComprasController,
    PagosController,
    CatalogoController,
    CotizacionController,
    InscripcionController,
    ProductoController,
    PedidoController,
    InventarioController,
    PaseController,
    AdminPaseController,
    CompetenciasController,
    CompetenciasPublicoController,
    TorneoAdminController,
    MisPartidosController,
    PatrocinadorController,
    AdminPatrocinadoresController,
    ValidacionController,
    AdminController,
    AdminInscripcionController,
    AdminEquipoController,
    AdminParticipanteController,
    AdminPagoController,
    AdminPersonaController,
    AdminAsistidoController,
    VideoController,
    AdminVideosController,
)

# ── Exception handlers globales ────────────────────────────────
register_exception_handlers(api)
