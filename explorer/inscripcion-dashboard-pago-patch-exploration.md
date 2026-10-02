# Exploration: Inscripcion Dashboard, Pago, and PATCH/Update

> **Project:** `salesianos`
> **Date:** 2026-09-20
> **Type:** Architecture Exploration
> **Mode:** Exploration — no implementation

---

## 1. Current State

### 1.1 Post-Creation Redirect Flow (Real Frontend)

**Location:** `frontend/src/features/inscripciones/hooks/useCreateInscripcion.ts`

```typescript
// line 31-33
onSuccess: (_data) => {
  toast.success("¡Inscripción creada con éxito!");
  router.push("/dashboard");  // ← redirects to /dashboard
},
```

**Current behavior:**
- After successful creation, redirects to `/dashboard`
- The `InscripcionOut` response data (including `id`) is available but not used for routing
- No dedicated detail page `/inscripcion/:id` exists
- Dashboard shows a blue gradient background (`linear-gradient(160deg, #1a1857 0%, #211e70 45%, #0c0c1f 100%)`)

**Missing:** No route to a detail page that would show the specific inscription with its ID and enable PATCH updates.

### 1.2 Dashboard Page (Real Frontend)

**Location:** `frontend/src/app/(auth)/dashboard/page.tsx`

- Uses `getMisInscripciones()` to fetch the responsible's inscriptions
- Renders `InscripcionCard` components with status badges
- Blue gradient background — **not white**
- No shadcn sidebar — pure inline layout
- "Nueva" button redirects to `/inscripcion`

### 1.3 Frontend-Mokup (Parallel Implementation)

The `frontend-mokup` directory has a separate implementation with:

- **Dashboard:** `frontend-mokup/src/app/(protected)/dashboard/page.tsx` → renders `<ResponsableDashboardView>`
- **Sidebar:** Uses `Sidebar` component from `frontend-mokup/src/components/ui/sidebar.tsx` (shadcn-style)
- **PATCH endpoint:** `frontend-mokup/src/app/api/inscripcion/[id]/route.ts` — full `PATCH /api/inscripcion/[id]` with `UpdateInscripcionSchema` supporting `teamName`, `deportistas`, `equiposConfig`
- **Redirect after create:** `useCreateInscripcion` in frontend-mokup does NOT redirect (no `router.push` in `onSuccess`)

**Note:** frontend-mokup appears to be a parallel/prototype implementation. The real production frontend is in `frontend/`.

---

## 2. Domain Model Analysis: Participants, Teams, Disciplines, and Substitutes

### 2.1 Current Schema Architecture

```
Inscripcion
  └── EquipoInscrito (one per inscription+discipline)
        └── ParticipacionDisciplina (one per persona+discipline+event) ← R11 unique constraint
              └── ParticipanteInscripcion (links participacion to equipo with rol)
```

**Model details:**

| Model | Role |
|-------|------|
| `Inscripcion` | Main record linking responsible, event, package |
| `EquipoInscrito` | Team registered for a specific discipline. `UniqueConstraint(inscripcion, disciplina)` |
| `ParticipacionDisciplina` | Records that a **person** participates in a discipline+event. `UniqueConstraint(evento, disciplina, persona)` — R11 |
| `ParticipanteInscripcion` | Links a `ParticipacionDisciplina` to an `EquipoInscrito` with a `rol` (JUGADOR/CAPITAN/DELEGADO) and `talle_camiseta` |

**Relational path for a participant:**
```
ParticipanteInscripcion
  .participacion → ParticipacionDisciplina (.persona, .disciplina, .evento)
  .equipo → EquipoInscrito (.inscripcion, .disciplina)
```

### 2.2 Role System (No Substitute/Reserve Concept)

**Current roles** (`backend/modules/inscripciones/domain/constants.py`):
```python
class RolParticipanteChoices(models.TextChoices):
    JUGADOR = "JUGADOR", "Jugador"
    CAPITAN = "CAPITAN", "Capitan"
    DELEGADO = "DELEGADO", "Delegado"
```

**Frontend roles** (`frontend-mokup/.../InscripcionEditModal.tsx`):
```typescript
const ROLES = ["Jugador", "Capitán", "Delegado"] as const;
```

**There is NO "suplente", "reserva", or "titular" role.** All registered participants are stored equally as `ParticipanteInscripcion` with one of these three roles.

