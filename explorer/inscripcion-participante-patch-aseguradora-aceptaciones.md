# Exploration: Participant PATCH — Aseguradora & Per-Person Aceptaciones

## Current State

### Backend PATCH Participant Flow (existing)

**Endpoint:** `PATCH /api/inscripciones/{inscripcion_id}/participantes/{participante_id}`

**Chain:**
```
InscripcionController.editar_participante()
  → InscripcionOrchestrator.editar_participante()
  → ParticipanteAccionFlujo._editar_participante()
  → _editar_participante_sync() [transaction.atomic]
  → ParticipanteService.actualizar()
```

**Current `ParticipanteEditIn` schema** (`presentation/schemas/inscripcion_schemas.py:178`):
```python
class ParticipanteEditIn(Schema):
    rol: str | None = None
    talle_camiseta: str | None = None
```

**Current `ParticipanteUpdateData`** (`domain/schemas/equipo_schemas.py:54`):
```python
class ParticipanteUpdateData(BaseModel):
    rol: str | None = None
    talle_camiseta: str | None = None
```

### Domain Models Already in Place

| Model | Location | Fields | Status |
|-------|----------|--------|--------|
| `Persona` | `modules/usuarios/domain/models/persona.py` | `aseguradora_nombre`, `aseguradora_numero_poliza` | **EXISTING** — no migration needed |
| `PersonaAceptacion` | `modules/usuarios/domain/models/persona_aceptacion.py` | `persona`, `tipo_aceptacion`, `documento_version`, `aceptado_en`, `ip_address`, `user_agent` | **EXISTING** — no migration needed |
| `TipoAceptacionChoices` | `modules/usuarios/domain/constants.py` | `BASES`, `APTITUD_FISICA`, `IMAGEN` | **EXISTING** |
| `BASES_VERSION_ACTIVA` | `modules/usuarios/domain/constants.py` | `"BASES-SF26-2026-09-06"` | **EXISTING** |

### Current `ParticipanteOut` Response (no aseguradora/aceptacion)
```python
class ParticipanteOut(Schema):
    id: str
    participacion_id: str
    equipo_id: str
    rol: str
    talle_camiseta: str | None = None
    persona: PersonaResumenOut  # only id, nombres, apellidos, numero_documento
```

### Frontend Current State

**`EditarParticipanteFormData`** (`frontend/src/features/inscripciones/schemas/participanteEdit.schema.ts`):
```typescript
rol: string (JUGADOR | CAPITAN | DELEGADO)
talle_camiseta: string | undefined (S | M | L | XL | XXL)
```

**`EditParticipanteModal`** — only renders `rol` and `talle_camiseta` fields.

**`EditarParticipantePayload`** (`inscripcion.service.ts:188`):
```typescript
interface EditarParticipantePayload {
  rol?: string;
  talle_camiseta?: string | null;
}
```

---

## Affected Areas

### Backend
- `backend/modules/inscripciones/presentation/schemas/inscripcion_schemas.py` — `ParticipanteEditIn` needs optional aseguradora fields
- `backend/modules/inscripciones/domain/schemas/equipo_schemas.py` — `ParticipanteUpdateData` needs optional aseguradora fields
- `backend/modules/inscripciones/domain/services/flujos/participante_accion_flujo.py` — `_editar_participante_sync` needs to update `Persona` if aseguradora provided
- `backend/modules/inscripciones/domain/services/orchestrators/inscripcion_orchestrator.py` — `editar_participante` signature needs optional aseguradora params
- `backend/modules/inscripciones/presentation/controllers/inscripcion_controller.py` — `editar_participante` endpoint needs to pass aseguradora fields through
- `backend/modules/inscripciones/domain/services/core/participante_service.py` — may need a new `actualizar_persona_aseguradora` method or accept cross-model update
- `backend/modules/usuarios/domain/services/core/persona_core_service.py` — add `actualizar_aseguradora` method

### Frontend
- `frontend/src/features/inscripciones/schemas/participanteEdit.schema.ts` — add aseguradora fields
- `frontend/src/features/inscripciones/components/EditParticipanteModal.tsx` — add aseguradora inputs
- `frontend/src/features/inscripciones/services/inscripcion.service.ts` — `EditarParticipantePayload` needs aseguradora fields
- `frontend/src/features/inscripciones/hooks/useEditarParticipante.ts` — no changes needed to hook, but payload shape changes

### New Files/Models
- No new models needed — both `aseguradora_*` fields and `PersonaAceptacion` already exist
- Optional: new schema for recording aceptaciones (can reuse existing `PersonaAceptacion` pattern)

---

## Approaches

