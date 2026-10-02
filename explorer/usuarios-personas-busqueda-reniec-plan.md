# Exploration: `usuarios-personas-busqueda-reniec-plan`

## 1. Participant Deletion / Persona Immutability — Current Behavior

### Finding: `Persona` is correctly preserved on participant delete

In `participante_accion_flujo.py` (`_remover_participante_sync`):

```
1. Line 168: participante.delete()  ← Deletes ParticipanteInscripcion only
2. Lines 171-177: checks if ParticipacionDisciplina has other links
3. If orphaned → participacion.delete()  ← Deletes ParticipacionDisciplina if orphaned
4. Persona is NEVER touched
```

**Confirmed**: Deleting a participant from an inscription/team does NOT delete the underlying `Persona`. `Persona` is preserved and reusable.

### Finding: `ParticipacionDisciplina` IS deleted when orphaned

When a participant is removed and no other `ParticipanteInscripcion` links to the same `ParticipacionDisciplina`, the orphan is deleted (line 177). This is correct domain behavior — the discipline participation record is cleaned up.

### Finding: Adding participant correctly reuses existing `Persona` by document

In both `crear_inscripcion_flujo.py` and `agregar_participantes_flujo.py`:

```
1. persona_core._get_persona_por_documento(tipo_doc, num_doc)  ← lookup by document
2. If found → reuse (update contact fields if empty)
3. If not found → create new Persona
```

`Persona` model has `UniqueConstraint(fields=["tipo_documento", "numero_documento"])` — duplicates by document are prevented at DB level.

**Confirmed**: Same document → same `Persona`. No inconsistent mutable duplicates. Correct behavior.

---

## 2. Current `entidades` Lookup Architecture

### Endpoint Shape
- **Route**: `GET /entidades/consulta/{documento}` (8–11 char path param)
- **Controller**: `consulta_controller.py` → `ConsultaController`
- **Auth**: `AllowAny` (public endpoint)
- **Response**: `ApiResponse[DocumentoConsultaOut]`

### Input/Output
```python
# Request
GET /entidades/consulta/45406196

# Response
{
  "success": true,
  "data": {
    "tipo_documento": "DNI",
    "numero_documento": "45406196",
    "razon_social": "ZARATE TORRES, DENNIS JOEL"
  }
}
```

### Call Chain
```
Controller (async)
  → ConsultaOrchestrator.consultar_documento()
    → ConsultaExternoFlujo._proceso_consulta_documento()
      → IConsultaExternaClient.consultar_documento()
        ├── ConsultaExternaSimulator (DEBUG) — returns mock deterministic data
        └── RealConsultaExternaClient (prod) — calls scraper microservice
```

### Key Files to Copy/Rename
| File | What it does | Copy? |
|------|-------------|-------|
| `consulta_presenter.py` | Transforms `ConsultaDocumentoResult` → `DocumentoConsultaOut` | Rename semantically |
| `consulta_schemas.py` (`DocumentoConsultaOut`) | HTTP response schema | Copy as-is |
| `consulta_orchestrator.py` | Thin async facade | Create new in usuarios |
| `consulta_externo_flujo.py` | Async flow delegating to client | Create new in usuarios |
| `infrastructure/services.py` (`IConsultaExter naClient`, `Simulator`, `RealClient`) | Port + implementations | Reuse via injection, NOT copy |
| `domain/ports/__init__.py` (`IConsultaExter naClient`) | ABC interface | Reuse, no copy |
| `domain/results/consulta_results.py` (`ConsultaDocumentoResult`) | Result DTO | Reuse, no copy |
| `domain/exceptions.py` (`ReniecNotFoundError`, `SunatNotFoundError`) | Domain exceptions | Reuse, no copy |

**Important**: The infrastructure client implementations (`ConsultaExter naSimulator`, `RealConsultaExter naClient`) should NOT be copied. The `usuarios` module should inject `IConsultaExter naClient` from `entidades`. Both modules share the same scraper microservice URL; the simulator is already environment-aware (uses `settings.DEBUG`).

---

## 3. Proposed `usuarios/personas/busqueda` Architecture

### New Files to Create

```
backend/modules/usuarios/
├── presentation/
│   ├── controllers/
│   │   └── persona_busqueda_controller.py   # NEW: thin controller
│   ├── schemas/
│   │   └── persona_busqueda_schemas.py      # NEW: DocumentoConsultaOut (same shape)
│   └── presenters/
│       └── persona_busqueda_presenter.py     # NEW: transform result → schema
├── domain/
│   ├── services/
│   │   ├── flujos/
│   │   │   └── persona_busqueda_flujo.py    # NEW: async flow
│   │   └── orchestrators/
│   │       └── persona_busqueda_orchestrator.py  # NEW: thin facade
```

### Routing Recommendation

