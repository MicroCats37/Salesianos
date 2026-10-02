# Exploration: Inscripcion Flow (Frontend + Backend)

> **Proyecto:** `salesianos`
> **Fecha:** 2026-09-20
> **Tipo:** Architecture Exploration
> **Modo:** Exploration — no implementation

---

## 1. Current State

### 1.1 End-to-End Flow Summary

The inscription flow is a 4-step wizard that creates a complete inscription (Inscripcion + EquipoInscrito + ParticipacionDisciplina + ParticipanteInscripcion) in a single POST request.

```
Step 1 (Promoción) → Step 2 (Paquete) → Step 3 (Equipos) → Step 4 (Declaraciones) → POST /inscripciones/
```

**Data resolution chain:**
- `evento` is derived server-side from `settings.EVENTO_ACTIVO_NOMBRE` — NOT sent by frontend
- `paquete` is selected by the user from a card list
- `promocion` is selected by the user from a searchable dropdown
- `equipos` are auto-created by frontend based on `paquete.cantidad_disciplinas_requeridas`
- Each equipo must have a `disciplina_id` from the package's discipline list
- Each equipo must have participants (at least 1)

---

## 2. Affected Areas

### Frontend (Real Implementation)

| File | Purpose |
|------|---------|
| `frontend/src/app/(auth)/inscripcion/page.tsx` | Route — renders InscripcionClientShell |
| `frontend/src/features/inscripciones/views/InscripcionClientShell.tsx` | Client shell component |
| `frontend/src/features/inscripciones/components/InscripcionWizard.tsx` | Main 4-step wizard component |
| `frontend/src/features/inscripciones/schemas/inscripcion.schema.ts` | Zod schemas + `toBackendPayload()` transform |
| `frontend/src/features/inscripciones/services/inscripcion.service.ts` | `createInscripcion()` API call |
| `frontend/src/features/inscripciones/services/catalog.service.ts` | `getPaquetes()`, `getPaqueteDisciplinas()`, `getDisciplinas()`, `getPromociones()`, `getCategorias()` |
| `frontend/src/features/inscripciones/hooks/useCreateInscripcion.ts` | TanStack Query mutation hook |
| `frontend/src/features/inscripciones/hooks/useInscripcionCatalogs.ts` | `usePaquetes`, `usePaqueteDisciplinas`, `usePromociones`, `useDisciplinas`, `useCategorias` |
| `frontend/src/features/inscripciones/components/smart-fields/SmartPaqueteCardsField.tsx` | Card-based package selector (discipline-aware) |
| `frontend/src/features/inscripciones/components/smart-fields/SmartEquipoField.tsx` | Dynamic equipo array with discipline filtering |
| `frontend/src/features/inscripciones/components/steps/StepDeclarations.tsx` | Step 4 — acceptance checkboxes |
| `frontend/src/lib/api.ts` | Axios instance with JWT interceptors |
| `frontend/src/types/api.types.ts` | `ApiResponse<T>` type |
| `frontend/src/features/landing/paquetes.service.ts` | Landing page package fetcher (separate from wizard) |

### Backend