### 2.3 What `min_jugadores` / `max_jugadores` Means

**On `Disciplina` model** (`backend/modules/inscripciones/domain/models/disciplina.py`):
```python
min_jugadores = PositiveIntegerField(null=True, ...)
max_jugadores = PositiveIntegerField(null=True, ...)
```

**Validation** (`ParticipanteService.validar_roster_equipos_de_inscripcion`):
```python
cantidad = equipo.participaciones.count()  # counts ParticipacionDisciplina records
roster_errors = validators.validar_roster_equipo(disciplina, cantidad)
```

**Interpretation:** `min_jugadores`/`max_jugadores` define the **roster size** — the total number of registered participants for that discipline/team. This is NOT "starters vs. substitutes." The model does not distinguish between playing and non-playing (reserve) participants.

### 2.4 The 10 Registered / 7 Playing Scenario

**Current model capability:** If 10 people are registered for a discipline (via 10 `ParticipanteInscripcion` records), the model considers all 10 as participants. The `max_jugadores` limit would be checked against 10, not against 7.

**What the model CAN support:**
- All 10 people are registered participants
- All 10 belong to the same team (`EquipoInscrito`) for that discipline
- All 10 are linked via `ParticipacionDisciplina` to that discipline

**What the model CANNOT express:**
- "7 are starters, 3 are substitutes"
- A participant's "playing status" (active/reserve)

**To support starters vs. substitutes, the model would need one of:**
1. A new `estado_participacion` field on `ParticipanteInscripcion` (e.g., "ACTIVO", "RESERVA") — **simplest change**
2. A separate "reserve list" mechanism — **more complex**
3. A `cantidad_titulares` field on `EquipoInscrito` — **complex, requires DB migration**

**For now (MVP):** The system should treat all registered participants as equally registered. Payment/roster validation should use the total count, not distinguish starters from reserves.

### 2.5 Participant Belongs to Team AND Discipline

**Answer to domain question:** A participant belongs to a **team** (`EquipoInscrito`) AND to a **discipline** (`ParticipacionDisciplina`), through two separate FK relationships:

- `ParticipanteInscripcion.equipo` → `EquipoInscrito` (the team)
- `ParticipanteInscripcion.participacion` → `ParticipacionDisciplina` (which contains `.disciplina` and `.evento`)

A participant can only be in **one team per discipline** (enforced by R11: unique person+discipline+event). But the same person can appear in multiple teams if they play multiple disciplines (via multiple `ParticipacionDisciplina` records).

---

## 3. Backend Gaps

### 3.1 Missing Endpoints in Django Backend

| Endpoint | Status | Notes |
|----------|--------|-------|
| `GET /api/inscripciones/{id}` | **Missing** | No detail endpoint for responsable to view their own inscription |
| `PATCH /api/inscripciones/{id}` | **Missing** | No update endpoint for responsable to edit team name, add participants |
| `POST /api/inscripciones/{id}/participantes` | **Missing** | No endpoint to add a participant to existing team |
| `DELETE /api/inscripciones/{id}/participantes/{pid}` | **Missing** | No endpoint to remove a participant |

**Existing endpoints:**
- `POST /api/inscripciones/` — create ✅
- `GET /api/inscripciones/mis-inscripciones/` — list for responsible ✅ (has PLACEHOLDER_USER_ID bug)
- `PATCH /api/inscripciones/{id}/estado` — admin status transition ✅

### 3.2 What the frontend-mokup Has (that real frontend needs)

The `frontend-mokup` has a full implementation of `PATCH /api/inscripcion/[id]` with:
- `UpdateInscripcionSchema` with `teamName`, `deportistas`, `equiposConfig`
- Upsert logic for deportistas (update if exists, insert if new)
- Persona upsert by `numeroDocumento`
- `DebuttereEquipos` link management
- Permission check: `existing.inscripcion.userId !== session.sub`

**This endpoint does NOT exist in the Django backend.** It would need to be created following the contract:
- Thin async controller → async orchestrator → async flujo (with `sync_to_async(transaction.atomic)`) → core sync services

---

## 4. Frontend Gaps

### 4.1 No Detail/Edit Page

After creation, the user lands on `/dashboard` which lists all inscriptions. There is:
- **No** `/inscripcion/:id` route to view a specific inscription
- **No** edit capability on the dashboard cards
- The blue dashboard theme doesn't match the white dashboard request

