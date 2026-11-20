"""Contrato HTTP del módulo `salesianos_fest` y su versión de schema.

Freeze: `FREEZE-PS-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-CM-1.0.0`
Evidence: `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/FR-07-presenter-schema-versions.md`

`SCHEMA_VERSION` es un REGISTRO, no un campo del wire: es el mecanismo de
detección de drift entre el backend y el espejo Zod del frontend (FR-07
§1.3). El valor declarado aquí debe coincidir con
`core.contract_versions.SCHEMA_VERSIONS["salesianos_fest"]`.

**DOM-02 (2026-11-19) — `1.0.0` → `1.1.0` (MINOR).** El paquete DOM-02
CONGELA cuatro rutas nuevas del módulo (`RT-IN-03`, `RT-IN-05`, `RT-IN-06`
y `RT-CM-01`) con sus presenters y wrappers. El cambio es ADITIVO: no se
modifica ni se elimina ninguna forma de respuesta existente, así que la
semántica de versionado es MINOR (`core.contract_versions.tipo_de_cambio`).

**DOM-03 (2026-11-19) — `1.1.0` → `1.2.0` (MINOR).** El paquete DOM-03
CONGELA diez rutas nuevas del módulo (`RT-PS-01`…`RT-PS-08`, `RT-CM-02` y
`RT-RT-03`) con sus presenters y wrappers. El cambio es ADITIVO: no se
modifica ni se elimina ninguna forma de respuesta existente, así que la
semántica de versionado vuelve a ser MINOR
(`core.contract_versions.tipo_de_cambio`).

El registro global `core.contract_versions.SCHEMA_VERSIONS` es de A0: este
paquete NO lo edita y deja constancia del DRIFT pendiente en su evidencia.
"""

#: Versión congelada del contrato de presenters/schemas del módulo.
SCHEMA_VERSION = "1.2.0"

__all__ = ["SCHEMA_VERSION"]