| File | Purpose |
|------|---------|
| `backend/modules/inscripciones/presentation/controllers/inscripcion_controller.py` | Thin controller — delegates to orchestrator |
| `backend/modules/inscripciones/presentation/controllers/paquete_controller.py` | Public catalog: list paquetes, list paquete disciplinas |
| `backend/modules/inscripciones/presentation/controllers/disciplina_controller.py` | Public catalog: list disciplinas, list categorias |
| `backend/modules/inscripciones/presentation/controllers/promocion_controller.py` | Public catalog: list promociones |
| `backend/modules/inscripciones/presentation/schemas/inscripcion_schemas.py` | HTTP request/response schemas (Ninja) |
| `backend/modules/inscripciones/presentation/schemas/paquete_schemas.py` | HTTP schemas for paquetes |
| `backend/modules/inscripciones/presentation/presenters/inscripcion_presenter.py` | Domain model → HTTP schema transformer |
| `backend/modules/inscripciones/presentation/presenters/paquete_presenter.py` | `present_paquete()` with derived `cantidad_maxima_equipos` |
| `backend/modules/inscripciones/domain/services/orchestrators/inscripcion_orchestrator.py` | Thin async facade |
| `backend/modules/inscripciones/domain/services/flujos/crear_inscripcion_flujo.py` | Full async flow with `transaction.atomic` |
| `backend/modules/inscripciones/domain/services/core/inscripcion_service.py` | Sync CRUD for Inscripcion |
| `backend/modules/inscripciones/domain/services/core/paquete_service.py` | Sync CRUD for Paquete + PaqueteDisciplina |
| `backend/modules/inscripciones/domain/services/core/equipo_service.py` | Sync CRUD for EquipoInscrito |
| `backend/modules/inscripciones/domain/services/core/disciplina_service.py` | Sync service for Disciplina |
| `backend/modules/inscripciones/domain/services/core/validators.py` | `validar_disciplina_en_paquete()`, `validar_cantidad_disciplinas_paquete()`, etc. |
| `backend/modules/inscripciones/domain/selectors/inscripcion_selector.py` | Complex queries: `listar_disciplinas_de_paquete()`, etc. |
| `backend/modules/inscripciones/domain/models/inscripcion.py` | `Inscripcion`, `InscripcionDelegado` Django models |
| `backend/modules/inscripciones/domain/models/paquete.py` | `Paquete`, `PaqueteDisciplina` Django models |
| `backend/modules/inscripciones/domain/models/equipo.py` | `EquipoInscrito`, `ParticipacionDisciplina`, `ParticipanteInscripcion` Django models |
| `backend/modules/inscripciones/domain/models/disciplina.py` | `Disciplina`, `Categoria` Django models |
| `backend/modules/inscripciones/domain/constants.py` | Choices: `EstadoInscripcionChoices`, `ModoDisciplinasPaqueteChoices`, `RolParticipanteChoices`, etc. |
| `backend/modules/inscripciones/domain/exceptions.py` | Domain exceptions: `DisciplinaNoEnPaqueteError`, `CantidadDisciplinasInvalidaError`, etc. |

---

## 3. Data Flow Detail

### 3.1 Frontend Call Sequence

```
User loads /inscripcion page
  ↓
usePromociones() → GET /inscripciones/promociones/  (auth=AllowAny)
  ↓
usePaquetes() → GET /inscripciones/paquetes/  (auth=AllowAny)
  ↓
User selects package → usePaqueteDisciplinas(paqueteId) → GET /inscripciones/paquetes/{id}/disciplinas/
  ↓
SmartPaqueteCardsField renders discipline tags per package card
  ↓
User advances to Step 3 (Equipos)
  ↓
SmartEquipoField auto-creates N equipo slots based on paquete.cantidad_maxima_equipos
  ↓
For each equipo slot: SearchableSelect filtered to paqueteDisciplinas (discipline_id)
  ↓
User fills participants per equipo
  ↓
User clicks "Enviar inscripción"
  ↓
toBackendPayload(data) transforms camelCase to snake_case
  ↓
POST /inscripciones/  (auth=JWT)
  ↓
Backend creates full inscription atomically
  ↓
Response: { success: true, data: { id, evento_id, paquete_id, estado, ... } }
```

### 3.2 Backend Request Processing

```
POST /inscripciones/  (InscripcionController.crear_inscripcion)
  ↓
Extract responsable_id from JWT
  ↓
Build equipos_data from payload
  ↓
Call orchestrator.crear_inscripcion_completa(...)
  ↓
CrearInscripcionFlujo._crear_inscripcion_completa (sync_via_sync_to_async)
  ↓
1. _resolver_evento_activo() → Evento from settings.EVENTO_ACTIVO_NOMBRE
  ↓
2. Validate package exists
  ↓
3. validators.validar_cantidad_disciplinas_paquete(paquete, equipos_data)
     - Checks mode FIJO/ELEGIBLE matches cantidad_disciplinas_requeridas
     - Checks distinct disciplines count
  ↓
4. transaction.atomic:
     a. Create Inscripcion record
     b. Create PersonaAceptacion records (BASES, APTITUD_FISICA, IMAGEN)
     c. For each equipo_data:
        - validators.validar_disciplina_en_paquete(paquete, disciplina_id)
        - Create EquipoInscrito
        - For each participant:
          - Resolve Persona (by persona_id or by document lookup/creation)
          - Create ParticipacionDisciplina
          - Create ParticipanteInscripcion
  ↓
5. Return Inscripcion instance
  ↓
InscripcionPresenter.present_inscripcion(inscripcion) → InscripcionOut
  ↓
success_response(InscripcionOut)
```

---

## 4. Package-Discipline Relationship

### 4.1 Backend Storage

**Model:** `PaqueteDisciplina` is an explicit many-to-many through table:

