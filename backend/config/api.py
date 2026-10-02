"""
Instancia central de NinjaExtraAPI.
Aquí se registran todos los routers y controllers del proyecto.
"""

from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

from core.exceptions import register_exception_handlers
from modules.usuarios.presentation.controllers.auth_controller import AuthLoginController
from modules.usuarios.presentation.controllers.registro_controller import RegistroController
from modules.usuarios.presentation.controllers.persona_busqueda_controller import PersonaBusquedaController
from modules.usuarios.presentation.controllers.me_controller import AuthMeController
from modules.inscripciones.presentation.controllers.disciplina_controller import DisciplinaController
from modules.inscripciones.presentation.controllers.paquete_controller import PaqueteController
from modules.inscripciones.presentation.controllers.evento_controller import EventoController
from modules.inscripciones.presentation.controllers.inscripcion_controller import InscripcionController
from modules.inscripciones.presentation.controllers.promocion_controller import PromocionController
from modules.pagos.presentation.controllers.pagos_controller import PagosController

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

# ── Controllers JWT (token/pair, token/refresh, token/verify) ─
api.register_controllers(NinjaJWTDefaultController)

# ── Auth Controllers (modular login by username/dni/email) ─
api.register_controllers(AuthLoginController)

# ── Registro Controller (public registration endpoint) ─
api.register_controllers(RegistroController)

# ── Persona Busqueda Controller (public document lookup endpoint) ─
api.register_controllers(PersonaBusquedaController)

# ── Auth Me Controller (revalidar sesión tras reload) ─
api.register_controllers(AuthMeController)

# ── Inscripciones Controllers (catalogs and lifecycle) ─
api.register_controllers(DisciplinaController)
api.register_controllers(PaqueteController)
api.register_controllers(EventoController)
api.register_controllers(PromocionController)
api.register_controllers(InscripcionController)

# ── Pagos Controller (Izipay Perú) ─
api.register_controllers(PagosController)

# ── Exception handlers globales ────────────────────────────────
register_exception_handlers(api)
