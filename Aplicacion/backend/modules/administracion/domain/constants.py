"""Vocabulario cerrado del módulo `administracion`.

Packet: `XCT-02` · Change: `salesianos-fest-rebuild`

Este archivo declara el vocabulario que el RESUMEN publica y que las vistas
operativas filtran. Es el ÚNICO sitio donde esos códigos viven: el frontend
recibe el código y la prosa, y nunca los inventa ni los reescribe.

## El vocabulario de los filtros del resumen

Una incidencia del resumen apunta a una vista operativa **filtrada**. Para que
el enlace sea RESOLUBLE, el nombre del filtro y el valor del filtro tienen que
ser los mismos en los dos lados:

| Código | Significado | Vista de destino |
|---|---|---|
| `estado_pago` | el saldo comercial de la inscripción | `/administracion/inscripciones` |
| `plantilla` | la completitud de la plantilla del equipo | `/administracion/equipos` |
| `estado_operativo` | el veredicto operativo del pago | `/administracion/pagos` |

`estado_operativo` es el filtro CONGELADO de `RT-PG-04` (`SH-05` `P-06`,
`F-9`): no se renombra ni se sustituye. `estado_pago` y `plantilla` los declara
este paquete (`XCT-02`) porque son los drilldowns que el resumen publica; las
rutas de listado que los atienden son las del work unit 2 de este paquete.

La lista es CERRADA: un filtro desconocido es un error de contrato, no un
filtro nuevo silencioso.
"""

from django.db import models


class FiltroResumen(models.TextChoices):
    """Los filtros con los que el resumen enlaza a las vistas operativas."""

    ESTADO_PAGO = "estado_pago", "Estado de pago"
    PLANTILLA = "plantilla", "Completitud de la plantilla"
    ESTADO_OPERATIVO = "estado_operativo", "Estado operativo"


class ValorEstadoPago(models.TextChoices):
    """Los valores del filtro `estado_pago`."""

    PENDIENTE = "PENDIENTE", "Pendiente de pago"
    PAGADO = "PAGADO", "Pagado"


class ValorPlantilla(models.TextChoices):
    """Los valores del filtro `plantilla`."""

    INCOMPLETA = "INCOMPLETA", "Plantilla incompleta"
    COMPLETA = "COMPLETA", "Plantilla completa"


class ValorEstadoOperativo(models.TextChoices):
    """Los valores del filtro `estado_operativo` (veredicto operativo)."""

    PENDIENTE = "PENDIENTE", "Pendiente de atención"
    PAGADO = "PAGADO", "Pagado"


class CodigoIncidencia(models.TextChoices):
    """El código estable de cada incidencia que el resumen publica.

    El código es MÁQUINA: la prosa viaja con él y el cliente la imprime
    verbatim. Un código que el cliente no conoce se muestra como desconocido,
    nunca se reinterpreta.
    """

    INSCRIPCIONES_PENDIENTES_DE_PAGO = (
        "INSCRIPCIONES_PENDIENTES_DE_PAGO",
        "Inscripciones con cupos sin pagar",
    )
    EQUIPOS_SIN_PLANTILLA = (
        "EQUIPOS_SIN_PLANTILLA",
        "Equipos sin plantilla activa",
    )
    LOTES_DE_PASES_PENDIENTES = (
        "LOTES_DE_PASES_PENDIENTES",
        "Lotes de pases pendientes de pago",
    )
    CORESIAS_SIN_BENEFICIARIO = (
        "CORESIAS_SIN_BENEFICIARIO",
        "Cortesías sin beneficiario asignado",
    )


class EntidadAuditada(models.TextChoices):
    """Las ENTIDADES sobre las que el ACTA transversal puede llevar registro.

    El código es MÁQUINA: es el que se filtra y el que se busca. La prosa
    acompaña al código en el acta, nunca al revés.
    """

    INSCRIPCION = "INSCRIPCION", "Inscripción"
    PARTICIPACION = "PARTICIPACION", "Participación"
    PERSONA = "PERSONA", "Persona"
    EQUIPO = "EQUIPO", "Equipo"
    PAGO = "PAGO", "Pago"
    COMPRA = "COMPRA", "Compra"
    PEDIDO = "PEDIDO", "Pedido"


