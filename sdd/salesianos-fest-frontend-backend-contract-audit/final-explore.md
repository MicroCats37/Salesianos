# Final Exploration: salesianos-fest-frontend-backend-contract-audit

**Status:** post-apply verification complete
**Fecha:** 2026-10-18
**Proyecto:** Salesianos
**Cambio:** `salesianos-fest-frontend-backend-contract-audit`
**Modo:** post-apply verification + CodeGraph analysis

---

## Executive Summary

| Area | Estado | Severidad |
|------|--------|-----------|
| Catalog flat event/package fields | VERIFIED | - |
| Nested team participants in detail | VERIFIED | - |
| PATCH /participaciones/{id}/retirar | VERIFIED | - |
| PATCH /participaciones/{id}/mover | VERIFIED | - |
| PATCH /participaciones/{id} (edit) | **MISSING** | **CRITICAL** |
| Frontend types/field names | VERIFIED | - |
| Response wrappers | VERIFIED | - |
| Cache consumers | VERIFIED | - |
| Multi-step creation flow | UNVERIFIED | - |
| Responsible-auth (GET /inscripciones/) | UNVERIFIED | MEDIUM |

---

## Confirmed Implemented (Evidence from CodeGraph)

### 1. Catalog — Flat event/package fields

- `PaqueteListOut` has `evento_id: str` (flat, not nested)
- `PaqueteDetailOut` has `evento_id: str` (flat)
- `CategoriaOut` has `evento_id: str` + `evento_nombre: str`
- Frontend `Paquete` interface uses flat `evento_id`
- Backend presenter transforms `PaqueteResult` -> `PaqueteDetailOut` with flat `evento_id`
- **No nested `evento` objects in catalog responses**

### 2. Nested Team Participants

- `InscripcionDetailOut.equipos: list[EquipoDetailSchema]`
- `EquipoDetailSchema` includes `participantes: list[ParticipacionOut]`
- `InscripcionDetailResult.equipos` dataclass has `participaciones: list[ParticipacionResult] = None` with `__post_init__` default
- Presenter `present_inscripcion_detail` iterates `eq.participaciones` and builds `ParticipacionOut` for each
- Selector `get_by_id_with_details` prefetches `equipos__participaciones__inscripcion_persona__persona`
- Frontend `EquipoDetalleOut` has `participantes: ParticipanteOut[]`

### 3. PATCH /participaciones/{id}/retirar

- `ParticipacionController.retirar_participacion` at line 333
- Route: `PATCH /api/participaciones/{id}/retirar`
- Calls `self._orch.retirer_participacion_proceso`
- Presenter returns `ParticipacionOut`

### 4. PATCH /participaciones/{id}/mover

- `ParticipacionController.mover_participacion` at line 348
- Route: `PATCH /api/participaciones/{id}/mover`
- Accepts `MoverParticipacionIn` payload with `equipo_destino_id`
- Orchestrator has `mover_participacion_proceso` + `_mover_atomico`

### 5. Frontend Types — Field Names

- `InscripcionDetalleOut.evento_nombre: string` (flat, not nested)
- `InscripcionDetalleOut.delegado_nombre: string | null` (flat)
- `ParticipanteOut.talla_camiseta: string | null`
- `EditarParticipantePayload.rol`, `talla_camiseta`, `notas` match `ActualizarParticipacionIn`
- All field names match between frontend and backend schemas
- `talla_camiseta` spelling correct (not `talle_camiseta`)

### 6. Response Wrappers

- All endpoints use `ApiResponse[T]` envelope: `{ success: bool, data: T, error: ErrorDetail, message: str }`
- Frontend `ApiResponse<T>` interface matches exactly
- `success_response()` wrapper applies `model_dump(mode='json')` + `_decimal_to_float`
- No generic `data` envelope or `z.any()` in type contracts

### 7. Cache Consumers

