"""El servicio CORE de VALIDACIONES: la auditoría y la idempotencia.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-04` §2.2 · `FR-05` §2.2

Es SYNC y NO abre su propia transacción
(`contract/django-app-architecture-contract.md` §4.3): la transacción la abre
el flujo que lo llama.

Responsabilidades:

- escribir el ACTA de cada intento (permitido o denegado);
- calcular la HUELLA de una intención, para distinguir una repetición fiel
  de un reusing con otra carga;
- reponer el resultado de una ejecución previa cuando la clave de
  idempotencia se repite.
"""

import hashlib

from django.db import IntegrityError, transaction

from modules.validaciones.domain.constants import ResultadoValidacionChoices
from modules.validaciones.domain.exceptions import (
    CantidadExcedidaError,
    DerechoRevocadoError,
    IdempotencyKeyReutilizadaError,
    TicketYaConsumidoError,
)
from modules.validaciones.domain.models import ValidacionTicket
from modules.validaciones.domain.results.validacion_results import (
    TicketConfirmadoResult,
)


#: El estado que publica un canje confirmado (`FR-05` §3.2).
ESTADO_CANJEADO = "CANJEADO"

#: La excepción de dominio que corresponde a cada motivo de un rechazo.
#:
#: El mapa traduce el CÓDIGO estable del motivo en la excepción tipada que
#: el catálogo público traduce a su mensaje. Es el ÚNICO lugar donde el
#: módulo relaciona un motivo con su error.
EXCEPCION_POR_MOTIVO = {
    "TICKET_YA_CONSUMIDO": TicketYaConsumidoError,
    "CANTIDAD_EXCEDIDA": CantidadExcedidaError,
    "DERECHO_REVOCADO": DerechoRevocadoError,
}


#: La prosa pública y SEGURA del motivo de cada rechazo.
#:
#: Es lo que queda en el ACTA: explica el intento sin exponer identificadores,
#: UUIDs ni detalles técnicos.
MOTIVO_POR_CODIGO = {
    "TICKET_NO_ENCONTRADO": "La credencial no existe.",
    "TICKET_YA_CONSUMIDO": "La credencial ya fue consumida.",
    "CANTIDAD_EXCEDIDA": "La cantidad solicitada no se puede confirmar.",
    "DERECHO_REVOCADO": "El derecho no está vigente.",
    "IDEMPOTENCY_KEY_REUTILIZADA": "La operación ya se confirmó con otra carga.",
    "CREDENCIAL_REVOCADA": "La credencial fue revocada.",
}


class ValidacionCoreService:
    """La escritura del acta y la idempotencia del canje."""

    @staticmethod
    def huella_de(codigo: str, cantidad: int | None) -> str:
        """La huella de una INTENCIÓN (código + cantidad).

        Es una huella, no un secreto: el código de la credencial NUNCA se
        guarda en claro en el acta, sólo su resumen.
        """
        resumen = hashlib.sha256(
            f"{codigo}|{cantidad if cantidad is not None else 'todos'}".encode(
                "utf-8"
            )
        )
        return resumen.hexdigest()

    @staticmethod
    def registrar_consumo(
        *,
        ticket,
        actor_usuario_id,
        actor_persona_id,
        idempotency_key: str,
        huella: str,
        cantidad: int,
        cantidad_restante: int,
    ) -> ValidacionTicket:
        """Escribe el ACTA de un canje PERMITIDO.

        Es idempotente por la clave: si otra ejecución con la MISMA clave
        ganó la carrera, su acta es la buena y esta NO se duplica.
        """
        try:
            with transaction.atomic():
                return ValidacionTicket.objects.create(
                    ticket=ticket,
                    operacion=ticket.operacion,
                    resultado=ResultadoValidacionChoices.PERMITIDO,
                    actor_usuario_id=actor_usuario_id,
                    actor_persona_id=actor_persona_id,
                    cantidad=cantidad,
                    cantidad_restante=cantidad_restante,
                    motivo_codigo="",
                    motivo_mensaje="",
                    idempotency_key=idempotency_key,
                    huella=huella,
                )
        except IntegrityError:
            # Otra ejecución con la misma clave ganó la carrera: SU acta es
            # la buena (`FR-04` I-2).
            existente = ValidacionTicket.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            if existente is None:
                raise
            return existente

    @staticmethod
    def registrar_denegacion(
        *,
        ticket,
        actor_usuario_id,
        actor_persona_id,
        idempotency_key: str,
        huella: str,
        motivo_codigo: str,
        motivo_mensaje: str,
    ) -> ValidacionTicket | None:
        """Escribe el ACTA de un intento DENEGADO.

        El rechazo NO consume, pero QUEDA en el historial (`RN-P07`): el
        operador necesita saber qué se intentó.

        Se escribe FUERA de la transacción que el rechazo revirtió: por eso
        abre la suya con `transaction.atomic()`. Si la clave ya está usada
        (carrera), no se duplica el acta.
        """
        if ticket is None:
            return None
        try:
            with transaction.atomic():
                return ValidacionTicket.objects.create(
                    ticket=ticket,
                    operacion=ticket.operacion,
                    resultado=ResultadoValidacionChoices.DENEGADO,
                    actor_usuario_id=actor_usuario_id,
                    actor_persona_id=actor_persona_id,
                    cantidad=0,
                    cantidad_restante=0,
                    motivo_codigo=motivo_codigo,
                    motivo_mensaje=motivo_mensaje,
                    idempotency_key=idempotency_key,
                    huella=huella,
                )
        except IntegrityError:
            return ValidacionTicket.objects.filter(
                idempotency_key=idempotency_key
            ).first()

    @staticmethod
    def resultado_de(acta: ValidacionTicket, *, repetido: bool) -> TicketConfirmadoResult:
        """El resultado de un canje, a partir de su acta."""
        return TicketConfirmadoResult(
            validacion_id=str(acta.id),
            tipo_derecho=acta.ticket.tipo_derecho,
            cantidad_consumida=acta.cantidad,
            cantidad_restante=acta.cantidad_restante,
            estado=ESTADO_CANJEADO,
            consumido_en=acta.registrado_en,
            actor_usuario_id=(
                str(acta.actor_usuario_id) if acta.actor_usuario_id else None
            ),
            actor_persona_id=(
                str(acta.actor_persona_id) if acta.actor_persona_id else None
            ),
            repetido=repetido,
        )

    @staticmethod
    def repetir(acta: ValidacionTicket, huella: str) -> TicketConfirmadoResult:
        """El resultado de la ejecución PREVIA de una clave repetida.

        - Si la ejecución previa fue PERMITIDA, devuelve su MISMO dato con
          `repetido=True` (`FR-05` §3.2).
        - Si fue DENEGADA, vuelve a lanzar el MISMO error: la repetición de un
          rechazo es el mismo rechazo.
        - Si la intención es OTRA (misma clave, otra carga), es un error del
          cliente (`FR-04` §2.2).
        """
        if acta.huella != huella:
            raise IdempotencyKeyReutilizadaError()

        if acta.resultado == ResultadoValidacionChoices.DENEGADO:
            excepcion = EXCEPCION_POR_MOTIVO.get(acta.motivo_codigo)
            if excepcion is not None:
                raise excepcion()
            raise IdempotencyKeyReutilizadaError()

        return ValidacionCoreService.resultado_de(acta, repetido=True)


__all__ = [
    "ESTADO_CANJEADO",
    "EXCEPCION_POR_MOTIVO",
    "ValidacionCoreService",
]
