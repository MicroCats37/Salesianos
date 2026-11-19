"""Contrato HTTP del módulo `eventos` y su versión de schema.

Freeze: `FREEZE-PS-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

`SCHEMA_VERSION` es el REGISTRO que A0 mantiene en
`core/contract_versions.py` y que el espejo Zod del frontend declara. No es
un campo del wire: es el mecanismo de detección de drift (FR-07 §1.3).

El valor declarado aquí debe coincidir con
`core.contract_versions.SCHEMA_VERSIONS["eventos"]`. Un test de contrato
(comprobado en VER-01) falla si difieren.
"""

from modules.eventos.presentation.schemas.edicion_schemas import (
    EdicionActualOut,
    EdicionEspecificaOut,
    EdicionGeneralOut,
    EdicionIdentidadOut,
    EdicionOut,
    ModuloHabilitadoOut,
)

#: Versión congelada del contrato de presenters/schemas del módulo `eventos`.
SCHEMA_VERSION = "1.0.0"

__all__ = [
    "SCHEMA_VERSION",
    "EdicionActualOut",
    "EdicionEspecificaOut",
    "EdicionGeneralOut",
    "EdicionIdentidadOut",
    "EdicionOut",
    "ModuloHabilitadoOut",
]
