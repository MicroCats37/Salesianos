"""
Pure domain validators for the salesianos_fest module.

No Django imports live here: these are plain functions over plain values, so
the business rules can be reasoned about (and tested) without the ORM or the
HTTP layer.
"""
from .participacion import (
    COMPATIBILIDADES_POR_GENERO,
    es_genero_compatible_con_modalidad,
)

__all__ = [
    "COMPATIBILIDADES_POR_GENERO",
    "es_genero_compatible_con_modalidad",
]
