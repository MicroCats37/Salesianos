"""La REFERENCIA DE INTENCIÓN de compra del módulo `salesianos_fest`.

Packet: `DOM-02` · Change: `salesianos-fest-rebuild`

La referencia es la IDENTIDAD de la intención de compra. La usa `commerce`
para reutilizar la compra pendiente en vez de duplicarla (`FR-04` I-4) y la
usa el ACTIVADOR de derechos para saber a qué inscripción pertenece la
compra que acaba de pagarse.

Formato (cerrado):

    INSCRIPCION:{inscripcion_id}:INICIAL
    INSCRIPCION:{inscripcion_id}:EXPANSION:{cantidad}

- `INICIAL` es la compra del ALTA: habilita los cupos del paquete.
- `EXPANSION` es la compra de cupos EXTRA: habilita los cupos comprados y
  NO vuelve a conceder los beneficios `FIJO_INICIAL` (`RN-I06`).

Este módulo es el DUEÑO del formato: lo produce el flujo de alta y el de
ampliación, y lo lee el activador. Es puro: no toca la base de datos ni
importa nada del exterior.
"""

import re
from dataclasses import dataclass
from uuid import UUID

from modules.salesianos_fest.domain.constants import (
    TipoActivacionCapacidad,
)

#: Prefijo de toda referencia de intención de este módulo.
PREFIJO_REFERENCIA = "INSCRIPCION"

#: Sufijo de la referencia de la compra del ALTA.
SUFIJO_INICIAL = TipoActivacionCapacidad.INICIAL

#: Sufijo de la referencia de la compra de cupos extra.
SUFIJO_AMPLIACION = TipoActivacionCapacidad.EXPANSION

#: El formato exacto de una referencia. Es cerrado: una referencia que no
#: encaja NO es de este módulo y el activador la rechaza sin adivinar.
PATRON_REFERENCIA = re.compile(
    r"^INSCRIPCION:(?P<inscripcion>[0-9a-fA-F-]{36}):"
    r"(?P<tipo>INICIAL|EXPANSION)(?::(?P<cantidad>\d+))?$"
)


@dataclass(frozen=True)
class ReferenciaIntencion:
    """La referencia de una intención de compra de inscripción, desarmada."""

    inscripcion_id: UUID
    tipo: str
    cantidad: int | None = None

    @property
    def es_inicial(self) -> bool:
        """Si la referencia es la de la compra del ALTA."""
        return self.tipo == TipoActivacionCapacidad.INICIAL

    @property
    def es_expansion(self) -> bool:
        """Si la referencia es la de una compra de cupos extra."""
        return self.tipo == TipoActivacionCapacidad.EXPANSION


def referencia_inicial(inscripcion_id) -> str:
    """La referencia de la compra del ALTA de una inscripción.

    Es ESTABLE: el reintento del alta abre la MISMA compra pendiente en vez
    de crear otra (`FR-04` I-4).
    """
    return f"{PREFIJO_REFERENCIA}:{inscripcion_id}:{SUFIJO_INICIAL}"


def referencia_expansion(inscripcion_id, cantidad: int) -> str:
    """La referencia de la compra de cupos extra de una inscripción.

    La cantidad viaja en la referencia porque la compra de ampliación es un
    hecho DISTINTO del alta: mientras su compra esté PENDIENTE, un reintento
    con la misma cantidad devuelve esa misma compra; una compra ya pagada no
    bloquea una nueva (`FR-04` I-4).
    """
    return f"{PREFIJO_REFERENCIA}:{inscripcion_id}:{SUFIJO_AMPLIACION}:{cantidad}"


def parsear_referencia(referencia: str) -> ReferenciaIntencion | None:
    """Desarma una referencia de intención, o `None` si no es de este módulo.

    No adivina: una referencia con otro formato devuelve `None` y el
    activador la rechaza con un código explícito.
    """
    if not referencia:
        return None
    coincidencia = PATRON_REFERENCIA.match(str(referencia).strip())
    if coincidencia is None:
        return None
    try:
        inscripcion_id = UUID(coincidencia.group("inscripcion"))
    except (ValueError, AttributeError, TypeError):
        return None
    cantidad = coincidencia.group("cantidad")
    return ReferenciaIntencion(
        inscripcion_id=inscripcion_id,
        tipo=coincidencia.group("tipo"),
        cantidad=int(cantidad) if cantidad is not None else None,
    )


__all__ = [
    "PATRON_REFERENCIA",
    "PREFIJO_REFERENCIA",
    "SUFIJO_AMPLIACION",
    "SUFIJO_INICIAL",
    "ReferenciaIntencion",
    "parsear_referencia",
    "referencia_expansion",
    "referencia_inicial",
]
