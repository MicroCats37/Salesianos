"""Extensión de registro de controllers (A0 · FR-07 §3.1.2).

GIVEN  `config.api`, la única puerta de registro del backend objetivo
WHEN   se consulta o se invoca el punto de extensión
THEN   una ruta no existe hasta que su controller se registra, el registro es
       idempotente y NO hay controllers de dominio inacabados.

Reconciliación A0 de FND-01 (2026-11-19), reconciliación A0 de DOM-01 +
DOM-04 (2026-11-19), reconciliación A0 de DOM-03 (2026-11-19) y reconciliación
A0 de DOM-05 + DOM-06 + DOM-07 + DOM-08 (2026-11-19, cierre del cableado
global) y reconciliación A0 de XCT-01 (2026-11-19): el registro permanente de
los controllers COMPLETADOS se aplica en este paquete. El conjunto registrado
es una lista CERRADA y explícita: si mañana aparece un controller nuevo, este
test falla y obliga a revisar el registro a propósito.
"""

from ninja_jwt.controller import NinjaJWTDefaultController

from config.api import controllers_registrados, registrar_controladores

from modules.administracion.presentation.controllers.admin_controller import (
    AdminController,
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
)
from modules.competencias.presentation.controllers.mis_partidos_controller import (
    MisPartidosController,
)
from modules.eventos.presentation.controllers.edicion_controller import EdicionController
from modules.marketplace.presentation.controllers.inventario_controller import (
    InventarioController,
)
from modules.marketplace.presentation.controllers.pedido_controller import PedidoController
from modules.marketplace.presentation.controllers.producto_controller import ProductoController
from modules.pagos.presentation.controllers.pagos_controller import PagosController
from modules.patrocinadores.presentation.controllers.patrocinadores_controller import (
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


#: Controllers vivos del objetivo, en ORDEN de registro. El orden es
#: significativo (FR-07 §3.1.2): cuando dos controllers comparten prefijo de
#: ruta, el último registrado es el que resuelve primero.
CONTROLLERS_COMPLETADOS = (
    NinjaJWTDefaultController,
    EdicionController,
    PersonaController,
    AuthController,
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
    MisPartidosController,
    PatrocinadorController,
    ValidacionController,
    AdminController,
    AdminInscripcionController,
    AdminEquipoController,
    AdminParticipanteController,
    AdminPagoController,
    AdminPersonaController,
    VideoController,
    AdminVideosController,
)

#: Prefijos de ruta que el API del objetivo puede exponer. Cada uno pertenece
#: a un módulo COMPLETADO.
PREFIJOS_PERMITIDOS = (
    "/api/token",        # ninja_jwt
    "/api/ediciones",    # FND-02 · eventos
    "/api/personas",     # FND-03 · usuarios
    "/api/auth",         # FND-03A · usuarios (rutas CORRECTIVAS)
    "/api/pagos",        # FND-04 · pagos
    "/api/catalogo",     # DOM-01 · salesianos_fest
    "/api/cotizaciones",  # DOM-01 · salesianos_fest (POST /cotizaciones)
    "/api/inscripciones",  # DOM-01 + DOM-02 · salesianos_fest
    "/api/marketplace",  # DOM-04 + DOM-05 · marketplace
    "/api/administracion/marketplace",  # DOM-06 · marketplace
    "/api/pases",        # DOM-03 · salesianos_fest
    "/api/administracion/pases",  # DOM-03 · salesianos_fest
    "/api/competencias",  # DOM-07 · competencias
    # Las lecturas de la CUENTA (historial comercial y "mis partidos"): son
    # de un usuario normal con sesión, sin capacidad administrativa.
    "/api/cuenta",  # DOM-07 · competencias · `partidos-marcadores-competencias`
    # La lectura PÚBLICA de los encuentros: prefijo DISJUNTO de
    # `/api/competencias`, que exige capacidad administrativa.
    "/api/publico/competencias",  # `partidos-marcadores-competencias`
    "/api/patrocinadores",  # DOM-08 · patrocinadores
    "/api/validaciones",  # XCT-01 · validaciones
    "/api/administracion",  # XCT-02 · administracion (las seis superficies)
    "/api/videos",  # `public-video-streaming-crud` · la sala de proyección
)

#: Superficie de dominio viva, exacta (ledger FR-07 §3.3). Las rutas de JWT
#: quedan fuera: las registra `ninja_jwt`, no un paquete del cambio.
RUTAS_DE_DOMINIO_CONGELADAS = {
    "/api/ediciones/actual",                    # RT-ED-01
    "/api/personas/busqueda/{documento}",       # RT-ID-01
    "/api/personas/resolver",                   # RT-ID-02
    "/api/personas/confirmar",                  # RT-ID-03
    # FND-03A · rutas CORRECTIVAS de autenticación: el ledger de GOV-01 no las
    # congeló, pero el módulo `usuarios` está implementado y versionado.
    "/api/auth/login/username",
    "/api/auth/login/dni",
    "/api/auth/login/email",
    "/api/auth/me",
    # El ALTA de la cuenta (`POST /api/auth/register`) es la ruta CORRECTIVA
    # que faltaba para el flujo de registro: el ledger de GOV-01 no la congeló,
    # pero el módulo `usuarios` está implementado, versionado y verificado
    # (`modules/usuarios/tests/integration/test_auth_registro.py`).
    "/api/auth/register",
    "/api/pagos/ordenes/{orden_id}",            # RT-PG-03
    "/api/pagos/ordenes/{orden_id}/confirmar",  # RT-PG-01
    "/api/pagos/izipay/notificacion",           # RT-PG-02
    "/api/catalogo/paquetes",                   # RT-IN-12 · DOM-01
    "/api/catalogo/disciplinas",                # RT-IN-13 · DOM-01
    "/api/catalogo/categorias",                 # DOM-01 (catálogo de categorías)
    "/api/catalogo/promociones",                # DOM-01 (catálogo de promociones)
    # DOM-01 · la cotización de un paquete (ruta PROVISIONAL ratificada):
    # la ruta existe porque `CotizacionController` está registrado.
    "/api/cotizaciones",                        # DOM-01
    "/api/inscripciones",                       # RT-IN-14 · DOM-01 (provisional ratificada)
    "/api/inscripciones/{inscripcion_id}",      # RT-IN-02 · DOM-01
    "/api/inscripciones/{inscripcion_id}/equipos",  # RT-IN-04 · DOM-01
    "/api/inscripciones/{inscripcion_id}/pool",  # RT-IN-03 · DOM-02
    "/api/inscripciones/{inscripcion_id}/participantes",  # RT-IN-05 · DOM-02
    "/api/inscripciones/{inscripcion_id}/participantes/{participacion_id}",  # RT-IN-06 · DOM-02
    "/api/inscripciones/{inscripcion_id}/compras/cupos",  # RT-CM-01 · DOM-02
    "/api/marketplace/productos",               # RT-MD-01 (POST) / RT-MK-02 (GET) · DOM-04
    "/api/marketplace/categorias",              # RT-MK-01 · DOM-04
    "/api/marketplace/productos/{slug}",        # RT-MK-03 · DOM-04
    "/api/pases",                               # RT-PS-01 · DOM-03
    "/api/pases/compras",                       # RT-CM-02 · DOM-03 (CONGELADO)
    "/api/pases/{pase_id}",                     # RT-PS-02 · DOM-03
    "/api/pases/compras/{compra_pase_id}",      # RT-PS-03 · DOM-03
    "/api/pases/compras/{compra_pase_id}/beneficiarios",  # RT-PS-04 · DOM-03
    "/api/pases/compras/{compra_pase_id}/beneficiarios/{persona_id}",  # RT-RT-03 · DOM-03 (CONGELADO)
    "/api/administracion/pases",                # RT-PS-06 · DOM-03
    "/api/administracion/pases/cortesias",      # RT-PS-07 · DOM-03
    # DOM-05 · el pedido de la tienda (módulo `marketplace`).
    "/api/marketplace/pedidos",                 # RT-CM-03 · DOM-05
    "/api/marketplace/pedidos/{token}",         # RT-MK-04 · DOM-05
    # DOM-06 · el inventario, los movimientos y las entregas (módulo
    # `marketplace`). Estas cinco rutas eran PROVISIONALES en el ledger
    # (`FR-07` §3.3): su módulo y su presenter ya están implementados y
    # versionados (`SCHEMA_VERSION = "1.2.0"`), que es la condición que exige
    # `config/api.py` para registrar un controller.
    "/api/administracion/marketplace/inventario",  # RT-MK-08 · DOM-06
    "/api/administracion/marketplace/inventario/movimientos",  # RT-MK-09 · DOM-06
    "/api/administracion/marketplace/inventario/movimientos/{movimiento_id}/revertir",  # RT-MK-12 · DOM-06
    "/api/administracion/marketplace/entregas",  # RT-MK-10 · DOM-06
    "/api/administracion/marketplace/entregas/{pedido_id}/confirmar",  # RT-MK-11 · DOM-06
    # DOM-07 · la superficie operativa de las competencias (módulo
    # `competencias`): dieciséis rutas.
    "/api/competencias",                        # DOM-07
    "/api/competencias/agenda",                 # DOM-07
    "/api/competencias/{competencia_id}",       # DOM-07
    "/api/competencias/{competencia_id}/cuadro",  # DOM-07
    "/api/competencias/{competencia_id}/equipos-elegibles",  # DOM-07
    "/api/competencias/{competencia_id}/equipos",  # DOM-07
    "/api/competencias/{competencia_id}/equipos/{participacion_id}",  # DOM-07
    "/api/competencias/{competencia_id}/rondas",  # DOM-07
    "/api/competencias/{competencia_id}/encuentros",  # DOM-07
    "/api/competencias/{competencia_id}/encuentros/{encuentro_id}",  # DOM-07
    "/api/competencias/{competencia_id}/encuentros/{encuentro_id}/resultado",  # DOM-07
    "/api/competencias/{competencia_id}/encuentros/{encuentro_id}/avance",  # DOM-07
    "/api/competencias/{competencia_id}/encuentros/{encuentro_id}/avance/preview",  # DOM-07
    "/api/competencias/{competencia_id}/encuentros/{encuentro_id}/correccion",  # DOM-07
    "/api/competencias/{competencia_id}/encuentros/{encuentro_id}/correccion/preview",  # DOM-07
    # `partidos-marcadores-competencias` · la superficie PÚBLICA de los
    # encuentros: una ruta de SOLO LECTURA, anónimo y de prefijo disjunto.
    "/api/publico/competencias/encuentros",  # `partidos-marcadores-competencias`
    # `partidos-marcadores-competencias` · la lectura de la CUENTA: la
    # identidad la resuelve la sesión y el cliente no envía ninguna persona.
    "/api/cuenta/mis-partidos",  # `partidos-marcadores-competencias`
    # DOM-08 · el alta de patrocinadores (módulo `patrocinadores`).
    "/api/patrocinadores",                      # RT-MD-02 · DOM-08
    # XCT-01 · la consola de validación de credenciales (módulo
    # `validaciones`): el ledger `FR-07` §3.3 congela sus dos rutas.
    "/api/validaciones/preview",                # RT-RT-01 · XCT-01
    "/api/validaciones/confirmar",              # RT-RT-02 · XCT-01
    # XCT-02 · el panel de administración (módulo `administracion`): las
    # seis superficies por dominio más el resumen y el acta transversales.
    "/api/administracion/resumen",              # RT-ADM-01 · XCT-02
    "/api/administracion/auditoria",            # RT-ADM-02 · XCT-02
    "/api/administracion/inscripciones",        # XCT-02
    "/api/administracion/inscripciones/{inscripcion_id}",  # XCT-02
    "/api/administracion/inscripciones/{inscripcion_id}/participantes/{participacion_id}",  # XCT-02
    "/api/administracion/equipos",              # XCT-02
    "/api/administracion/equipos/{equipo_id}",  # XCT-02
    "/api/administracion/participantes",        # XCT-02
    "/api/administracion/pagos",                # XCT-02
    "/api/administracion/pagos/{compra_id}",    # XCT-02
    "/api/administracion/personas",             # XCT-02
    "/api/administracion/personas/{persona_id}",  # XCT-02
    # `public-video-streaming-crud` · la SALA DE PROYECCIÓN: la galería
    # pública y su gestión. Cuatro rutas: la lista, el detalle y las dos
    # verbs de administración que comparten camino con el detalle.
    "/api/videos",                        # `public-video-streaming-crud`
    "/api/videos/{video_id}",             # `public-video-streaming-crud`
    "/api/administracion/videos",         # `public-video-streaming-crud`
    "/api/administracion/videos/{video_id}",  # `public-video-streaming-crud`
}


def test_el_registro_expone_los_controllers_vivos():
    assert controllers_registrados() == CONTROLLERS_COMPLETADOS


def test_los_controllers_de_dominio_completados_estan_registrados():
    """Cada módulo completado expone su superficie HTTP por el proyecto API."""
    for controller in (
        EdicionController,
        PersonaController,
        AuthController,
        PagosController,
        CatalogoController,
        InscripcionController,
        ProductoController,
        PedidoController,
        InventarioController,
        PaseController,
        AdminPaseController,
        CompetenciasController,
        PatrocinadorController,
        ValidacionController,
        CotizacionController,
        AdminController,
        AdminInscripcionController,
        AdminEquipoController,
        AdminParticipanteController,
        AdminPagoController,
        AdminPersonaController,
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


def test_el_modulo_de_validaciones_esta_registrado():
    """`validaciones` (XCT-01) tiene módulo, DI, migración, controller y suite
    VERDE (20 de 20): el bloqueo de SQLite que la dejaba roja se resolvió en
    el harness de fixtures, no en el módulo de dominio.

    Un controller con pruebas verdes y su módulo versionado SÍ expone rutas
    (FR-07 §3.1 regla 2). La comprobación es sobre el SURFACE REAL (el
    esquema OpenAPI del API vivo): sus dos rutas congeladas existen.
    """
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    assert "/api/validaciones/preview" in paths
    assert "/api/validaciones/confirmar" in paths


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

    Los dominios pendientes (`beneficios`) no tienen módulo terminado en el
    objetivo: sus controllers no existen y, por tanto, no pueden estar
    registrados. Si uno apareciese, su ruta existiría sin presenter, sin
    versión y sin pruebas.

    `pases` ya NO está en esa lista: DOM-03 lo implementó dentro de
    `modules/salesianos_fest` y A0 registró `PaseController` y
    `AdminPaseController` (reconciliación A0 de DOM-03, 2026-11-19).

    `patrocinadores` (DOM-08) y `competencias` (DOM-07) ya NO están en esa
    lista: A0 registró sus controllers en la reconciliación A0 de 2026-11-19
    (cierre del cableado global). `validaciones` (XCT-01) tampoco: su suite de
    integración está verde y A0 registró su controller en la reconciliación A0
    de XCT-01 (2026-11-19).

    `administracion` (XCT-02) tampoco: su suite de integración está verde y
    A0 registró sus seis controllers en la reconciliación A0 de XCT-02
    (2026-11-20). `CotizacionController` (DOM-01) tampoco: su ruta
    PROVISIONAL `POST /cotizaciones` dejó de ser código muerto cuando A0 la
    registró (2026-11-20).

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
    "modules.competencias",
    "modules.patrocinadores",
    "modules.validaciones",
    "modules.notificaciones",
    "modules.administracion",
    "modules.videos",
)

#: Módulos de DI registrados. Sólo los de las apps COMPLETADAS.
MODULOS_DE_DI_COMPLETADOS = (
    "modules.usuarios.di.UsuariosModule",
    "modules.eventos.di.EventosModule",
    "modules.pagos.di.PagosModule",
    "modules.commerce.di.CommerceModule",
    "modules.salesianos_fest.di.SalesianosFestModule",
    "modules.marketplace.di.MarketplaceModule",
    "modules.competencias.di.CompetenciasModule",
    "modules.patrocinadores.di.PatrocinadoresModule",
    "modules.validaciones.di.ValidacionesModule",
    "modules.notificaciones.di.NotificacionesModule",
    "modules.administracion.di.AdministracionModule",
    "modules.videos.di.VideosModule",
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
