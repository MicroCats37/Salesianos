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
from modules.pagos.presentation.controllers.pagos_controller import PagosController
from modules.salesianos_fest.presentation.controllers.catalogo_controller import CatalogoController
from modules.salesianos_fest.presentation.controllers.inscripcion_controller import (
    InscripcionController,
    EquipoController,
    ParticipacionController,
)
from modules.salesianos_fest.presentation.controllers.compra_controller import CompraController
from modules.salesianos_fest.presentation.controllers.asignacion_controller import AsignacionController, InscripcionSaldoController
from modules.salesianos_fest.presentation.controllers.acreditacion_controller import AcreditacionController, AccesoController
from modules.salesianos_fest.presentation.controllers.cotizacion_controller import CotizacionController
from modules.administracion.presentation.controllers.admin_fundacion_controller import (
    AdminFundacionController,
)
from modules.administracion.presentation.controllers.admin_resumen_controller import (
    AdminResumenController,
)
from modules.administracion.presentation.controllers.admin_inscripcion_controller import (
    AdminInscripcionController,
)
from modules.administracion.presentation.controllers.admin_pago_controller import (
    AdminPagoController,
)
from modules.administracion.presentation.controllers.admin_operacion_controller import (
    AdminOperacionController,
)
from modules.administracion.presentation.controllers.admin_usuario_controller import (
    AdminUsuarioController,
)
from modules.competencias.presentation.controllers.admin_competencias_controller import (
    AdminCompetenciasController,
)
from modules.competencias.presentation.controllers.admin_encuentros_controller import (
    AdminEncuentrosController,
)
from modules.competencias.presentation.controllers.public_competencias_controller import (
    PublicCompetenciasController,
)

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

# ── Pagos Controller (Izipay Perú) ──
api.register_controllers(PagosController)

# ── Salesianos FEST Controller (Catálogo público — Fase 2) ─────
api.register_controllers(CatalogoController)

# ── Salesianos FEST Controllers (Inscripción deportiva — Fase 3) ─────
api.register_controllers(InscripcionController)
api.register_controllers(EquipoController)
api.register_controllers(ParticipacionController)

# ── Salesianos FEST Controllers (Compras y Pagos — Fase 4) ─────
api.register_controllers(CompraController)

# ── Salesianos FEST Controllers (Asignacion Cupos — Fase 5) ─────
api.register_controllers(AsignacionController)
api.register_controllers(InscripcionSaldoController)

# ── Salesianos FEST Controllers (Acreditacion y Acceso — Fase 5) ─────
api.register_controllers(AcreditacionController)
api.register_controllers(AccesoController)

# ── Salesianos FEST Controllers (Cotización — Fase 3/4) ─────
api.register_controllers(CotizacionController)

# ── Administración Operativa FEST (read-only, admin-only) ─────
api.register_controllers(AdminFundacionController)
api.register_controllers(AdminResumenController)
api.register_controllers(AdminInscripcionController)
api.register_controllers(AdminPagoController)
api.register_controllers(AdminOperacionController)
api.register_controllers(AdminUsuarioController)

# ── Competencias: superficie administrativa (RequireAdmin) ─────
# The order matters: the commands of the encounters live under the prefix
# "/administracion/competencias/encuentros".
api.register_controllers(AdminCompetenciasController)
api.register_controllers(AdminEncuentrosController)

# ── Competencias: superficie pública (solo lectura, eventos autorizados) ─────
api.register_controllers(PublicCompetenciasController)

# ── Exception handlers globales ────────────────────────────────
register_exception_handlers(api)
