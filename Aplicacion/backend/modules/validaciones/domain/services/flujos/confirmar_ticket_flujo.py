"""`ConfirmarTicketFlujo` — el canje atómico e idempotente de una credencial.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` · `FR-05` §2.2 · `FR-04` §2.2 · `RN-P07`

**ES UNA MUTACIÓN ATÓMICA.** Todo el canje ocurre en UNA transacción: la
revalidación bajo bloqueo, el consumo en el módulo dueño y el acta de
auditoría. O pasa todo, o no pasa nada.

**REVALIDA EN EL MOMENTO DE CONFIRMAR** (`FR-05` §2.2): no confía en el
preview. El dueño vuelve a comprobar su regla BAJO BLOQUEO, de modo que dos
operadores simultáneos sólo pueden consumir la cantidad autorizada
(`QA-V02`).

**LA IDEMPOTENCIA** es por CLAVE: una repetición devuelve el resultado de la
primera ejecución y reutilizar la clave con otra carga es un error del
cliente (`FR-04` §2.2).

**EL RECHAZO QUEDA EN EL HISTORIAL** (`RN-P07`): el acta del intento denegado
se escribe en la MISMA transacción que lo produjo y se confirma; el error
se lanza DESPUÉS, para que el registro no se pierda.
"""

from asgiref.sync import sync_to_async
from django.db import transaction
from injector import inject

from modules.validaciones.domain.constants import (
    EstadoTicketChoices,
    ResultadoValidacionChoices,
)
from modules.validaciones.domain.exceptions import (
    CantidadExcedidaError,
    DerechoRevocadoError,
    IdempotencyKeyReutilizadaError,
    TicketNoEncontradoError,
    TicketYaConsumidoError,
)
from modules.validaciones.domain.results.validacion_results import (
    TicketConfirmadoResult,
)
from modules.validaciones.domain.schemas.validacion_schemas import ConfirmarTicketData
from modules.validaciones.domain.selectors.ticket_selector import (
    TicketSelector,
    referencia_de,
)
from modules.validaciones.domain.services.core.validacion_core_service import (
    MOTIVO_POR_CODIGO,
    ValidacionCoreService,
)
from modules.validaciones.infrastructure.services import RegistroVerificadoresDerecho

#: Los errores de dominio que PRODUCEN un acta denegada.
ERRORES_DENEGABLES = (
    TicketYaConsumidoError,
    CantidadExcedidaError,
    DerechoRevocadoError,
)


class ConfirmarTicketFlujo:
    """El flujo async del canje confirmado."""

    @inject
    def __init__(
        self,
        selector: TicketSelector | None = None,
        core: ValidacionCoreService | None = None,
        registro: RegistroVerificadoresDerecho | None = None,
    ):
        self.selector = selector or TicketSelector()
        self.core = core or ValidacionCoreService()
        self.registro = registro or RegistroVerificadoresDerecho()

    async def _confirmar(
        self,
        actor_usuario_id: str | None,
        actor_persona_id: str | None,
        data: ConfirmarTicketData,
    ) -> TicketConfirmadoResult:
        """El canje confirmado de la credencial indicada."""
        return await sync_to_async(self._confirmar_sync)(
            actor_usuario_id,
            actor_persona_id,
            data,
        )

    # ── Internos ──────────────────────────────────────────────────────────────

    def _confirmar_sync(
        self,
        actor_usuario_id: str | None,
        actor_persona_id: str | None,
        data: ConfirmarTicketData,
    ) -> TicketConfirmadoResult:
        """El cuerpo sync del canje: una transacción, un resultado."""
        huella = self.core.huella_de(data.codigo, data.cantidad)
        resultado: TicketConfirmadoResult | None = None
        error: Exception | None = None

        with transaction.atomic():
            previa = self.selector.obtener_acta_por_idempotencia(
                data.idempotency_key, bloquear=True
            )
            if previa is not None:
                # Repetición: el resultado de la primera ejecución.
                resultado = self.core.repetir(previa, huella)
            else:
                ticket = self.selector.obtener_por_codigo(
                    data.codigo, bloquear=True
                )
                if ticket is None:
                    # No hay credencial: NO hay acta que escribir.
                    raise TicketNoEncontradoError()
                if ticket.estado != EstadoTicketChoices.VIGENTE:
                    error = DerechoRevocadoError()
                    self._registrar_denegacion(
                        ticket,
                        actor_usuario_id,
                        actor_persona_id,
                        data,
                        huella,
                        error,
                    )
                else:
                    try:
                        resultado = self._consumir(
                            ticket,
                            actor_usuario_id,
                            actor_persona_id,
                            data,
                            huella,
                        )
                    except ERRORES_DENEGABLES as Rechazo:
                        error = Rechazo
                        repetida = self._registrar_denegacion(
                            ticket,
                            actor_usuario_id,
                            actor_persona_id,
                            data,
                            huella,
                            error,
                        )
                        if repetida is not None:
                            # Otra ejecución con la MISMA clave ya había
                            # confirmado: su resultado es el bueno
                            # (`FR-04` §2.2).
                            resultado = repetida
                            error = None

        if error is not None:
            raise error
        return resultado

    def _consumir(
        self,
        ticket,
        actor_usuario_id: str | None,
        actor_persona_id: str | None,
        data: ConfirmarTicketData,
        huella: str,
    ) -> TicketConfirmadoResult:
        """El consumo en el módulo dueño y el acta, en la misma transacción."""
        verificador = self.registro.verificador_de(ticket.tipo_derecho)
        referencia = referencia_de(ticket)

        antes = verificador.resolver(referencia)
        despues = verificador.consumir(
            referencia, data.cantidad, actor_usuario_id
        )
        consumida = max(0, despues.cantidad_consumida - antes.cantidad_consumida)

        acta = self.core.registrar_consumo(
            ticket=ticket,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
            idempotency_key=data.idempotency_key,
            huella=huella,
            cantidad=consumida,
            cantidad_restante=despues.cantidad_disponible,
        )
        return self.core.resultado_de(acta, repetido=False)

    def _registrar_denegacion(
        self,
        ticket,
        actor_usuario_id: str | None,
        actor_persona_id: str | None,
        data: ConfirmarTicketData,
        huella: str,
        error: Exception,
    ) -> TicketConfirmadoResult | None:
        """El acta del intento denegado, dentro de la misma transacción.

        Devuelve el resultado de la ejecución VINCULANTE si la clave ya
        estaba usada por un canje PERMITIDO (carrera de dos peticiones con
        la misma clave): en ese caso la repetición gana y NO se lanza el
        error.
        """
        codigo = getattr(error, "code", "") or ""
        existente = self.core.registrar_denegacion(
            ticket=ticket,
            actor_usuario_id=actor_usuario_id,
            actor_persona_id=actor_persona_id,
            idempotency_key=data.idempotency_key,
            huella=huella,
            motivo_codigo=codigo,
            motivo_mensaje=MOTIVO_POR_CODIGO.get(codigo, ""),
        )
        if (
            existente is not None
            and existente.resultado == ResultadoValidacionChoices.PERMITIDO
        ):
            if existente.huella != huella:
                raise IdempotencyKeyReutilizadaError()
            return self.core.resultado_de(existente, repetido=True)
        return None


__all__ = [
    "ERRORES_DENEGABLES",
    "ConfirmarTicketFlujo",
]
