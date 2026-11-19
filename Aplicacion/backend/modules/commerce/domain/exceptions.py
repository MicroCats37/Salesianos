"""Excepciones de dominio del módulo `commerce`.

Freeze: `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-04-commerce-payments-idempotency.md`

Reglas que se aplican a TODAS estas excepciones
(`contract/django-app-architecture-contract.md` §10,
`contract/api-wrapper-presenter-contract.md` §8):

- Declaran un `code` estable y legible por máquina.
- El TEXTO que construyen es técnico: **nunca** sale al cliente.
- El mensaje público lo decide el catálogo `core/exceptions.py` a partir del
  `code`.
- No interpolan UUIDs, ids internos, montos, SQL ni payloads de proveedores.

`COMPRA_NO_AUTORIZADA` y `COMPRA_SIN_COMPRADOR` ya están en el catálogo público
de A0. `COMPRA_TOTAL_INCOHERENTE` y `COMPRA_REFERENCIA_INVALIDA` proceden de
este paquete y su prosa pública está REQUESTED a A0 (ver la evidencia de
FND-04).
"""

from core.exceptions import ConflictError, UnprocessableEntityError
from ninja.errors import HttpError


class CompraNoAutorizadaError(ConflictError):
    """El actor no puede operar sobre esta compra (403/409).

    La titularidad se comprueba contra la persona compradora: el documento de
    identidad NO es una credencial (RN-U04).
    """

    code = "COMPRA_NO_AUTORIZADA"

    def __init__(self):
        super().__init__(
            "No tiene autorización para realizar esta acción.",
            code=self.code,
        )


class CompraSinCompradorError(HttpError):
    """La compra no tiene comprador persona (422).

    Una compra **siempre** tiene comprador: es la persona que paga (FR-04
    §1.1). Una cuenta técnica sin persona no puede comprar.
    """

    code = "COMPRA_SIN_COMPRADOR"

    def __init__(self):
        super().__init__(422, "La compra no tiene un comprador asignado.")


class CompraTotalIncoherenteError(UnprocessableEntityError):
    """El total declarado no coincide con el total de las líneas (422).

    El total **lo congela el servidor** a partir de las líneas de la compra
    (`RN-C02`): el cliente no impone un importe. Si el total recibido no
    coincide con el derivado de las líneas, la compra se rechaza en lugar de
    aceptarse un importe arbitrario. El código está REQUESTED a A0 (ver la
    evidencia de FND-04).
    """

    code = "COMPRA_TOTAL_INCOHERENTE"

    def __init__(self):
        super().__init__(
            message="El total de la compra no coincide con sus líneas.",
            code=self.code,
        )


class CompraReferenciaInvalidaError(UnprocessableEntityError):
    """La referencia de intención de la compra no es válida (422).

    La referencia identifica **una intención de compra** y es lo que permite
    reutilizar una compra pendiente en vez de duplicarla (FR-04 I-4). El
    código está REQUESTED a A0 (ver la evidencia de FND-04).
    """

    code = "COMPRA_REFERENCIA_INVALIDA"

    def __init__(self):
        super().__init__(
            message="La referencia de la compra no es válida.",
            code=self.code,
        )


class CompraNoEncontradaError(HttpError):
    """La compra referenciada no existe (404).

    El código está REQUESTED a A0 (ver la evidencia de FND-04).
    """

    code = "COMPRA_NO_ENCONTRADA"

    def __init__(self):
        super().__init__(404, "No se encontró la compra solicitada.")


__all__ = [
    "CompraNoAutorizadaError",
    "CompraNoEncontradaError",
    "CompraReferenciaInvalidaError",
    "CompraSinCompradorError",
    "CompraTotalIncoherenteError",
]
