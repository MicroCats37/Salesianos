# Liquidaciones Module — Architecture Documentation

> Last updated: 2026-08-07
> Status: Production-ready (Habilitación Urbana + Inspeccion de Obra validated)

This document describes the 4-layer architecture of the `liquidaciones` module and the **replicable pattern** (95%) for adding new liquidation types.

## 1. File Tree

```
modules/liquidaciones/
├── domain/
│   ├── models/
│   │   ├── liquidacion/liquidacion_general/liquidacion.py
│   │   ├── liquidacion/liquidacion_especifico/{liquidacion_habilitacion_urbana, liquidacion_mecanica_suelos, ...}
│   │   └── liquidacion/liquidacion_tipo/liquidacion_tipo.py
│   ├── results/
│   │   ├── liquidacion_general/liquidacion_general_result.py
│   │   ├── liquidacion_especifico/{tipo}_primera_revision_result.py
│   │   └── liquidacion_tipo/{liquidacion_m2_result, liquidacion_visitas_result, ...}
│   └── services/
│       ├── core/{liquidacion_general, liquidacion_tipo}/
│       ├── flujos/liquidacion_especifico/{tipo}_flujo.py
│       └── orchestrators/liquidacion_especifico/{tipo}_orchestrator.py
├── presentation/
│   ├── controllers/liquidacion_especifico/{tipo}_controller.py
│   ├── presenters/liquidacion_especifico/{tipo}_presenter.py
│   └── schemas/
│       ├── liquidacion_general/general_schemas.py
│       ├── liquidacion_tipo/{tipo, visitas}_schemas.py
│       └── liquidacion_especifico/{tipo}_schemas.py
└── tests/integration/{tipo}_endpoint.py
```

## 2. The 3 Endpoints (Habilitación Urbana pattern)

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/api/liquidaciones/habilitacion-urbana/tarifas/vigentes` | Read active tariffs and derecho for HU |
| POST | `/api/liquidaciones/habilitacion-urbana/cotizar` | Calculate quote (no DB write) |
| POST | `/api/liquidaciones/habilitacion-urbana/nueva-liquidacion/primera-revision` | Create liquidation (DB write) |

## 3. Layer Trace (for `primera-revision`)

[Insert the sequence diagram showing Controller → Orchestrator → Flujo → Core → Presenter]

## 4. The Replicable Pattern (95%)

To add a new liquidation type (e.g., Mecánica de Suelos), you need to create these files:
- `domain/models/liquidacion/liquidacion_especifico/liquidacion_<tipo>.py`
- `domain/results/liquidacion_especifico/<tipo>_primera_revision_result.py`
- `domain/services/orchestrators/liquidacion_especifico/<tipo>_orchestrator.py`
- `domain/services/flujos/liquidacion_especifico/<tipo>_flujo.py`
- `presentation/presenters/liquidacion_especifico/<tipo>_presenter.py`
- `presentation/schemas/liquidacion_especifico/<tipo>_schemas.py`
- `presentation/controllers/liquidacion_especifico/<tipo>_controller.py`
- `tests/integration/<tipo>_endpoint.py`

You can reuse:
- `LiquidacionGeneralResult`
- `LiquidacionPorMetroCuadradoCoreService` (for M2-based)
- `LiquidacionPorCategoriaVisitasCoreService` (for Visitas-based)
- `GeneralCoreService`
- The 3-wrapper input/output pattern

## 5. The 4 Wrapper Contract (Input/Output)

### Input (2 wrappers):
```json
{
  "liquidacion_general": { ... proyecto inline ... },
  "liquidacion_especifica": {
    "datos": { ... cálculo ... },
    "tarifa": { ... }
  }
}
```

### Output (3 wrappers):
```json
{
  "liquidacion_general": { ... },
  "liquidacion_tipo": { "id": ..., "numero": ... },
  "liquidacion_especifica": { ... }
}
```

## 6. Layer Rules (from contract)

| Layer | Rule |
|-------|------|
| Controller | sync `def`, no async, no logic, no ORM |
| Orchestrator | sync `def`, validates with HttpError, no ORM |
| Flujo | sync `def` with `@transaction.atomic` |
| Core | sync `def`, pure ORM, no transaction, no logic |
| Presenter | `@staticmethod`, no async, no DB |
| Schemas | Inherit from `BaseSchema` |
| Imports | Absolute (`from modules.xxx...`) |

## 7. Current Validated Types

- [x] Habilitación Urbana (M2-based): `liquidacion_habilitacion_urbana_*`
- [x] Inspeccion de Obra (Visitas-based): `liquidacion_inspeccion_obra_*`
- [ ] Mecánica de Suelos (M2-based) — TODO
- [ ] Impacto Vial (M2-based) — TODO
- [ ] Taludes (M2-based) — TODO
