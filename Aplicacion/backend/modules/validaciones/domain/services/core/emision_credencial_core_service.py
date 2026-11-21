"""La escritura de la credencial (`Ticket`).

Change: `administracion-pases-alta-directa` · Apply C

Contract: `contract/django-app-architecture-contract.md` §4.3 (servicios core
SÍNCRONOS, sin `transaction.atomic` propio: la transacción la abre el flujo).

**EL CÓDIGO ES UN SECRETO.** Se genera aquí, con entropía criptográfica, y
NO se deriva del derecho: un código predecible es una credencial predecible.
Se devuelve UNA vez, en la respuesta de la emisión; no se publica en ningún
listado, no se registra en la auditoría y no se escribe en ningún log.

**UNA CREDENCIAL POR DERECHO.** Si el derecho ya tiene una credencial
VIGENTE, NO se emite una segunda: la segunda credencial duplicaría el acceso
y dejaría dos códigos vivos para la misma persona.
"""

import secrets

from django.db import IntegrityError

from core.exceptions import ConflictError
from modules.validaciones.domain.constants import EstadoTicketChoices
from modules.validaciones.domain.models import Ticket
from modules.validaciones.domain.ports.emisor_credencial import ReferenciaCredencial

#: Los bytes de entropía del código generado.
BYTES_CODIGO = 12

#: El prefijo legible del código generado.
PREFIJO_CODIGO = "FEST"


class EmisionCredencialCoreService:
    """La escritura de la credencial que referencia un derecho."""

    #: Los intentos de generar un código libre de colisiones. La colisión es
    #: improbabilísima, pero un `IntegrityError` en la emisión sería un fallo
    #: del servidor, y no tiene por qué serlo.
    INTENTOS_DE_CODIGO = 3

    @staticmethod
    def emitir(referencia: ReferenciaCredencial) -> Ticket:
        """La credencial que referencia ese derecho.

        Es ONE-SHOT por derecho: si ya hay una credencial VIGENTE para ese
        derecho, NO se emite una segunda y se lanza `ConflictError` (409).

        Raises:
            ConflictError: el derecho ya tiene una credencial vigente (409).
        """
        if EmisionCredencialCoreService._hay_credencial_vigente(
            referencia.derecho_id
        ):
            raise ConflictError()

        ultimo_error: IntegrityError | None = None
        for _intento in range(EmisionCredencialCoreService.INTENTOS_DE_CODIGO):
            codigo = EmisionCredencialCoreService._generar_codigo()
            try:
                return Ticket.objects.create(
                    codigo=codigo,
                    edicion_id=referencia.edicion_id,
                    tipo_derecho=referencia.tipo_derecho,
                    operacion=referencia.operacion,
                    pase_beneficiario_id=referencia.derecho_id,
                )
            except IntegrityError as error:
                # La única unicidad de `Ticket` es el CÓDIGO: un choque aquí
                # es una colisión de entropía, no un dato inválido.
                ultimo_error = error

        raise ultimo_error

    @staticmethod
    def _hay_credencial_vigente(derecho_id: str) -> bool:
        """Si ese derecho ya tiene una credencial VIGENTE."""
        return Ticket.objects.filter(
            pase_beneficiario_id=derecho_id,
            estado=EstadoTicketChoices.VIGENTE,
        ).exists()

    @staticmethod
    def _generar_codigo() -> str:
        """Un código impredecible. No se deriva del derecho."""
        return f"{PREFIJO_CODIGO}-{secrets.token_urlsafe(BYTES_CODIGO)}"


__all__ = [
    "BYTES_CODIGO",
    "PREFIJO_CODIGO",
    "EmisionCredencialCoreService",
]