**Option A** (recommended): `/personas/busqueda/{documento}`
- Aligns with REST resource naming (`personas` as resource, `busqueda` as action)
- Controller at `usuarios/presentation/controllers/persona_busqueda_controller.py`
- Route decorator: `@route.get("/personas/busqueda/{documento}", ...)`

**Option B**: `/usuarios/personas/busqueda/{documento}`
- More explicit but redundant namespace

The router is registered in the main API, so the prefix depends on how `usuarios` is mounted. Based on existing patterns, Option A is cleaner.

### Input/Output (same as entidades)
```python
# Request
GET /personas/busqueda/45406196

# Response (identical to entidades)
{
  "success": true,
  "data": {
    "tipo_documento": "DNI",
    "numero_documento": "45406196",
    "razon_social": "ZARATE TORRES, DENNIS JOEL"
  }
}
```

### DI Changes (`usuarios/di.py`)
```python
# Add binding for IConsultaExter naClient (reuse from entidades)
from modules.entidades.domain.ports import IConsultaExter naClient
from modules.entidades.infrastructure.services import ConsultaExter naSimulator, RealConsultaExter naClient

# In configure():
if settings.DEBUG:
    binder.bind(IConsultaExter naClient, to=ConsultaExter naSimulator, scope=singleton)
else:
    binder.bind(IConsultaExter naClient, to=RealConsultaExter naClient, scope=singleton)
```

---

## 4. Comparison of Approaches

| Approach | Description | Pros | Cons | Effort |
|----------|-------------|------|------|--------|
| **A. Copy/minimal (recommended)** | Create new controller/presenter/orchestrator/flujo in `usuarios`, inject `IConsultaExter naClient` from entidades, reuse schemas and result DTOs as-is | Minimal duplication; follows contract; shared client impl; same I/O shape | Slight cross-module DI coupling via shared port | Medium |
| **B. Extract shared module** | Extract `IConsultaExter naClient`, simulator, real client to `core/` or a new `shared/` module, then both `entidades` and `usuarios` inject from it | Cleaner shared code; single source of truth | Requires moving infrastructure code; more changes; risk of breaking entidades | High |
| **C. Duplicate everything** | Copy all files to `usuarios` verbatim (including infrastructure/services.py) | Completely independent; no cross-module coupling | Code duplication; must keep in sync manually | Medium (but maintenance burden) |

**Recommendation**: Approach A — minimal copy of presentation+domain orchestration, inject `IConsultaExter naClient` from entidades.

---

## 5. Testing Plan

### Existing Pattern (from entidades tests — if they exist)
- Use `ninja_extra.testing.TestAsyncClient` for async controllers
- Use `ninja.testing.TestClient` for sync controllers
- Mock `IConsultaExter naClient` at DI level using injector binding override

### New Tests for `persona_busqueda`

```
backend/modules/usuarios/tests/
├── integration/
│   └── test_persona_busqueda.py
└── fixtures/
    └── __init__.py
```

**Test scenarios**:
1. `test_busqueda_dni_existente` — DNI in simulator returns expected mock data
2. `test_busqueda_ruc_existente` — RUC in simulator returns expected mock data
3. `test_busqueda_dni_desconocido` — unknown DNI returns `tipo_documento="DESCONOCIDO"`
4. `test_busqueda_con_error_reniec` — DNI not found raises `ReniecNotFoundError`
5. `test_busqueda_endpoint_no_borra_entidades` — ensure `entidades` endpoint still works

### No Behavioral Change for `entidades`
The `entidades` endpoint stays unchanged. No test modifications needed for existing `entidades` tests.

---

## 6. Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Cross-module import of `IConsultaExter naClient` creates tight coupling between `entidades` and `usuarios` | Medium | The port is stable; both modules share the same scraper infrastructure. Acceptable for this project. |
| If `entidades` module is later refactored/removed, `usuarios` breaks | Low | User explicitly said `entidades` is a reference/SUNAT-style module; the intent is to migrate semantic ownership to `usuarios`. No removal planned. |
| Simulator data diverges between modules | Low | Both bind the same simulator class from `entidades.infrastructure.services` — single instance |
| Route collision if `usuarios` and `entidades` both mount at overlapping paths | Low | Different paths (`/entidades/consulta/` vs `/personas/busqueda/`) — no collision |

---

## 7. No Changes to Source — Confirmation

The following are NOT modified by this exploration/plan:
- `entidades` module — left intact
- `inscripciones` module — participant delete/reuse behavior already correct
- `Persona` model — already has correct unique constraint
- `PersonaCoreService` — already correctly looks up/creates by document

---

## 8. Next Steps

1. **sdd-propose** — formalize the change proposal with scope and approach
2. **sdd-spec** — write delta spec defining the new endpoint contract
3. **sdd-design** — technical design with file list and DI changes
4. **sdd-tasks** — break into implementable tasks
5. **sdd-apply** — implement following the plan above
6. **sdd-verify** — run new tests + ensure entidades endpoint unchanged