```python
class PaqueteDisciplina(BaseModel):
    paquete = ForeignKey(Paquete)
    disciplina = ForeignKey(Disciplina)
    # UniqueConstraint(paquete, disciplina)
```

### 4.2 API Endpoints for Package Disciplines

| Endpoint | Returns | Auth |
|----------|---------|------|
| `GET /inscripciones/paquetes/` | List of packages with `cantidad_maxima_equipos` derived by presenter | AllowAny |
| `GET /inscripciones/paquetes/{id}/disciplinas/` | List of `PaqueteDisciplinaOut` (`disciplina_id`, `disciplina_nombre`, `disciplina_sigla`) | AllowAny |

### 4.3 Frontend Consumption

**In `SmartPaqueteCardsField.tsx`:**
- Each package card independently calls `usePaqueteDisciplinas(card.id)` to fetch disciplines
- Displays discipline tags on each card (e.g., "Fútbol (FUT)", "Básquet (BAS)")
- Disciplines are fetched lazily per card

**In `SmartEquipoField.tsx`:**
- `usePaqueteDisciplinas(paqueteId)` fetches disciplines for the selected package
- `availableDisciplinas` filters out already-selected disciplines per equipo
- Prevents duplicate discipline selection across equipos

### 4.4 Validation Chain (Backend)

```
CrearInscripcionFlujo._crear_inscripcion_sync
  ↓
validators.validar_cantidad_disciplinas_paquete(paquete, equipos_data)
  - FIJO mode: requires exact match between selected disciplines count and cantidad_disciplinas_requeridas
  - ELEGIBLE mode: requires exact match between selected disciplines count and cantidad_disciplinas_requeridas
  ↓
For each equipo in equipos_data:
  validators.validar_disciplina_en_paquete(paquete, disciplina_id)
    → queries PaqueteDisciplina.objects.filter(paquete=paquete, disciplina_id=disciplina_id).exists()
  → Raises DisciplinaNoEnPaqueteError if discipline not in package
```

### 4.5 Key Risk: Frontend Forces Discipline IDs

**Current implementation is CORRECT — no hardcoded IDs.**

The frontend:
1. Fetches disciplines from `GET /inscripciones/paquetes/{id}/disciplinas/` — gets real UUIDs from DB
2. Presents these as options in SearchableSelect
3. Sends `disciplina_id` from that list in the payload
4. Backend validates that each `disciplina_id` exists in `PaqueteDisciplina` for the given package

**However, a risk exists if:**
- Frontend used a stale cached list of discipline IDs
- Frontend manually constructed discipline IDs without fetching from the package endpoint

**Current state: SAFE** — the frontend correctly uses `usePaqueteDisciplinas(paqueteId)` which triggers fresh fetches.

### 4.6 `cantidad_maxima_equipos` Derivation

**Backend presenter (`paquete_presenter.py`):**
```python
def calcular_cantidad_maxima_equipos(paquete: Paquete) -> int:
    if paquete.modo_disciplinas == ModoDisciplinasPaqueteChoices.FIJO:
        return PaqueteDisciplina.objects.filter(paquete=paquete).count()
    return paquete.cantidad_disciplinas_requeridas or 1
```

- **FIJO mode:** `cantidad_maxima_equipos` = count of disciplines linked to the package via `PaqueteDisciplina`
- **ELEGIBLE mode:** `cantidad_maxima_equipos` = `cantidad_disciplinas_requeridas` field

**Frontend usage:**
- `EquiposStepLayout` passes `paqueteActual.cantidad_maxima_equipos` to `SmartEquipoField`
- `SmartEquipoField` auto-creates exactly that many equipo slots
- User CANNOT add or remove equipo slots manually — this is by design (contract: no manual controls for FIJO packages)

---

## 5. Contract Compliance Analysis

### 5.1 Backend Architecture Contract (django-app-architecture-contract.md)

| Rule | Status | Notes |
|------|--------|-------|
| Controllers thin, delegate to orchestrator | ✅ | `InscripcionController.crear_inscripcion` builds equipos_data and calls orchestrator |
| Orchestrator async, delegates to flujo | ✅ | `InscripcionOrchestrator.crear_inscripcion_completa` delegates to `CrearInscripcionFlujo` |
| Flujo async with transaction.atomic | ✅ | `CrearInscripcionFlujo._crear_inscripcion_sync` wrapped in `@transaction.atomic()` |
| Core services sync, no transaction.atomic own | ✅ | `InscripcionService`, `EquipoService`, etc. are sync, no atomic |
| Domain exceptions for business errors | ✅ | `DisciplinaNoEnPaqueteError`, `CantidadDisciplinasInvalidaError`, etc. |
| Selectors for complex queries | ✅ | `InscripcionSelector.listar_disciplinas_de_paquete()` etc. |
| Presenters transform only, no DB access | ✅ | `InscripcionPresenter` is pure transformer |
| Schemas HTTP in presentation layer | ✅ | `InscripcionCreateIn`, `InscripcionOut` in `presentation/schemas/` |
| Internal DTOs in domain layer | ✅ | `InscripcionCreateData`, `EquipoCreateData` in `domain/schemas/` |

