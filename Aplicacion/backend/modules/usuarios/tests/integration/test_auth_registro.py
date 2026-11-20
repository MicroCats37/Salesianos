"""
Registro de la superficie de sesión en la API del proyecto.

GIVEN: `config/api.py`, la única puerta de registro del backend objetivo.
WHEN: se consulta la API viva.
THEN: las cuatro rutas de sesión están REGISTRADAS y el controller de
autenticación figura en el registro de A0.

Una ruta no existe hasta que su controller está registrado: código escrito
y no registrado es código muerto (`FR-07` §3.1.2).
"""

from config.api import controllers_registrados
from modules.usuarios.presentation.controllers import AuthController

#: Rutas de sesión que el paquete `FND-03A` congeló.
RUTAS_DE_SESION = (
    "/api/auth/login/username",
    "/api/auth/login/dni",
    "/api/auth/login/email",
    "/api/auth/me",
)


def test_el_controller_de_autenticacion_esta_registrado():
    """El controller de sesión está en el registro de A0."""
    assert AuthController in controllers_registrados()


def test_las_rutas_de_sesion_estan_registradas_en_la_api_viva():
    """La API viva expone EXACTAMENTE las cuatro rutas de sesión."""
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    assert paths, "El API del objetivo no expone ninguna ruta."

    for ruta in RUTAS_DE_SESION:
        assert ruta in paths, ruta


def test_las_rutas_de_sesion_usan_los_metodos_congelados():
    """Cada ruta de sesión expone el método HTTP congelado."""
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    metodos = {
        "/api/auth/login/username": "post",
        "/api/auth/login/dni": "post",
        "/api/auth/login/email": "post",
        "/api/auth/me": "get",
    }

    for ruta, metodo in metodos.items():
        assert metodo in paths[ruta], (ruta, metodo)


def test_las_rutas_de_login_son_publicas_y_la_sesion_exige_jwt():
    """El login es público; la sesión actual exige autenticación."""
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    for ruta in (
        "/api/auth/login/username",
        "/api/auth/login/dni",
        "/api/auth/login/email",
    ):
        assert not paths[ruta]["post"].get("security"), ruta

    assert paths["/api/auth/me"]["get"].get("security"), "/api/auth/me"


def test_el_registro_es_idempotente_para_el_controller_de_autenticacion():
    """Registrar dos veces el controller de sesión no duplica rutas."""
    from config.api import registrar_controladores

    nuevos = registrar_controladores(AuthController)

    assert nuevos == []
    assert controllers_registrados().count(AuthController) == 1
