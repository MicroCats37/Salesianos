"""
Esquemas HTTP del módulo `usuarios`.

Freeze: `FREEZE-ID-1.0.0` · `FREEZE-PS-1.0.0` (`FR-07` §2, §5).

Rutas y wrappers de este módulo (`FR-07` §3.1.2 / ledger `RT-ID-*`):

| Ruta | Método | Wrapper de salida | Wrapper de entrada | Presenter |
|---|---|---|---|---|
| `/personas/busqueda/{documento}` | GET | `DocumentoConsultaOut` | — | `PersonaBusquedaPresenter` |
| `/personas/resolver` | POST | `PersonaResueltaOut` | `PersonaResolverIn` | `PersonaResolverPresenter` |
| `/personas/confirmar` | POST | `PersonaOut` | `PersonaConfirmarIn` | `PersonaConfirmarPresenter` |

Composición de schemas (`contract/SCHEMA_DRY_INTENTION.md`): cada wrapper se
compone con el bloque GENERAL (datos de la persona), el bloque IDENTIDAD
(ids, marcas de tiempo y procedencia) y el bloque ESPECÍFICO del caso de uso.

La versión del contrato de este módulo es `SCHEMA_VERSION`; el registro global
vive en `core/contract_versions.py` (A0).
"""

from modules.usuarios.presentation.schemas.persona_schemas import (
    DocumentoConsultaOut,
    PersonaConfirmarIn,
    PersonaDatosOut,
    PersonaIdentidadOut,
    PersonaOut,
    PersonaResueltaOut,
    PersonaResolverIn,
)

#: Versión congelada del contrato de presenters/schemas de `usuarios`.
SCHEMA_VERSION = "1.0.0"

__all__ = [
    "SCHEMA_VERSION",
    "DocumentoConsultaOut",
    "PersonaConfirmarIn",
    "PersonaDatosOut",
    "PersonaIdentidadOut",
    "PersonaOut",
    "PersonaResueltaOut",
    "PersonaResolverIn",
]
