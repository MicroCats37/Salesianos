"""La REFERENCIA DE INTENCIÓN de la compra de PASES.

Packet: `DOM-03` · Change: `salesianos-fest-rebuild`

La referencia es la IDENTIDAD de la intención de compra. La usa `commerce`
para reutilizar la compra pendiente en vez de duplicarla (`FR-04` I-4) y la
usa el ACTIVADOR de derechos para saber a qué lote pertenece la compra que
acaba de pagarse.

Formato (cerrado):

    PASE:{edicion_id}:{pase_id}:{comprador_id}:{cantidad}

La referencia es **ESTABLE**: dos peticiones idénticas del mismo comprador
sobre el mismo pase con la misma cantidad describen la MISMA intención, así
que un reintento RECUPERA el lote pendiente en vez de crear otro.

OJO — la referencia NO es la clave del lote. La clave es `CompraPase.compra`
(la compra de `commerce`): una vez pagada, una compra nueva con la misma
referencia es una compra NUEVA y legítima. Por eso el activador de derechos
resuelve el lote por `compra_id` y usa la referencia sólo como comprobación.

Este módulo es el DUEÑO del formato: lo produce el flujo de compra y lo lee
el activador. Es puro: no toca la base de datos ni importa nada del
exterior.
"""

import re
from dataclasses import dataclass
from uuid import UUID

from modules.salesianos_fest.domain.constants import MAX_LEN_REFERENCIA_PASE

#: Prefijo de toda referencia de intención de compra de pases.
PREFIJO_REFERENCIA = "PASE"

#: El formato exacto de una referencia. Es cerrado: una referencia que no
#: encaja NO es de este módulo y el activador la rechaza sin adivinar.
PATRON_REFERENCIA = re.compile(
    r"^PASE:(?P<edicion>[0-9a-fA-F-]{36}):"
    r"(?P<pase>[0-9a-fA-F-]{36}):"
    r"(?P<comprador>[0-9a-fA-F-]{36}):"
    r"(?P<cantidad>\d+)$"
)


@dataclass(frozen=True)
class ReferenciaPase:
    """La referencia de una intención de compra de pases, desarmada."""

    edicion_id: UUID
    pase_id: UUID
    comprador_id: UUID
    cantidad: int

    def coincide_con(self, *, edicion_id, pase_id, comprador_id, cantidad) -> bool:
        """Si la referencia describe la intención indicada."""
        return (
            str(self.edicion_id) == str(edicion_id)
            and str(self.pase_id) == str(pase_id)
            and str(self.comprador_id) == str(comprador_id)
            and self.cantidad == int(cantidad)
        )


def referencia_compra_pase(*, edicion_id, pase_id, comprador_id, cantidad: int) -> str:
    """La referencia de la intención de comprar `cantidad` pases.

    Es ESTABLE: el reintento del checkout abre la MISMA compra pendiente en
    vez de crear otra (`FR-04` I-4).
    """
    referencia = (
        f"{PREFIJO_REFERENCIA}:{edicion_id}:{pase_id}:{comprador_id}:{int(cantidad)}"
    )
    if len(referencia) > MAX_LEN_REFERENCIA_PASE:
        raise ValueError("La referencia de la compra de pases excede el límite.")
    return referencia


def parsear_referencia_pase(referencia: str) -> ReferenciaPase | None:
    """Desarma una referencia de intención de pases, o `None` si no lo es.

    No adivina: una referencia con otro formato devuelve `None` y el
    activador la rechaza con un código explícito.
    """
    if not referencia:
        return None
    coincidencia = PATRON_REFERENCIA.match(str(referencia).strip())
    if coincidencia is None:
        return None
    try:
        edicion_id = UUID(coincidencia.group("edicion"))
        pase_id = UUID(coincidencia.group("pase"))
        comprador_id = UUID(coincidencia.group("comprador"))
        cantidad = int(coincidencia.group("cantidad"))
    except (ValueError, AttributeError, TypeError):
        return None
    if cantidad <= 0:
        return None
    return ReferenciaPase(
        edicion_id=edicion_id,
        pase_id=pase_id,
        comprador_id=comprador_id,
        cantidad=cantidad,
    )


__all__ = [
    "PATRON_REFERENCIA",
    "PREFIJO_REFERENCIA",
    "ReferenciaPase",
    "parsear_referencia_pase",
    "referencia_compra_pase",
]
