# Exploration: inscripcion-participantes-side-form-dnd-plan

**Date:** 2026-09-20
**Project:** salesianos
**Status:** exploration-complete

---

## 1. Backend Support Matrix

| Capability | Supported | Evidence |
|---|---|---|
| Add participants batch to one equipo | ✅ YES | `PATCH /inscripciones/{id}/equipos/{equipo_id}/participantes` — `agregar_participantes_flujo.py` |
| Edit participant `rol` | ✅ Service exists | `ParticipanteService.actualizar()` — NO HTTP endpoint |
| Edit participant `talle_camiseta` | ✅ Service exists | `ParticipanteService.actualizar()` — NO HTTP endpoint |
| Edit persona fields (`tipoDocumento`, `numeroDocumento`, `nombres`, `apellidos`, `genero`, phone) | ❌ NO | No endpoint. Would require `usuarios` module cross-update |
| Remove participant from equipo | ❌ NO | No service method or endpoint exists |
| Move participant between equipos/disciplines | ❌ NO | No endpoint or service method exists |
| Persist participant ordering within team | ❌ NO | No `orden`/`posicion` field on `ParticipanteInscripcion` |

**Key finding:** `ParticipanteService.actualizar()` already supports editing `rol` and `talle_camiseta`. Only the HTTP endpoint is missing.

---

## 2. Domain Rules for Dragging Participant to Another Equipo

### Data Model Reality

```
ParticipacionDisciplina
  unique(evento, disciplina, persona)  ← R11 constraint
  equipo_id (ForeignKey, NOT in uniqueness)

ParticipanteInscripcion
  participacion (FK to ParticipacionDisciplina)
  equipo (FK to EquipoInscrito)
  rol, talle_camiseta
```

The uniqueness is on `(evento, disciplina, persona)`, NOT on `(evento, disciplina, persona, equipo)`. This means the same person CAN have multiple `ParticipacionDisciplina` records across different equipos in the same event+discipline.

### Same Disciplina, Different Equipo

- **No new `ParticipacionDisciplina` needed** (R11 would reject duplicate).
- Simply update `ParticipanteInscripcion.equipo_id` to point to new team.
- Old `ParticipanteInscripcion` record can be deleted or kept (keep is safer — preserves audit trail).

### Different Disciplina

- **New `ParticipacionDisciplina` required** for `(evento, new_disciplina, persona)`.
- R11 pre-check must run: if person already in new disciplina+event → `ParticipacionDuplicadaError`.
- Old `ParticipacionDisciplina` and old `ParticipanteInscripcion` are orphaned if move semantics apply; they should be deleted within the same atomic transaction.
- Package capacity validation (Nivel 2) must run for the target inscripcion.

### Recommended Behavior

**MOVE (not copy)** — drag-and-drop between teams should atomically remove from source and add to target. The user intent is "put this player on that team," not "also add to that team."

---

## 3. Frontend Architecture for Desired UI

### 3.1 Team Card with Internal Add Button

`SortableEquipoCard` currently has no internal add button. The add button is a full-width dashed `Button` below each card in `InscripcionDetailView`.

**Target UX:** The equipo card header contains an inline "+" or "Agregar jugador" button. Clicking it opens the add-person side panel for that specific equipo.

### 3.2 Team Card Expand/Collapse

`SortableEquipoCard` renders all participants always. Desired: participants list is collapsible, collapsed by default showing only a participant count badge. Clicking the card body (not the drag handle) expands/collapses.

### 3.3 Side Panel / Modal for Adding a Person

The `AddParticipantesModal` is a full `AppFormModal` — but the user wants it to feel like a **side panel for adding a person**, NOT a whole-form modal for the entire inscription.

**Pattern to follow:** `AppFormModal` from `@/components-app/forms/AppFormModal` with:
- `size="md"` or custom side-panel width
- The form fills person data (DNI lookup auto-fills nombres/apellidos)
- On submit, person is added to the participant list — NOT saved to the inscription yet
- Uses `useDocumentoLookup` hook from `@/features/entidades/hooks/useConsultaExterna`

**DNI Lookup Pattern (from `PersonaNaturalFormModal`):**
```tsx
// Watch the documento field
const dniValue = watch("numeroDocumento") || "";

// Lookup button disabled unless 8 digits
<Button onClick={handleDocumentoLookup} disabled={dniValue.length !== 8}>
  <Search className="h-4 w-4" />
</Button>

// On success, set nombres/apellidos from razon_social split
const parts = result.razon_social.split(", ");
if (parts.length === 2) {
  setValue("apellidos", parts[0], { shouldValidate: true });
  setValue("nombres", parts[1], { shouldValidate: true });
}
```

### 3.4 Participant Row Edit Button

Each `ParticipanteRow` currently shows `{participante.rol}` and `{participante.talle_camiseta}`. Add an Edit button that opens the same side-panel in edit mode with pre-filled data.

**With current backend:** Edit is read-only (no PATCH endpoint). Phase A shows the button but it opens a read-only view of the data.

**After Phase B:** Edit button opens editable side-panel → `PATCH .../participantes/{id}`.

### 3.5 Drag-and-Drop for Participants (Not Teams)

Current: `DndContext` wraps the entire `orderedEquipos` array — dragging the grip handle reorders teams.

**Target:** Each `SortableEquipoCard` has its own `SortableContext` for its participants. Drag handle is per-participant row. Dropping on a different team card triggers a move operation.

