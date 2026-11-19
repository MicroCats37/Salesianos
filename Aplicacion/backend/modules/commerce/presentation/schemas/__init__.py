"""Contrato HTTP del módulo `commerce` y su versión de schema.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

`commerce` **no tiene superficie HTTP**: el ledger `FR-07` no le asigna
ninguna ruta y cada dominio crea su propia compra por su propio endpoint
(`RN-C01`, `DEC-10`). Este archivo declara igualmente la versión congelada
del módulo, que es lo que el registro global `core/contract_versions.py`
exige (`FR-07` §2).

`SCHEMA_VERSION` es un REGISTRO, no un campo del wire: es el mecanismo de
detección de drift entre el backend y el espejo Zod del frontend (FR-07
§1.3). El valor declarado aquí debe coincidir con
`core.contract_versions.SCHEMA_VERSIONS["commerce"]`.
"""

#: Versión congelada del contrato de presenters/schemas del módulo
#: `commerce`.
SCHEMA_VERSION = "1.0.0"

__all__ = ["SCHEMA_VERSION"]