### Approach 1: Extend PATCH Endpoint for Aseguradora + New Aceptaciones Endpoint

**Description:** Add `aseguradora_nombre` and `aseguradora_numero_poliza` to `ParticipanteEditIn`, pass through the entire edit chain, and update `Persona` from within `ParticipanteAccionFlujo`. Record aceptaciones via a **separate** dedicated endpoint (e.g., `PATCH /inscripciones/{id}/participantes/{pid}/aceptaciones`) since accepting a legal document is a distinct semantic action from editing team role.

| Aspect | Detail |
|--------|--------|
| Pros | Separation of concerns — field edits vs. legal record actions; simpler PATCH schema; each action has clear intent |
| Cons | Two round trips for full participant update (edit + accept); aceptaciones endpoint is new surface area |
| Effort | Low-Medium |

### Approach 2: Single PATCH with Embedded Aceptaciones

**Description:** Add both aseguradora and aceptaciones (as a list of `tipo_aceptacion` strings) to `ParticipanteEditIn`. On the backend, update `Persona.aseguradora_*` and create `PersonaAceptacion` records for each acceptance type. All in one transaction.

| Aspect | Detail |
|--------|--------|
| Pros | Single round trip; atomic — all changes succeed or fail together |
| Cons | `aceptaciones` in a PATCH is semantically odd (PATCH is for updates, not actions that create audit records); `aceptado_en` and `ip_address` can't come from client (tamperable) — server must set these |
| Effort | Medium-High |

### Approach 3: Extend PATCH for Aseguradora + Add Aceptaciones to Add-Participant Flow

**Description:** Keep aceptaciones recording in the participant creation/add flow (where acceptances are naturally triggered), and only add aseguradora to the PATCH edit flow.

| Aspect | Detail |
|--------|--------|
| Pros | Aceptaciones are already being recorded at creation time; aligns with existing pattern |
| Cons | If user needs to update acceptances after initial creation (e.g., re-accept with new version), there's no mechanism; user intent specifically asks for edit/patch flow |
| Effort | Low |

---

## Recommendation

**Approach 1** with a distinction:

1. **Extend PATCH for `aseguradora_nombre` + `aseguradora_numero_poliza`** — these are truly field updates on `Persona`, natural fit for PATCH
2. **Record aceptaciones via separate endpoint** — BUT since the user asked specifically for "patch/edit flow", consider embedding aceptaciones recording in the PATCH as an optional `aceptaciones: list[tipo]` field where the server interprets it as "record these acceptances now" rather than as data to store. The backend sets `aceptado_en=now`, `ip_address= request IP`, `documento_version=BASES_VERSION_ACTIVA`.

**Recommended `ParticipanteEditIn` extension:**
```python
class ParticipanteEditIn(Schema):
    rol: str | None = None
    talle_camiseta: str | None = None
    # NEW — aseguradora (optional, updates Persona)
    aseguradora_nombre: str | None = None
    aseguradora_numero_poliza: str | None = None
    # NEW — aceptaciones (optional, records PersonaAceptacion)
    aceptaciones: list[Literal["BASES", "APTITUD_FISICA", "IMAGEN"]] | None = None
```

**Transaction boundary:** The `aceptaciones` recording (creating `PersonaAceptacion` records) should happen inside the same `transaction.atomic()` as the `ParticipanteInscripcion` update, since both are part of the same participant editing session.

---

## Risks

1. **Cross-model update in PATCH**: The PATCH currently updates only `ParticipanteInscripcion`. Adding aseguradora update means the flow must also update `Persona` — needs careful handling to avoid partial updates if `Persona` update fails
2. **Transaction atomicity**: If `aseguradora_nombre` updates successfully but `ParticipanteInscripcion` update fails, we need to rollback the aseguradora update — requires the flujo to handle cross-entity atomicity
3. **No existing pattern for cross-entity PATCH**: The `ParticipanteAccionFlujo` only knows about `ParticipanteInscripcion`. Adding `Persona` update requires injecting `PersonaCoreService` into the flujo or creating a separate service call
4. **Aceptaciones versioning**: If `BASES_VERSION_ACTIVA` changes, existing participants won't auto-reject. Acceptances are tied to a specific version — re-accepting may be needed when versions change
5. **Frontend form complexity**: Adding aseguradora + aceptaciones to the edit modal increases modal complexity significantly — currently only 2 fields
6. **IP address for aceptaciones**: The server must extract client IP from the request for `PersonaAceptacion.aceptado_en` audit field — requires access to Django request object in the flujo

---

## Validation Rules and Edge Cases

