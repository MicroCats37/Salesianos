# Plan: Auto-Equipo / Auto-Disciplina Assignment for Paquetes

> **Proyecto:** `salesianos`
> **Fecha:** 2026-09-20
> **Tipo:** Planning Report
> **Modo:** `explorer/` — no implementation

---

## 1. Current State

### 1.1 How Equipos Are Created Today

The inscription wizard (Step 3 — Equipos) uses `SmartEquipoField`, which:

1. **Receives** from `EquiposStepLayout`:
   ```ts
   paqueteActual: {
     id: string;
     cantidad_disciplinas_requeridas: number;  // e.g. 3
     cantidad_maxima_equipos: number;           // e.g. 3 (FIJO) or 3 (ELEGIBLE)
     cantidad_maxima_participantes: number;
   }
   ```

2. **Auto-creates** exactly `cantidad_maxima_equipos` equipo slots via `useFieldArray.replace()` when the package changes.

3. **Renders** one `EquipoCard` per slot, each with a `SearchableSelect` for discipline. The select is **disabled** when `!paqueteId`.

4. **Filters out already-selected disciplines** per slot via `availableDisciplinas`, preventing duplicates across teams.

5. **Backend validates** with `validators.validar_cantidad_disciplinas_paquete()` which enforces exact discipline count per mode (`FIJO` or `ELEGIBLE`).

### 1.2 What Is Already Exposed by Backend

**`GET /inscripciones/paquetes/` → `PaqueteOut`:**
```python
{
    "id": "...", "nombre": "...",
    "modo_disciplinas": "FIJO",          # ← already in PaqueteOut
    "cantidad_disciplinas_requeridas": 3, # ← already in PaqueteOut
    "cantidad_maxima_equipos": 3,          # ← already in PaqueteOut (derived)
    ...
}
```

**`GET /inscripciones/paquetes/{id}/disciplinas/` → `PaqueteDisciplinaOut[]`:**
```python
[
    {"disciplina_id": "uuid1", "disciplina_nombre": "Fútbol", "disciplina_sigla": "FUT"},
    {"disciplina_id": "uuid2", "disciplina_nombre": "Básquet", "disciplina_sigla": "BAS"},
    {"disciplina_id": "uuid3", "disciplina_nombre": "Vóley", "disciplina_sigla": "VOL"},
]
```

### 1.3 What Is NOT Passed to SmartEquipoField

`EquiposStepLayout` builds `paqueteActual` but **omits `modo_disciplinas`**:

```ts
// frontend/src/features/inscripciones/components/InscripcionWizard.tsx:416-426
paqueteActual={
  paqueteActual
    ? {
        id: paqueteActual.id,
        cantidad_disciplinas_requeridas: paqueteActual.cantidad_disciplinas_requeridas ?? 1,
        cantidad_maxima_equipos: paqueteActual.cantidad_maxima_equipos ?? 1,
        cantidad_maxima_participantes: paqueteActual.cantidad_maxima_participantes,
        // ❌ modo_disciplinas is MISSING
      }
    : undefined
}
```

`SmartEquipoFieldProps` also lacks `modo_disciplinas`:

```ts
// frontend/src/features/inscripciones/components/smart-fields/SmartEquipoField.tsx:541-549
interface SmartEquipoFieldProps {
  fieldName: "equipos";
  paqueteIdFieldName: "paquete_id";
  paqueteActual?: {
    id: string;
    cantidad_disciplinas_requeridas: number;
    cantidad_maxima_equipos: number;
    cantidad_maxima_participantes: number;
    // ❌ modo_disciplinas: string is MISSING
  };
}
```

---

## 2. Rule Matrix

| `modo_disciplinas` | Available Disciplines | `cantidad_disciplinas_requeridas` | `cantidad_maxima_equipos` | Expected UI Behavior |
|---|---|---|---|---|
| `FIJO` | 1 | 1 | 1 | **Auto-lock**: 1 equipo slot auto-created with the single discipline pre-selected and **locked** (selector disabled). User cannot change it. |
| `FIJO` | N | N | N (N = count of `PaqueteDisciplina`) | **Auto-assign all**: N equipo slots auto-created; each is pre-assigned a distinct discipline from `paqueteDisciplinas` in order, **all locked**. No selector shown. |
| `FIJO` | N | M | M (M < N) | **Invalid DB state** — `validators.py` enforces `cantidad_seleccionada == cantidad_requerida` for FIJO; if N > M the DB is misconfigured. Treat as error. |
| `ELEGIBLE` | N | N | N | **All pre-assigned but unlocked**: N slots created, each pre-filled with one of the N disciplines; all selectors are **enabled** so user can rearrange. Duplicate prevention still applies. |
| `ELEGIBLE` | N | M | M (M < N) | **Partial select**: M slots created; user selects M distinct disciplines from the N available; selectors enabled; no duplicates allowed. |
| `null` / missing | — | `null` or missing | — | **Default behavior**: treat as `ELEGIBLE` with `cantidad_maxima_equipos = 1`. Current code already does `?? 1`. |
| Any mode | 0 | — | 0 | **Error state**: package has no disciplines configured. Show error message. |

