"""
Constants — the filter vocabularies of the administracion area.

The administrative area publishes the vocabularies of the OWNING modules; it
never declares a second copy of a domain vocabulary. The TWO vocabularies it
does own are the ones of its OWN filters, which no owning module declares:

- the completeness of a roster (`COMPLETO` / `INCOMPLETO`) — DERIVED by the
  teams selector from the registered players and the minimum of the discipline,
- the commercial kind of a purchase row (`INICIAL` / `AMPLIACION` / `PASE`) —
  the two sports kinds of the domain plus the independent pass batch.

They live HERE so the filters, the selectors and the published catalogs read
the SAME values: one vocabulary, one owner, no drift.
"""
from modules.salesianos_fest.domain.constants import TipoCompraChoices

#: The roster is complete: the team registers at least the minimum of its
#: discipline.
ROSTER_COMPLETO = "COMPLETO"

#: The roster is incomplete: the team registers fewer players than the
#: minimum of its discipline.
ROSTER_INCOMPLETO = "INCOMPLETO"

#: The completeness values of a roster, in publication order.
ROSTER_ESTADOS = (ROSTER_COMPLETO, ROSTER_INCOMPLETO)

#: The commercial kind of an INDEPENDENT pass batch.
TIPO_COMPRA_PASE = "PASE"

#: The commercial kinds of a purchase row, in publication order.
TIPOS_COMPRA_ADMIN = (
    *(valor for valor, _etiqueta in TipoCompraChoices.choices),
    TIPO_COMPRA_PASE,
)


__all__ = [
    "ROSTER_COMPLETO",
    "ROSTER_INCOMPLETO",
    "ROSTER_ESTADOS",
    "TIPO_COMPRA_PASE",
    "TIPOS_COMPRA_ADMIN",
]