class CodigoAccionAdmin(models.TextChoices):
    """Las ACCIONES sensibles que el acta transversal registra.

    Un comando sensible sin motivo NO se ejecuta: sin motivo no hay acta y
    sin acta no hay comando.
    """

    RETIRAR_PARTICIPANTE = "RETIRAR_PARTICIPANTE", "Retirar participante"
    APROBAR_PAGO_MANUAL = "APROBAR_PAGO_MANUAL", "Aprobar pago manual"
    AGREGAR_PARTICIPANTE_EQUIPO = (
        "AGREGAR_PARTICIPANTE_EQUIPO",
        "Agregar participante a un equipo",
    )
    COMPRAR_PASE_PARA_CLIENTE = (
        "COMPRAR_PASE_PARA_CLIENTE",
        "Comprar pases para un cliente",
    )
    COMPRAR_PEDIDO_PARA_CLIENTE = (
        "COMPRAR_PEDIDO_PARA_CLIENTE",
        "Comprar un pedido de tienda para un cliente",
    )


class CodigoAlertaAdmin(models.TextChoices):
    """Las ALERTAS que una fila operativa puede publicar.

    Una alerta es un HECHO con su código: el cliente la imprime y nunca
    decide que una fila está bien.
    """

    INSCRIPCIONES_PENDIENTES_DE_PAGO = (
        "INSCRIPCIONES_PENDIENTES_DE_PAGO",
        "Inscripciones con cupos sin pagar",
    )
    EQUIPOS_PLANTILLA_INCOMPLETA = (
        "EQUIPOS_PLANTILLA_INCOMPLETA",
        "Equipos con la plantilla incompleta",
    )
    PARTICIPACION_DUPLICADA = (
        "PARTICIPACION_DUPLICADA",
        "La persona participa dos veces en la misma disciplina",
    )


class CodigoAccionOperativa(models.TextChoices):
    """Las ACCIONES que el presenter proyecta en las filas del panel.

    Son PROYECCIONES (`acciones_disponibles`, `siguiente_accion`), no
    autorizaciones: el 403 del backend sigue siendo el control.
    """

    REVISAR_PAGO = "REVISAR_PAGO", "Revisar pagos"
    REVISAR_PLANTILLA = "REVISAR_PLANTILLA", "Revisar equipos"


#: Las PROSAS de los veredictos que este módulo proyecta.
#:
#: El `codigo` del veredicto es siempre el del DUEÑO del hecho; lo que este
#: módulo publica es la EXPLICACIÓN de qué significa ese código aquí.
DESCRIPCIONES_ESTADO_ADMIN = {
    "CREADA": "La inscripción está dada de alta y admite participantes.",
    "CANCELADA": "La inscripción está cancelada: no admite participantes.",
    "PENDIENTE": "El pago todavía no se ha verificado.",
    "PAGADO": "El pago está verificado y los cupos están habilitados.",
    "ACTIVA": "La participación está vigente.",
    "RETIRADA": "La participación fue retirada y ya no ocupa cupo.",
    "ACTIVO": "El equipo está vigente.",
    "RETIRADO": "El equipo fue retirado.",
    "COMPLETA": "La plantilla cumple el mínimo de la disciplina.",
    "INCOMPLETA": "La plantilla no llega al mínimo de la disciplina.",
}

#: La PROSA de las alertas operativas.
MENSAJES_ALERTA_ADMIN = {
    CodigoAlertaAdmin.INSCRIPCIONES_PENDIENTES_DE_PAGO: (
        "Hay cupos contratados que un pago verificado no habilitó."
    ),
    CodigoAlertaAdmin.EQUIPOS_PLANTILLA_INCOMPLETA: (
        "El equipo no llega al mínimo de participantes que exige su disciplina."
    ),
    CodigoAlertaAdmin.PARTICIPACION_DUPLICADA: (
        "La persona participa dos veces en la misma disciplina de la edición."
    ),
}

#: Las PROSAS de las acciones operativas proyectadas.
MENSAJES_ACCION_ADMIN = {
    CodigoAccionOperativa.REVISAR_PAGO: "Revisar los pagos de la edición.",
    CodigoAccionOperativa.REVISAR_PLANTILLA: "Revisar las plantillas de los equipos.",
}

__all__ = [
    "CodigoAccionAdmin",
    "CodigoAccionOperativa",
    "CodigoAlertaAdmin",
    "CodigoIncidencia",
    "DESCRIPCIONES_ESTADO_ADMIN",
    "EntidadAuditada",
    "FiltroResumen",
    "MENSAJES_ACCION_ADMIN",
    "MENSAJES_ALERTA_ADMIN",
    "ValorEstadoOperativo",
    "ValorEstadoPago",
    "ValorPlantilla",
]