**Implementation note:** dnd-kit's `closestCenter` collision detection combined with `onDragEnd` checking `over.id` (which would be a `participante.id` or `equipo.id`) determines if it's an intra-team reorder or inter-team move.

---

## 4. Phased Plan

### Phase A: Frontend-Only (No Backend Changes)

**Deliverables:**
1. `AddParticipanteSidePanel` — new component reusing `AppFormModal` + `useDocumentoLookup` for DNI auto-fill. Side-panel feel, not full-form modal. Validates with `ParticipanteSchema` + `superRefine` for cross-field rules (e.g., telefono/whatsapp format).
2. `SortableEquipoCard` with expand/collapse — `useState(false)` for `isExpanded`. Click on card body toggles. Collapsed shows participant count only.
3. Internal add button inside card header — `onClick` → opens `AddParticipanteSidePanel` for that equipo.
4. Participant `ParticipanteRow` with Edit button — initially read-only side panel.
5. Refactor `DndContext` to participant-level sorting within each team. Teams themselves are NOT sortable in this phase.
6. Participant drag-and-drop with optimistic UI update (TanStack Query cache manipulation). No persistence yet.

**Files changed:**
- New: `frontend/src/features/inscripciones/components/AddParticipanteSidePanel.tsx`
- Modified: `frontend/src/features/inscripciones/components/SortableEquipoCard.tsx`
- Modified: `frontend/src/features/inscripciones/views/InscripcionDetailView.tsx`
- New: `frontend/src/features/inscripciones/schemas/participante.schema.ts` (Zod `superRefine`)

### Phase B: Backend Endpoints

**New HTTP endpoints:**

1. **`PATCH /inscripciones/{inscripcion_id}/participantes/{participante_id}`**
   - Input: `{ rol?, talle_camiseta? }`
   - Service: `ParticipanteService.actualizar()`
   - Validation: ownership check (participante belongs to inscripcion)

2. **`DELETE /inscripciones/{inscripcion_id}/participantes/{participante_id}`**
   - Service: new `ParticipanteService.remover()` — deletes `ParticipanteInscripcion` and optionally `ParticipacionDisciplina` if no other `ParticipanteInscripcion` links to it
   - Validation: roster minimum check (remove would break `min_jugadores` → error)

3. **`PATCH /inscripciones/{inscripcion_id}/participantes/{participante_id}/mover`**
   - Input: `{ equipo_destino_id }` (target equipo UUID)
   - Same disciplina: update `ParticipanteInscripcion.equipo_id`
   - Different disciplina: create new `ParticipacionDisciplina`, delete old one atomically
   - Validation: R11 check, package capacity, roster limits

**Files changed:**
- `backend/modules/inscripciones/presentation/controllers/inscripcion_controller.py` — 3 new endpoints
- `backend/modules/inscripciones/presentation/schemas/inscripcion_schemas.py` — `ParticipanteEditIn`, `ParticipanteMoveIn`
- `backend/modules/inscripciones/domain/services/core/participante_service.py` — add `mover()`, `remover()`
- `backend/modules/inscripciones/domain/services/orchestrators/inscripcion_orchestrator.py` — add orchestrator methods

### Phase C: Full Frontend Integration

**Deliverables:**
1. Edit button in `ParticipanteRow` → opens side panel in edit mode → calls `PATCH` endpoint.
2. Remove button with confirmation dialog → calls `DELETE` endpoint.
3. Drag-and-drop between teams → calls `PATCH .../mover` endpoint with optimistic updates.
4. Persist participant ordering — if ordering field is added to model, wire `PATCH` to save order on drag end.

---

## 5. Recommended API Changes (Backend)

### New Schema: `ParticipanteEditIn`
```python
class ParticipanteEditIn(Schema):
    rol: str | None = None  # e.g., "JUGADOR", "CAPITAN"
    talle_camiseta: str | None = None  # e.g., "M", "L"
```

### New Schema: `ParticipanteMoveIn`
```python
class ParticipanteMoveIn(Schema):
    equipo_destino_id: str
    disciplina_destino_id: str | None = None  # if None, same disciplina as source
```

### New Schema: `ParticipanteRemoveIn`
```python
class ParticipanteRemoveIn(Schema):
    confirm: bool = True  # explicit confirmation flag
```

---

## 6. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| R11 constraint blocks move to disciplina where person already exists | High | Catch `ParticipacionDuplicadaError` → show user-friendly "Ya está registrado en esa disciplina" message |
| Removing participant violates roster minimum | Medium | Pre-check in `remover()` service, return clear error |
| Package capacity exceeded on move | Medium | Validate `validar_cupo_paquete()` in move flow |
| No `orden` field means no persistent drag reorder | Low | Phase C adds field if ordering is a real requirement |
| DNI lookup service unavailable | Low | Fallback to manual entry, show toast warning |
| `useDocumentoLookup` lives in `entidades` module | Low | Import from shared location; already designed as reusable hook |

---

## 7. Next Recommended

**Phase A (frontend-only)** can begin immediately using the existing backend. The side-panel add-person UI, expand/collapse cards, and participant-level DnD (optimistic-only) require zero backend changes.

**After Phase A is validated by the user**, proceed to **Phase B** (backend endpoints) — add the edit, remove, and move endpoints. Then **Phase C** connects them all.

**Next SDD phase:** `sdd-propose` for the full scope definition and prioritization.