- `useInscripcionCacheSync` at `frontend/src/features/inscripciones/hooks/useInscripcionCacheSync.ts`
- `inscripcionCacheHelpers` provides `addParticipante`, `removeParticipante`, `updateParticipante`, `moveParticipante`
- `updateParticipante` uses `ParticipanteOut` shape, updates in-place preserving array order
- All hooks (`useAgregarParticipantes`, `useEliminarParticipante`, `useMoverParticipante`, `useEditarParticipante`) consume this cache
- `inscripcionDetalleKey` generates cache key from `inscripcionId`

---

## Confirmed Blocker

### CRITICAL — `PATCH /participaciones/{id}` (edit participant) endpoint MISSING

**Evidence:**
- Frontend `editarParticipante()` calls: `PATCH /participaciones/${participanteId}` with payload `{ rol?, talla_camiseta?, aseguradora_nombre?, aseguradora_numero_poliza?, notas? }`
- Backend `ParticipacionController` has **NO** `PATCH /{id}` route
- `ParticipacionController` only has: `POST /`, `GET /{id}`, `GET /equipo/{id}`, `PATCH /{id}/retirar`, `PATCH /{id}/mover`
- `ParticipacionOrchestrator` has **NO** `actualizar_participacion_proceso` method
- `ParticipacionOrchestrator` methods: `crear_participacion_proceso`, `obter_participacion_proceso`, `listar_por_equipo_proceso`, `mover_participacion_proceso`, `retirer_participacion_proceso`
- Schema `ActualizarParticipacionIn` exists in `inscripcion_schemas.py` (line 126) but is **NEVER USED** by any controller route
- `ParticipacionCoreService.actualizar()` exists (line 72) but orchestrator doesn't expose it

**Impact:** Frontend `editarParticipante()` will always get a 404. Participant rol, talla_camiseta, and notas **CANNOT be updated** from the UI.

**Required fix:** Add `PATCH /participaciones/{id}` endpoint to `ParticipacionController` and `actualizar_participacion_proceso` to `ParticipacionOrchestrator`.

---

## Unverified / Outstanding (Not Implemented Unless Evidenced)

### Multi-step creation flow — NOT VERIFIED

The original exploration flagged this as a critical issue. The flow requires:
1. Create inscripcion: `POST /inscripciones/` (JWT auth, flat payload)
2. Create equipos: `POST /equipos/` (public, requires `inscripcion_id`)
3. Add participants: `POST /inscripciones/{id}/personas` (public, creates roster + Participacion atomically)

**I did not verify:**
- Whether the frontend wizard actually calls these endpoints in sequence
- Whether the frontend has the full multi-step flow implemented
- Whether `agregarParticipantesAEquipo` properly chains after `crearEquipo`

