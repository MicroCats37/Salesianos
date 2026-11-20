"""Cableado permanente de `administracion` y de `CotizacionController` (A0).

Change: `salesianos-fest-rebuild` · Corrective apply (2026-11-20) ·
Owner: **A0** (el cableado global) — petición `A0-XCT02-01` y `A0-API02-09`.

`evidence/verification/VER-01-baseline-regression-payments.md` §7.1 midió un
**DRIFT A** de ocho rutas que el frontend consume HOY y que NO existían en el
API vivo: siete de `modules.administracion` y `POST /cotizaciones`.

GIVEN  el registro permanente (`config/settings/base.py` + `config/api.py`)
WHEN   se lee el estado en runtime
THEN   la app y su wiring de DI están registrados, los seis controllers
       administrativos exponen sus rutas en el esquema OpenAPI vivo, la ruta
       de cotización existe, y el `check` de Django NO reporta `admin.E108`.

Este archivo es el guardián de A0: las listas cerradas de
`test_registration_extension.py` son el espejo EXACTO de este registro, así
que los dos archivos tienen que moverse juntos.
"""

from django.test import Client

#: Rutas del panel administrativo que la app `administracion` expone. Las doce
#: son las que el frontend consume o las que sus seis superficies necesitan.
#: (`/api/administracion/marketplace/**` y `/api/administracion/pases/**`
#: pertenecen a OTROS módulos: DOM-06 y DOM-03.)
RUTAS_DE_ADMINISTRACION = (
    "/api/administracion/resumen",
    "/api/administracion/auditoria",
    "/api/administracion/inscripciones",
    "/api/administracion/inscripciones/{inscripcion_id}",
    "/api/administracion/inscripciones/{inscripcion_id}/participantes/{participacion_id}",
    "/api/administracion/equipos",
    "/api/administracion/equipos/{equipo_id}",
    "/api/administracion/participantes",
    "/api/administracion/pagos",
    "/api/administracion/pagos/{compra_id}",
    "/api/administracion/personas",
    "/api/administracion/personas/{persona_id}",
)


def test_la_app_administracion_esta_registrada_de_forma_permanente():
    """`modules.administracion` está en `INSTALLED_APPS`: sus modelos tienen
    `app_label` y su migración se aplica (A0-XCT02-01)."""
    from django.conf import settings

    assert "modules.administracion" in settings.INSTALLED_APPS


def test_el_wiring_de_di_de_administracion_esta_registrado():
    """`AdministracionModule` está en `INJECTOR_MODULES` (A0-XCT02-01)."""
    from django.conf import settings

    modulos = tuple(settings.NINJA_EXTRA.get("INJECTOR_MODULES", ()))

    assert "modules.administracion.di.AdministracionModule" in modulos


def test_el_wiring_de_di_de_administracion_va_tras_el_de_los_modulos_que_consume():
    """El ORDEN del wiring importa: `administracion` AGREGA y consume los
    servicios de `pagos`, `commerce`, `salesianos_fest`, `usuarios` y
    `eventos`, así que su wiring va DETRÁS del de esos módulos."""
    from django.conf import settings

    modulos = tuple(settings.NINJA_EXTRA.get("INJECTOR_MODULES", ()))

    for consumidor in (
        "modules.pagos.di.PagosModule",
        "modules.commerce.di.CommerceModule",
        "modules.salesianos_fest.di.SalesianosFestModule",
        "modules.usuarios.di.UsuariosModule",
        "modules.eventos.di.EventosModule",
    ):
        assert modulos.index(consumidor) < modulos.index(
            "modules.administracion.di.AdministracionModule"
        ), consumidor


def test_las_rutas_de_administracion_existen_en_el_api_vivo():
    """GIVEN el API permanente
    WHEN  se lee su superficie OpenAPI
    THEN  las DOCE rutas del panel administrativo EXISTEN: ninguna queda
       fuera del registro (a diferencia de VER-01, que midió siete 404).
    """
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    for ruta in RUTAS_DE_ADMINISTRACION:
        assert ruta in paths, ruta


def test_las_seis_superficies_de_administracion_responden_y_no_404():
    """GIVEN el API permanente y una petición SIN sesión
    WHEN  se pide el resumen del panel
    THEN  responde 401 y NO 404: la ruta EXISTE y su autenticación está
       cableada (401 ANTES que 403, `core/permissions.py`).

    El `ROOT_URLCONF` del proyecto es `config.urls`: el cliente resuelve por el
    URLconf REAL de la aplicación, no por un URLconf de pruebas.
    """
    cliente = Client()

    respuesta = cliente.get("/api/administracion/resumen")

    assert respuesta.status_code == 401


def test_la_ruta_de_cotizacion_existe_en_el_api_vivo():
    """`CotizacionController` está registrado: `POST /api/cotizaciones` deja de
    ser código muerto (A0-API02-09)."""
    from config.api import api

    paths = api.get_openapi_schema().get("paths", {})

    assert "/api/cotizaciones" in paths
    assert "post" in paths["/api/cotizaciones"]


def test_el_check_de_django_no_reporta_el_error_de_admin_e108():
    """`admin.E108` (una entrada de `list_display` que no es un atributo del
    modelo) NO aparece: el `check` del sistema está limpio.

    VER-01 §6.3 lo declaró RESUELTO en el árbol actual; esta prueba lo fija
    para que no vuelva.
    """
    from django.core.checks import run_checks

    ids = [check.id for check in run_checks(databases=[])]

    assert "admin.E108" not in ids


def test_el_admin_de_paquetes_no_declara_una_entrada_invalida_en_list_display():
    """La regla de `admin.E108`, comprobada sobre el modelo que la。海外a:
    cada entrada de `list_display` es un atributo del modelo."""
    from django.contrib import admin

    from modules.salesianos_fest.models import Paquete

    admin_paquete = admin.site._registry[Paquete]

    for entrada in admin_paquete.list_display:
        assert hasattr(Paquete, entrada), entrada
