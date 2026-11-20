"""`AdminResumenPresenter` — la proyección HTTP del resumen operativo.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

El presenter NO calcula cifras: proyecta el resultado del dominio a la forma
HTTP. Lo único que arma es el `href` del drilldown: la ruta del panel que
EXISTE y el filtro DECLARADO que la incidencia declara (`FiltroResumen`).

El `href` es un hecho del BACKEND, no una decisión del navegador: el cliente
no inventa rutas ni filtros (`D-API01-01`).
"""

from urllib.parse import urlencode

from modules.administracion.presentation.schemas.admin_resumen_schemas import (
    ResumenAccionOut,
    ResumenIncidenciaOut,
    ResumenMetricaOut,
    ResumenOperativoOut,
)

#: Las vistas operativas del panel a las que un drilldown puede apuntar.
#:
#: Son las rutas que el panel TIENE (`src/lib/routes.ts`): un enlace a una
#: vista que no existe sería un dead end y por tanto un enlace roto.
VISTAS_PANEL = {
    "inscripciones": "/administracion/inscripciones",
    "equipos": "/administracion/equipos",
    "participantes": "/administracion/participantes",
    "pagos": "/administracion/pagos",
    "pases": "/administracion/pases",
    "validaciones": "/administracion/validaciones",
}


class AdminResumenPresenter:
    """Proyecta el resumen del dominio a la forma HTTP."""

    @staticmethod
    def present(resultado) -> ResumenOperativoOut:
        """La forma HTTP del resumen de una edición."""
        return ResumenOperativoOut(
            edicion_id=resultado.edicion_id,
            edicion_nombre=resultado.edicion_nombre,
            edicion_estado=resultado.edicion_estado,
            metricas=[
                AdminResumenPresenter.present_metrica(metrica)
                for metrica in resultado.metricas
            ],
            incidencias=[
                AdminResumenPresenter.present_incidencia(incidencia)
                for incidencia in resultado.incidencias
            ],
        )

    @staticmethod
    def present_metrica(metrica) -> ResumenMetricaOut:
        """La forma HTTP de una cifra."""
        return ResumenMetricaOut(
            codigo=metrica.codigo,
            etiqueta=metrica.etiqueta,
            descripcion=metrica.descripcion,
            valor=metrica.valor,
        )

    @staticmethod
    def present_incidencia(incidencia) -> ResumenIncidenciaOut:
        """La forma HTTP de una incidencia y su acción."""
        return ResumenIncidenciaOut(
            codigo=incidencia.codigo,
            etiqueta=incidencia.etiqueta,
            descripcion=incidencia.descripcion,
            cantidad=incidencia.cantidad,
            accion=ResumenAccionOut(
                codigo=incidencia.accion_codigo,
                etiqueta=incidencia.accion_etiqueta,
                href=AdminResumenPresenter.href_de_incidencia(incidencia),
            ),
        )

    @staticmethod
    def href_de_incidencia(incidencia) -> str:
        """La vista operativa FILTRADA de una incidencia.

        La ruta sale de `VISTAS_PANEL` y el filtro de `FiltroResumen`. Una
        vista que el panel no tiene NO se publica: el enlace caería en un
        dead end.
        """
        base = VISTAS_PANEL.get(incidencia.vista)

        if not base:
            return "/administracion"

        if not incidencia.filtro:
            return base

        return f"{base}?{urlencode({incidencia.filtro: incidencia.filtro_valor})}"


__all__ = ["AdminResumenPresenter", "VISTAS_PANEL"]