**Apply artifact (#8841) does NOT mention multi-step creation implementation.** This work is **NOT evidenced as complete**. **Do NOT mark as implemented.**

### Dashboard auth guard for `getMisInscripciones` — NOT VERIFIED

**Evidence:**
- Backend `GET /inscripciones/` has `auth=JWTAuth()` — JWT required
- Frontend `DashboardPage` calls `getMisInscripciones()` inside `useEffect` with no auth guard
- `useAuthUser()` exists but is only used for display name, not to gate the API call

**Impact:** If an unauthenticated user somehow reaches the dashboard, the API call will fail with 401 at the network level (not gracefully handled).

**Apply artifact (#8841) mentions this as an outstanding concern.** Not a blocker for logged-in users, but a UX issue. **Do NOT mark as implemented.**

### `agregarParticipantesAEquipo` sends wrong payload

Apply artifact (#8841) notes:
> "The `agregarParticipantesAEquipo` function still sends an array of participants but the backend expects a single `persona_id`."

The frontend function extracts `payload.participantes[0]?.persona_id` before sending, so it works by accident (sends one). But this is fragile — the function signature accepts an array but only uses the first element.

**Status:** Functional but not properly designed. Not a blocker.

---

## Schema Field Compatibility Matrix

| Frontend Type | Frontend Field | Backend Schema | Backend Field | Status |
|--------------|----------------|---------------|--------------|--------|
| `InscripcionDetalleOut` | `evento_nombre` | `InscripcionDetailOut` | `evento_nombre` | VERIFIED |
| `InscripcionDetalleOut` | `paquete_nombre` | `InscripcionDetailOut` | `paquete_nombre` | VERIFIED |
| `InscripcionDetalleOut` | `delegado_nombre` | `InscripcionDetailOut` | `delegado_nombre` | VERIFIED |
| `InscripcionDetalleOut` | `equipos[].participantes` | `InscripcionDetailOut.equipos` | `participantes` | VERIFIED |
| `ParticipanteOut` | `talla_camiseta` | `ParticipacionOut` | `talla_camiseta` | VERIFIED |
| `ParticipanteOut` | `rol` | `ParticipacionOut` | `rol` | VERIFIED |
| `ParticipanteOut` | `persona.nombre` | `ParticipacionOut.persona` | `nombre` | VERIFIED |
| `EditarParticipantePayload` | `talla_camiseta` | `ActualizarParticipacionIn` | `talla_camiseta` | VERIFIED |
| `MoverParticipantePayload` | `equipo_destino_id` | `MoverParticipacionIn` | `equipo_destino_id` | VERIFIED |
| `EquipoDetalleOut` | `disciplina_id` | `EquipoDetailSchema` | (not present) | FE-only |
| `EquipoDetalleOut` | `inscripcion_id` | `EquipoDetailSchema` | (not present) | FE-only |

Note: `EquipoDetailSchema` does NOT have `disciplina_id` or `inscripcion_id` — only nested `disciplina: DisciplinaSummarySchema`. Frontend `EquipoDetalleOut` has both flat `disciplina_id` and nested `disciplina` — this is a minor type divergence but not a runtime issue.

---

## Routes Verified

| Route | Auth | Status |
|-------|------|--------|
| `GET /catalogo/disciplinas/` | AllowAny | VERIFIED |
| `GET /catalogo/promociones/` | AllowAny | VERIFIED |
| `GET /catalogo/categorias/` | AllowAny | VERIFIED |
| `GET /catalogo/paquetes/` | AllowAny | VERIFIED |
| `GET /catalogo/paquetes/{id}/` | AllowAny | VERIFIED |
| `POST /inscripciones/` | JWTAuth | VERIFIED |
| `GET /inscripciones/` | JWTAuth | VERIFIED (auth guard unverified) |
| `GET /inscripciones/{id}/detalle` | AllowAny | VERIFIED |
| `PATCH /inscripciones/{id}` | AllowAny | VERIFIED |
| `POST /inscripciones/{id}/personas` | AllowAny | VERIFIED |
| `PATCH /inscripciones/{id}/personas/{pid}/retirar` | AllowAny | VERIFIED |
| `POST /equipos/` | AllowAny | VERIFIED |
| `GET /equipos/{id}` | AllowAny | VERIFIED |
| `GET /equipos/inscripcion/{id}` | AllowAny | VERIFIED |
| `POST /participaciones/` | AllowAny | VERIFIED |
| `GET /participaciones/{id}` | AllowAny | VERIFIED |
| `GET /participaciones/equipo/{id}` | AllowAny | VERIFIED |
| `PATCH /participaciones/{id}/retirar` | AllowAny | VERIFIED |
| `PATCH /participaciones/{id}/mover` | AllowAny | VERIFIED |
| `PATCH /participaciones/{id}` | AllowAny | **MISSING** |

---

## Risks

1. **CRITICAL — Participant editing broken:** `PATCH /participaciones/{id}` does not exist. Users cannot update participant rol, talla_camiseta, or notas from the UI.
2. **MEDIUM — Dashboard auth UX:** `getMisInscripciones` will 401 at network level for unauthenticated users instead of redirecting gracefully.
3. **LOW — Multi-step creation unverified:** Cannot confirm the frontend wizard properly sequences the create flow without further investigation.

---

## Conclusion

**Not ready.** The contract audit apply phase completed significant work (nested participantes, PATCH retire/mover, flat event fields, type fixes), but one **CRITICAL** endpoint remains missing: `PATCH /participaciones/{id}` for editing participant details.

The following do NOT block but should be addressed:
- Dashboard auth guard (UX improvement)
- Multi-step creation verification (requires frontend flow audit)
- `agregarParticipantesAEquipo` payload design (fragile but functional)
