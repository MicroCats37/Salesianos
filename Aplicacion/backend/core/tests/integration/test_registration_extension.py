"""Extensión de registro de controllers (A0 · FR-07 §3.1.2).

GIVEN  `config.api`, la única puerta de registro del backend objetivo
WHEN   se consulta o se invoca el punto de extensión
THEN   una ruta no existe hasta que su controller se registra, el registro es
       idempotente y NO hay controllers de dominio inacabados.

Reconciliación A0 de FND-01 (2026-11-19) y reconciliación A0 de DOM-01 +
DOM-04 (2026-11-19): el registro permanente de los controllers COMPLETADOS se
aplica en este paquete. El conjunto registrado es una lista CERRADA y
explícita: si mañana aparece un controller nuevo, este test falla y obliga a
revisar el registro a propósito.
"""

from ninja_jwt.controller import NinjaJWTDefaultController

from config.api import controllers_registrados, registrar_controladores

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


#: Controllers vivos del objetivo, en ORDEN de registro. El orden es
#: significativo (FR-07 §3.1.2): cuando dos controllers comparten prefijo de
#: ruta, el último registrado es el que resuelve primero.
CONTROLLERS_COMPLETADOS = (
    NinjaJWTDefaultController,
    EdicionController,
    PersonaController,
    PagosController,
    CatalogoController,
    InscripcionController,
    ProductoController,
)

#: Prefijos de ruta que el API del objetivo puede exponer. Cada uno pertenece
#: a un módulo COMPLETADO.
PREFIJOS_PERMITIDOS = (
    "/api/token",        # ninja_jwt
    "/api/ediciones",    # FND-02 · eventos
    "/api/personas",     # FND-03 · usuarios
    "/api/pagos",        # FND-04 · pagos
    "/api/catalogo",     # DOM-01 · salesianos_fest
    "/api/inscripciones",  # DOM-01 · salesianos_fest
    "/api/marketplace",  # DOM-04 · marketplace
)

#: Superficie de dominio viva, exacta (ledger FR-07 §3.3). Las rutas de JWT
#: quedan fuera: las registra `ninja_jwt`, no un paquete del cambio.
RUTAS_DE_DOMINIO_CONGELADAS = {
    "/api/ediciones/actual",                    # RT-ED-01
    "/api/personas/busqueda/{documento}",       # RT-ID-01
    "/api/personas/resolver",                   # RT-ID-02
    "/api/personas/confirmar",                  # RT-ID-03
    "/api/pagos/ordenes/{orden_id}",            # RT-PG-03
    "/api/pagos/ordenes/{orden_id}/confirmar",  # RT-PG-01
    "/api/pagos/izipay/notificacion",           # RT-PG-02
    "/api/catalogo/paquetes",                   # RT-IN-12 · DOM-01
    "/api/catalogo/disciplinas",                # RT-IN-13 · DOM-01
    "/api/inscripciones",                       # RT-IN-14 · DOM-01 (provisional ratificada)
    "/api/inscripciones/{inscripcion_id}",      # RT-IN-02 · DOM-01
    "/api/inscripciones/{inscripcion_id}/equipos",  # RT-IN-04 · DOM-01
    "/api/marketplace/productos",               # RT-MD-01 (POST) / RT-MK-02 (GET) · DOM-04
    "/api/marketplace/categorias",              # RT-MK-01 · DOM-04
    "/api/marketplace/productos/{slug}",        # RT-MK-03 · DOM-04
}


def test_el_registro_expone_los_controllers_vivos():
    assert controllers_registrados() == CONTROLLERS_COMPLETADOS


def test_los_controllers_de_dominio_completados_estan_registrados():
    """Cada módulo completado expone su superficie HTTP por el proyecto API."""
    for controller in (
        EdicionController,
        PersonaController,
        PagosController,
        CatalogoController,
        InscripcionController,
        ProductoController,
    ):
        assert controller in controllers_registrados(), controller


def test_no_hay_controllers_de_dominio_registrados():
    """A0 no registra controllers de dominio inacabados.

    Los paquetes de dominio (FND-02…DOM-08) registrarán los suyos cuando su
    módulo y su presenter estén implementados y versionados. El conjunto
    registrado es una lista CERRADA: ningún controller ajeno a
    `CONTROLLERS_COMPLETADOS` puede estar vivo.
    """
    for controller in controllers_registrados():
        assert controller in CONTROLLERS_COMPLETADOS, controller


