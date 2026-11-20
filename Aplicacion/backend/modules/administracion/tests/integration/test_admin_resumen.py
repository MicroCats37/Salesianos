"""Tests del resumen operativo transversal.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

GIVEN  el resumen de una edición
WHEN   se leen sus cifras y sus incidencias
THEN   las cifras cuentan los hechos del módulo DUEÑO y cada incidencia
       declara un filtro del vocabulario cerrado y apunta a una vista
       operativa FILTRADA del panel.
"""

from modules.administracion.domain.constants import (
    FiltroResumen,
    ValorEstadoPago,
)
from modules.administracion.domain.results.admin_resultados import (
    ResumenIncidenciaResultado,
)
from modules.administracion.presentation.presenters.admin_resumen_presenter import (
    AdminResumenPresenter,
)


def test_las_cifras_cuentan_los_hechos_del_dueno(
    db,
    selector,
    edicion_publicada,
    inscripcion,
):
    metricas = selector.metricas(edicion_publicada.id)
    por_codigo = {metrica.codigo: metrica.valor for metrica in metricas}

    assert por_codigo["INSCRIPCIONES"] >= 1
    assert por_codigo["CUPOS_DISPONIBLES"] <= por_codigo["CUPOS_PAGADOS"]

    for metrica in metricas:
        assert metrica.codigo
        assert metrica.etiqueta
        assert metrica.descripcion


def test_cada_incidencia_declara_un_filtro_del_vocabulario_cerrado(
    db,
    selector,
    edicion_publicada,
    inscripcion,
):
    declarados = set(FiltroResumen.values)
    incidencias = selector.incidencias(edicion_publicada.id)

    assert incidencias

    for incidencia in incidencias:
        assert incidencia.filtro in declarados
        assert incidencia.cantidad >= 0
        assert incidencia.accion_codigo
        assert incidencia.accion_etiqueta


def _incidencia(vista, filtro, filtro_valor):
    return ResumenIncidenciaResultado(
        codigo="INSCRIPCIONES_PENDIENTES_DE_PAGO",
        etiqueta="Inscripciones con cupos sin pagar",
        descripcion="Cupos contratados que un pago verificado no habilitó.",
        cantidad=3,
        vista=vista,
        filtro=filtro,
        filtro_valor=filtro_valor,
        accion_codigo="REVISAR_INSCRIPCIONES",
        accion_etiqueta="Revisar inscripciones",
    )


def test_el_drilldown_apunta_a_una_vista_filtrada_del_panel():
    incidencia = _incidencia(
        "inscripciones",
        FiltroResumen.ESTADO_PAGO,
        ValorEstadoPago.PENDIENTE,
    )

    href = AdminResumenPresenter.href_de_incidencia(incidencia)

    assert href == "/administracion/inscripciones?estado_pago=PENDIENTE"


def test_una_vista_que_el_panel_no_tiene_no_publica_un_enlace_roto():
    incidencia = _incidencia(
        "vista_que_no_existe",
        FiltroResumen.ESTADO_PAGO,
        ValorEstadoPago.PENDIENTE,
    )

    assert AdminResumenPresenter.href_de_incidencia(incidencia) == "/administracion"
