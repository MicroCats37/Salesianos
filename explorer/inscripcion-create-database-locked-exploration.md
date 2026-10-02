# Exploration: Backend Error When Creating Inscription

**Date**: 2026-09-20
**Topic**: SQLite `database is locked` error on `POST /api/inscripciones/`
**Project**: salesianos

---

## 1. Current State

### 1.1 End-to-End Creation Flow

```
POST /api/inscripciones/
  └─> InscripcionController.crear_inscripcion (async controller)
        └─> InscripcionOrchestrator.crear_inscripcion_completa (thin async facade)
              └─> CrearInscripcionFlujo._crear_inscripcion_completa (async)
                    └─> sync_to_async(self._crear_inscripcion_sync)()
                          └─> @transaction.atomic() _crear_inscripcion_sync (sync)
                                ├── _resolver_evento_activo() → Evento query
                                ├── paquete_svc.obtener() → Paquete query
                                ├── validators.validar_cantidad_disciplinas_paquete()
                                ├── inscripcion_svc.crear() → INSERT Inscripcion
                                ├── _crear_aceptaciones() → INSERT PersonaAceptacion ×N
                                └── for each equipo_data in equipos_data:
                                      ├── equipo_svc.crear() → INSERT EquipoInscrito
                                      └── for each p_data in participantes:
                                            ├── persona_core._get_persona_por_documento() → SELECT Persona
                                            ├── persona_core._crear_persona() [if not exists] → INSERT Persona
                                            ├── participacion_svc.crear() → INSERT ParticipacionDisciplina
                                            └── participante_svc.crear() → INSERT ParticipanteInscripcion
```

### 1.2 Key Files Involved

| File | Role |
|------|------|
| `presentation/controllers/inscripcion_controller.py` | Thin async controller |
| `domain/services/orchestrators/inscripcion_orchestrator.py` | Thin async facade |
| `domain/services/flujos/crear_inscripcion_flujo.py` | **CRITICAL** — contains the bug |
| `domain/services/core/inscripcion_service.py` | Sync core service, no transaction.atomic |
| `domain/services/core/equipo_service.py` | Sync core service, no transaction.atomic |
| `domain/services/core/participacion_service.py` | Sync core service, no transaction.atomic |
| `domain/services/core/participante_service.py` | Sync core service, no transaction.atomic |
| `domain/services/core/validators.py` | Pure validation functions |
| `modules/usuarios/domain/services/core/persona_core_service.py` | Sync persona lookup/create |
| `presentation/schemas/inscripcion_schemas.py` | HTTP schema with `participantes: list = Field(default_factory=list)` |

---

## 2. Root Cause Hypothesis (Ranked by Confidence)

### H1: `sync_to_async` Wrapping `@transaction.atomic()` Decorated Method — **Confidence: 95%**

**This is the primary cause.**

All flujos follow this antipattern:

```python
# crear_inscripcion_flujo.py line 151
return await sync_to_async(self._crear_inscripcion_sync)(...)

@transaction.atomic()  # ← decorator applied to class method
def _crear_inscripcion_sync(self, ...):
    ...
```

**Why this fails with SQLite:**

1. `sync_to_async()` from `asgiref` runs the wrapped sync function in a thread pool (not the main async thread)
2. `transaction.atomic()` in Django uses thread-local storage to track the transaction connection
3. When the decorated function runs in a worker thread, the transaction context is not properly propagated
4. SQLite's locking model is single-writer — if the transaction is not properly managed, writes get serialized and lock timeouts occur
5. Under concurrent load (even 2 simultaneous requests), this causes "database is locked"

**Same pattern exists in all flujos:**
- `crear_inscripcion_flujo.py` — line 151: `sync_to_async(self._crear_inscripcion_sync)`
- `agregar_participante_flujo.py` — line 66: `sync_to_async(self._agregar_participante_sync)`
- `cambiar_estado_inscripcion_flujo.py` — line 56: `sync_to_async(self._cambiar_estado_sync)`
- `asignar_delegado_flujo.py` — lines 49, 83: `sync_to_async(self._asignar_delegado_sync)`, `sync_to_async(self._remover_delegado_sync)`

