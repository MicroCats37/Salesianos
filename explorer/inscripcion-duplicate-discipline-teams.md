# Exploration: Allow Duplicate Discipline Teams (Same Discipline × Multiple Teams)

> **Proyecto:** `Salesianos`
> **Fecha:** 2026-09-21
> **Tipo:** Architecture Exploration
> **Artifact:** `sdd/inscripcion-duplicate-discipline-teams/explore`
> **Modo:** Exploration — no implementation

---

## 1. Current State

### 1.1 The Problem

Currently, both the **frontend** and **backend** enforce that each discipline can appear at most once per inscription (one team per discipline). The user wants to allow selecting the same discipline multiple times **when the package's `cantidad_maxima_equipos` allows more teams than distinct disciplines available**.

**Example:** Package allows 2 teams, 1 discipline available (Fútbol) → user should be able to create 2 teams both with Fútbol.

### 1.2 Where Duplicate Prevention Is Enforced

#### Frontend — `SmartEquipoField.tsx` (lines 57–66)

```typescript
const disciplinasUsadasPorOtrosEquipos = equiposSeleccionados
  .map((equipo, equipoIndex) =>
    equipoIndex === index ? "" : equipo.disciplina_id,
  )
  .filter(Boolean);
const disciplinasSeleccionables = (paqueteDisciplinas ?? []).filter(
  (disciplina) =>
    disciplina.disciplina_id === disciplinaActual ||
    !disciplinasUsadasPorOtrosEquipos.includes(disciplina.disciplina_id),
);
```

This filter **always** excludes disciplines selected by other teams — it's a hardcoded "unique per inscription" rule. No consideration of `cantidad_maxima_equipos` vs. number of available disciplines.

#### Backend — `EquipoInscrito` Model (`backend/modules/inscripciones/domain/models/equipo.py`, lines 52–57)

```python
constraints = [
    models.UniqueConstraint(
        fields=["inscripcion", "disciplina"],
        name="uq_equipo_inscripcion_disciplina"
    )
]
```

Database-level enforcement of one team per discipline per inscription.

#### Backend — `EquipoService.crear()` (`backend/modules/inscripciones/domain/services/core/equipo_service.py`, lines 29–33)

```python
if validators.validar_equipo_duplicado(data.inscripcion_id, data.disciplina_id):
    raise exc.EquipoDuplicadoError(
        f"Ya existe un equipo para esta inscripción y disciplina."
    )
```

Application-level pre-check before creating each `EquipoInscrito`.

#### Backend — `validar_equipo_duplicado()` (`backend/modules/inscripciones/domain/services/core/validators.py`, lines 93–107)

```python
def validar_equipo_duplicado(inscripcion_id: str, disciplina_id: str) -> bool:
    return EquipoInscrito.objects.filter(
        inscripcion_id=inscripcion_id,
        disciplina_id=disciplina_id,
    ).exists()
```

Query-based check called by `EquipoService.crear()`.

#### Backend — `validar_cantidad_disciplinas_paquete()` (same file, lines 219–277)

Counts **distinct** discipline IDs in `equipos_data`. For `ELEGIBLE` mode:
```python
if cantidad_seleccionada != cantidad_requerida:
    errors.append(...)
```

This correctly validates **distinct** disciplines match required count. If user selects `[Fútbol, Fútbol]` with `cantidad_requerida=2`, `cantidad_seleccionada=1` → validation **fails**. This is the correct guard — removing D7 duplicate prevention won't break this validator.

### 1.3 Domain Behavior Summary

| Constraint | Current | Correct for "duplicate discipline" feature |
|---|---|---|
| DB `UniqueConstraint(inscripcion, disciplina)` | Enforces unique | ❌ Must be removed |
| `validar_equipo_duplicado()` in `EquipoService.crear()` | Enforces unique | ❌ Must be removed |
| `validar_cantidad_disciplinas_paquete()` distinct count | Enforces required count of **distinct** disciplines | ✅ Correct — does NOT block duplicates |
| `validar_disciplina_en_paquete()` discipline in package | Validates discipline belongs to package | ✅ Correct |
| R11 `UniqueConstraint(evento, disciplina, persona)` | Prevents same person in same discipline twice | ✅ Correct — per-person-per-discipline, not per-team |
| Per-team `max_jugadores` check | Enforces max players per team | ✅ Correct |

---

## 2. Affected Areas

### Files to Change