**Deviation:** `PromocionController` directly queries the ORM without using a selector or service:
```python
#直接在controller里query ORM，违反contract
promociones = Promocion.objects.filter(activa=True).order_by("-anio")
```
**Should use:** a selector or `PromocionService.listar_activas()`.

### 5.2 Frontend Architecture Contract (next-app-architecture-contract.md)

| Rule | Status | Notes |
|------|--------|-------|
| `app/` for routing only | ✅ | `app/(auth)/inscripcion/page.tsx` is thin, renders `InscripcionClientShell` |
| Business logic in `src/features/` | ✅ | `features/inscripciones/` contains all wizard logic |
| `GenericForm` owns validation/state | ✅ | `InscripcionWizard` wraps `GenericForm<InscripcionFormData>` |
| Features own layout/transform | ✅ | `SmartPaqueteCardsField`, `SmartEquipoField` own their layout |
| Smart fields adapt UI to RHF/Zod | ✅ | Both fields use `Controller` + `useFieldArray` |
| TanStack Query for server state | ✅ | `usePaquetes`, `usePaqueteDisciplinas`, etc. |
| No generic `z.any()` | ✅ | All schemas are strictly typed |

### 5.3 API Wrapper/Presenter Contract (api-wrapper-presenter-contract.md)

| Rule | Status | Notes |
|------|--------|-------|
| Typed module-specific wrappers | ✅ | `InscripcionOut`, `PaqueteOut`, etc. |
| Selector loads relations, presenter transforms only | ✅ | `InscripcionSelector` loads; `InscripcionPresenter` transforms |
| No `z.any()` or leaking unrelated fields | ✅ | All schemas are strictly typed |
| Frontend mirrors backend wrapper exactly | ✅ | `InscripcionBackendPayload` matches `InscripcionCreateIn` |

### 5.4 Smart Fields Contract (contract/smart.md)

| Rule | Status | Notes |
|------|--------|-------|
| Smart fields as adapters (not validators) | ✅ | Both fields delegate validation to Zod |
| `useController` for complex fields | ✅ | Both use `Controller` from react-hook-form |
| `hideErrorMessage` prop respected | ✅ | `SearchableSelect` accepts `hideErrorMessage` |
| `customFields` for domain-specific components | ✅ | `SmartPaqueteCardsField` and `SmartEquipoField` are custom |

---

## 6. Key Gaps and Risks

### Gap 1: `categoria_id` Always Null

**Location:** `toBackendPayload()` in `inscripcion.schema.ts`
```typescript
categoria_id: null,  // Always null!
```

**Issue:** Frontend never selects a category, but `Categoria` exists in the backend. For disciplines that have categories (e.g., age-based categories in sports), this is a missing UI feature.

**Backend accepts null:** `EquipoInscrito.categoria` is nullable, so this doesn't break anything.

**Recommendation:** If categories are needed, add category selection step per equipo in the wizard. If not needed for MVP, document as deferred feature.

### Gap 2: `PromocionController` Bypasses Service Layer

**Location:** `backend/modules/inscripciones/presentation/controllers/promocion_controller.py`

The controller directly queries `Promocion.objects.filter(...)` instead of using a selector or service.

**Contract violation:** Controllers should be thin and delegate to orchestrators/services.

**Impact:** Low — it's a simple read-only query with no business logic.

**Recommendation:** Create `PromocionService.listar_activas()` and use it, or use the selector. Not blocking for MVP.

### Gap 3: No Admin List Endpoint

**Location:** Missing `GET /inscripciones/admin/listar`

The frontend admin panel (if implemented) would need to list all inscriptions with enriched data. This endpoint doesn't exist.

**Impact:** Medium — only if admin UI is in scope for MVP.

**Recommendation:** Create `InscripcionAdminController` with `GET /inscripciones/admin/listar` if admin UI is needed.

### Gap 4: No Discipline Validation in `SmartPaqueteCardsField`

**Location:** `SmartPaqueteCardsField.tsx`