### H2: Nested Writes in Loops Within Transaction — **Confidence: 70%**

The `_crear_inscripcion_sync` method does multiple INSERT loops inside a single `@transaction.atomic()`:

- 1× `Inscripcion`
- N× `PersonaAceptacion`
- N× `EquipoInscrito` (one per discipline)
- N× `ParticipacionDisciplina` + N× `ParticipanteInscripcion` (per participant)

SQLite's write lock is held for the entire transaction duration. The longer the transaction, the higher the chance of lock contention. Combined with H1, this amplifies the problem.

### H3: Concurrent Requests Under Load — **Confidence: 60%**

If the user is testing with rapid submissions or has multiple users, the SQLite lock timeout (default 5 seconds) can be exceeded. SQLite only allows one writer at a time.

---

## 3. Contract Violations

### 3.1 Architecture Contract (`contract/django-app-architecture-contract.md`)

| Rule | Violation |
|------|-----------|
| **P5**: `transaction.atomic()` se abre en el flujo | ✓ Correct — `_crear_inscripcion_sync` has `@transaction.atomic()` |
| **Cadena async**: Controller async → orchestrator async → flujo async → core sync | ✓ Correct pattern |
| **sync_to_async usage** | ✗ **VIOLATION**: `sync_to_async` wraps the entire `transaction.atomic` decorated method instead of individual service calls |
| **Core services sync, no transaction.atomic** | ✓ Compliant — no core service uses `transaction.atomic()` |

**The actual violation**: The contract's intent is:
```
Controller async → sync_to_async(orchestrator sync call) → flujo async (no atomic) → sync_to_async(core service method)
```

**The actual code:**
```
Controller async → orchestrator async → sync_to_async(flujo sync method with @transaction.atomic)
```

The `@transaction.atomic()` decorator is applied to the method, then `sync_to_async` wraps it. This breaks the thread-local transaction context when `sync_to_async` moves execution to a worker thread.

### 3.2 Correct Pattern Per Contract

The contract says (section 4.4):
> "Flujos async — son async. Usan `async def`. **ABREN `transaction.atomic()`** cuando hay que crear/actualizar múltiples entidades atómicamente. **Reciben operaciones sync del core service y las envuelven en `sync_to_async` donde corresponde.**"

The correct pattern should be:
```python
async def _crear_inscripcion_completa(self, ...):
    # Open transaction at flujo level, not as a decorator
    async with sync_to_async(transaction.atomic)():
        # Call core services wrapped with sync_to_async
```

Or even better, restructure so `sync_to_async` wraps individual service calls, not the whole transaction block.

---

## 4. Empty `participantes: []` Compatibility

### 4.1 Backend Contract

**HTTP Schema** (`presentation/schemas/inscripcion_schemas.py` line 140):
```python
participantes: list[ParticipanteCreateIn] = Field(default_factory=list)
```

**Validation** (`domain/services/core/validators.py` line 240-242):
```python
# If no equipos provided, skip validation (empty initial inscription is allowed)
if not equipos_data:
    return errors
```

**Behavior:**
- `participantes: []` is **allowed** by the schema
- Empty `equipos` or empty `participantes` skips roster validation
- Roster validation (`validar_roster_equipo`) only runs at **submit/confirm time**, not at creation

**Backend allows this.** The frontend relaxation to allow `equipo.participantes = []` is **compatible with the backend**.

### 4.2 `ParticipanteService` Comments Confirm

```python
# participante_service.py line 28-34
def crear(self, data) -> ParticipanteInscripcion:
    """
    Create a new ParticipanteInscripcion linked to a participacion.

    Does NOT validate roster min/max at creation time (draft mode).
    Roster validation happens at submit/confirm time via validar_roster_equipo.
    """
```