| File | Why | Change |
|---|---|---|
| `backend/modules/inscripciones/domain/models/equipo.py` | `EquipoInscrito` has hard `UniqueConstraint(inscripcion, disciplina)` | Remove constraint; replace with conditional or remove entirely |
| `backend/modules/inscripciones/domain/services/core/equipo_service.py` | `crear()` calls `validar_equipo_duplicado()` | Remove the validation call |
| `backend/modules/inscripciones/domain/services/core/validators.py` | `validar_equipo_duplicado()` and its call site | Remove function or make it a no-op (keep for future use) |
| `frontend/src/features/inscripciones/components/smart-fields/SmartEquipoField.tsx` | `disciplinasSeleccionables` filter always excludes duplicates | Add logic: allow duplicates when `cantidad_maxima_equipos > paqueteDisciplinas.length` |
| `backend/modules/inscripciones/domain/services/core/validators.py` — `validar_cantidad_disciplinas_paquete()` | Currently validates distinct count equals required | Verify it correctly handles duplicate disciplines (it counts `set(disciplina_ids)` — correct as-is) |

### Files to Verify (no change expected)

| File | Why |
|---|---|
| `backend/modules/inscripciones/domain/services/flujos/crear_inscripcion_flujo.py` | Calls `equipo_svc.crear()` → will work once D7 is removed |
| `backend/modules/inscripciones/domain/services/flujos/agregar_participantes_flujo.py` | Adds participants to existing teams; discipline is per-equipo — no change needed |
| `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts` | Schema doesn't validate uniqueness — no change needed |

---

## 3. Correct Domain Behavior

### The Rule
> Multiple teams **can** share the same discipline if `cantidad_maxima_equipos > cantidad_disciplinas_requeridas` (i.e., the package allows more teams than distinct disciplines available).

### Implied Validations That Remain

1. **Discipline must be in package** — `validar_disciplina_en_paquete()` ✅
2. **Distinct discipline count = required count** — `validar_cantidad_disciplinas_paquete()` ✅ (counts `set`, not list length)
3. **Person enrolled at most once per discipline per event** (R11) — DB constraint on `ParticipacionDisciplina` ✅
4. **Max players per team** — checked in `agregar_participantes_flujo` ✅
5. **Package participant capacity** — `validar_cupo_paquete()` ✅

### Scenarios

| Scenario | Expected Behavior |
|---|---|
| Package: 1 discipline, `cantidad_maxima_equipos=2`, `cantidad_requerida=2` | ✅ User selects Fútbol for Team 1 AND Team 2 |
| Package: 2 disciplines, `cantidad_maxima_equipos=2`, `cantidad_requerida=2` | ✅ User selects Fútbol + Vóley (distinct, no duplicates) |
| Package: 1 discipline, `cantidad_maxima_equipos=2`, `cantidad_requerida=1` | ✅ Valid — only 1 required but 2 allowed |
| Same person added to two teams of same discipline | ❌ R11 blocks it: "La persona ya está registrada en Fútbol en este evento." |
| Team exceeds `max_jugadores` | ❌ `MaxJugadoresExcedidoError` |

---

## 4. Approaches

### Approach A — Remove DB Constraint + Frontend Conditional (RECOMMENDED)

**Backend:**
1. Remove `UniqueConstraint(inscripcion, disciplina)` from `EquipoInscrito.Meta.constraints`
2. Remove `validar_equipo_duplicado()` call from `EquipoService.crear()`
3. Keep `validar_equipo_duplicado()` function (it may be useful for future edge cases)

**Frontend:**
1. Modify `disciplinasSeleccionables` filter to conditionally allow duplicates
2. Condition: `permiteDuplicados = (paqueteActual?.cantidad_maxima_equipos ?? 1) > (paqueteDisciplinas?.length ?? 0)`
3. When `permiteDuplicados=true`: only exclude disciplines selected by other teams if they are currently in a slot (preserve current selection) but still allow re-selecting disciplines already used
4. When `permiteDuplicados=false`: current strict behavior

**Migration:** One Django migration to remove the constraint.

- **Pros:** Minimal backend change; frontend condition is clear and matches business rule; no new test cases for backend uniqueness
- **Cons:** Requires frontend logic change with condition
- **Effort:** Low-Medium

### Approach B — Keep DB Constraint, Remove Only in ELEGIBLE Mode with >1 Team Capacity

**Backend:**
1. Change `UniqueConstraint` to conditional: only enforce when `cantidad_maxima_equipos <= count_of_distinct_disciplines_in_package` (complex — requires stored procedure or deferrable constraint)
2. OR: keep constraint but make `validar_equipo_duplicado` conditional based on package metadata (requires passing package info into the service layer)