Each package card independently calls `usePaqueteDisciplinas(card.id)`. If the package has no disciplines configured, it shows "Sin disciplinas configuradas".

**Risk:** Low — this is handled gracefully with a skeleton loader and fallback text.

### Gap 5: `cantidad_maxima_participantes` Not Enforced in Wizard

**Location:** Frontend wizard

The package's `cantidad_maxima_participantes` limit is displayed in the card but NOT enforced in the UI (no validation preventing adding more participants than allowed).

**Backend enforcement:** `validar_cupo_paquete()` in `validators.py` checks total distinct persons in the inscription against package capacity. But this is only enforced at submit time.

**Recommendation:** Add participant count validation in `EquipoSchema` or in the `InscripcionFormSchema` to surface this error before submit.

---

## 7. Correction Plan

### 7.1 Frontend Corrections (UI + Flow)

| # | Correction | Priority | Files |
|---|-----------|---------|-------|
| F1 | Add participant count validation against `paquete.cantidad_maxima_participantes` at form-level (sum of all equipo participants) | Medium | `inscripcion.schema.ts`, `InscripcionWizard.tsx` |
| F2 | Add category selection UI per equipo when backend categories exist for the discipline | Low (deferred) | `SmartEquipoField.tsx` |
| F3 | Add loading skeleton for the equipo cards while disciplines are loading | Low | `SmartEquipoField.tsx` |
| F4 | Verify `EquiposStepLayout` handles `undefined` paquetes from query gracefully (currently finds by `paqueteId` but doesn't guard against undefined) | Medium | `InscripcionWizard.tsx` |

### 7.2 Backend Corrections

| # | Correction | Priority | Files |
|---|-----------|---------|-------|
| B1 | Create `PromocionService.listar_activas()` and use it in `PromocionController` instead of direct ORM query | Low | `domain/services/core/promocion_service.py` (new), `presentation/controllers/promocion_controller.py` |
| B2 | Add `GET /inscripciones/admin/listar` endpoint with pagination, filters by estado, and enriched data (equipos count, participantes count) | Medium (if admin in scope) | New controller or extend existing |
| B3 | Consider adding `modo_disciplinas` to `PaqueteOut` HTTP schema explicitly (currently only in `present_paquete()` dict but not in Ninja schema) | Low | `presentation/schemas/paquete_schemas.py` |

---

## 8. Findings Summary

### 8.1 Package-Discipline Relationship — VERIFIED SAFE

The package-discipline relationship is correctly implemented:
- **Storage:** `PaqueteDisciplina` through table with unique constraint
- **API:** `GET /inscripciones/paquetes/{id}/disciplinas/` returns disciplines per package
- **Frontend:** `usePaqueteDisciplinas(paqueteId)` fetches disciplines; `SearchableSelect` filtered to available disciplines only
- **Validation:** Backend validates each `disciplina_id` against `PaqueteDisciplina` before creating `EquipoInscrito`

**No hardcoded IDs. No forced relationships. The frontend correctly uses the API to get valid discipline IDs per package.**

### 8.2 `evento_id` Correctly Derived Server-Side

The frontend does NOT send `evento_id`. Backend derives it from `settings.EVENTO_ACTIVO_NOMBRE` in `CrearInscripcionFlujo._resolver_evento_activo()`.

### 8.3 Auto-Equipo Creation is Contract-Compliant

Per the `paquete_presenter.py` docstring:
> "FIJO: The frontend MUST create exactly `len(paquete.paquete_disciplinas)` teams and MUST NOT add manual controls."

The frontend implementation matches this: `SmartEquipoField` auto-creates equipo slots based on `cantidad_maxima_equipos` and provides NO UI to add/remove slots manually.

### 8.4 `categoria_id` Nullable but UI Not Implemented

Backend model allows null (confirmed at model level and in `EquipoCreateIn` schema). Frontend always sends `null`. This is correct for MVP but should be enhanced if categories are needed.

---

## 9. Exploration Artifacts

- **Report:** `explorer/inscripcion-flow-exploration.md`
- **Engram artifact:** `sdd/salesianos/inscripcion-flow-exploration` (type: architecture)

---

## 10. Next Steps

1. **F1 (Frontend):** Add participant count validation in Zod schema
2. **B1 (Backend):** Refactor `PromocionController` to use service layer
3. **B2 (Backend):** Create admin list endpoint if admin UI is in scope
4. **F4 (Frontend):** Guard against undefined `paquetes` in `EquiposStepLayout`