### 4.2 Dashboard Needs White Theme + Sidebar

| Component | Current State | Requested State |
|-----------|---------------|-----------------|
| Background | Blue gradient (`#1a1857` → `#211e70` → `#0c0c1f`) | White |
| Layout | Full-width inline | Shadcn-style sidebar with `Inscripciones` section |
| Sidebar | None | `Sidebar` with collapsible menu sections |

### 4.3 Payment Placeholder

No payment UI exists. The states `PAGO_PENDIENTE` and `PAGADA` exist in `EstadoInscripcionChoices` but:
- No payment flow is implemented
- No "pagar" call-to-action on the dashboard
- No payment pending notice on the detail page

---

## 5. Recommended SDD Phases

### Phase 1: Backend — Detail + PATCH Endpoints (sdd-propose → sdd-spec → sdd-design → sdd-tasks → sdd-apply)

Create in Django backend:
1. `GET /api/inscripciones/{id}` — return full inscription with equipos, participantes, personas
2. `PATCH /api/inscripciones/{id}` — update team name and/or participants
3. Both must follow contract: thin controller → orchestrator → flujo (async, `sync_to_async(transaction.atomic)`) → core sync services

### Phase 2: Frontend — Detail Page + PATCH Mutation (sdd-propose → sdd-spec → sdd-design → sdd-tasks → sdd-apply)

1. Add `/inscripcion/[id]/page.tsx` route
2. Create `InscripcionDetailView` showing inscription data with edit capability
3. Add `useUpdateInscripcion` mutation hook
4. Change `useCreateInscripcion` redirect from `/dashboard` to `/inscripcion/${data.id}`
5. Add PATCH integration for updating team name and participants

### Phase 3: Dashboard — White Theme + Sidebar (sdd-propose → sdd-spec → sdd-design → sdd-tasks → sdd-apply)

1. Refactor dashboard to use shadcn `Sidebar` component
2. Add `Inscripciones` section with links
3. Change background to white
4. Ensure sidebar is collapsible

### Phase 4: Payment Placeholder (sdd-propose → sdd-spec → sdd-design → sdd-tasks → sdd-apply)

1. Add "Pagar" button / callout on detail page when status is `PAGO_PENDIENTE`
2. Show "Pago pendiente" status badge
3. Payment integration can be stubbed/future

### Phase 5: Roster Min/Max Respect on PATCH

1. When adding participants via PATCH, validate `max_jugadores` on the discipline
2. Show clear error if roster limit would be exceeded
3. This uses existing `validators.validar_roster_equipo()` which already exists

---

## 6. Verification Recommendations

1. **Backend endpoint tests:** Test `PATCH /api/inscripciones/{id}` with valid/invalid data, auth, and roster limit scenarios
2. **Frontend redirect test:** Verify that after creation, the user lands on the detail page (not just dashboard)
3. **Dashboard visual test:** Screenshot both the blue dashboard (before) and white dashboard (after) to confirm theme change
4. **Sidebar test:** Verify collapsible behavior and `Inscripciones` section presence
5. **Payment placeholder test:** Verify "Pagar" callout appears for `PAGO_PENDIENTE` status

---

## 7. Summary of Key Findings

| Item | Finding |
|------|---------|
| **Participant belongs to** | Team (`EquipoInscrito`) via `ParticipanteInscripcion.equipo` AND Discipline (`ParticipacionDisciplina.disciplina`) via `ParticipanteInscripcion.participacion` |
| **Substitutes/Reserves** | **Not modeled.** All registered participants are equal. A new field (e.g., `estado_participacion`) would be needed to distinguish playing vs. non-playing. |
| **min/max players** | Means **roster size** — total registered participants, not starters vs. reserves. |
| **After creation redirect** | Currently goes to `/dashboard`. Should redirect to `/inscripcion/${id}`. |
| **PATCH endpoint** | Missing in Django backend. Exists in frontend-mokup. |
| **Detail page** | Does not exist in real frontend. Needs creation. |
| **Dashboard theme** | Blue gradient — needs to be white. |
| **Sidebar** | None — needs shadcn-style sidebar with `Inscripciones` section. |
| **Payment** | Not implemented. Needs placeholder callout. |