def test_el_registro_es_idempotente():
    """Registrar dos veces el mismo controller no duplica rutas."""
    nuevos = registrar_controladores(*CONTROLLERS_COMPLETADOS)

    assert nuevos == []
    assert controllers_registrados() == CONTROLLERS_COMPLETADOS


def test_la_extension_acepta_varios_controllers_a_la_vez():
    nuevos = registrar_controladores()

    assert nuevos == []
    assert controllers_registrados() == CONTROLLERS_COMPLETADOS


def test_la_lista_de_registro_es_una_tupla():
    """El orden de registro es significativo: se expone como tupla."""
    assert isinstance(controllers_registrados(), tuple)


def test_el_registro_no_contiene_ningun_dominio_inacabado():
    """El API sólo expone rutas de módulos COMPLETADOS.

    Los dominios pendientes (`pases`, `beneficios`, `validaciones`,
    `patrocinadores`, `competencias`, `administracion`) no tienen módulo
    terminado en el objetivo: sus controllers no existen y, por tanto, no
    pueden estar registrados. Si uno apareciese, su ruta existiría sin
    presenter, sin versión y sin pruebas.

    La prueba es sobre el SURFACE REAL (el esquema OpenAPI del API vivo), no
    sobre el nombre de la clase: el decorador `@api_controller` reescribe
    `__module__`, así que el nombre de la clase no identifica al dueño.
    """
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    assert paths, "El API del objetivo no expone ninguna ruta."

    for path in paths:
        assert any(
            path.startswith(prefijo) for prefijo in PREFIJOS_PERMITIDOS
        ), f"Ruta no autorizada (dominio inacabado): {path}"


def test_las_rutas_de_dominio_son_exactamente_las_congeladas():
    """La superficie de dominio viva es EXACTAMENTE la del ledger congelado.

    Ninguna ruta de más (un dominio inacabado registrado por error) y ninguna
    ruta de menos (un controller completado sin registrar).
    """
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})
    rutas_de_dominio = {
        path for path in paths if not path.startswith("/api/token")
    }

    assert rutas_de_dominio == RUTAS_DE_DOMINIO_CONGELADAS


# ── Apps y módulos de DI (A0 · reconciliación DOM-01 / DOM-04) ───────────────
#
# Registrar la app es la mitad del contrato: la otra mitad es que SÓLO se
# registran las apps COMPLETADAS, y en el orden del GRAFO DE MIGRACIONES.
# Un dominio inacabado registrado dejaría sus modelos sin migración, y su
# código muerto por diseño (FR-07 §3.1 regla 2).


#: Apps de dominio registradas en el objetivo. Todas están COMPLETADAS.
APPS_DE_DOMINIO_COMPLETADAS = (
    "modules.eventos",
    "modules.usuarios",
    "modules.pagos",
    "modules.commerce",
    "modules.salesianos_fest",
    "modules.marketplace",
)

#: Módulos de DI registrados. Sólo los de las apps COMPLETADAS.
MODULOS_DE_DI_COMPLETADOS = (
    "modules.usuarios.di.UsuariosModule",
    "modules.eventos.di.EventosModule",
    "modules.pagos.di.PagosModule",
    "modules.commerce.di.CommerceModule",
    "modules.salesianos_fest.di.SalesianosFestModule",
    "modules.marketplace.di.MarketplaceModule",
)


def test_no_hay_apps_de_dominio_inacabadas_registradas():
    """`INSTALLED_APPS` registra exactamente las apps de dominio completadas."""
    from django.conf import settings

    registradas = tuple(
        app for app in settings.INSTALLED_APPS if app.startswith("modules.")
    )

    assert registradas == APPS_DE_DOMINIO_COMPLETADAS


def test_solo_se_registran_los_modulos_de_di_completados():
    """`NINJA_EXTRA["INJECTOR_MODULES"]` sólo lista los módulos completados."""
    from django.conf import settings

    modulos = tuple(settings.NINJA_EXTRA.get("INJECTOR_MODULES", ()))

    assert modulos == MODULOS_DE_DI_COMPLETADOS
    for modulo in modulos:
        assert modulo.split(".")[1] in {
            app.split(".")[1] for app in APPS_DE_DOMINIO_COMPLETADAS
        }, modulo