### Decision Tree (for implementation)

```
START
├── modo_disciplinas == null → default to ELEGIBLE, equipos = 1
├── modo_disciplinas == "FIJO"
│   ├── available_disciplines.length == 0 → error: "No disciplines configured"
│   ├── available_disciplines.length == 1 && required == 1
│   │   → Auto-fill slot[0].disciplina_id = available[0]
│   │   → Lock slot[0] discipline selector (disabled=true, locked=true)
│   ├── available_disciplines.length == required
│   │   → Auto-fill all slots with distinct disciplines (slot[i].disciplina_id = available[i])
│   │   → Lock ALL discipline selectors
│   └── available_disciplines.length != required
│       → This is a DB config error; surface user-friendly error
└── modo_disciplinas == "ELEGIBLE"
    ├── available_disciplines.length == required
    │   → Auto-fill all slots with distinct disciplines (slot[i].disciplina_id = available[i])
    │   → Enable ALL selectors (user can rearrange)
    ├── available_disciplines.length > required
    │   → Create `required` slots (cantidad_maxima_equipos)
    │   → Leave selectors enabled; user picks distinct disciplines
    └── available_disciplines.length < required
        → Error: "Package allows X disciplines but requires Y"
```

---

## 3. Files to Change

### 3.1 Frontend

| File | Change |
|------|--------|
| `frontend/src/features/inscripciones/components/InscripcionWizard.tsx` | Add `modo_disciplinas` to the `paqueteActual` object built in `EquiposStepLayout` |
| `frontend/src/features/inscripciones/components/smart-fields/SmartEquipoField.tsx` | (a) Add `modo_disciplinas: string` to `SmartEquipoFieldProps.paqueteActual` interface; (b) Add locked/auto-fill logic in the `useEffect` that syncs equipos when package changes; (c) Add `locked: boolean` to `EquipoCardProps`; (d) Conditionally render discipline selector as locked/disabled when in FIJO mode |
| `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts` | Consider adding `locked?: boolean` to `EquipoFormData` if locked state needs to be part of the schema (or handle purely in UI state) |
| `frontend/src/features/inscripciones/components/smart-fields/SmartPaqueteCardsField.tsx` | (Optional) Add `modo_disciplinas` display badge on card to visually distinguish FIJO vs ELEGIBLE packages |

### 3.2 Backend

| File | Change |
|------|--------|
| `backend/modules/inscripciones/presentation/schemas/paquete_schemas.py` | **No change needed** — `modo_disciplinas` already in `PaqueteOut` ✅ |
| `backend/modules/inscripciones/presentation/presenters/paquete_presenter.py` | **No change needed** — `present_paquete` already includes `modo_disciplinas` ✅ |
| `backend/modules/inscripciones/domain/services/core/validators.py` | Consider enhancing `validar_cantidad_disciplinas_paquete` to surface a clearer error when `FIJO` mode has `len(paquete_disciplinas) != cantidad_disciplinas_requeridas` (DB misconfiguration) |

---

## 4. Backend Gap Analysis

| Gap | Severity | Status |
|-----|----------|--------|
| `modo_disciplinas` not in `PaqueteOut` | — | **RESOLVED** — already present ✅ |
| `cantidad_disciplinas_requeridas` not in `PaqueteOut` | — | **RESOLVED** — already present ✅ |
| `cantidad_maxima_equipos` not derived correctly | — | **RESOLVED** — `calcular_cantidad_maxima_equipos()` handles both modes ✅ |
| `PaqueteDisciplinaOut` missing fields | — | **RESOLVED** — returns `disciplina_id`, `disciplina_nombre`, `disciplina_sigla` ✅ |
| No endpoint to validate package configuration | Low | New low-priority endpoint `GET /inscripciones/paquetes/{id}/validacion/` that checks `FIJO` mode consistency (available count vs required count) |

**Verdict: Backend has all necessary metadata exposed. No schema changes required.**

---

