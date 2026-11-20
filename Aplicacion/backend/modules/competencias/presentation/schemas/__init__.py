"""Contrato HTTP del módulo `competencias` y su versión de schema.

Freeze: `FREEZE-ENV-1.0.0` · `FREEZE-ED-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

`SCHEMA_VERSION` es un REGISTRO, no un campo del wire: es el mecanismo de
detección de drift entre el backend y el espejo Zod del frontend (FR-07
§1.3). El valor declarado aquí debe coincidir con
`core.contract_versions.SCHEMA_VERSIONS["competencias"]`.

**DOM-07 (2026-11-19) — `1.0.0`.** El paquete DOM-07 CONGELA la superficie
operativa de las competencias: 16 rutas, el presenter operativo ÚNICO
(`CompetenciasPresenter`) y sus wrappers. Es el PRIMER contrato del módulo,
así que la versión es la inicial.

El registro global `core.contract_versions.SCHEMA_VERSIONS` es de A0: este
paquete NO lo edita y deja constancia del DRIFT pendiente en su evidencia.
"""

#: Versión congelada del contrato de presenters/schemas del módulo.
SCHEMA_VERSION = "1.0.0"

__all__ = ["SCHEMA_VERSION"]
