"""Contrato HTTP del módulo `patrocinadores` y su versión de schema.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

`SCHEMA_VERSION` es el REGISTRO que A0 mantiene en
`core/contract_versions.py` y que el espejo Zod del frontend declara. No es
un campo del wire: es el mecanismo de detección de drift (FR-07 §1.3).

El valor declarado aquí debe coincidir con
`core.contract_versions.SCHEMA_VERSIONS["patrocinadores"]`. Un test de
contrato falla si difieren.
"""

from modules.patrocinadores.presentation.schemas.patrocinadores_schemas import (
    CrearPatrocinadorIn,
    ImagenPatrocinadorIn,
    PatrocinadorEspecificaOut,
    PatrocinadorGeneralOut,
    PatrocinadorIdentidadOut,
    PatrocinadorImagenOut,
    PatrocinadorLogoOut,
    PatrocinadorOut,
)

#: Versión congelada del contrato de presenters/schemas del módulo
#: `patrocinadores`.
#:
#: `1.0.0` — la ficha, el logo y la galería ordenada (DOM-08): `RT-MD-02` con
#: sus wrappers (`CrearPatrocinadorIn`, `PatrocinadorOut`).
#:
#: El registro global `core.contract_versions.SCHEMA_VERSIONS["patrocinadores"]`
#: es de **A0** y ya declara `1.0.0`: no hay drift que corregir.
SCHEMA_VERSION = "1.0.0"

__all__ = [
    "SCHEMA_VERSION",
    "CrearPatrocinadorIn",
    "ImagenPatrocinadorIn",
    "PatrocinadorEspecificaOut",
    "PatrocinadorGeneralOut",
    "PatrocinadorIdentidadOut",
    "PatrocinadorImagenOut",
    "PatrocinadorLogoOut",
    "PatrocinadorOut",
]
