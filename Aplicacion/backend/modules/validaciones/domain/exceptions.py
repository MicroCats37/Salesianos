"""Excepciones de dominio del módulo de VALIDACIONES.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`
Freeze: `FREEZE-RT-1.0.0` (`FR-05`)

Cada excepción declara un `code` ESTABLE y su status HTTP. El texto que ve el
usuario sale del catálogo público de `core/exceptions.py`: estas clases NO
construyen prosa pública (`contract/api-wrapper-presenter-contract.md` §8).

Los códigos salen del ledger congelado `FR-07` §3.3:

| Ruta | Código | Status |
|---|---|---|
| `RT-RT-01` | `TICKET_NO_ENCONTRADO` | 404 |
| `RT-RT-01` | `ACTION_NOT_ALLOWED` | 403 |
| `RT-RT-02` | `TICKET_YA_CONSUMIDO` | 409 |
| `RT-RT-02` | `CANTIDAD_EXCEDIDA` | 409 |
| `RT-RT-02` | `DERECHO_REVOCADO` | 409 |
| `RT-RT-02` | `IDEMPOTENCY_KEY_REUTILIZADA` | 409 |

`ACTION_NOT_ALLOWED` (403) lo produce la puerta compartida
`RequireAcreditacionesEscribir` de `core/permissions.py`; no se declara aquí
porque no es una excepción de este módulo.

**Petición a A0 (A0-XCT01-02).** Cuatro de estos códigos
(`TICKET_NO_ENCONTRADO`, `TICKET_YA_CONSUMIDO`, `CANTIDAD_EXCEDIDA`,
`DERECHO_REVOCADO`) todavía NO están en `PUBLIC_ERROR_MESSAGES`: hasta que A0
los catalogue, la respuesta usa el mensaje GENÉRICO del status — que es seguro
— y el detalle técnico queda en los logs. La prosa exacta que este paquete
propone está en la evidencia del paquete.
"""

from core.exceptions import ConflictError, NotFoundError
from ninja.errors import HttpError


class TicketNoEncontradoError(NotFoundError):
    """La credencial no existe en el alcance (404).

    La credencial es un SECRETO: la respuesta dice que no se encontró, nunca
    qué códigos existen ni qué derechos hay.
    """

    code = "TICKET_NO_ENCONTRADO"

    def __init__(self):
        super().__init__(resource="Ticket de validación", code=self.code)


class TicketYaConsumidoError(ConflictError):
    """La credencial ya se canjeó por completo (409).

    La relectura de un ticket consumido NO permite un segundo uso
    (`FL-10` paso 5 · `QA-V01`).
    """

    code = "TICKET_YA_CONSUMIDO"

    def __init__(self):
        super().__init__(
            message="El ticket ya fue consumido.",
            code=self.code,
        )


class CantidadExcedidaError(ConflictError):
    """La cantidad pedida no se puede confirmar (409).

    Cubre los dos sentidos del exceso (`FR-05` §2.2): pedir más unidades de
    las disponibles, y pedir una entrega parcial que el módulo dueño no
    ratifica (`PD-03` sigue ABIERTO).
    """

    code = "CANTIDAD_EXCEDIDA"

    def __init__(self):
        super().__init__(
            message="La cantidad solicitada no se puede confirmar.",
            code=self.code,
        )


class DerechoRevocadoError(ConflictError):
    """El derecho no está vigente para esta operación (409).

    El estado del derecho lo publica su módulo dueño (`PaseBeneficiario.
    estado`, `Pedido.estado`). Un derecho revocado invalida las validaciones
    futuras y conserva las pasadas (`RN-P08`).
    """

    code = "DERECHO_REVOCADO"

    def __init__(self):
        super().__init__(
            message="El derecho no está vigente para esta operación.",
            code=self.code,
        )


class IdempotencyKeyReutilizadaError(ConflictError):
    """La clave de idempotencia ya identifica otra operación (409).

    Una clave identifica UNA intención (`FR-04` §2.2): reutilizarla con otro
    código o con otra cantidad es un error del cliente, no una repetición
    tolerada.
    """

    code = "IDEMPOTENCY_KEY_REUTILIZADA"

    def __init__(self):
        super().__init__(
            message="La clave de idempotencia ya se usó con otra operación.",
            code=self.code,
        )


class VerificadorNoDisponibleError(HttpError):
    """No hay adaptador para ese tipo de derecho (500).

    Es una FALLA DE CONFIGURACIÓN, no un problema del cliente: el código de
    la credencial es correcto pero el módulo no tiene adaptador para él. El
    texto es técnico y NUNCA sale al cliente: el catálogo público lo
    sustituye por el mensaje genérico del status.
    """

    code = "VERIFICADOR_NO_DISPONIBLE"

    def __init__(self, tipo_derecho: str):
        self.code = self.code
        super().__init__(500, f"No hay verificador de derechos para '{tipo_derecho}'.")


__all__ = [
    "CantidadExcedidaError",
    "DerechoRevocadoError",
    "IdempotencyKeyReutilizadaError",
    "TicketNoEncontradoError",
    "TicketYaConsumidoError",
    "VerificadorNoDisponibleError",
]
