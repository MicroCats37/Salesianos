"""La versión del contrato HTTP del módulo `validaciones`.

Packet: `XCT-01` · Change: `salesianos-fest-rebuild`

`SCHEMA_VERSION` es la versión CONGELADA de los wrappers de este módulo. La
comparte con el registro global de `core/contract_versions.py` (que ya
declara `validaciones` en `1.0.0`) y con el espejo Zod del frontend
(`features/validaciones/schemas/validacion.schema.ts`).

`FREEZE-RT-1.0.0` · `FR-07` §1.2
"""

SCHEMA_VERSION = "1.0.0"

__all__ = ["SCHEMA_VERSION"]