**Frontend:**
1. Same conditional as Approach A

- **Pros:** DB still protects in simple cases
- **Cons:** Complex conditional constraint; still requires frontend change; edge cases around package re-selection
- **Effort:** High

---

## 5. Recommended Approach

**Approach A** — Remove DB constraint + `validar_equipo_duplicado` call + frontend conditional.

Rationale:
- The DB constraint is overly restrictive and prevents valid business cases
- The application-level check in `EquipoService.crear()` is the primary gate — removing it is safe since the frontend now controls what can be selected
- `validar_cantidad_disciplinas_paquete` correctly enforces distinct-discipline count (using `set`)
- R11 is the real protection for person+discipline uniqueness
- One Django migration needed; minimal backend risk

---

## 6. Test Cases Needed

### Backend Integration Tests

1. **Create inscription with 2 teams, same discipline, package allows it** → succeeds, both equipos created with same disciplina_id
2. **Create inscription with 2 teams, same discipline, package requires 2 distinct** → fails with `CantidadDisciplinasInvalidaError`
3. **Create inscription with 2 teams, distinct disciplines, package allows duplicates** → succeeds
4. **Add same person to 2 teams of same discipline** → fails with `ParticipacionDuplicadaError`
5. **Create inscription with 1 team, then edit to add second team with same discipline** → succeeds (package allows)
6. **Create inscription with 2 teams, same discipline, package has `modo=FIJO`** → succeeds (FIJO locks disciplines pre-selected by package, user can't change)

### Frontend / Type-Level Tests

1. **SmartEquipoField: `cantidad_maxima_equipos=2`, `disciplinas=[Futbol]`, `cantidad_requerida=2`** → Fútbol appears for both team slots
2. **SmartEquipoField: `cantidad_maxima_equipos=2`, `disciplinas=[Futbol]`, `cantidad_requerida=1`** → Fútbol appears for both team slots
3. **SmartEquipoField: `cantidad_maxima_equipos=2`, `disciplinas=[Futbol, Voley]`, `cantidad_requerida=2`** → Each discipline appears only once (distinct rule applies when enough disciplines exist)
4. **SmartEquipoField: FIJO mode** → Disciplines locked, current behavior preserved

### Manual QA

1. Create inscription with 2 "Fútbol" teams → confirm both created in DB
2. Add participant to first team, then same person to second team → confirm R11 blocks it
3. Create inscription with 2 distinct discipline teams → confirm current behavior unchanged

---

## 7. Minimal Implementation Plan

### Phase 1: Backend (smallest risk first)
1. Create Django migration to remove `uq_equipo_inscripcion_disciplina` constraint
2. Remove `validar_equipo_duplicado()` call from `EquipoService.crear()`
3. Run existing tests to confirm nothing breaks

### Phase 2: Frontend
1. In `SmartEquipoField.tsx`, compute `permiteDuplicados`
2. Modify `disciplinasSeleccionables` filter to allow duplicates when `permiteDuplicados=true`
3. Update `locked` condition logic (FIJO with matched disciplines still locks correctly)

### Phase 3: Testing
1. Backend integration tests for new behavior
2. Manual verification
3. Smoke test existing inscription flows

---

## 8. Risks and Open Questions

| Risk | Severity | Mitigation |
|---|---|---|
| Existing inscriptions with duplicate-discipline teams can't be loaded/edited | Low | Edge case — creation was blocked, so no data exists |
| Removing DB constraint breaks referential integrity checks | Low | Constraint was application-level duplicate-prevention, not FK integrity |
| Frontend condition is backwards (allows when should block) | Medium | Clear test cases per Section 6 |
| FIJO mode with duplicates behaves unexpectedly | Low | FIJO pre-fills disciplines from package — if package has 1 discipline and FIJO requires 2, the package is misconfigured |

### Open Questions

1. **Should `EquipoService.actualizar()` also check for duplicate discipline on discipline change?** Currently it does NOT call `validar_equipo_duplicado`. If a user edits an existing team to change its discipline to one already used by another team, should that be blocked? **Recommendation:** Yes, block it — but that's a separate refinement, not part of this change.
2. **Should the constraint be replaced with a partial/conditional one?** For future robustness, a conditional constraint like `UNIQUE(inscripcion_id, disciplina_id) WHERE categoria_id IS NOT NULL` would allow same discipline+different category. **Not in scope for this change.**