## 5. Frontend Gap Analysis

| Gap | Severity | Status |
|------|----------|--------|
| `modo_disciplinas` not passed to `SmartEquipoField` | **HIGH** | Must add to `paqueteActual` prop and `SmartEquipoFieldProps` interface |
| FIXO mode: discipline not auto-selected when only 1 available | **HIGH** | Must add auto-fill logic in `SmartEquipoField` useEffect |
| FIJO mode: disciplines not auto-assigned across N slots | **HIGH** | Must add auto-assign logic in `SmartEquipoField` useEffect |
| FIJO mode: discipline selectors not locked | **HIGH** | Must add `locked` prop to `EquipoCard` and disable selectors |
| No error surfaced when `available == 0` | Medium | Should show "No disciplines configured" error in `EquipoCard` |
| `modo_disciplinas` not shown on package card | Low | Optional UI enhancement for FIJO vs ELEGIBLE badge |
| `validators.py` does not surface FIJO misconfiguration | Low | Backend error improvement |

**Verdict: Frontend requires changes to `InscripcionWizard.tsx` and `SmartEquipoField.tsx`. Schema changes minimal.**

---

## 6. No Hardcoded IDs — Confirmed

The discipline IDs come exclusively from `GET /inscripciones/paquetes/{id}/disciplinas/` at runtime. No hardcoded UUIDs. No forced relationships. ✅

---

## 7. Recommended SDD Apply Task List

### Phase 1: Prop Chain Fix (unblock everything)
- [ ] Add `modo_disciplinas: string` to `EquiposStepLayout`'s `paqueteActual` construction
- [ ] Add `modo_disciplinas: string` to `SmartEquipoFieldProps.paqueteActual` interface
- [ ] Verify `usePaqueteDisciplinas` is called with correct package ID and returns fresh data

### Phase 2: FIJO — Auto-Lock Single Discipline
- [ ] In `SmartEquipoField`'s `useEffect` (equipo sync): detect `modo_disciplinas === "FIJO" && availableDisciplinas.length === 1 && required === 1`
- [ ] Pre-fill `equipos[0].disciplina_id` with the single available discipline
- [ ] Pass `locked: true` to `EquipoCard` for discipline selector
- [ ] In `EquipoCard`: if `locked === true`, render discipline as a static badge (not a selectable dropdown)
- [ ] Zod schema: `disciplina_id` still required (the auto-fill satisfies the requirement)

### Phase 3: FIJO — Auto-Assign All Disciplines (N = required)
- [ ] In `SmartEquipoField`'s `useEffect`: detect `modo_disciplinas === "FIJO" && availableDisciplinas.length === required`
- [ ] Auto-assign `equipos[i].disciplina_id = availableDisciplinas[i]` for all N slots
- [ ] Pass `locked: true` to all `EquipoCard` instances
- [ ] Render all discipline selectors as locked badges

### Phase 4: ELEGIBLE — Pre-fill Without Locking
- [ ] In `SmartEquipoField`'s `useEffect`: detect `modo_disciplinas === "ELEGIBLE" && availableDisciplinas.length === required`
- [ ] Pre-assign disciplines to slots but leave selectors enabled
- [ ] User can still change which slot has which discipline (but duplicate prevention still applies)

### Phase 5: Error States
- [ ] When `modo_disciplinas === "FIJO" && availableDisciplinas.length === 0`: show error in `SmartEquipoField` ("Este paquete no tiene disciplinas configuradas")
- [ ] When `modo_disciplinas === "FIJO" && availableDisciplinas.length !== required`: show error ("Configuración de paquete inválida")
- [ ] When `modo_disciplinas === "ELEGIBLE" && availableDisciplinas.length < required`: show error ("Este paquete permite X disciplinas pero requiere Y")

### Phase 6: Optional UI Polish
- [ ] Add FIJO/ELEGIBLE badge on `SmartPaqueteCardsField` package cards
- [ ] Backend: enhance `validar_cantidad_disciplinas_paquete` error message for FIJO misconfiguration
- [ ] Add unit test for `calcular_cantidad_maxima_equipos` with edge cases

---

## 8. Constraints Honored

- **No hardcoded IDs**: All discipline IDs come from the API at runtime ✅
- **Backend as source of truth**: Backend `validators.py` enforces discipline count per mode; frontend just implements the UI pattern that matches ✅
- **No implementation**: This is a planning document only ✅
- **Dirty worktree respected**: No git operations attempted ✅
- **Report in `explorer/`**: `explorer/inscripcion-auto-equipo-disciplina-plan.md` ✅
