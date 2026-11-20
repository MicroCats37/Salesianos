"""`AdminResumenSelector` — los agregados de la edición para el panel.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Este selector NO es dueño de ningún dato: cuenta hechos que los módulos DUEÑOS
publican. Lee los modelos del módulo dueño a través de su capa `domain/models`
y NO importa jamás la capa `presentation/` de otro módulo.

Las reglas que el selector NO reimplementa: qué es una inscripción viva lo
decide `EstadoInscripcion` del dueño, qué es una plantilla activa lo decide
`EstadoParticipacion` y qué es un lote pendiente de pago lo decide
`EstadoCompraPase`.

El selector sólo cuenta y proyecta: la etiqueta de cada cifra y el drilldown de
cada incidencia los declara el módulo (`domain/constants.py`).
"""

from django.db.models import F, Sum

from modules.administracion.domain.constants import (
    CodigoIncidencia,
    FiltroResumen,
    ValorEstadoOperativo,
    ValorEstadoPago,
    ValorPlantilla,
)
from modules.administracion.domain.results.admin_resultados import (
    ResumenIncidenciaResultado,
    ResumenMetricaResultado,
)
from modules.salesianos_fest.domain.constants import (
    EstadoCompraPase,
    EstadoDerechoPase,
    EstadoParticipacion,
)
from modules.salesianos_fest.domain.models import (
    CompraPase,
    Equipo,
    Inscripcion,
    PaseBeneficiario,
    Participacion,
)


class AdminResumenSelector:
    """Agregados de lectura de UNA edición."""

    def _participaciones_activas(self, edicion_id):
        return Participacion.objects.filter(
            edicion_id=edicion_id,
            estado=EstadoParticipacion.ACTIVA,
        )

    def metricas(self, edicion_id) -> list:
        """Las cifras del resumen, en el orden en que se publican."""
        inscripciones = Inscripcion.objects.filter(edicion_id=edicion_id)
        totales = inscripciones.aggregate(
            pagados=Sum("cupos_pagados"),
            asignados=Sum("cupos_asignados"),
        )
        pagados = totales["pagados"] or 0
        asignados = totales["asignados"] or 0
        equipos = Equipo.objects.filter(inscripcion__edicion_id=edicion_id)

        return [
            ResumenMetricaResultado(
                codigo="INSCRIPCIONES",
                etiqueta="Inscripciones",
                descripcion="Inscripciones dadas de alta en la edición.",
                valor=inscripciones.count(),
            ),
            ResumenMetricaResultado(
                codigo="EQUIPOS",
                etiqueta="Equipos",
                descripcion="Equipos declarados en las inscripciones.",
                valor=equipos.count(),
            ),
            ResumenMetricaResultado(
                codigo="PARTICIPANTES_ACTIVOS",
                etiqueta="Participantes activos",
                descripcion="Participaciones activas de la edición.",
                valor=self._participaciones_activas(edicion_id).count(),
            ),
            ResumenMetricaResultado(
                codigo="CUPOS_PAGADOS",
                etiqueta="Cupos pagados",
                descripcion="Cupos habilitados por un pago verificado.",
                valor=pagados,
            ),
            ResumenMetricaResultado(
                codigo="CUPOS_DISPONIBLES",
                etiqueta="Cupos disponibles",
                descripcion="Cupos pagados que todavía no están asignados.",
                valor=max(pagados - asignados, 0),
            ),
            ResumenMetricaResultado(
                codigo="LOTES_DE_PASES",
                etiqueta="Lotes de pases",
                descripcion="Lotes de pases comprados en la edición.",
                valor=CompraPase.objects.filter(edicion_id=edicion_id).count(),
            ),
            ResumenMetricaResultado(
                codigo="BENEFICIARIOS_ACTIVOS",
                etiqueta="Beneficiarios activos",
                descripcion="Derechos de entrada vigentes de la edición.",
                valor=PaseBeneficiario.objects.filter(
                    compra_pase__edicion_id=edicion_id,
                    estado=EstadoDerechoPase.ACTIVO,
                ).count(),
            ),
        ]

    def incidencias(self, edicion_id) -> list:
        """Los problemas visibles del resumen y su drilldown declarado."""
        pendientes_pago = Inscripcion.objects.filter(
            edicion_id=edicion_id,
            cupos_pagados__lt=F("cupos_solicitados"),
        ).count()

        con_plantilla = self._participaciones_activas(edicion_id).values("equipo_id")
        sin_plantilla = (
            Equipo.objects.filter(inscripcion__edicion_id=edicion_id)
            .exclude(id__in=con_plantilla)
            .count()
        )

        lotes_pendientes = CompraPase.objects.filter(
            edicion_id=edicion_id,
            estado=EstadoCompraPase.PENDIENTE,
        ).count()

        return [
            ResumenIncidenciaResultado(
                codigo=CodigoIncidencia.INSCRIPCIONES_PENDIENTES_DE_PAGO,
                etiqueta="Inscripciones con cupos sin pagar",
                descripcion="Cupos contratados que un pago verificado no habilitó.",
                cantidad=pendientes_pago,
                vista="inscripciones",
                filtro=FiltroResumen.ESTADO_PAGO,
                filtro_valor=ValorEstadoPago.PENDIENTE,
                accion_codigo="REVISAR_INSCRIPCIONES",
                accion_etiqueta="Revisar inscripciones",
            ),
            ResumenIncidenciaResultado(
                codigo=CodigoIncidencia.EQUIPOS_SIN_PLANTILLA,
                etiqueta="Equipos sin plantilla activa",
                descripcion="Equipos sin ninguna participación activa.",
                cantidad=sin_plantilla,
                vista="equipos",
                filtro=FiltroResumen.PLANTILLA,
                filtro_valor=ValorPlantilla.INCOMPLETA,
                accion_codigo="REVISAR_EQUIPOS",
                accion_etiqueta="Revisar equipos",
            ),
            ResumenIncidenciaResultado(
                codigo=CodigoIncidencia.LOTES_DE_PASES_PENDIENTES,
                etiqueta="Lotes de pases pendientes de pago",
                descripcion="Lotes comprados que todavía no habilitan ningún derecho.",
                cantidad=lotes_pendientes,
                vista="pagos",
                filtro=FiltroResumen.ESTADO_OPERATIVO,
                filtro_valor=ValorEstadoOperativo.PENDIENTE,
                accion_codigo="REVISAR_PAGOS",
                accion_etiqueta="Revisar pagos",
            ),
        ]


__all__ = ["AdminResumenSelector"]
