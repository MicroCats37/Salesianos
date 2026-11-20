"""Vocabulario cerrado del módulo de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` (`FR-05` §3.1)

Los valores son ESTABLES: viajan por el cable (`tipo_derecho`, `operacion`,
`resultado`) y los publica el presenter. Son los mismos que el ledger
`FR-07` §3.3 congela para `RT-RT-01` y `RT-RT-02`.
"""

from django.db import models


class TipoDerechoChoices(models.TextChoices):
    """El discriminante del MÓDULO DUEÑO del derecho (`FR-05` §3.1).

    `PASE` y `ENTRADA_CORTESIA` los produce `salesianos_fest`; `PRODUCTO` lo
    produce `marketplace`. `INSCRIPCION` queda FUERA de este freeze: un cupo
    deportivo no es una entrada (`DEC-07`) y no se valida en la puerta.
    """

    PASE = "PASE", "Pase comprado"
    ENTRADA_CORTESIA = "ENTRADA_CORTESIA", "Entrada de cortesía"
    PRODUCTO = "PRODUCTO", "Producto de la tienda"


class OperacionValidacionChoices(models.TextChoices):
    """La operación que el operador ejecuta (`FL-10` paso 1).

    El INGRESO y la ENTREGA comparten INFRAESTRUCTURA, nunca la pantalla ni la
    decisión de negocio (`RB-07`): cada operación tiene su propio módulo
    dueño y su propia regla.
    """

    INGRESO = "INGRESO", "Ingreso a la fiesta"
    ENTREGA = "ENTREGA", "Entrega de la tienda"


class ResultadoValidacionChoices(models.TextChoices):
    """El resultado auditado de una validación (`FR-05` §2.2).

    Un `DENEGADO` también queda en el historial: el intento fallido es un
    hecho auditable (`RN-P07`).
    """

    PERMITIDO = "PERMITIDO", "Permitido"
    DENEGADO = "DENEGADO", "Denegado"


class EstadoTicketChoices(models.TextChoices):
    """El estado de la CREDENCIAL (`Ticket`).

    El ticket NO tiene ciclo de vida propio más allá de su credencial: el
    estado del DERECHO lo publica su módulo dueño (`PaseBeneficiario.estado`,
    `Pedido.estado_entrega`). `REVOCADO` existe para que una credencial
    emitida pueda invalidarse sin borrar la auditoría que ya dejó.
    """

    VIGENTE = "VIGENTE", "Vigente"
    REVOCADO = "REVOCADO", "Revocado"


#: La operación que corresponde a cada tipo de derecho.
#:
#: Es UNA regla, escrita una vez: la base de datos la impone con una
#: restricción y el dominio la lee. El ticket no puede decir "entrega" y
#: apuntar a un pase (`FR-05` §1: el ticket NO inventa el derecho).
OPERACION_POR_TIPO_DERECHO = {
    TipoDerechoChoices.PASE: OperacionValidacionChoices.INGRESO,
    TipoDerechoChoices.ENTRADA_CORTESIA: OperacionValidacionChoices.INGRESO,
    TipoDerechoChoices.PRODUCTO: OperacionValidacionChoices.ENTREGA,
}


__all__ = [
    "OPERACION_POR_TIPO_DERECHO",
    "EstadoTicketChoices",
    "OperacionValidacionChoices",
    "ResultadoValidacionChoices",
    "TipoDerechoChoices",
]