### Aseguradora
- `aseguradora_nombre`: max 255 chars, optional
- `aseguradora_numero_poliza`: max 50 chars, optional
- If either is provided, both should be accepted (not required to provide both)
- Clearing aseguradora: pass `null` explicitly (different from not providing the field)

### Aceptaciones
- Valid types: `BASES`, `APTITUD_FISICA`, `IMAGEN` (from `TipoAceptacionChoices`)
- Duplicate acceptance for same type: idempotent — update `aceptado_en` to now if already exists
- Server-set fields: `aceptado_en` (current datetime), `ip_address` (from request), `user_agent` (from request), `documento_version` (from `BASES_VERSION_ACTIVA`)
- Cannot "unaccept" — once recorded, `PersonaAceptacion` is append-only per tipo_aceptacion (latest is current)

---

## Minimal Patch-Oriented Change Plan

### Phase 1: Backend — Extend PATCH for Aseguradora (Low Risk)
1. Add `aseguradora_nombre` and `aseguradora_numero_poliza` to `ParticipanteEditIn`
2. Add `PersonaCoreService.actualizar_aseguradora(persona_id, nombre, numero_poliza)` method
3. In `ParticipanteAccionFlujo._editar_participante_sync`, after updating `ParticipanteInscripcion`, also update `Persona` if aseguradora fields present
4. Add `PersonaAceptacion` recording method to `PersonaCoreService`

### Phase 2: Backend — Add Aceptaciones Recording to PATCH (Medium)
5. Add optional `aceptaciones: list[str]` to `ParticipanteEditIn`
6. In `_editar_participante_sync`, after aseguradora update, iterate aceptaciones and create `PersonaAceptacion` records via `PersonaCoreService._crear_aceptacion()`
7. All inside same `transaction.atomic()`

### Phase 3: Frontend — Extend Edit Modal (Medium)
8. Add aseguradora fields to `participanteEdit.schema.ts`
9. Add aseguradora inputs to `EditParticipanteModal.tsx` (insurance section)
10. Add aceptaciones checkboxes to modal (if user needs to record acceptances)
11. Update `EditarParticipantePayload` in service file

---

## Verification Tests

### Backend Tests to Add

**`test_editar_participante_aseguradora_success`**:
```python
# GIVEN: participant with Persona that has no aseguradora
# WHEN: PATCH with aseguradora_nombre="Seguros Peru" and aseguradora_numero_poliza="SP-12345"
# THEN: 200, Persona.aseguradora_nombre and aseguradora_numero_poliza updated
```

**`test_editar_participante_aseguradora_partial`**:
```python
# GIVEN: participant with Persona that has existing aseguradora
# WHEN: PATCH with only aseguradora_nombre (no numero_poliza)
# THEN: 200, nombre updated, numero_poliza unchanged
```

**`test_editar_participante_aceptaciones_crea_registro`**:
```python
# GIVEN: participant with persona
# WHEN: PATCH with aceptaciones=["BASES"]
# THEN: 200, PersonaAceptacion record created with tipo=BASES, aceptdo_en=now, documento_version=BASES_VERSION_ACTIVA
```

**`test_editar_participante_aceptaciones_idempotente`**:
```python
# GIVEN: participant with persona that already has BASES acceptance from today
# WHEN: PATCH with aceptaciones=["BASES"]
# THEN: 200, aceptdo_en updated to new now timestamp (idempotent re-accept)
```

**`test_editar_participante_inscripcionAjena_aseguradora_rechazado`**:
```python
# GIVEN: user tries to edit participant in another user's inscription
# WHEN: PATCH with aseguradora fields
# THEN: 404 or 400 (consistent with existing rol/talle rejection)
```

**Run command:**
```bash
cd backend && python -m pytest modules/inscripciones/tests/integration/test_participante_crud_move.py -v
```

### Frontend Verification

**Typecheck:**
```bash
cd frontend && npx tsc --noEmit
```

**Build:**
```bash
cd frontend && npm run build
```

---

## Ready for Proposal

**Yes** — this exploration is complete. The architecture is clear, the domain models already exist (no migrations needed), and the approach is well-defined.

The orchestrator should tell the user:
- `aseguradora_nombre` and `aseguradora_numero_poliza` **already exist on `Persona`** — no DB migration needed
- `PersonaAceptacion` **already exists** — no new model needed for acceptances
- The minimal change adds optional aseguradora fields to `ParticipanteEditIn` and updates `Persona` from within `ParticipanteAccionFlujo._editar_participante_sync` (cross-entity update in same transaction)
- Aceptaciones can be added to the same PATCH as an optional list — the backend creates `PersonaAceptacion` records with server-set audit fields
- The frontend modal needs a new section for insurance data and optionally acceptance checkboxes