---

## 5. Exact Files and Functions to Change (Later SDD Apply)

### Primary Target (Root Cause Fix)

| File | Function | Change Required |
|------|----------|-----------------|
| `backend/modules/inscripciones/domain/services/flujos/crear_inscripcion_flujo.py` | `_crear_inscripcion_completa` + `_crear_inscripcion_sync` | Restructure to use `sync_to_async(transaction.atomic)` context manager instead of decorator pattern |
| `backend/modules/inscripciones/domain/services/flujos/agregar_participante_flujo.py` | `_agregar_participante` + `_agregar_participante_sync` | Same restructure |
| `backend/modules/inscripciones/domain/services/flujos/cambiar_estado_inscripcion_flujo.py` | `_cambiar_estado` + `_cambiar_estado_sync` | Same restructure |
| `backend/modules/inscripciones/domain/services/flujos/asignar_delegado_flujo.py` | `_asignar_delegado`, `_remover_delegado` + sync variants | Same restructure |

### Suggested Fix Pattern

```python
# Instead of:
@transaction.atomic()
def _crear_inscripcion_sync(self, ...):
    # ... writes ...

return await sync_to_async(self._crear_inscripcion_sync)(...)

# Do:
async def _crear_inscripcion_completa(self, ...):
    # Use transaction.atomic as context manager inside async
    from asgiref.sync import sync_to_async
    from django.db import transaction
    
    atomic = sync_to_async(transaction.atomic)
    async with atomic():
        # ... writes using sync_to_async for each service call ...
```

---

## 6. Suggested Verification Commands

```bash
# 1. Check if development uses SQLite
cd backend
python -c "import os; print('SQLite:', os.environ.get('USE_SQLITE','').lower() in ('1','true','yes'))"

# 2. Run a single inscription creation test
cd backend
python -m pytest modules/inscripciones/tests/integration/test_inscripciones_lifecycle.py::test_crear_inscripcion_authenticated_sin_equipos -v -x

# 3. Run the full inscription lifecycle test suite
cd backend
python -m pytest modules/inscripciones/tests/integration/test_inscripciones_lifecycle.py -v -x

# 4. Test concurrent inscriptions (if pytest-xdist available)
cd backend
python -m pytest modules/inscripciones/tests/integration/test_inscripciones_lifecycle.py -v -n 2

# 5. Check for any running migrations
python manage.py showmigrations
```

---

## 7. Summary

| Item | Finding |
|------|---------|
| **Root Cause** | `sync_to_async()` wrapping `@transaction.atomic()` decorated method — breaks thread-local transaction context in SQLite |
| **Confidence** | 95% — the antipattern is present in all 4 flujos and would cause SQLite lock under any concurrent load |
| **Contract Violations** | Yes — `sync_to_async` should wrap individual service calls, not whole decorated methods |
| **Empty `participantes: []`** | **Compatible** — backend allows it, roster validation is deferred to submit/confirm |
| **Fix Complexity** | Medium — requires restructuring all flujo methods but pattern is consistent across all of them |
| **Files to Change** | 4 flujo files: `crear_inscripcion_flujo.py`, `agregar_participante_flujo.py`, `cambiar_estado_inscripcion_flujo.py`, `asignar_delegado_flujo.py` |

---

## 8. Ready for Proposal

**YES** — ready for an SDD proposal.

The change is well-understood:
1. Root cause identified (the `sync_to_async(transaction.atomic)` decorator pattern)
2. All affected files follow the same pattern (easy to fix systematically)
3. Contract violations clearly documented
4. The `participantes: []` frontend change is confirmed compatible with backend

**Recommended SDD scope**: Fix the transaction pattern in all flujos. This is a single focused change that will resolve the SQLite lock issue while staying consistent with the project's architecture contract.
