# Exploration: pool-participant-crud

## Metadata

- **Change**: `pool-participant-crud`
- **Project**: `salesianos`
- **Artifact store**: engram
- **Topic key**: `sdd/pool-participant-crud/explore`
- **Date**: 2026-10-25
- **Mode**: read-only exploration (no code modified)
- **Contracts read before any code inspection**: all 7 files under `contract/`
  (`api-wrapper-presenter-contract.md`, `django-app-architecture-contract.md`,
  `next-app-architecture-contract.md`, `PLAN_REFACTORIZACION.md`,
  `SCHEMA_DRY_INTENTION.md`, `smart.md`, `TEST_ARCHITECTURE_CONTRACT.md`)
- **Prior artifacts read**: `sdd/pool-first-participant-registration-ux/explore` (#9125),
  `sdd/pool-first-participant-registration-ux/apply-progress` (#9132),
  `sdd/participacion-multidisciplina-por-inscripcion/ux-explore` (#9109),
  `sdd/participacion-multidisciplina-por-inscripcion/apply-progress` (#9118),
  `architecture/ux/team-participant-assignment` (#9108),
  `doc_dev/CONTRATO_POOL_PARTICIPANTES_PAGO_PREVIO.md` (§3.1, §4, §5, §8)

---

## Current State

### The lifecycle already exists — what is MISSING is the middle of the CRUD

| Step | Endpoint | Status |
|---|---|---|
| Create (preregistrar) | `POST /inscripciones/{id}/personas` (no `equipo_id`) | ✅ exists, pool-first, claims the paid cup FIFO |
| Read (pool) | `GET /inscripciones/{id}/pool` | ✅ exists (`PoolOut` → `PoolEntryOut[]`) |
| Read (assignable) | `GET /inscripciones/{id}/equipos/{equipo_id}/elegibles` | ✅ exists |
| **Update (person / preregistration)** | — | ❌ **NO ENDPOINT ANYWHERE** |
| **Update (team participation)** | `PATCH /participaciones/{id}` | ⚠️ exists but accepts only `rol`, `talla_camiseta`, `notas`, `estado` |
| Delete (remove from ONE discipline) | `PATCH /participaciones/{id}/retirar` | ✅ exists — keeps cup + other participations |
| Delete (remove from the inscription) | `PATCH /inscripciones/{id}/personas/{persona_id}/retirar` | ✅ exists — retires ALL participaciones + releases cup + FIFO realloc |
| Hard-delete `Persona` | — | ✅ correctly impossible (no `DELETE` route; `on_delete=PROTECT`) |

**The requested semantics are ALREADY the implemented semantics** of the two retire endpoints:

- `RetirarPersonaFlujo._retirar_atomico` (`backend/modules/salesianos_fest/domain/services/flujos/retirar_persona_flujo.py:40-105`) — retires every ACTIVA `Participacion` of the person in the inscription (L62-65), releases the `AsignacionCupo` to `LIBERADA` (L70-78), retires the `InscripcionPersona` (L80-82) and then re-runs the **FIFO allocator** `asignar_cupos_a_preregistrados` (L88-90). Covered by `test_pool_cupo_pagado_status_sync.py::test_retiro_devuelve_la_capacidad_y_la_reasigna_fifo` and `test_inscripcion.py::test_t20_retirar_persona_despues_de_fecha_limite_bloqueado`.
- `ParticipacionCoreService.retirer()` (`domain/services/core/participacion_service.py:170-172`) — retires ONE roster row, cup untouched, other disciplines untouched. Exactly "remove from one team/discipline keeps their cup and other participations".

⇒ **The gap is not the removal semantics — it is that none of it is reachable from the pool UI, and that the person/preregistration data cannot be edited at all.**

### Backend gaps (exact)

**B1 — There is NO endpoint to update a participant's person data.**
`Persona` (`backend/modules/usuarios/domain/models/persona.py`) owns every identity field: `nombres`, `apellidos`, `tipo_documento`, `numero_documento`, `genero`, `telefono`, `whatsapp`, `contacto_emergencia_nombre`, `contacto_emergencia_telefono`, `aseguradora_nombre`, `aseguradora_numero_poliza`.
The `usuarios` module exposes only `POST /auth/{username,dni,email}`, `GET /usuarios/me`, `GET /personas/busqueda/{documento}`, `POST /usuarios/register`, `GET /ingenieros/habilitados/{cip}` — **no `PATCH`/`PUT`/`DELETE` on `Persona` anywhere in the repo**.
Consequence: a typo in a name/phone/DNI entered at preregistration can never be corrected. The preregistration upsert (`AgregarPersonaFlujo._agregar_atomico`, `domain/services/flujos/agregar_persona_flujo.py:222-237`) **only CREATES** a `Persona` when `(tipo_documento, numero_documento)` is unknown; when it exists, the submitted `persona_data` is **silently ignored** (no update branch).

**B2 — The team edit endpoint silently discards the person-scoped fields the UI sends.**
`EditParticipanteModal.tsx:74-85` sends `rol`, `talla_camiseta`, `aseguradora_nombre`, `aseguradora_numero_poliza`, `notas` to `PATCH /participaciones/{id}`.
`ActualizarParticipacionIn` (`presentation/schemas/inscripcion_schemas.py:177-183`) declares only `rol`, `talla_camiseta`, `notas`, `estado`. `BaseSchema` (`backend/core/types.py`) does **not** set `extra="forbid"`, so pydantic's default `ignore` applies ⇒ **the two insurance fields are accepted, dropped, and the UI reports success.** Real silent data loss.

**B3 — The same loss happens at preregistration time.**
`AddParticipanteModal.tsx` collects `aseguradora_nombre`, `aseguradora_numero_poliza` (and the Zod schema has `notas`), but `buildPreregistroPayload` (`utils/pool.preregistro.ts:38-52`) sends only the 7 identity fields, and `PersonaInlineIn` (`presentation/schemas/inscripcion_schemas.py:117-132`) accepts only `tipo_documento`, `numero_documento`, `nombres`, `apellidos`, `genero`, `telefono`, `whatsapp`. ⇒ the insurance data typed at registration is discarded.

**B4 — The wrapper never exposes the person data the UI needs.**
`PersonaSummarySchema` (`presentation/schemas/inscripcion_schemas.py:15-22`) returns only `id`, `nombre`, `nombres`, `apellidos`, `numero_documento`. It is used by `PoolEntryOut`, `ElegibleOut`, `ParticipacionOut`, `InscripcionPersonaSummarySchema`, `InscripcionPersonaOut`. ⇒ `telefono`, `whatsapp`, `genero`, `aseguradora_*`, `contacto_emergencia_*` are **never returned to any client**, so the "Seguro Médico" section of the edit modal is permanently empty and its save is dropped (B2+B3+B4 = one lie, three layers).

**B5 — Two id spaces in the same feature, undocumented.**
The pool entry id is `InscripcionPersona.id` (`PoolEntryOut.id`); the retire route takes `persona_id` = **`Persona.id`** (`inscripcion_controller.py:299`); the participation routes take the `Participacion.id`. The pool card carries only the `InscripcionPersona.id`; `entry.persona.id` is available but the naming gives no hint. A new CRUD surface must pick one id and say so.

**B6 — Two divergent release paths.**
`POST /asignaciones/liberar` (`LiberarCupoFlujo`, `domain/services/flujos/liberar_cupo_flujo.py:84-148`) retires participaciones (optionally discipline-scoped) and releases the cup, but it does **NOT** retire the `InscripcionPersona` and does **NOT** re-run the FIFO allocator ⇒ the freed paid slot can sit idle while somebody waits in the pool, and the released person stays ACTIVE in the inscription without a right. `RetirarPersonaFlujo` does all of it. It has no frontend caller and is not in the contract doc §3.1.

**B7 — Deadline asymmetry.**
`RetirarPersonaFlujo` and `LiberarCupoFlujo` enforce `evento.puede_modificar()` → `FECHA_LIMITE_EXCEDIDA` (409). `ParticipacionCoreService.retirer()` and `PATCH /participaciones/{id}` do NOT check the deadline. So "remove from a team" is allowed after the deadline while "remove from the inscription" is not.

**B8 — Authorization is already uniform.** Every participant mutation uses `check_ownership_or_admin(request, inscripcion_id)` (owner of the inscription or `is_staff`/`is_superuser`), except `ParticipacionController._check_participacion_ownership` which does the same check inline (L464-493). `403 FORBIDDEN` for an unrelated user is already tested (`test_participacion_phase3_auth.py::test_retirar_persona_403_for_unrelated_user`).

### Frontend gaps (exact)

**F1 — The pool card has exactly one action: "Asignar".** `PoolParticipanteCard.tsx` renders the "Asignar" button or a lock. There is **no edit, no remove, no retire** on a pool participant. `PoolParticipantesSeccion.tsx` only wires `onAsignar`.

**F2 — The only edit modal is team-scoped.** `EditParticipanteModal.tsx` takes a `ParticipanteOut` (a roster row) and an `equipoLabel`; it edits `rol`/`talla_camiseta`/`notas` **plus a person-scoped "Seguro Médico" section that the backend drops** (B2).

**F3 — Removal uses `window.confirm()`.** `InscripcionDetailView.tsx:375-394` (`handleRemoveParticipante`) uses the native `confirm()`. The repo already ships the convention: `frontend/src/components/confirmationDialog/ConfirmationDialog.tsx` (GenericModal + destructive button), currently unused by this feature.

**F4 — Cache invalidation misses the eligible lists.** `useInscripcionCacheSync.invalidate()` invalidates `detalle` + `pool` + `saldo` only. The prefix key `["inscripcion-elegibles", inscripcionId]` (used by the selector, `useElegiblesEquipo`) is invalidated **only** in `usePreregistrarEnPool.ts:59`. ⇒ after an edit or a removal, a retired participant can still appear in the selector until the query goes stale.

**F5 — Duplicated, contradictory frontend type.** `inscripcion.service.ts` declares `export interface PersonaResumen` **twice** (L117-126 and L214-218). TypeScript merges them into one type that declares `aseguradora_nombre?`, `aseguradora_numero_poliza?`, `contacto_emergencia_*?` — fields the backend **never returns** — while the backend marks `nombres`/`apellidos` as `Optional[str] = None` and the frontend declares them required. Contract drift + a lie about the wire shape.

**F6 — No service/hook for the inscription-level removal.** `inscripcion.service.ts:353-363` `eliminarParticipante()` calls `PATCH /participaciones/{id}/retirar` (team-scoped, keeps the cup). Nothing calls the inscription-scoped retire. `inscripcion.service.ts:340` `editarParticipante()` has an unused `inscripcionId` parameter (pre-existing biome warning).

**F7 — Reusable pieces already available (no new UI system needed).** `AppFormModal` + `GenericForm`/`GenericInput` (manual mode, `smart.md` contract), `ModalShell`, `GenericModal` (full-screen on mobile, `ScrollArea` body, sticky footer), `ConfirmationDialog`, `dropdown-menu`, `Sheet`, `Badge`, `Tooltip`, `notify`/`getErrorMessage` from `@/errors`, TanStack Query v5 + `queryOptions`, `node --experimental-strip-types --test` as the frontend test runner.

### Stale artifact warning

`explorer/inscripcion-participante-patch-aseguradora-aceptaciones.md` describes a codebase that **no longer exists** (`modules/inscripciones`, `ParticipanteInscripcion`, `ParticipanteAccionFlujo`, `modules/inscripciones/presentation/schemas/...`, `PersonaAceptacion` in `usuarios`). The current module is `modules/salesianos_fest` with `InscripcionPersona`, `AceptacionInscripcion` (inscription-scoped) and no `PersonaAceptacion`. **Do not use it as a spec** — only its idea (extend the PATCH so the insurance data is actually persisted) survives.

---

## Affected Areas

### Backend — create
- `backend/modules/salesianos_fest/presentation/controllers/inscripcion_controller.py` — new participant routes (module-owned, `check_ownership_or_admin`).
- `backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py` — `ActualizarParticipanteIn` (person fields) + a dedicated participant-detail wrapper.
- `backend/modules/salesianos_fest/presentation/presenters/inscripcion_presenter.py` — `present_participante_detalle()` (pure transformer).
- `backend/modules/salesianos_fest/domain/results/inscripcion_results.py` — `ParticipanteDetalleResult`.
- `backend/modules/salesianos_fest/domain/services/flujos/editar_participante_flujo.py` — NEW flujo (`transaction.atomic`, deadline check, ownership upstream).
- `backend/modules/salesianos_fest/domain/services/orchestrators/inscripcion_orchestrator.py` — thin async facade for the new flujo.
- `backend/modules/usuarios/domain/services/core/persona_core_service.py` — NEW `actualizar_datos()` (the `usuarios` module must own the `Persona` write; `salesianos_fest` must not write the `Persona` table directly for updates — it already does for creates, `agregar_persona_flujo.py:6,229-237`).
- `backend/modules/usuarios/domain/services/flujos/…` — only if a usuarios-side flujo is preferred over the core service.
- `backend/modules/salesianos_fest/domain/exceptions.py` — new stable codes (e.g. `PARTICIPANTE_NO_ENCONTRADO`, `DOCUMENTO_NO_EDITABLE`).
- `backend/core/exceptions.py` — public Spanish messages + status mapping (`api-wrapper-presenter-contract.md` §8).
- `backend/modules/salesianos_fest/domain/services/core/participacion_service.py` — `retirer()`: optional deadline check + explicit "cup survives" documentation.

### Backend — modify
- `backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py` — `PersonaInlineIn` (accept `aseguradora_*`, `contacto_emergencia_*`) so the preregistration stops losing them; `ActualizarParticipacionIn` (drop the person-scoped intent, keep participation-only).
- `backend/modules/salesianos_fest/domain/services/flujos/agregar_persona_flujo.py` — the `persona_data` branch only CREATEs; decide whether a re-registration with the same document may update (recommend: no, keep the upsert create-only and let the new PATCH own corrections).
- `backend/modules/salesianos_fest/domain/services/flujos/liberar_cupo_flujo.py` — divergence B6 (no FIFO realloc, no `InscripcionPersona` retirement): either delegate to the retirement semantics or document it as a discipline-scoped-only API.
- `backend/modules/salesianos_fest/domain/selectors/inscripcion_selector.py` — a participant-detail selector (person + cup state + participations) if the read is served by the backend.

### Frontend — create
- `frontend/src/features/inscripciones/services/participante.service.ts` — `getParticipanteDetalle`, `editarParticipante` (person data), `retirarParticipanteDeInscripcion`; types mirroring the backend wrappers 1:1 (`api-wrapper-presenter-contract.md` §7, no `z.any()`).
- `frontend/src/features/inscripciones/hooks/useParticipanteDetalle.ts` — query hook (`queryOptions`, prefix key).
- `frontend/src/features/inscripciones/hooks/useEditarParticipanteDatos.ts` — mutation (optimistic + rollback + invalidation incl. the eligible-lists prefix).
- `frontend/src/features/inscripciones/hooks/useRetirarParticipante.ts` — mutation (invalidates detalle + pool + saldo + elegibles).
- `frontend/src/features/inscripciones/components/EditarParticipantePoolModal.tsx` — NEW `AppFormModal` + `GenericInput` (Mode 1) for the person/preregistration fields.
- `frontend/src/features/inscripciones/schemas/participantePersona.schema.ts` — Zod schema for the person edit (reuse the doc/phone regexes of `participante.schema.ts`).
- `frontend/src/features/inscripciones/utils/participante.acciones.ts` (+ `.test.ts`) — pure mapping of the pool entry → available actions, so the card and the modal share one vocabulary.

### Frontend — modify
- `frontend/src/features/inscripciones/components/PoolParticipanteCard.tsx` — add the overflow menu (Edit / Remove) using `dropdown-menu`; keep "Asignar" as the visible primary action; icon-only on mobile.
- `frontend/src/features/inscripciones/components/PoolParticipantesSeccion.tsx` — wire the new actions.
- `frontend/src/features/inscripciones/components/EditParticipanteModal.tsx` — **remove the "Seguro Médico" section** (person-scoped, currently a no-op) and keep only rol/talla/notas; adjust the footer hint.
- `frontend/src/features/inscripciones/components/AddParticipanteModal.tsx` — keep the insurance fields only if the preregistration payload starts carrying them; otherwise remove the fields (today they are collected and discarded).
- `frontend/src/features/inscripciones/views/InscripcionDetailView.tsx` — replace `window.confirm()` with `ConfirmationDialog`; wire the pool edit/remove actions.
- `frontend/src/features/inscripciones/hooks/useInscripcionCacheSync.ts` — `invalidate()` must also invalidate the prefix key `["inscripcion-elegibles", inscripcionId]`.
- `frontend/src/features/inscripciones/services/inscripcion.service.ts` — merge the duplicated `PersonaResumen`; align the fields with the backend wrapper; drop the unused `inscripcionId` param.
- `frontend/src/features/inscripciones/hooks/useEditarParticipante.ts` — invalidate the eligible lists too.

### Docs & tests
- `doc_dev/CONTRATO_POOL_PARTICIPANTES_PAGO_PREVIO.md` — §3.1 (endpoint table: add the participant CRUD + document the id semantics), §4 (permission matrix), §5 (new error codes), §6 (final flow), §8 (frontend contract), new §15 (the CRUD change).
- `backend/modules/salesianos_fest/tests/integration/test_pool_participant_crud.py` — NEW (pure-dict factories in `tests/factories.py`, `integration/` folder, no `unittest.mock.patch`, no `unit/`).
- `backend/modules/salesianos_fest/tests/factories.py` — payload builders for the new schemas.
- `frontend/src/features/inscripciones/utils/participante.acciones.test.ts` — pure-mapping tests.

---

## Approaches

### Option A — ONE participant resource under `/inscripciones/{id}/participantes/{participante_id}` (RECOMMENDED)

Introduce the **participant** (`InscripcionPersona` = person + preregistration) as a first-class resource of the inscription module, distinct from the **participation** (`Participacion` = roster row):

- `GET /inscripciones/{id}/participantes/{participante_id}` → `ParticipanteDetalleOut` (person data + cup state + participations)
- `PATCH /inscripciones/{id}/participantes/{participante_id}` → `ActualizarParticipanteIn` → `ParticipanteDetalleOut`
- Removals reuse the existing endpoints: `PATCH /participaciones/{id}/retirar` (one discipline) and `PATCH /inscripciones/{id}/personas/{persona_id}/retirar` (the whole inscription)
- The `Persona` write goes through `usuarios`' `PersonaCoreService.actualizar_datos()` (module ownership of the model); `salesianos_fest` never writes the `Persona` table directly for updates
- The document (`tipo_documento`/`numero_documento`) is **not editable** in this change (it is the global identity and the uniqueness key)
- The "Seguro Médico" section moves from `EditParticipanteModal` (team) to the new participant modal (person) — and the preregistration payload starts carrying it

- Pros: makes the product's own distinction ("person/preregistration edits" vs "team participation edits") literal in the URL space; one owner per field family; no route conflict with the existing `/personas/{persona_id}/retirar` (different path segment, different id semantics); the removal semantics stay exactly as implemented and tested; no migration; the wrapper contract is respected with a dedicated wrapper; the frontend gets one coherent participant card/modal; fixes the three silent-loss layers.
- Cons: adds 2 endpoints + 1 wrapper family; `Persona` is a GLOBAL record shared across inscriptions, so editing it in inscription A is visible in inscription B (product decision, see Risks); the two id spaces (`participante_id` vs `persona_id` on the legacy retire route) must be documented carefully; the frontend type cleanup surfaces pre-existing drift.
- Effort: Medium.

### Option B — Extend the existing `/participaciones/{id}` PATCH with the person fields

Add `aseguradora_*` / `contacto_emergencia_*` to `ActualizarParticipacionIn` and update the `Persona` inside the participation flow (the idea in the stale explorer doc).

- Pros: smallest backend diff; reuses the existing modal and hook; immediately makes the "Seguro Médico" section truthful.
- Cons: **violates the product intent** — it keeps person data inside a team-participation endpoint, so the same person in two disciplines has two "person editors" writing the same global record (last write wins, no way to tell which team owns the value); it still leaves **no way to edit a pool participant that has no team yet** (the CRUD the change is about); it silently widens a roster-row endpoint into a cross-module `Persona` write; the `Persona` update happens on a roster-row transaction, coupling two aggregates.
- Effort: Low.

### Option C — Participant-scoped copy of the person data on `InscripcionPersona` (new fields + migration)

Add `nombres`, `apellidos`, `telefono`, `whatsapp`, `aseguradora_*`, `contacto_emergencia_*` to `InscripcionPersona` so each inscription keeps its own copy of the participant's data; the global `Persona` stays the master identity.

- Pros: no cross-module write at all; per-inscription data (a different phone number per inscription is possible); the removal semantics become trivially "the copy is retired with the inscription".
- Cons: **migration**; duplicated data with a drift problem and no single source of truth; the master `Persona` would still hold stale copies; the preregistration upsert would need to reconcile two copies; a much bigger review surface; the previous three changes deliberately avoided migrations.
- Effort: High.

### Option D — Frontend-only CRUD (use what already exists)

Wire the existing endpoints in the UI: pool card → "Quitar de la inscripción" (`PATCH /inscripciones/{id}/personas/{persona_id}/retirar`) and team card → existing edit modal; add no backend endpoint and accept that person data cannot be corrected.

- Pros: smallest possible change; delivers the removal half of the intent immediately; zero contract risk; no new wrappers.
- Cons: **cannot deliver "CRUD"** — the update of the preregistration/person data stays impossible (B1/B2/B3/B4); the "Seguro Médico" section stays a lie; the id ambiguity (`persona_id` vs `participante_id`) is pushed onto the frontend with no documentation.
- Effort: Low.

---

## Recommendation

**Option A**, executed in this order:

1. **Backend — the participant resource.**
   - New route family under the inscription module: `GET` + `PATCH /inscripciones/{id}/participantes/{participante_id}`.
   - `PATCH` body = `ActualizarParticipanteIn` with the **person** fields only: `nombres`, `apellidos`, `genero`, `telefono`, `whatsapp`, `aseguradora_nombre`, `aseguradora_numero_poliza`, `contacto_emergencia_nombre`, `contacto_emergencia_telefono`. The **document is not editable** (global identity + uniqueness key).
   - Chain per the Django contract: controller (thin) → `InscripcionOrchestrator` (thin async) → `EditarParticipanteFlujo` (async, `transaction.atomic`, deadline check) → `PersonaCoreService.actualizar_datos()` (in `usuarios`, the owner of the model) + `InscripcionSelector` for the read.
   - Authorization: `check_ownership_or_admin(request, inscripcion_id)` — owner or Django admin (identical to every other participant mutation; 403 for anyone else).
   - Response: a dedicated `ParticipanteDetalleOut` (explicit named wrapper, no `data`/`contexto` envelope) that the frontend mirrors 1:1. `PersonaSummarySchema` stays untouched (it is the minimal summary used by the list wrappers).
2. **Backend — stop losing the person data.**
   - `PersonaInlineIn` accepts `aseguradora_*` and `contacto_emergencia_*` so the preregistration persists what the form collects (or the form stops collecting them — one of the two, not both).
   - `ActualizarParticipacionIn` keeps **participation-only** fields (`rol`, `talla_camiseta`, `notas`, `estado`). The person-scoped fields leave the participation endpoint entirely.
3. **Backend — keep the removal semantics, make them reachable and unambiguous.**
   - `PATCH /participaciones/{id}/retirar` = "quitar de esta disciplina" (cup and other participations survive).
   - `PATCH /inscripciones/{id}/personas/{persona_id}/retirar` = "quitar de la inscripción" (all participaciones retired, cup released, FIFO reallocation triggered) — **already implemented**; it keeps `persona_id` because a sibling route with the same shape and a different id would be ambiguous for the router.
   - **No hard delete of `Persona`** — state it in the contract doc; `on_delete=PROTECT` already guarantees it.
   - Align B6: either make `POST /asignaciones/liberar` delegate to the same retirement semantics (FIFO realloc included) or explicitly document it as a discipline-scoped API that does NOT reallocate. It has no frontend caller.
   - Align B7: apply the deadline check to the participation retire/edit too, or explicitly document that team-level changes remain allowed after the deadline.
4. **Frontend — participant card + two edit surfaces.**
   - Pool card: keep "Asignar" as the visible action and add an overflow `dropdown-menu` with **"Editar datos"** and **"Quitar de la inscripción"**; the menu is icon-only on mobile.
   - NEW `EditarParticipantePoolModal` (`AppFormModal` + `GenericInput`, manual mode) for the person/preregistration fields; the remove action uses the existing `ConfirmationDialog` with `variant="danger"` and copy that states the consequences (all participaciones retired, cupo released, the freed cupo goes to the next person in the pool).
   - `EditParticipanteModal` (team) keeps rol/talla/notas and **loses the "Seguro Médico" section** — it moves to the participant modal.
   - `InscripcionDetailView` replaces `window.confirm()` with `ConfirmationDialog`.
   - Cache: every participant mutation invalidates `detalle` + `pool` + `saldo` + **the eligible-lists prefix** `["inscripcion-elegibles", inscripcionId]` (fix F4 — a retired participant must vanish from the selector immediately).
   - Types: merge the duplicated `PersonaResumen`, align it with the backend wrapper, and add the new participant-detail types 1:1.
5. **Tests + docs.**
   - New `test_pool_participant_crud.py` in `tests/integration/` with pure-dict factories: edit persists; edit touches no roster row; 403 for an unrelated user; the document is not editable; removal from one discipline keeps the cup and the other participations; removal from the inscription retires every participacion, releases the cup and re-allocates FIFO; the `Persona` still exists after the removal; the preregistration persists the insurance data.
   - Update `doc_dev/CONTRATO_POOL_PARTICIPANTES_PAGO_PREVIO.md` §3.1 (new routes + the id semantics table), §4, §5 (new codes), §6, §8, and a new §15.

**Why A over B/D:** the change is literally about separating two edit surfaces that today are conflated (and silently broken). Option B fixes the symptom of the conflation by deepening it; Option D leaves the update half of the CRUD unimplementable. Option C buys per-inscription isolation with a migration and a duplicated source of truth — not worth it while `Persona` is the only identity store.

---

## Risks

- **`Persona` is global and shared across inscriptions.** Editing a participant's name/phone/insurance in inscription A changes what inscription B shows. Mitigation: keep the editable field set to the participant-scoped data actually needed at the venue (insurance, emergency contact, phone) and treat names/document as global identity; document the rule in the contract doc. **This is the one product decision the orchestrator must confirm.**
- **The document cannot be edited** under Option A, and a wrong DNI at preregistration is a plausible real case. Mitigation: if the user insists, allow the document edit ONLY when the `Persona` has no other `InscripcionPersona`/participation, and enforce the `(tipo_documento, numero_documento)` uniqueness (409 `DOCUMENTO_YA_EXISTE`) — a scoped, explicit exception rather than a general one.
- **Cross-module write.** `salesianos_fest` updating `usuarios.Persona` touches the boundary of `api-wrapper-presenter-contract.md` §1/§6. Mitigation: the write goes through `usuarios`' `PersonaCoreService` (the `usuarios` module keeps ownership of the model); `salesianos_fest` must not import `usuarios` presenters or schemas. Note the precedent: the preregistration already creates `Persona` rows directly (`agregar_persona_flujo.py:6,229-237`) — that create-path coupling is pre-existing and out of scope, but the new update path must not repeat it.
- **The FIFO reallocation is a visible side effect.** Removing a participant immediately hands their cupo to the next preregistration in the pool ⇒ the pool, the saldo chips and the "Cupo por asignar" callout all change. Mitigation: the confirmation dialog must state it, and pool + saldo + detail must be invalidated together (they are three separate queries today).
- **Route/id ambiguity.** `PATCH /inscripciones/{id}/personas/{persona_id}/retirar` (Persona id) coexisting with `PATCH /inscripciones/{id}/participantes/{participante_id}` (InscripcionPersona id) is a foot-gun. Mitigation: name the frontend params `personaId` vs `participanteId`, document both in the contract doc, and add the `participantes` resource to the doc's endpoint table with an explicit "id" column.
- **Deadline semantics.** If the edit/remove is blocked by `FECHA_LIMITE_EXCEDIDA` the UI must show the backend message honestly; the current asymmetry (team-level changes allowed after the deadline, inscription-level not) may surprise the committee at the venue.
- **`LiberarCupoFlujo` divergence (B6)** — if it stays as is, two "release" APIs mean different things and one of them silently does not reallocate. Mitigation: unify or document in the same change; it has no frontend caller, so unification is cheap.
- **Frontend type cleanup (F5)** — merging the duplicated `PersonaResumen` will surface real type errors where the code assumed `nombres`/`apellidos` are always present (the backend marks them optional). Expect a small follow-up inside the same change.
- **Contract drift.** `doc_dev/CONTRATO_POOL_PARTICIPANTES_PAGO_PREVIO.md` §3.1/§4/§5 must be updated in the same change, and `explorer/inscripcion-participante-patch-aseguradora-aceptaciones.md` must be marked obsolete (it describes a codebase that no longer exists).
- **Pre-existing failures (not caused by this change):** `test_cotizacion.py::test_obtener_precio_vigente_respeta_fechas_no_fallback` (UTC vs local date) and `modules/usuarios/tests/integration/test_persona_busqueda.py::test_busqueda_endpoint_devuelve_forma_contractual` (envelope shape). Both documented in the prior apply-progress artifacts.
- **No migration** is needed under Option A — the previous three changes deliberately avoided them and this one should too.

---

## Ready for Proposal

**Yes.** The exploration proves that the *removal* semantics the change asks for already exist and are correct (`RetirarPersonaFlujo` = retire all participations + release the cup + FIFO reallocation; `ParticipacionCoreService.retirer()` = leave one discipline keeping the cup and the other participations), and that `Persona` can never be hard-deleted (`PROTECT` + no `DELETE` routes). The real gaps are: **(a)** no way to edit the person/preregistration data at all, in any layer; **(b)** the person-scoped data that the UI collects (insurance) is silently dropped at three layers (schema, payload, wrapper); **(c)** none of the removal operations are reachable from the pool UI; and **(d)** the frontend type mirror for `Persona` is duplicated and contradicts the backend wrapper.

The orchestrator should ask the user for exactly **one** decision before writing the proposal:

> **How wide is the "person" edit?**
> (a) **Participant-scoped only** (RECOMMENDED): names, phone, WhatsApp, insurance and emergency contact may be corrected; the document (DNI/CE/PAS) is NOT editable, because it is the global identity and the uniqueness key of a `Persona` shared across inscriptions.
> (b) **Document included**: the document may be corrected too, but only when the `Persona` has no other inscription or participation (otherwise 409) — a scoped exception with a uniqueness check.
>
> (A secondary question, only if the user wants a single release API: should `POST /asignaciones/liberar` be unified with the inscription-level retirement so that every cup release also re-allocates FIFO, or documented as a discipline-scoped API that does not?)
