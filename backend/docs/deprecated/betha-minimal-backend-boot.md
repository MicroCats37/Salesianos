# Betha Minimal Backend Boot — Post-Purge Stabilization

**Date**: 2026-07-29
**Branch**: betha
**Status**: Django boots successfully

---

## What Was Disabled/Removed

### Model Bugs Fixed (syntax errors blocking Django boot)
| File | Issue | Fix |
|------|-------|-----|
| `liquidaciones/domain/models/delegado.py:21` | `UniqueConstraint` used `on_delete` (FK-only param) | Converted to `ForeignKey` |
| `liquidaciones/domain/models/proyectista.py:26` | Same `UniqueConstraint` issue | Converted to `ForeignKey` |
| `liquidaciones/domain/models/liquidacion/calculos_tarifas.py:91` | `PositiveIntegerField` with `min_value` (not a valid kwarg) | Removed `min_value` |
| `liquidaciones/domain/models/liquidacion/liquidacion_edificaciones.py:39` | `nullable=True` (invalid; should be `null=True`) | Changed to `null=True` |

### Model Name/Import Fixes
| File | Issue | Fix |
|------|-------|-----|
| `liquidaciones/domain/models/__init__.py` | Wrong class names `MunicipalidadDelegado`, `PeriodoDelegado` | Fixed to `DelegadoMunicipalidad`, `DelegadoMunicipalidadPeriodo` |
| `liquidaciones/domain/models/__init__.py` | Import from deleted `especialidades` module | Changed to import from `modules.usuarios.domain.models.perfil_ingeniero` |
| `liquidaciones/domain/models/__init__.py` | Import of non-existent `ContactoProyecto` | Removed |
| `liquidaciones/models.py` | Wrong model names, removed models | Updated imports and `__all__` to match actual class names |
| `liquidaciones/domain/models/liquidacion/__init__.py` | `LiquidacionPorcentajeObra` imported from wrong module | Fixed to import from `calculos_tarifas` |

### Cross-Model Reference Fixes
| File | Issue | Fix |
|------|-------|-----|
| `liquidaciones/domain/models/liquidacion/liquidacion.py` | `ManyToManyField` to `Especialidad` resolved to wrong app | Changed to `usuarios.Especialidad` |
| `liquidaciones/domain/models/delegado.py` | `DelegadoMunicipalidad.delegado` FK to non-existent `usuarios.Delegado` | Changed to local `Delegado` model |
| `liquidaciones/domain/models/delegado.py` | `Delegado.perfil_ingeniero` `related_name` clash with `Proyectista` | Changed to `related_name="delegados"` |
| `liquidaciones/domain/models/liquidacion/liquidacion.py` | `LiquidacionGeneral.proyecto_propiedad` FK to non-existent `ProyectoPropiedad` | Changed to `Proyecto` |
| `liquidaciones/domain/models/liquidacion/liquidacion.py` | `ordering` referenced `proyecto` instead of `proyecto_propiedad` | Fixed ordering |
| `liquidaciones/domain/models/liquidacion/liquidacion.py` | `LiquidacionContacto` ordering referenced `liquidacion__proyecto__denominacion` | Fixed to `liquidacion__proyecto_propiedad__denominacion` |
| `liquidaciones/domain/models/liquidacion_delegado.py` | `ordering` and `__str__` referenced non-existent `delegado` field | Fixed to use `perfil_ingeniero` |
| `liquidaciones/domain/models/proyecto.py` | `ProyectoPropietario` ordering referenced `nombre` | Fixed to `nombre_propietario` |
| `liquidaciones/domain/models/liquidacion/tarifas_reglas.py` | `ReglaTarifaLiquidacion` referenced non-existent `tramite_accion` field in ordering/constraints/indexes | Removed invalid references |
| `liquidaciones/domain/models/liquidacion/tarifas_reglas.py` | `ReglaTarifaInspeccionObra` same `tramite_accion` issue | Removed invalid references |

### DI Bindings Disabled (services deleted in purge)
| File | Action |
|------|--------|
| `liquidaciones/di.py` | All bindings commented out (24 deleted service bindings) |
| `finanzas/di.py` | All bindings commented out (deleted `FinanzasCoreService`, `FinanzasOrchestrator`) |
| `finanzas/domain/services/__init__.py` | Removed import of non-existent `finanzas_core_service` |
| `liquidaciones/domain/services/core/__init__.py` | All imports commented out |
| `liquidaciones/domain/services/flujos/__init__.py` | All imports commented out |
| `liquidaciones/domain/services/orchestrators/__init__.py` | All imports commented out |
| `liquidaciones/domain/services/builders/__init__.py` | All imports commented out |

### Controller Routes Disabled (deleted controllers)
| File | Action |
|------|--------|
| `config/api.py` | All liquidaciones controller imports and registrations commented out (9 controllers) |
| `config/api.py` | `FinanzasController` registration commented out |

### Stub Files Created (minimal to allow import)
| File | Purpose |
|------|---------|
| `entidades/domain/results/sunat_results.py` | Stub `SunatInstitucionResult` dataclass |
| `entidades/domain/results/reniec_results.py` | Stub `ReniecPersonaResult` dataclass |

### Placeholder Responses
| File | Change |
|------|--------|
| `finanzas/presentation/controllers/finanzas_controller.py` | `obtener_variables_vigentes` returns placeholder response instead of calling deleted orchestrator |

---

## What Remains Intact
- `finanzas/models.py` — IGV and UIT models preserved
- `entidades` module — mostly intact
- `usuarios` module — mostly intact
- Core models: `LiquidacionGeneral`, delegate models, tariff models, project models (but some have ordering/meta issues)

---

## Remaining Disabled Functionality
1. **All liquidaciones presentation layer** — controllers, presenters, schemas deleted
2. **All liquidaciones service layer** — core services, flows, orchestrators, builders deleted
3. **Finanzas orchestrator** — deleted, IGV/UIT retrieval endpoint returns placeholder
4. **Delegate batch operations** — orchestrator deleted
5. **Project/Proyectista services** — deleted

---

## Next Rebuild Slice Recommendation

**Priority 1 — Restore minimal liquidaciones boot:**
1. Create one `LiquidacionesGeneralOrchestrator` with basic list/detail
2. Create one `LiquidacionesGeneralFlujo` for list queries
3. Create minimal schemas for IGV/UIT-enabled responses
4. Wire up one test controller endpoint

**Priority 2 — Restore specific liquidation types:**
- Start with one type (e.g., Habilitacion Urbana) to establish the pattern
- Re-add core services, flows, orchestrators incrementally

**Priority 3 — Restore finanzas:**
- Rebuild `FinanzasOrchestrator` and `FinanzasCoreService`
- Restore IGV/UIT variable retrieval
