# Salesianos FEST Rebuild Packet State

Initial state: all packets are `pending`. Apply agents update this board and persist the same transition to `sdd/salesianos-fest-rebuild/state`.

| Packet | Status | Dependencies | Owner | Last evidence |
|---|---|---|---|---|
| GOV-00 | completed | none | A0 + product | `evidence/checkpoint/GOV-00-checkpoint-summary.md` · apply-progress #11227 |
| GOV-01 | completed | GOV-00 | A0 | `evidence/contracts/GOV-01-contract-freeze-summary.md` · apply-progress #11229 |
| GOV-02 | completed | GOV-01 | A0 + A7 + A9 | `evidence/routes/GOV-02-route-brief-index.md` · `evidence/baseline/BL-01-baseline-summary.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/apply-progress`) |
| FND-01 | completed | GOV-01,GOV-02 | A0 | `evidence/foundations/FND-01-backend-shared-api-media.md` · `evidence/foundations/FND-01-a0-reconciliation.md` (A0 reconciliation of FND-02/03/04) · `evidence/foundations/FND-01-a0-reconciliation-dom01-dom04.md` (A0 reconciliation of DOM-01/DOM-04) · apply-progress (topic `sdd/salesianos-fest-rebuild/apply-progress`) |
| FND-02 | completed | GOV-01,FND-01 | A1 | `evidence/foundations/FND-02-event-edition-scope.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/apply-progress`) |
| FND-03 | completed | GOV-01,FND-01 | A1 | `evidence/foundations/FND-03-identity-reniec.md` · `Aplicacion/backend/modules/usuarios/**` (35 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/fnd-03-apply-progress`) |
| FND-04 | completed | GOV-01,FND-01 | A2 | `evidence/foundations/FND-04-commerce-payments.md` · `Aplicacion/backend/modules/commerce/**` + `Aplicacion/backend/modules/pagos/**` (79 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/fnd-04-apply-progress`) |
| FND-05 | completed | FND-04 | A0 | `evidence/foundations/FND-05-rights-activation.md` · `Aplicacion/backend/modules/commerce/**` + `modules/pagos/**` (96 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/fnd-05-apply-progress`) |
| FND-06 | verification_required | GOV-02 | A0 + A7 | `evidence/fnd-06-frontend-shell.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/fnd-06-implementation-progress` #11303) — implementation pass applied (26 files in `Aplicacion/frontend/**`); the ONLY runtime command was `npx tsc --noEmit` exit **0** — Vitest / Biome / `next build` / HTTP probe / five-width browser audit **NOT RUN**; 4 tests WRITTEN, NOT EXECUTED |
| FND-07 | verification_required | FND-06 | A0 + A7 | `evidence/foundations/FND-07-forms-lifecycle-errors-payloads.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/apply-progress`) — implementation pass applied (12 creados + 9 modificados en `Aplicacion/frontend/**`); el ÚNICO comando de runtime fue `npx tsc --noEmit` exit **0** — Vitest / Biome / `next build` / navegador NOT RUN; 4 suites ESCRITAS, NO EJECUTADAS |
| FND-08 | verification_required | FND-06,FND-07 | A0 + A7 | `evidence/foundations/FND-08-query-cache-consolidation.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/apply-progress`) — implementation pass applied (13 ficheros modificados + 8 creados + 1 eliminado en `Aplicacion/frontend/**`); el ÚNICO comando de runtime fue `npx tsc --noEmit` exit **0** — Vitest / Biome / `next build` NOT RUN; 6 suites ESCRITAS, NO EJECUTADAS |
| DOM-01 | completed | FND-02,FND-03,FND-04 | A3 | `evidence/domains/DOM-01-inscripcion-catalogo-compra.md` · `Aplicacion/backend/modules/salesianos_fest/**` (45 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-01-apply-progress`) |
| DOM-02 | completed | DOM-01,FND-05 | A3 | `evidence/domains/DOM-02-pool-asignacion-ampliacion.md` · `Aplicacion/backend/modules/salesianos_fest/**` (102 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-02-apply-progress`) |
| DOM-03 | completed | FND-02,FND-03,FND-04,FND-05 | A4 | `evidence/domains/DOM-03-passes-beneficios-cortesia.md` · `evidence/foundations/A0-reconciliation-dom03.md` · `evidence/domains/DOM-03-05-07-08-runtime-verification.md` (runtime closure) · `Aplicacion/backend/modules/salesianos_fest/**` (**164 tests, all pass** — 59 cases of DOM-03 + the rest of the module) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-03-apply-progress` #11318) |
| DOM-04 | completed | FND-02,FND-01 | A5 | `evidence/domains/DOM-04-marketplace-catalog-media.md` · `Aplicacion/backend/modules/marketplace/**` (35 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-04-apply-progress`) |
| DOM-05 | completed | DOM-04,FND-04 | A5 | `evidence/domains/DOM-05-marketplace-order.md` · `evidence/domains/DOM-03-05-07-08-runtime-verification.md` (runtime closure) · `Aplicacion/backend/modules/marketplace/**` (**97 tests, all pass** — 34 cases of DOM-05) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-05-apply-progress` #11298) · **A0 wiring NOT applied (2026-11-19, re-proved): `PedidoController` NOT registered → its 2 routes DO NOT EXIST** (`A0-RTV-02`) · `evidence/foundations/A0-wiring-validation.md` |
| DOM-06 | completed | DOM-04,DOM-05,FND-05 | A5 | `evidence/domains/DOM-06-inventory-reservation-delivery.md` · `Aplicacion/backend/modules/marketplace/**` (97 tests, all pass: 69 of DOM-04/DOM-05 + 28 new — runtime verified with `uv run`) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-06-apply-progress` #11361 · facts #11362) · **A0 wiring NOT applied (2026-11-19, re-proved): `InventarioController` NOT registered → its 5 routes DO NOT EXIST** (`A0-RTV-02`) · `evidence/foundations/A0-wiring-validation.md` |
| DOM-07 | completed | FND-02,DOM-02 | A6 | `evidence/domains/DOM-07-competitions.md` · `evidence/domains/DOM-03-05-07-08-runtime-verification.md` (runtime closure) · `Aplicacion/backend/modules/competencias/**` (**55 cases, all pass** — 43 functions) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-07-apply-progress` #11340) · **A0 wiring NOT applied (2026-11-19, re-proved): `modules.competencias` NOT in `INSTALLED_APPS` and `CompetenciasController` NOT registered → its 16 routes DO NOT EXIST** (`A0-RTV-01`/`A0-RTV-02`) · `evidence/foundations/A0-wiring-validation.md` |
| DOM-08 | completed | FND-02,FND-01 | A8 | `evidence/domains/DOM-08-patrocinadores-logo-galeria.md` · `evidence/domains/DOM-03-05-07-08-runtime-verification.md` (runtime closure) · `Aplicacion/backend/modules/patrocinadores/**` (**53 tests, all pass**) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-08-apply-progress` #11347) · **A0 wiring NOT applied (2026-11-19, re-proved): `modules.patrocinadores` NOT in `INSTALLED_APPS` and `PatrocinadorController` NOT registered → its 1 route DOES NOT EXIST** (`A0-RTV-01`/`A0-RTV-02`) · `evidence/foundations/A0-wiring-validation.md` |
| UI-01 | verification_required | GOV-02,FND-06,FND-07 | A7 | `evidence/ui/UI-01-public-account-shells.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/ui-01-apply-progress`) — implementation pass applied (34 files created + 2 modified in `Aplicacion/frontend/**`); the ONLY runtime command was `npx tsc --noEmit` exit **0** — Vitest / Biome / `next build` / five-width browser audit NOT RUN; 4 suites WRITTEN, NOT EXECUTED; the corrective sub-batch **UI-01A** stays completed (row below); `PUB-01` / `AUTH-01` / `AUTH-02` were left OUT of the allowed edit roots (evidence §10) |
| UI-01A | completed | FND-06 | A7 | apply-progress (topic `sdd/salesianos-fest-rebuild/ui-01a-apply-progress` #11256) · bugfix #11257 — corrective sub-batch of UI-01; the five-width browser audit stays OPEN |
| UI-02 | verification_required | GOV-02,FND-06,FND-07 | A7 | `evidence/ui/UI-02-inscription-shells.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/ui-02-apply-progress`) - implementation pass applied (18 created + 9 rewritten in `Aplicacion/frontend/**`); the ONLY runtime command was `npx tsc --noEmit`: the roots of THIS packet were GREEN (0 errors) in EVERY run and the project-wide gate was RED only because of CONCURRENT out-of-scope trees (`features/pases/**`, then `features/marketplace/**`); after UI-03 completed and repaired its own errors the final global `npx tsc --noEmit` exited 0; 3 suites WRITTEN, NOT EXECUTED; the five-width browser audit NOT RUN |
| UI-03 | verification_required | GOV-02,FND-06,FND-07 | A7 | `evidence/ui/UI-03-commerce-shells.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/ui-03-apply-progress`) — implementation pass applied (32 files created + 5 route files modified in `Aplicacion/frontend/**`); the ONLY runtime command was `npx tsc --noEmit` exit **0** — Vitest / Biome / `next build` / navegador de cinco anchos **NOT RUN**; 2 suites WRITTEN, NOT EXECUTED; `PedidoController` / `InventarioController` NOT bound (no registrados) |
| UI-04 | verification_required | GOV-02,FND-06,FND-07 | A7 | `evidence/ui/UI-04-admin-operations-shells.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/ui-04-apply-progress`) — implementation pass applied (48 created + 6 route files modified in `Aplicacion/frontend/**`); the ONLY runtime command was `npx tsc --noEmit` exit **0** — Vitest / Biome / `next build` / five-width browser audit **NOT RUN**; 5 suites WRITTEN, NOT EXECUTED; **NONE** of the administrative routes (`RT-IN-07…11`, `RT-PG-04…07`, `RT-ID-07/08`) is registered in `Aplicacion/backend/config/api.py` ⇒ the six routes keep their HONEST state |
| UI-05 | verification_required | GOV-02,FND-06,FND-07 | A7 | `evidence/ui/UI-05-competition-validation-shells.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/ui-05-apply-progress`) — implementation pass applied (47 created + 8 route files modified in `Aplicacion/frontend/**`; 3 NEW features: `features/competencias/**`, `features/validaciones/**`, `features/patrocinadores/**`); the ONLY runtime command was `npx tsc --noEmit` — **0 errors in the roots of this packet in EVERY run**; the last project-wide run was RED only because of the CONCURRENT out-of-scope tree of UI-04 (`features/admin/**`), which was NOT touched, not reverted and not merged — **the LAST recorded project-wide run is UI-04's `V4`, exit 0 ⇒ the GLOBAL GATE is GREEN**; 3 suites WRITTEN, NOT EXECUTED; the five-width browser audit NOT RUN; `CompetenciasController` / `PatrocinadorController` / `InventarioController` NOT registered and the `validaciones` module DOES NOT EXIST ⇒ the routes keep their HONEST state (A0 requests `A0-UI05-01`…`08`; `A0-UI05-08` = the ownership of `ADM-15/17/18/19` is UNATTRIBUTED: FND-06's root, disclaimed by UI-04, untouched by UI-05, produced by the non-SDD `general` agent of #11314) |
| API-01 | verification_required | UI-01,FND-02,FND-03,FND-08 | A7 | `evidence/api/API-01-public-account-integration.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/api-01-apply-progress`) — implementation pass applied (16 created + 12 modified + 3 deleted in `Aplicacion/frontend/**`); the ONLY runtime command was `npx tsc --noEmit` and it reported **0 errors in the roots of this packet** in EVERY run (the project-wide gate was GREEN in one run and RED in the others ONLY because of CONCURRENT out-of-scope trees: `features/inscripciones/**` of API-02 and `features/pases/**` + `features/marketplace/**` of API-03); 2 suites WRITTEN, NOT EXECUTED; the five-width browser audit NOT RUN; the edition/identity/session datasets are BOUND to registered routes, but `RT-ID-04/05/06`, `RT-RC-01` and the account registration have NO registered route ⇒ the account area and the recovery keep their honest state (A0 requests `A0-API01-01…03`) |
| API-02 | verification_required | UI-02,DOM-01,DOM-02,FND-08 | A7 | `evidence/api/API-02-inscription-integration.md` - apply-progress (topic `sdd/salesianos-fest-rebuild/api-02-apply-progress`) - implementation pass applied (17 created + 17 modified + 7 deleted in `Aplicacion/frontend/src/features/inscripciones/**`); the ONLY runtime command was `npx tsc --noEmit` - **0 errors in the roots of this packet in EVERY run** (V1 to V4): the two RED runs (V2, V3) were caused ONLY by CONCURRENT out-of-scope trees of `features/pases/**` and `features/marketplace/views/**` (API-03), which were NOT touched, reverted or merged and whose owners repaired them; the packet's own V4 was already exit **0**, and the **LAST recorded project-wide run** (API-03's final verification, exit **0**) leaves the **global gate GREEN**; 6 suites WRITTEN, NOT EXECUTED; the five-width browser audit NOT RUN; `RT-IN-02/03/05/06/12/13/14` and `RT-CM-01` are BOUND to REGISTERED routes, while `RT-IN-01` (list of the inscriptions), the listing of the purchases and the granted benefits have NO route, so those surfaces keep their HONEST empty state (A0 requests `A0-API02-01`...`03`) |
| API-03 | verification_required | UI-03,DOM-03..DOM-06,FND-08 | A7 | `evidence/api/API-03-commercial-integration.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/api-03-apply-progress`) — implementation pass applied (25 creados + 21 modificados + 2 fixtures eliminados en `Aplicacion/frontend/**`); the ONLY runtime command was `npx tsc --noEmit` exit **0** (after fixing 1 own error) — Vitest / Biome / `next build` / navegador / five-width audit NOT RUN; 4 suites WRITTEN, NOT EXECUTED; `PedidoController` / `InventarioController` NOT bound (no registrados) |
| API-04 | verification_required | UI-04,DOM-01,DOM-02,FND-04,FND-08 | A7 | `evidence/api/API-04-admin-operations-integration.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/api-04-apply-progress`) — implementation pass applied (30 created + 26 modified + **4 provisional fixtures DELETED** in `Aplicacion/frontend/src/features/admin/**`); the ONLY runtime command was `npx tsc --noEmit` exit **0** (V3/V4) ⇒ **the GLOBAL GATE is GREEN**; Vitest / Biome / `next build` / five-width browser audit **NOT RUN**; **5 suites WRITTEN, NOT EXECUTED**; **ZERO routes BOUND**: `AdminInscripcionController`/`AdminEquipoController`/`AdminParticipanteController`/`AdminPagoController`/`AdminPersonaController` are **NOT registered** in `Aplicacion/backend/config/api.py` ⇒ the six routes keep their HONEST state; the four Zod mirrors are a **seam, not a binding**, and a **guard** in the ONE service of the area makes it **impossible** to emit a request to an unregistered route (A0 requests `A0-API04-01`…`08`) |
| API-05 | verification_required | UI-05,DOM-03,DOM-07,DOM-08,FND-08 | A0 + A7 | `evidence/api/API-05-competition-admin-integration.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/api-05-apply-progress`) — implementation pass applied (10 creados + 11 modificados + 3 fixtures provisionales ELIMINADOS en `Aplicacion/frontend/src/features/{competencias,validaciones,patrocinadores}/**`); el ÚNICO comando de runtime fue `npx tsc --noEmit`: las raíces de este packet fueron **limpias en TODAS las corridas** (V1 a V4) y la **última corrida project-wide salió 0** (las corridas V1 y V2 fueron ROJAS sólo por el árbol **concurrente y ajeno** de `features/admin/**`, que fue reparado por su dueño durante este packet y que este packet NO tocó, NO revirtió y NO fusionó); Vitest / Biome / `next build` / navegador / five-width audit NOT RUN; 6 suites ESCRITAS, NO EJECUTADAS; **CERO rutas ligadas**: `CompetenciasController` (16), `PatrocinadorController` (1) e `InventarioController` (5) **NO registrados**, `modules.competencias`/`modules.patrocinadores` **NO** en `LOCAL_APPS` y el módulo `validaciones` **NO EXISTE** ⇒ las 8 rutas del alcance conservan su **estado honesto** (A0 requests `A0-API05-01`…`07`; `A0-API05-05` = la propiedad de `ADM-15/17/18/19` sigue **NO ATRIBUIDA** y **no** se tocó `features/admin/**`) |
| XCT-01 | verification_required | DOM-03,DOM-06,API-03,API-05 | A8 + A4 + A5 | `evidence/cross-cutting/XCT-01-tickets-validation.md` · apply-progress (topic `sdd/salesianos-fest-rebuild/apply-progress`) — implementation pass applied (30 creados en `Aplicacion/backend/modules/validaciones/**` + 2 adaptadores de dueño + 12 creados / 5 modificados en `Aplicacion/frontend/**`); comandos de runtime: `ast.parse` (45 ficheros) **0**, `manage.py makemigrations --check --dry-run` **0** ("No changes detected"), `manage.py check` **0** ("no issues"), chequeo de imports **0**, `npx tsc --noEmit` **0** (puerta GLOBAL VERDE) — **pytest / vitest / Biome / build / navegador / audit de cinco anchos NOT RUN**: 20 casos de backend + 1 suite de frontend ESCRITOS, NO EJECUTADOS; **A0 wiring NOT applied**: `modules.validaciones` NO está en `INSTALLED_APPS` y `ValidacionController` NO está registrado ⇒ `RT-RT-01` y `RT-RT-02` **NO EXISTEN** en runtime (A0-XCT01-01/02/03) · 4 códigos de error pendientes de catálogo (A0-XCT01-04) |
| XCT-02 | pending | API-02..API-05,XCT-01 | A8 | none |
| XCT-03 | pending | FND-05,DOM-02,DOM-03,DOM-06,XCT-02 | A0 + A2 | none |
| VER-01 | pending | all implementation packets | A9 + A2 | none |
| VER-02 | pending | VER-01 | A9 + domain/UI owners | none |
| VER-03 | pending | VER-02 | A0 + product | none |

## Update Contract

For each transition record timestamp, apply-progress observation ID, changed-file list, commands/exit codes, known baseline failures, regressions, rollback point, and next packet. Never place secret values in this file.

---

## Transition Log

### 2026-11-18 — GOV-00 → completed

**Timestamp:** 2026-11-18 23:55 (local) · **Apply-progress observation:** #11227 · **Owner:** A0 + product

**Checkpoint:**

| Point | Branch | HEAD | `git status --short` | `git ls-files Aplicacion` |
|---|---|---|---|---|
| T0 (packet start) | `master` | `eb17e7bdc837130fe715c863cd968eca03be19ba` | 74 lines (49 `M` + 25 `??`) | 0 |
| T1 (observed mid-packet) | `master` | `f3df5401c56b41c340f257e67d5a306904a9e670` | 2 lines (own evidence) | 390 |

**Concurrent checkpoint commit:** `f3df540` (`betha 4`, parent `eb17e7b`, 644 files) was created by the user
during packet execution and absorbed the entire pre-existing dirty tree plus `Aplicacion/`. Not created by
GOV-00. Gate G1 is satisfied in fact by this commit. Security check: 0 `.env*` paths in the commit.

**Changed files:**

| File | Action |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/manifest-aplicacion.csv` | created (138 071 B, SHA-256 `1DF80E9…D8D8A`) |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/excluded-generated-trees.csv` | created (2 643 B, SHA-256 `C603818…2180C`) |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/GOV-00-checkpoint-summary.md` | created |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/GOV-00-classification-and-rollback.md` | created |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | modified (this transition) |

**Commands / exit codes:** `git rev-parse --show-toplevel` 0 · `git rev-parse HEAD` 0 ·
`git status --short` 0 · `git ls-files Aplicacion` 0 ·
`git diff --name-only -- contract Aplicacion/plan .opencode/skills .opencode/agents` 0 (empty) ·
packet PowerShell SHA-256 validation 0 (422 files / 7 524 842 B; manifest scope 384 files / 6 782 988 B).

**Classification:** 384 authored files — `COPY/REBUILD` 281 · `KEEP` 74 · `QUARANTINE` 26 ·
`NEVER-DELETE` 3 · `GENERATED` 17 excluded entries (70 080 files / 2 424 434 696 B) · `REVIEW` 0.

**Known baseline failures:** none (governance packet; no product suite executed).
**Regressions:** none. No product file modified. No deletion. No commit created by this packet.

**Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670`. Packet rollback = delete
`evidence/checkpoint/**` and restore `STATE.md`. Do not revert or reset `f3df540`.

**Unresolved decisions carried forward:** GAP-1, GAP-2, GAP-3, GAP-4, D-A, D-B, D-C, D-D, D-E, PD-01…PD-10.

**Next packet:** `GOV-01` — `wave-00-governance/GOV-01-contract-freeze.md` (`T-003`…`T-007`). Dependency satisfied.

---

### 2026-11-18 — GOV-01 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** #11229 · **Owner:** A0 (+ A1, A2, A4, A7, A8)
**Original task IDs:** `T-003`, `T-004`, `T-005`, `T-006`, `T-007` (5 of the 54 source-defined IDs)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670`

**Freezes emitted (9):** `FREEZE-ED-1.0.0` · `FREEZE-ID-1.0.0` · `FREEZE-CM-1.0.0` · `FREEZE-RT-1.0.0` ·
`FREEZE-MD-1.0.0` · `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-FX-1.0.0`

**Contradictions resolved (3):** `C-ENV-01` pagination shape (single form `data:{items,total,page,page_size,total_pages}`;
`PaginatedApiResponse` deprecated) · `C-ENV-02` field errors (`error.field_errors[]` as the only per-field channel;
`error.details` narrowed to non-field context) · `C-ENV-03` test client (**operative** decision `FREEZE-TC-1.0.0`;
**documentary** amendment still open as `GOV-01-OPEN-01` / GAP-2). No contract file was modified.

**Changed files:**

| File | Action |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/GOV-01-contract-freeze-summary.md` | created |
| `…/evidence/contracts/FR-01-envelope-error-pagination.md` | created (17 437 B) |
| `…/evidence/contracts/FR-02-edition-scope.md` | created (10 172 B) |
| `…/evidence/contracts/FR-03-identity-titularidad.md` | created (10 459 B) |
| `…/evidence/contracts/FR-04-commerce-payments-idempotency.md` | created (10 220 B) |
| `…/evidence/contracts/FR-05-rights-lifecycle.md` | created (9 398 B) |
| `…/evidence/contracts/FR-06-media.md` | created (8 167 B) |
| `…/evidence/contracts/FR-07-presenter-schema-versions.md` | created (12 440 B) |
| `…/evidence/contracts/FR-08-provisional-fixtures.md` | created (13 620 B) |
| `…/evidence/contracts/FR-09-open-decisions-register.md` | created |
| `…/evidence/contracts/route-to-wrapper-ledger.csv` | created (19 proposed routes) |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | modified (this transition) |

**Commands / exit codes:** `git rev-parse --show-toplevel` 0 · `git rev-parse HEAD` 0 ·
`git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion .opencode/skills .opencode/agents` 0 (empty) ·
product-root diff 0 (empty) · `git status --short` 0 · `EVENTO_ACTIVO_NOMBRE` search 0 (15 hits in `backend/`, 1 in `Aplicacion/backend`) ·
`ImageField`/`upload_to` search 0 (0 hits) · async-controller count 0 (23/24) · `register_controllers` count 0 (28) ·
test-client import survey 0 (three clients in use) · `EstadoOperativoPago` read 0 (8 values, not renumbered) ·
task-matrix ID recount 0 (54) · verification greps 0. **Deviation:** `rg` is not installed in this environment;
the packet's `rg` commands were executed with the semantic equivalent `git grep` (same patterns, same scope).

**Known baseline failures:** none — governance packet; no product suite executed.
**Regressions:** none. No product file modified. No deletion. No commit created by this packet.

**Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670`. Packet rollback = delete
`evidence/contracts/**` and restore `STATE.md`; in Engram restore `sdd/salesianos-fest-rebuild/apply-progress`
and `/state` to #11227 / #11228. Do not revert or reset `f3df540`.

**Open decisions carried forward:** `PD-01`…`PD-10` (none ratified) · `GOV-01-OPEN-01`…`GOV-01-OPEN-13` ·
GAP-1…GAP-4 · D-A…D-E.

**Next packet:** `GOV-02` — `wave-00-governance/GOV-02-route-ux-baseline.md` (`T-001`, `T-002`). Dependency satisfied.

---

### 2026-11-19 — GOV-02 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/apply-progress` (upsert) · **Owner:** A0 + A7 + A9
**Original task IDs:** `T-001`, `T-002` (2 of the 54 source-defined IDs)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged)

| Point | HEAD | `git status --short` | Frozen/product-root diff |
|---|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | 17 lines (5 concurrent + 12 prior packets) | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | 21 lines (17 pre-existing + `evidence/routes/` + `evidence/baseline/` + `STATE.md`) | empty |

**Route briefs produced:** 38 of 38 plan page IDs (16 public/account + 22 admin) across `RB-01`…`RB-08`, plus 1 conceptual route without a page ID (`/competencias/[id]`, public bracket) registered as `RT-CP-10`.
**Count correction:** the exploration recorded "40 page IDs"; the plan's own tables define **38** (`frontend/01` §2 = 16, §3 = 22). 38 + 1 unnumbered proposal = 39 route proposals.

**Shared specs produced:** `SH-01` visual direction + semantic tokens (legacy palette → roles, light/dark, chart tokens) · `SH-02` responsive + a11y matrix (360/390/768/1024/1440) · `SH-03` state matrix (10 states) + recovery patterns · `SH-04` shadcn candidate comparison (MCP execution record) · `SH-05` provisional endpoint/presenter register (78 rows, **78/78 provisional**) · `SH-06` wireframe intent for the 6 high-priority flows (mobile + desktop).

**Commands / exit codes (frozen source):**

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `python -m pytest modules -q` | `backend` | **1** | `13 failed, 1333 passed, 641 warnings in 718.52s` |
| 2 | `python manage.py check` | `backend` | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` |
| 3 | `python manage.py makemigrations --check --dry-run` | `backend` | **1** | same `DB_NAME` failure |
| 4 | `npx tsc --noEmit` | `frontend` | **0** | clean |
| 5 | `npx vitest run` | `frontend` | **1** | `1 failed \| 33 passed (34)` files · `2 failed \| 274 passed (276)` tests |
| 6 | `npx biome check .` | `frontend` | **1** | `566 files` · `105 errors` · `93 warnings` |
| 7 | `git status --short` | repo root | **0** | 17 lines at baseline time |

**Diagnostics (classification only, not the target contract):** `pytest --collect-only` → 0 (1346 collected, 7.21 s) · `manage.py check` with `config.settings.development` + `USE_SQLITE=true` → 0 ("no issues") · `makemigrations --check --dry-run` with the same → 0 ("No changes detected") · `makemigrations` with `config.settings.test` → 1 (`debug_toolbar` `app_label`).

**Known baseline failures:** **13 backend** (envelope drift 1 · status-code mismatch 3 · SQLite limitation 4 · UNIQUE violation 3 · async/sync 1 · count assertion 2 — itemised in `BL-04` §3.1) + **1 frontend red file / 2 tests** (`admin.catalogos.schema.test.ts`, `estado_capacidad_equipo` drift — matches the documented stable red) + **2 environment failures** (`manage.py` DB_NAME) + Biome ceiling 105/93 + 4 React duplicate-key warnings in `AdminPagosLista.test.tsx`. The documented order-dependent file `CompetenciaEncuentroEditors.test.tsx` **passed** in this run.
**Regressions:** none. **Zero frozen files modified. No commit created. `git stash` not invoked.**

**Changed files (this packet — 21 paths):** created `evidence/routes/**` (15 files) and `evidence/baseline/**` (5 files); modified `STATE.md` (this transition). No other file touched.

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/frontend/doc_dev/brief-gov02-parte-a-sistema-visual-y-shell.md` appeared during the packet — a parallel design brief covering the visual system and shell. It overlaps `SH-01` and diverges on two facts: it reports the shadcn registry as **219 items** while the MCP listing in `SH-04` measured **471**, and it states the shadcn MCP was unavailable in that session. It also carries defect findings this packet did not enumerate (`ThemeProvider` not mounted, global `scroll-snap-type`, global `body { overflow-y: scroll }`, duplicated `--color-gold` / `--radius` definitions, missing font weight 900). **Neither file was edited by the other**; A0 must decide the merge order and which source wins before FND-06 consumes either.

**Open decisions carried forward:** `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`GOV-01-OPEN-13` · `GAP-1`…`GAP-4` · D-A…D-E · **`GOV-02-UX-01`…`05`** · **`GOV-02-SH-01`…`08`** · **`GOV-02-BL-01`…`12`** · **`GOV-02-CM-01`…`05`** · route provisionals **`P-01`…`P-12`**.

**Consumers unblocked:** **FND-01** (backend shared API/media — now has a target command matrix and a baseline oracle) · **FND-06** (frontend shell — now has the semantic token system, the shadcn candidate comparison and the responsive/a11y contract) · **FND-07 / FND-08** (query keys, Zod mirrors, cache — now know the frozen envelope includes `message`) · **UI-01…UI-05** (skeletons — now have per-route briefs, the ten-state matrix and the five-width contract) · **API-01…API-05** (now have a 78-row provisional endpoint register) · **XCT-01…XCT-03** and **VER-01…VER-03** (now have the baseline oracle and the regression decision procedure).

**Next packet:** `FND-01` — `wave-01-foundations/FND-01-backend-shared-api-media.md` — and `FND-06` — `wave-01-foundations/FND-06-frontend-shell.md` — after A0 scheduling. Both dependencies are satisfied.

---

### 2026-11-19 — FND-01 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/apply-progress` (upsert) · **Owner:** A0
**Original task IDs:** `T-016` (media contract), `T-018` (auth/permissions contract) — 2 of the 54 source-defined IDs
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged)

| Point | HEAD | `git status --short -- Aplicacion/backend` | Forbidden/product-root diff |
|---|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | clean (0 lines) | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | 9 lines (6 `M` + 3 `??`) | empty |

**Delivered:** the frozen HTTP envelope (one success / one error with `field_errors` / one pagination
shape inside `data`; the deprecated `PaginatedApiResponse` + `meta` form removed) · the safe public
error catalog (uncatalogued codes fall back to a generic per-status message; raw exception text is
never returned) · the permission and authentication authority (`core/capacidades.py` unchanged as the
single map; `RequireAdmin` / `RequireCapability`; **401 before 403**) · the media contract
(`core/media.py`: persistent root, MIME allowlist, 5 MiB cap, content-signature check, single storage
path, multipart token protocol, orphan-file rejection, cleanup helpers; no secrets) · the A0
registration extension point in `config/api.py` with **no unfinished domain controller** · the contract
version registry (`core/contract_versions.py`, `ENVELOPE_VERSION = "1.0.0"` + per-module
`SCHEMA_VERSION = "1.0.0"`).

**Freezes respected:** `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0`.
No ledger route marked `provisional = sí` was registered.

**Changed files (this packet — 12 paths, all inside the allowed edit roots):** created
`Aplicacion/backend/core/media.py`, `Aplicacion/backend/core/contract_versions.py`,
`Aplicacion/backend/core/tests/**` (12 files), `evidence/foundations/FND-01-backend-shared-api-media.md`;
modified `Aplicacion/backend/core/{responses,exceptions,permissions}.py`,
`Aplicacion/backend/config/api.py`, `Aplicacion/backend/config/settings/base.py`,
`Aplicacion/backend/conftest.py`, `STATE.md` (this transition).

**Commands / exit codes (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`):**

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `manage.py check` | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — identical to the pre-packet baseline (environmental, class B7) |
| V2 | `manage.py makemigrations --check --dry-run` | **1** | same `DB_NAME` failure — identical to the pre-packet baseline |
| V3 | `manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| V4 | `manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` — no pending model migration |
| V5 | `python -m pytest core/tests modules/usuarios/tests -q` | **4** | `ERROR: file or directory not found: modules/usuarios/tests` — the exact command was run and the failure recorded; the target `modules/` holds only `__init__.py` by design |
| V6 | `python -m pytest core/tests -q` | **0** | **89 passed in 0.60 s** (the valid focused target suite) |
| V7 | `python -m pytest -q` (whole target root) | **0** | 89 passed |
| V8 | `python -m pytest modules -q` (BL-05 backend gate) | **5** | `no tests ran` — the target has no module tests yet |
| V9 | import sanity of every touched module | **0** | `imports OK` · `controllers vivos: (NinjaJWTDefaultController,)` |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` (root) | **0** | **empty** |
| R2 | `git diff --name-only -- backend frontend worker proxy` (root) | **0** | **empty** — frozen roots untouched |
| R3 | `git diff --name-only -- .opencode/skills .opencode/agents` (root) | **0** | **empty** |

**Known baseline failures:** unchanged. The two `manage.py` failures remain environmental (the target
root behaves exactly as the frozen root: `manage.py` defaults to `config.settings.production`, which
needs `DB_NAME`/`DB_USER`/`DB_PASSWORD`; `BL-05` §2 pins the settings module per command). The 13
frozen-backend test failures were **not** touched: they live in the frozen `backend/modules/**` and
belong to the domain packets.
**Regressions:** none. Zero frozen files modified. No commit created. `git stash` not invoked.

**Deviations (9, detailed in the evidence file §11):** creation of `core/contract_versions.py`
outside the enumerated edit roots (assigned to FND-01 by FR-07 §5) · `ValueError` handler 401→422 ·
Django `ValidationError` 400→422 with `field_errors` · root `conftest.py` modified for the
`FREEZE-TC-1.0.0` test client · the deprecated `PaginatedApiResponse` removed · `core/pagination.py`
imported but not modified · `core/utils.py` / `core/types.py` not modified (the orphan-file gap is
closed in `core/media.py`) · `EVENTO_ACTIVO_NOMBRE` kept with a pointer to FND-02 · dimension limits
and the backup policy left open (`GOV-01-OPEN-10`, `GOV-01-OPEN-09`) rather than invented.

**Byproduct removed:** `manage.py check --settings=config.settings.development` creates a 0-byte
`Aplicacion/backend/db.sqlite3`; it was deleted after the verification runs. `*.sqlite3` is not in
`Aplicacion/backend/.gitignore` — reported to A0 (outside this packet's edit roots).

**Physical task matrix still unsynced:** `00-matriz-tareas.md` rows `T-016` and `T-018` still read
`pending` — the matrix is outside every packet's allowed edit roots. **A0 must sync it explicitly.**

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/frontend/**` changed
substantially during this packet (route groups `(public)` / `(administracion)` / `(cuenta)`,
`features/`, `components/shell/`, `lib/routes.ts`, `providers/AppProviders.tsx` and a large set of
`src/**` edits and deletions). That is **FND-06's** work. **None of it was touched, reverted or merged
by this packet.**

**Consumers unblocked:** **FND-02** (edición) · **FND-03** (identidad) · **FND-04** (commerce/pagos) ·
**DOM-04** and **DOM-08** (media) · **DOM-01…DOM-08** (presenters + `SCHEMA_VERSION`) · **FND-07 /
FND-08** (Zod mirrors, query keys) · **API-01…API-05** (registration extension point + drift test) ·
**XCT-03** (media/deployment/permissions).

**Next packet:** `FND-02`, `FND-03` and `FND-04` — `wave-01-foundations/` — on disjoint roots.
Their DAG dependency (FND-01) is satisfied.

---

### 2026-11-19 — FND-02 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/apply-progress` (upsert) · **Owner:** A1
**Original task IDs:** `T-010` — 1 of the 54 source-defined IDs
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)

| Point | HEAD | `git status --short -- Aplicacion/backend` | Forbidden/product-root diff |
|---|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | FND-01 + FND-03 (`modules/usuarios/`) present | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | + `modules/eventos/` (56 files, new) | empty |

**Delivered:** the `eventos` Django module — `Evento` (id + nombre + slug) and `Edicion` (id +
`evento_id` + nombre + slug + anio + estado + `modulos_habilitados` + fechas + timestamps) with the
**"at most one `PUBLICADA` edition per event"** invariant as a conditional `UniqueConstraint` · the
**single frozen resolution order** (FR-02 §2.2) in `EdicionScopeService` (explicit id → actor's
active edition → unique `PUBLICADA` → error), with **no** silent fallback to any level · read-only
selectors (the frozen `obtener_activo` / `obtener_activo_por_nombre` are deliberately **not**
carried over) · sync core service, async flow with `transaction.atomic()`, thin async orchestrator ·
internal DTOs and result objects · HTTP schemas composed from the three blocks of
`SCHEMA_DRY_INTENTION` · pure presenter · public controller `GET /ediciones/actual` · idempotent
management command `crear_edicion_inicial` · migration `0001_initial` · **63 tests**.

**Freezes respected:** `FREEZE-ED-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0`
(the e2e test uses `django.test.Client`, the sync alternative permitted for async controllers).
**No ledger route marked `provisional = sí` was registered** — registration is A0's (A0-03).

**Commands / exit codes (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`):**

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/eventos/tests -q` (env `DJANGO_SETTINGS_MODULE=modules.eventos.tests.settings_overlay`) | **0** | **63 passed** |
| V2 | `python -m pytest modules/eventos/tests -q` (without the overlay) | **4** | `RuntimeError: ... isn't in an application in INSTALLED_APPS` — A0-02 pending, not a module defect |
| V3 | `manage.py check` | **1** | `DB_NAME` — identical to the FND-01 baseline (environmental) |
| V4 | `manage.py makemigrations --check --dry-run` | **1** | same `DB_NAME` — identical baseline |
| V5 | `manage.py check --settings=config.settings.development` | **0** | `no issues` |
| V6 | `manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| V7 | `manage.py check --settings=…overlay` | **0** | `no issues` |
| V8 | `manage.py makemigrations --check --dry-run --settings=…overlay` | **0** | `No changes detected` — `0001_initial` matches the models exactly |
| V9–V12 | `showmigrations eventos` → `migrate` → `migrate` (idempotent) → `showmigrations` | **0** | `[X] 0001_initial` |
| V13 | `migrate eventos zero --settings=…overlay` | **0** | `Unapplying eventos.0001_initial... OK` — reversible |
| V14 | `migrate eventos --settings=…overlay` | **0** | `Applying eventos.0001_initial... OK` — second replay |
| V15 | SQLite schema inspection | **0** | `edicion_publicada_unica_evento` partial UNIQUE index + `edicion_slug_unico_evento` present |
| V16 | `manage.py crear_edicion_inicial … --publicar` | **0** | edition created and published; row verified |
| V17 | `manage.py crear_edicion_inicial …` (repeat) | **0** | `La edición ya existía; no se creó una segunda.` — idempotent |
| V18 | `python -m pytest core/tests -q` (default settings) | **0** | **89 passed** — FND-01 baseline intact |
| V19 | `python -m pytest core/tests modules/eventos/tests -q` (overlay) | **0** | **152 passed** |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **empty** — frozen roots untouched |
| R3 | `git grep -n "EVENTO_ACTIVO_NOMBRE" -- Aplicacion/backend` | **0** | 2 hits, **both** in `config/settings/base.py` (A0-04); **0** in `modules/eventos/**` |

**Known baseline failures:** unchanged (V3/V4 environmental; the 13 frozen-backend failures belong
to the domain packets). **New:** V2 — the package cannot be imported until A0 registers the app in
`INSTALLED_APPS` (A0-02); with the local overlay everything passes.
**Regressions:** none. Zero frozen files modified. No commit created. `git stash` not invoked.

**Changed files (this packet — 57 paths, all inside the allowed edit roots):** created
`Aplicacion/backend/modules/eventos/**` (56 files) and
`evidence/foundations/FND-02-event-edition-scope.md`; modified `STATE.md` (this transition).
**No shared A0 file was edited** — `config/settings/base.py`, `config/api.py` and
`core/exceptions.py` are requested by evidence (A0-01…A0-07).

**A0 requests:** A0-01 public error catalog (8 codes) · A0-02 app + DI registration ·
A0-03 controller registration · A0-04 removal of `EVENTO_ACTIVO_NOMBRE` from settings ·
A0-05 `*.sqlite3` in `.gitignore` · A0-06 `details` support for the ambiguous-edition candidate
list · A0-07 sync of the physical task matrix (`T-010`).

**Byproduct removed:** `manage.py check --settings=config.settings.development` creates a 0-byte
`Aplicacion/backend/db.sqlite3`; it was deleted after the verification runs (FND-01 F-2).

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/backend/modules/usuarios/**`
(**FND-03**, identity) and `Aplicacion/frontend/**` (**FND-06**, shell) appeared during this packet.
**None of it was touched, reverted or merged.**

**Consumers unblocked:** **DOM-01, DOM-03, DOM-04, DOM-07, DOM-08** (edition anchor + module
enablement) · **FND-03, FND-04** (shared DI + scope anchor) · **API-01…API-05** (`RT-ED-01`
implemented, `RT-ED-02` scoped to the catalog owners) · **FND-07 / FND-08** (exact wrapper shape for
the Zod mirror) · **UI-01…UI-05 / FND-06** (the frontend reads the edition from
`GET /ediciones/actual`) · **XCT-01…XCT-03, VER-01…VER-03**.

**Next packet:** **DOM-01**, **DOM-03**, **DOM-04**, **DOM-07** and **DOM-08** after their other
dependencies.

---

### 2026-11-19 — FND-03 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/fnd-03-apply-progress` (packet-specific) merged into the shared topic `sdd/salesianos-fest-rebuild/apply-progress` · **Owner:** A1
**Original task IDs:** `T-011` (Persona/Usuario/roles/titularidad), `T-012` (resolver local→RENIEC + persistencia confirmada) — 2 of the 54 source-defined IDs (cumulative with GOV-00/01/02, FND-01 and FND-02: **12 of 54**)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)

| Point | HEAD | `git status --short -- Aplicacion/backend` | Forbidden/product-root diff |
|---|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | FND-01 files + FND-02's `modules/eventos/` | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | + `modules/usuarios/` (53 new files) | empty |

**Delivered:** the `usuarios` Django module — `Persona` (civil identity, unique by `(tipo_documento, numero_documento)`, **exists without an account**, normalized document, origin/date of the recovered data) · `Usuario` (custom auth user, `Persona` relation 1:1 and **optional in both directions**, technical accounts allowed) · the **two** functional Django groups `Normal` / `Administrador` created by a data migration, with `is_superuser` kept as the technical tier · the frozen **titularidad interface** (four titularidades, resource-agnostic primitives, no central service, no document-as-authorization) · the **local-first resolver** with the four frozen origins and **five typed external states**, deferred persistence and a database-authoritative anti-duplicate with a controlled retry on `IntegrityError` · the HTTP adapter of the **already existing** document service (`worker/scraper`) with no invented provider payload and no invented credential · three frozen routes (`RT-ID-01` `GET /personas/busqueda/{documento}` public, `RT-ID-02` `POST /personas/resolver`, `RT-ID-03` `POST /personas/confirmar`) with the ledger's presenter and wrapper names · `SCHEMA_VERSION = "1.0.0"` · **35 behaviour tests**.

**Freezes respected:** `FREEZE-ID-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-ENV-1.0.0` · `FREEZE-TC-1.0.0` · `FREEZE-FX-1.0.0`.
No ledger route marked `provisional = sí` was registered (registration is A0's).

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`; env `PYTEST_ADDOPTS = "--ds=modules.usuarios.tests.settings_usuarios"`):

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/usuarios/tests -q` (with the package settings) | **0** | **35 passed**, 1 skipped (the A0-registration marker) |
| V2 | `python -m pytest modules/usuarios/tests -q` (project settings, app not registered) | **0** | 1 skipped + explicit stderr notice — the 35 tests are **omitted**, not silently passed |
| V3 | `python manage.py makemigrations --check --dry-run --settings=modules.usuarios.tests.settings_usuarios` | **0** | `No changes detected` |
| V4 | `python manage.py check --settings=modules.usuarios.tests.settings_usuarios` | **0** | `System check identified no issues (0 silenced)` |
| V5 | `python manage.py migrate --settings=…` (file SQLite) | **0** | `Applying usuarios.0002_grupos_funcionales... OK` — migration replay |
| V6 | `manage.py shell` after the replay | **0** | `GRUPOS: ['Administrador', 'Normal']` · tables `usuarios_persona`, `usuarios_usuario`, `usuarios_historicalpersona`, `usuarios_usuario_groups`, `usuarios_usuario_user_permissions` |
| V7 | `python -m pytest core/tests -q` (project settings) | **0** | **89 passed** — FND-01 baseline intact |
| V8 | `python manage.py check --settings=config.settings.development` | **0** | `no issues` (baseline re-check) |
| V9 | `python manage.py check` / `makemigrations --check --dry-run` (default settings) | **1** | `DB_NAME` — identical to the FND-01/FND-02 baseline (environmental) |
| R1 | `git status --short -- backend frontend worker proxy contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** — frozen roots untouched |
| R2 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — unchanged, no commit |

**Stability:** the package suite was executed **12 consecutive times** after the last fix: `35 passed` on every run.

**Known baseline failures:** unchanged (the two default-settings `manage.py` gates remain environmental).
**New:** the package cannot be imported until A0 registers the app in `INSTALLED_APPS` (A0-01); with the
local verification settings everything passes.
**Regressions:** none. Zero frozen files modified. No commit created. `git stash` not invoked.

**Changed files (this packet — 54 paths, all inside the allowed edit roots):** created
`Aplicacion/backend/modules/usuarios/**` (53 files, incl. `migrations/0001_initial.py` and
`migrations/0002_grupos_funcionales.py`) and
`evidence/foundations/FND-03-identity-reniec.md`; modified `STATE.md` (this transition).
**No shared A0 file was edited** — `config/settings/base.py`, `config/api.py` and
`core/exceptions.py` are requested by evidence (A0-01…A0-04).

**A0 requests:** A0-01 app + DI registration in `config/settings/base.py` (`INSTALLED_APPS`,
`AUTH_USER_MODEL = "usuarios.Usuario"`, `NINJA_EXTRA["INJECTOR_MODULES"]`) — **before the first
migration of the target** · A0-02 `registrar_controladores(PersonaController)` in `config/api.py` ·
A0-03 public error catalog (`FUENTE_EXTERNA_NO_DISPONIBLE`, `FUENTE_EXTERNA_TIMEOUT`,
`PERSONA_DATOS_INCOMPLETOS`, `PERSONA_DUPLICADA`) · A0-04 sync of the physical task matrix
(`T-011`, `T-012`).

**Review slices:** the packet exceeds the ~400-line review budget (2 592 code lines + 829 docstring
lines, of which 406 code lines are the generated migration). It was split into four autonomous
slices — WU-A domain · WU-B behaviour · WU-C surface · WU-D tests — all verified together. No
unrelated domain was mixed in and no commit was made.

**Physical task matrix still unsynced:** `00-matriz-tareas.md` rows `T-011` and `T-012` still read
`pending` — the matrix is outside every packet's allowed edit roots. **A0 must sync it explicitly.**

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/backend/modules/eventos/**`
(**FND-02**, edition scope) and `Aplicacion/frontend/**` (**FND-06**, shell). **None of it was
touched, reverted or merged.**

**Consumers unblocked:** **DOM-01** (Responsable + `RecursoTitularidad`) · **DOM-03**
(`TITULARIDAD_BENEFICIARIO` with revocation) · **DOM-04 / DOM-08** (`Persona` as buyer identity) ·
**API-01** (`RT-ID-02` / `RT-ID-03` with the frozen wrappers) · **XCT-01** (`TITULARIDAD_ADMIN`) ·
**FND-05** (actor shape) · **FND-08** (`SCHEMA_VERSION` of `usuarios`) · **VER-01…VER-03**.
**Still blocked on A0:** any consumer that needs the routes served by the project API.

**Next packet:** **DOM-01**, **DOM-03**, **DOM-04**, **DOM-07** and **DOM-08** after their other
dependencies.

---

### 2026-11-19 — FND-04 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/fnd-04-apply-progress` (packet-specific) merged into the shared topic `sdd/salesianos-fest-rebuild/apply-progress` · **Owner:** A2
**Original task IDs:** `T-013` (Compra snapshots + origin), `T-014` (OrdenPago / TransaccionPago / idempotencia) — 2 of the 54 source-defined IDs (cumulative with GOV-00/01/02, FND-01, FND-02 and FND-03: **14 of 54**)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)

| Point | HEAD | `git status --short -- Aplicacion/backend` | Forbidden/product-root diff |
|---|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | FND-01 files + `modules/eventos/` + `modules/usuarios/` | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | + `modules/commerce/` (40 files) + `modules/pagos/` (55 files) | empty |

**Delivered:** the two shared commerce/payment modules of the target —

- **`modules/commerce/`** (40 files): `Compra` (comprador `Persona` obligatorio, `origen` de tres valores
  cerrados, `estado` `PENDIENTE|PAGADA|CANCELADA`, `total` `Decimal` congelado, `moneda` ISO-4217,
  `lineas_snapshot` inmutable, `orden_pago` OneToOne nullable, `referencia` de la intención) · el flujo
  **crear-o-reutilizar** una compra pendiente · el derivado del total a partir de las líneas · los
  adaptadores de `pagos` (estado comercial de la compra y titularidad de la orden).
- **`modules/pagos/`** (55 files): `OrdenPago` (5 estados) · `TransaccionPago` (intento, ordinal creciente,
  `verificada`, `evidencia`) con **historial completo de intentos** · `RegistroIdempotencia` · la
  verificación de firma **en servidor** (HMAC-SHA256 sobre el payload crudo, comparación en tiempo constante,
  sin fallback) · el saneado del payload del proveedor · el flujo de confirmación **idempotente** (duplicada
  y tardía) · el flujo de ciclo de vida del intento · `EstadoOperativoPagoService`, **único dueño** del
  veredicto operativo · tres rutas congeladas (`RT-PG-01`, `RT-PG-02`, `RT-PG-03`) con los nombres de
  presenter y wrapper del ledger · `SCHEMA_VERSION = "1.0.0"` en ambos módulos.

**Freezes respected:** `FREEZE-CM-1.0.0` · `FREEZE-ENV-1.0.0` (FR-01 §5) · `FREEZE-PS-1.0.0` ·
`FREEZE-TC-1.0.0` (el e2e usa `django.test.Client`, la alternativa sincrónica permitida para controllers
`async def`). **No ledger route marked `provisional = sí` was registered** — registration is A0's (A0-03).

**Divergence declared (traceable):** FR-04 §1.1/§1.2 describe DOS FKs entre `Compra` y `OrdenPago`
(`Compra.orden_pago_id` y `OrdenPago.compra_id`). Dos FKs físicas entre las mismas tablas son una
dependencia de migración **circular** y Django no las construye. El backend congelado resolvió el mismo
problema igual (`backend/modules/commerce/migrations/0003_remove_compra_from_ordenpago.py`): la columna
física vive en UN lado. Este paquete conserva literal `Compra.orden_pago_id` (FR-04 §1.1) y materializa
`OrdenPago.compra_id` como la relación inversa, a la que `pagos` llega por el port
`IEstadoCompraOrdenPagoService` y nunca por un import. La dirección de dependencias queda
`commerce → pagos` y el grafo de módulos sigue acíclico.

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`; env
`DJANGO_SETTINGS_MODULE = "modules.pagos.tests.settings_overlay"` — el overlay registra `usuarios` +
`commerce` + `pagos`, `AUTH_USER_MODEL` y los tres módulos de DI, porque el registro permanente es de A0):

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/commerce/tests modules/pagos/tests -q` | **0** | **79 passed** (15 commerce + 64 pagos) |
| V2 | `python -m pytest modules/pagos/tests -q` | **0** | **64 passed** |
| V3 | `python -m pytest modules/commerce/tests -q` | **0** | **15 passed** |
| V4 | `python manage.py check --settings=modules.pagos.tests.settings_overlay` | **0** | `no issues` |
| V5 | `python manage.py makemigrations --check --dry-run --settings=…overlay` | **0** | `No changes detected` — la migración coincide con los modelos |
| V6 | `python manage.py check` (default settings) | **1** | `DB_NAME` — **idéntico al baseline FND-01/02/03** (ambiental) |
| V7 | `python manage.py makemigrations --check --dry-run` (default settings) | **1** | mismo `DB_NAME` — baseline idéntico |
| V8 | `python manage.py check --settings=config.settings.development` | **0** | `no issues` |
| V9 | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| V10–V12 | `migrate` → `migrate` (idempotente) → `showmigrations` (fichero SQLite) | **0** | `Applying pagos.0001_initial... OK` · `Applying commerce.0001_initial... OK` · `[X] 0001_initial` |
| V13–V15 | `migrate commerce zero` → `migrate pagos zero` → `migrate` (replay) | **0** | `Unapplying ... OK` × 2 → `Applying ... OK` — reversible y reproducible |
| V16 | inspección del esquema SQLite de las 4 tablas | **0** | 3 índices UNIQUE (2 parciales) + 2 CHECK de dinero presentes |
| V17 | `python -m pytest core/tests -q` (default settings) | **0** | **89 passed** — baseline FND-01 intacto |
| V18 | `python -m pytest modules/eventos/tests -q` (overlay FND-02) | **0** | **63 passed** — baseline FND-02 intacto |
| V19 | `python -m pytest modules/usuarios/tests -q` (overlay FND-03) | **0** | **35 passed, 1 skipped** — baseline FND-03 intacto |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **empty** — raíces congeladas intactas |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — sin cambios, **ningún commit creado** |
| R4 | `git stash` | — | **nunca invocado** |

**Stability:** la suite del paquete se ejecutó **5 veces consecutivas** tras el último cambio: `79 passed`
en todas.

**Known baseline failures:** unchanged — las dos puertas `manage.py` con settings por defecto (V6/V7)
siguen siendo ambientales e idénticas a FND-01/FND-02/FND-03.
**New (no es un defecto):** los dos paquetes no se pueden importar hasta que A0 registre las apps en
`INSTALLED_APPS` (A0-01); con el overlay local de verificación todo pasa.
**Regressions:** none. Zero frozen files modified. No commit created. `git stash` not invoked.

**Changed files (this packet — 97 paths, all inside the allowed edit roots):** created
`Aplicacion/backend/modules/commerce/**` (40 files) and `Aplicacion/backend/modules/pagos/**` (55 files);
created `evidence/foundations/FND-04-commerce-payments.md`; modified `STATE.md` (this transition).
**No shared A0 file was edited** — `config/settings/base.py`, `config/api.py` and `core/exceptions.py` are
requested by evidence (A0-01…A0-08).

**A0 requests:** A0-01 registro de apps + DI en `config/settings/base.py` (con `usuarios` como
prerrequisito: `Compra.persona` es FK a `usuarios.Persona`) · A0-02 orden de migración
`usuarios → pagos → commerce` antes de la primera migración del objetivo · A0-03
`registrar_controladores(PagosController)` en `config/api.py` · A0-04 catálogo público de 6 códigos nuevos
(`IDEMPOTENCY_KEY_REUTILIZADA`, `IDEMPOTENCY_KEY_INVALIDA`, `ORDEN_PAGO_NO_PAGABLE`,
`COMPRA_TOTAL_INCOHERENTE`, `COMPRA_REFERENCIA_INVALIDA`, `COMPRA_NO_ENCONTRADA`) · A0-05 confirmar el status
HTTP de los códigos nuevos (400 para las firmas, 409 para los conflictos de idempotencia, 422 para el total
incoherente) · A0-06 `*.sqlite3` en `.gitignore` · A0-07 sincronizar la matriz física (`T-013`, `T-014`) ·
A0-08 decidir si `IZIPAY_KEY_HASH` debe estar en el `.env` del objetivo **antes** de la salida (sin ella el
proveedor no puede autenticarse y el canal servidor a servidor falla cerrado).

**Secret-redaction proof:** la clave del comercio nunca aparece en la evidencia, el metadata ni los logs; el
payload del proveedor se sanea antes de persistirse (sin datos de tarjeta, sin tokens, sin 3-DS, sin firma,
sin payload firmado); el registro de idempotencia guarda una **huella** y nunca el payload; la referencia
técnica del proveedor no se publica en ningún wrapper. **Ningún valor de secreto fue leído, impreso, copiado
ni commiteado**; los tests usan una constante pública que sólo existe en el proceso de prueba.

**Physical task matrix still unsynced:** `00-matriz-tareas.md` rows `T-013` and `T-014` still read
`pending` — the matrix is outside every packet's allowed edit roots. **A0 must sync it explicitly.**

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/backend/modules/eventos/**`
(**FND-02**) and `Aplicacion/backend/modules/usuarios/**` (**FND-03**) were already present; their suites were
re-run green (V18/V19). `Aplicacion/frontend/**` (**FND-06**, frontend shell) is owned by another agent and
was **not** touched. The **FND-06 row of the board was deliberately NOT touched**: A0/A7 owns it.

**Unresolved decisions carried forward:** `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 · D-A…D-E ·
`GOV-02-UX-01`…`05` · `GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` · `P-01`…`P-12` ·
`GOV-01-OPEN-09` · `GOV-01-OPEN-10` · `NEW-FND03-01`…`04` · `D-FND-02-01`…`09` · **new:** `D-FND-04-01`
(formato de la `Compra.referencia`, que debe acordarse antes de DOM-01/03/05) · `D-FND-04-02` (qué
referencia de orden hace eco el proveedor) · `D-FND-04-03` (aprobación manual `RT-PG-05`, owner A0) ·
`D-FND-04-04` (apertura de sesión en el proveedor: llamada viva, fuera del alcance de FND-04) ·
`D-FND-04-05` (la incidencia de activación es de FND-05) · `D-FND-04-06` (`commerce` no tiene superficie HTTP:
los dominios crean su compra en proceso).

**Consumers unblocked:** **DOM-01 / DOM-03 / DOM-05** (Compra + orquestador + snapshot congelado) ·
**DOM-02 / DOM-06** · **FND-05** (el pago queda durable antes de cualquier activación; `Compra.estado =
PAGADA` es idempotente) · **XCT-03** (conciliación: los tres estados están separados y la incidencia es
visible) · **API-03 / API-04** (`estado_operativo` publicado por el backend) · **VER-01…VER-03**.
**Still blocked on A0:** cualquier consumidor que necesite las tres rutas servidas por la API del proyecto.

**Next packet:** **FND-05** — *Coordinate Exactly-Once Rights Activation* (`T-015`). Sus raíces permitidas
incluyen `modules/commerce/**` y `modules/pagos/**`: **los ficheros de este paquete son el suelo sobre el
que construye y no deben reescribirse**; el coordinador añade la clave/estado/incidencia de activación y la
interfaz de activación por origen, y reutiliza `Compra.estado`, el port
`IEstadoCompraOrdenPagoService` y `EstadoOperativoPagoService`.

---

### 2026-11-19 — FND-01 → A0 reconciliation of FND-02 / FND-03 / FND-04 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** shared topic
`sdd/salesianos-fest-rebuild/apply-progress` (merge) · **Owner:** A0
**Nature:** **serialized A0 reconciliation** of the completed foundations — **NOT a new packet**;
no domain behaviour was broadened. **Full report:**
`evidence/foundations/FND-01-a0-reconciliation.md`.

**Original task IDs:** none new. It discharges the pending A0 requests of FND-02 (`T-010`), FND-03
(`T-011`, `T-012`) and FND-04 (`T-013`, `T-014`) that live in A0's shared files, plus FND-01's own
`T-016`/`T-018` follow-up.

**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged;
**no commit created**, `git stash` never invoked)

| Point | HEAD | Forbidden / frozen-root diff |
|---|---|---|
| reconciliation start | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |
| reconciliation close | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |

**Delivered (A0 shared files only):**

- `config/settings/base.py` — `LOCAL_APPS` now registers the **completed** apps in the order of the
  migration graph: `modules.eventos` → `modules.usuarios` → `modules.pagos` → `modules.commerce`
  (effective migration order `usuarios` → `pagos` → `commerce`; `eventos` independent) ·
  `AUTH_USER_MODEL = "usuarios.Usuario"` fixed **before** the target's first real migration ·
  `NINJA_EXTRA["INJECTOR_MODULES"]` now registers the four completed DI modules
  (`UsuariosModule`, `EventosModule`, `PagosModule`, `CommerceModule`) · the rejected global
  **`EVENTO_ACTIVO_NOMBRE`** assumption **removed** (FR-02 §2.4 · D-01), with **no replacement
  setting invented**.
- `config/api.py` — the three completed controllers registered through the FND-01 extension point:
  `registrar_controladores(EdicionController, PersonaController, PagosController)`. **No unfinished
  domain controller is registered.**
- `core/exceptions.py` — **18 safe public error codes** merged into the frozen catalog (8 `eventos`
  + 4 `usuarios` + 6 `commerce`/`pagos`), plus 503/504 in the generic fallback map. **No raw error
  leaks; no handler was weakened.**
- `core/contract_versions.py` — verified (no edit needed): the registry already covers the four
  completed foundations at `1.0.0`; two new A0 tests assert the coverage and the **drift** against
  each module's declared `SCHEMA_VERSION`.
- `core/tests/integration/test_registration_extension.py` — rewritten for the closed registry: the
  completed controllers are registered, the registry is idempotent, and the live OpenAPI surface is
  **exactly** the frozen ledger's 7 domain routes (no unfinished controller, no missing one).
- Requirement-8 exception: the three domain verification overlays were **adapted** to an idempotent
  registration (their own evidence asks A0 to retire them; adaptation keeps every documented command
  working), and the intentional registration-pending marker
  `modules/usuarios/tests/test_registro_de_la_app_pendiente.py` was **deleted** as FND-03 §8.1
  explicitly requires.

**Live surface (proof):** `GET /api/ediciones/actual` · `GET /api/personas/busqueda/{documento}` ·
`POST /api/personas/resolver` · `POST /api/personas/confirmar` ·
`POST /api/pagos/ordenes/{orden_id}/confirmar` · `POST /api/pagos/izipay/notificacion` ·
`GET /api/pagos/ordenes/{orden_id}` + the 3 JWT routes. **Nothing else.**

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`): `check
--settings=config.settings.development` **0** · `makemigrations --check --dry-run
--settings=config.settings.development` **0** · `check` and `makemigrations --check --dry-run` with
the default settings **1** (`DB_NAME` — **identical environmental baseline**, not a regression) ·
integrated `migrate` from an empty DB **0** (`usuarios` → `pagos` → `commerce`, `eventos`
independent) · `migrate` repeat **0** (idempotent) · `showmigrations` **0** (all `[X]`) ·
`migrate <app> zero` × 4 **0** (reversible) · `migrate` replay **0** · **`python -m pytest
core/tests modules/eventos/tests modules/usuarios/tests modules/commerce/tests modules/pagos/tests
-q` → 0 (277 passed)** · whole target root **0 (277 passed)** · per package `core 99` · `eventos
63` · `usuarios 35` (the pending marker is gone: no more skip) · `commerce 15` · `pagos 64` ·
focused registration test **0 (8 passed)** · the three adapted overlays **0 (63 / 35 / 79)** ·
forbidden-root diff **0 (empty)** · frozen-root diff **0 (empty)** · `git rev-parse HEAD` **0
(unchanged)**.

**Known baseline failures:** unchanged — the two default-settings `manage.py` gates remain
environmental (`DB_NAME`), identical to FND-01/FND-02/FND-03/FND-04. **New:** none.
**Regressions:** none. Zero frozen files modified. No commit created. `git stash` not invoked.
**Byproduct removed:** the migration rehearsal created `Aplicacion/backend/db.sqlite3`; it was
**deleted** after the verification runs (databases are a forbidden artifact).

**A0 requests still deferred (recorded, not applied):** `*.sqlite3` in the target `.gitignore`
(outside the allowed edit roots) · the physical task-matrix sync `00-matriz-tareas.md` (rows
`T-010`…`T-014`, `T-016`, `T-018`; outside the allowed edit roots) · `D-FND-02-08` (candidate list
in `error.details` — open decision; the A0 side would have to import domain vocabulary into the
shared error boundary) · `NEW-FND03-04` (whether `core/capacidades.py::es_admin` must honour the
`Administrador` group — open authorization decision) · `IZIPAY_KEY_HASH` in the target `.env`
(forbidden root, release decision).

**Deviations:** `D-A0R-01` (overlays adapted, not retired) · `D-A0R-02` (pending-registration
marker deleted) · `D-A0R-03` (the `commerce` overlay needed no change) · `D-A0R-04` (the
`usuarios` conftest keeps an inert pending branch) · `D-A0R-05` (`D-FND-02-08` not implemented) ·
`D-A0R-06` (`core/capacidades.py` untouched).

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/frontend/**` (**FND-06**) is
owned by another agent and was **not** touched; the **FND-06 row of this board was deliberately NOT
touched** (A0/A7 owns it). The GOV-00 checkpoint CSVs show as modified in `git status` — that is a
**pre-existing** line-ending change written by GOV-00 (mtime 2026-11-18 18:51), **not** from this
reconciliation.

**Consumers unblocked:** **FND-05** (the payment is durable in the target database before any
activation) · **DOM-01…DOM-08** · **API-01…API-05** (the completed routes are now served by the
project API instead of being dead code) · **FND-07 / FND-08** · **XCT-01…XCT-03** ·
**VER-01…VER-03**.

**Next packet:** **FND-05** — *Coordinate Exactly-Once Rights Activation* (`T-015`). Its allowed
roots include `modules/commerce/**` and `modules/pagos/**`: **those files are the ground it builds
on and must not be rewritten**.

---

### 2026-11-19 — DOM-01 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/dom-01-apply-progress` (packet-specific) merged into the shared topic `sdd/salesianos-fest-rebuild/apply-progress` · **Owner:** A3
**Original task IDs:** `T-020`, `T-021` — 2 of the 54 source-defined IDs (cumulative with GOV-00/01/02, FND-01…FND-05: **17 of 54**)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)

| Point | HEAD | Forbidden / frozen-root diff |
|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |

**Delivered:** the **edition-scoped inscription catalog** and the **initial registration with its
pending purchase**.

- **`Aplicacion/backend/modules/salesianos_fest/`** (new module, 63 files): `Disciplina`,
  `Paquete`, `PaqueteDisciplina`, `PaqueteBeneficio`, `PaquetePrecio` (the catalog, always
  scoped to an `eventos.Edicion`) · `Inscripcion` (with `HistoricalRecords`) and `Equipo` ·
  `CatalogoFlujo` / `InscripcionFlujo` (async, the flow is the only place with
  `transaction.atomic()`) · `CatalogoOrchestrator` / `InscripcionOrchestrator` (thin async
  facades) · two **ports** (`IAlcanceEdicionService`, `ITitularidadService`) with their adapters
  in `infrastructure/services/` · the typed HTTP schemas composed by the three DRY blocks,
  the pure presenters and the two "sacred" controllers · `di.py` · `admin.py` ·
  migration `0001_initial` (dependencies `eventos.0001_initial`, `usuarios.0002_grupos_funcionales`).
- **The initial purchase goes through the FROZEN commerce interface**: `InscripcionFlujo` calls
  `commerce.CompraFlujo.crear_o_reutilizar_compra` with `CompraCreateData(origen=INSCRIPCION)`
  and a `LineaCompraSnapshot` carrying the **server-resolved** catalogue price. The total is
  derived by `commerce`; this module never declares an amount (`RN-C01`, `RN-C02`).
- **Capacity stays at zero until a verified activation**: `cupos_pagados` is born at `0`, the
  available balance is derived server-side (`RN-I02`, `QA-I01`), and the `CHECK
  (cupos_asignados <= cupos_pagados)` constraint holds at the database level (`RN-I03`).
- **The purchase is recoverable and the registration is never duplicated**: the intent
  reference is stable (`INSCRIPCION:{id}:INICIAL`), the DB conditional `UNIQUE
  (edicion_id, responsable_id, paquete_id) WHERE NOT (estado = 'CANCELADA')` is the authority,
  and a retry returns the SAME inscription, the SAME pending purchase and the SAME teams.
- **45 behaviour tests, all green** (38 integration + 7 e2e), covering success, invalid
  edition/package/discipline, pending payment, duplicate submit, permission and concurrency.

**Interfaces consumed (frozen):** `commerce.CompraFlujo` + `CompraCreateData` /
`LineaCompraSnapshot` (**direct** — the shared commercial infrastructure, `D-FND-04-06`) ·
`eventos.EdicionScopeService` and `usuarios.TitularidadService` (**through ports**, with their
adapters in `infrastructure/`) · `eventos.ModuloLogico.INSCRIPCIONES` for the module-enablement
check (`FR-02` §2.5).

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`; verification
settings `modules.salesianos_fest.tests.settings_overlay`, SQLite in memory):

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/salesianos_fest/tests -q -k "paquete or inscripcion"` | **0** | **45 passed** — the packet's filter selects 100 % of the module's tests |
| V2 | `python -m pytest modules/salesianos_fest/tests -q` | **0** | **45 passed** |
| V3 | `manage.py makemigrations --check --dry-run --settings=…overlay` | **0** | `No changes detected` |
| V4 | `manage.py check --settings=…overlay` | **0** | `no issues` |
| V5 | `manage.py check` (default settings) | **1** | `DB_NAME` — **identical environmental baseline** (FND-01…FND-05), not a regression |
| V6 | `manage.py makemigrations --check --dry-run` (default settings) | **1** | same `DB_NAME` baseline |
| V7–V12 | `migrate` → `showmigrations` → `migrate` (idempotent) → `migrate salesianos_fest zero` → replay → SQLite schema inspection | **0** | `Applying salesianos_fest.0001_initial... OK` · `[X] 0001_initial` · `No migrations to apply` · `Unapplying … OK` · `Applying … OK` · the conditional UNIQUE index + the CHECK constraint are present |
| V13 | `python -m pytest core/tests -q` | **0** | **100 passed** — FND-01 baseline intact |
| V14 | `python -m pytest modules/eventos/tests -q` | **0** | **63 passed** — FND-02 baseline intact |
| V15 | `python -m pytest modules/usuarios/tests -q` | **0** | **35 passed** — FND-03 baseline intact |
| V16 | `python -m pytest modules/commerce/tests modules/pagos/tests -q` | **0** | **96 passed** — FND-04/FND-05 baselines intact |
| V17 | `python -m pytest -q` (whole target root, overlay) | **1** | **338 passed · 1 failed** — the single failure is `R-DOM-01-01` (see below) |
| V18 | `python -m pytest -q` (whole target root, default settings) | **2** | `RuntimeError: … isn't in an application in INSTALLED_APPS` — **A0-01 pending**, same class as FND-02's V2, not a module defect |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **empty** — frozen roots untouched |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — no commit created |
| R4 | `git stash` | — | **never invoked** |

**Known baseline failures:** unchanged — the two default-settings `manage.py` gates stay
environmental (`DB_NAME`), identical to FND-01…FND-05. **New:** the whole-root run with the
DEFAULT settings stops at collection with `RuntimeError: … isn't in an application in
INSTALLED_APPS`: the package cannot register its own app (`config/settings/base.py` is A0's).
Same class as FND-02's V2; the local verification overlay replicates the permanent registration
exactly.

**Regressions (1, INTRODUCED by this packet):** `R-DOM-01-01` —
`modules/pagos/tests/integration/test_pago_confirmacion.py::test_la_compra_se_marca_pagada_sin_activar_derechos`
asserts `not apps.is_installed("modules.salesianos_fest")` to prove that no rights app exists
yet in the target. **DOM-01 creates that app** (the inscription app — which still owns NO rights
table and NO activator; that is DOM-02), so the test's premise is obsolete. The file lives in a
**forbidden root** for this packet, so it was **NOT edited**: it is recorded as request **A0-04**.
The failure only appears when the app is registered (V17); the `commerce`+`pagos` suites stay
green with the default settings (V16). **No assertion of `commerce`, `pagos`, `eventos` or
`usuarios` was touched.** Zero frozen files modified. No commit created. `git stash` not invoked.

**Byproducts removed:** the migration rehearsal used a SQLite file **outside the repository**
(`%TEMP%\opencode\dom01_migraciones.sqlite3`) and it was deleted; no `*.sqlite3` remains under
`Aplicacion/backend/` (databases are a forbidden artifact).

**Changed files:** created `Aplicacion/backend/modules/salesianos_fest/**` (63 files) and
`evidence/domains/DOM-01-inscripcion-catalogo-compra.md`; modified `STATE.md` (this transition).
**No shared A0 file was edited** and **no file of `commerce`, `pagos`, `eventos` or `usuarios`
was edited**.

**A0 requests (recorded, NOT applied):** A0-01 register the app + DI module ·
A0-02 register the two controllers · A0-03 add six public error codes (`PAQUETE_NO_VIGENTE`,
`DISCIPLINA_NO_PERMITIDA`, `EQUIPO_DUPLICADO`, `INSCRIPCION_NO_ENCONTRADA`,
`INSCRIPCION_NO_AUTORIZADA`, `COMPRADOR_SIN_PERSONA`) · A0-04 update FND-05's obsolete
assertion · A0-05 ratify the new route `RT-IN-14` and the presenter names in the ledger ·
A0-06 register `salesianos_fest` in `core/contract_versions.py` + the drift test ·
A0-07 sync the physical task matrix (`T-020`, `T-021`) · A0-08 `*.sqlite3` in the target
`.gitignore` · A0-09 decide the wire shape of money (`D-DOM-01-01`).

**Deviations:** `D-DOM-01-01`…`D-DOM-01-11` (evidence file §9) — the money wire shape, the new
provisional route `RT-IN-14`, the server-owned quantity, the recoverable separation of
inscription and purchase, the price-validity rule, one team per discipline, the audit trail,
the module naming, the port/direct asymmetry, the winner-visibility retry and the absence of a
`factories.py`.

**Review slices:** 8 autonomous slices (WU-1…WU-8), ≈ 5 644 lines in total (706 of them the
generated migration, ≈ 1 590 tests); the rollback order is WU-8 → WU-1 (evidence file §10). No
slice mixes unrelated domains.

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/backend/modules/marketplace/**`
(**DOM-04**, A5) was created during this packet — **not touched, not reverted, not merged**, and
its **DOM-04 row was deliberately NOT edited** (DOM-04 owns it). `Aplicacion/frontend/**`
(FND-06 / UI-01A) kept advancing and was not touched; the **FND-06 row was not edited** (A0/A7
owns it). `modules/commerce`, `modules/pagos`, `modules/eventos` and `modules/usuarios` were not
edited; their suites were re-run green (V13…V16).

**Consumers unblocked:** **DOM-02** (the inscription, the purchase of origin `INSCRIPCION`, the
capacity fields and the DB constraints it builds on; the activation adapter and the expansion
route `RT-CM-01` are still DOM-02's) · **API-02 / API-04** (the inscription detail, teams and
the catalogue wrappers) · **UI-02 / UI-03** (the catalogue read models) · **XCT-01 / XCT-03** ·
**VER-01…VER-03**.
**Still blocked on A0:** every consumer that needs the routes served by the project API.

**Next packet:** **DOM-02** — `wave-02-domain-backend/DOM-02-inscription-pool-expansion.md`
(`T-022`, `T-023`) — after A0-01/A0-02.

---

### 2026-11-19 — FND-05 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/fnd-05-apply-progress` (packet-specific) merged into the shared topic `sdd/salesianos-fest-rebuild/apply-progress` · **Owner:** A0
**Original task IDs:** `T-015` (coordinador de activación exactly-once) — 1 of the 54 source-defined IDs (cumulative with GOV-00/01/02, FND-01…FND-04: **15 of 54**)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)
**Freezes respected:** `FREEZE-CM-1.0.0` (FR-04 §2.1 I-2, §2.3, §4) · `RN-C06` · `RN-C08`

| Point | HEAD | Forbidden / frozen-root diff |
|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |

**Delivered:** el coordinador de la activación de derechos —

- **`ActivacionCompra`** (nuevo, dueño `commerce`): la fila de activación con su **clave de
  idempotencia estable**, su **estado** (`PENDIENTE`/`ACTIVADA`/`FALLIDA`), su **incidencia** de
  datos seguros y su **lease** de intento. Restricción única `(compra_id, origen)` en base de
  datos.
- **`CoordinadorActivacionCompra`**: despacha por **origen** a un puerto tipado
  (`IActivadorDominioCompra`), con **cuatro** guardas de exactly-once (restricción única, clave
  UNIQUE, `ACTIVADA` terminal y reserva condicional del intento).
- **`IActivacionCompraService`** (puerto declarado por `pagos`, implementado en `commerce`): el
  eslabón `ActivarDominio` de la secuencia congelada §2.3, ejecutada al final de la confirmación
  del pago.
- **`ActivadorDominioFake`** + `registro_activadores`: dobles de prueba reutilizables por los
  dominios de origen, que **no duplican** reglas de cupos, pases ni stock.
- **17 tests de comportamiento nuevos** (duplicado, retraso, fallo parcial, reintento, reintento
  concurrente, dispatch por origen, seguridad de la incidencia, sin presentación).

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`; settings del
proyecto = `config.settings.test`, SQLite en memoria; rehearsal de migraciones con
`USE_SQLITE=true` + `--settings=config.settings.development`):

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/commerce/tests modules/pagos/tests -q -k "activ or idempot"` | **0** | **29 passed**, 67 deselected |
| V2 | `python -m pytest modules/commerce/tests modules/pagos/tests -q` | **0** | **96 passed** (27 commerce + 69 pagos) |
| V3 | `python -m pytest -q` (raíz del objetivo) | **0** | **294 passed** (277 antes del paquete) |
| V4 | `python -m pytest core/tests -q` | **0** | **100 passed** — baseline FND-01 intacto |
| V5 | `manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| V6 | `manage.py check --settings=config.settings.development` | **0** | `no issues` |
| V7 | `manage.py check` (settings por defecto) | **1** | `DB_NAME` — **baseline conocido, idéntico a FND-01/02/03/04** |
| V8 | `manage.py makemigrations --check --dry-run` (por defecto) | **1** | mismo `DB_NAME` — baseline conocido |
| V9–V12 | `migrate` → `showmigrations commerce` → `migrate commerce zero` → `migrate` | **0** | `Applying commerce.0002_activacioncompra... OK` · `[X] 0002_activacioncompra` · `Unapplying … OK` × 2 · `Applying … OK` |
| V13 | inspección del esquema SQLite | **0** | `UNIQUE ("compra_id","origen")` + `clave UNIQUE` presentes |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **vacío** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **vacío** — raíces congeladas intactas |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — sin commit creado |
| R4 | `git stash` | — | **nunca invocado** |

**Changed files (this packet — 22 paths, all inside the allowed edit roots):** created
`Aplicacion/backend/modules/commerce/domain/models/activacion_compra.py`,
`…/commerce/domain/services/core/{activacion_compra_core_service,coordinador_activacion_compra,registro_activadores_compra}.py`,
`…/commerce/infrastructure/services/activacion_compra.py`,
`…/commerce/migrations/0002_activacioncompra.py`,
`…/commerce/tests/fixtures/activacion_fakes.py`,
`…/commerce/tests/integration/test_activacion_compra.py`,
`…/pagos/tests/integration/test_pago_activacion.py`;
modified `…/commerce/{admin.py,di.py,models.py}`,
`…/commerce/domain/{constants.py,ports/__init__.py,schemas/compra_schemas.py}`,
`…/commerce/domain/models/__init__.py`,
`…/commerce/infrastructure/services/__init__.py`,
`…/commerce/tests/conftest.py`,
`…/pagos/{di.py}`,
`…/pagos/domain/ports/__init__.py`,
`…/pagos/domain/schemas/pago_schemas.py`,
`…/pagos/domain/services/flujos/pago_confirmacion_flujo.py`,
`…/pagos/tests/integration/test_pago_confirmacion.py` (**docstring only**),
`evidence/foundations/FND-05-rights-activation.md`, `STATE.md` (esta transición).
**Ningún archivo compartido de A0 fue editado** (`config/settings/base.py`, `config/api.py`,
`core/exceptions.py`) y **ninguna migración de FND-04 se editó**.

**Known baseline failures:** unchanged — las dos puertas `manage.py` con los settings por defecto
(V7/V8) siguen siendo ambientales (`DB_NAME`), idénticas a FND-01/FND-02/FND-03/FND-04.
**Regressions:** none. Zero frozen files modified. No commit created. `git stash` not invoked.
**Byproduct removed:** la rehearsal de migraciones creó `Aplicacion/backend/db.sqlite3` (471 040 B);
se **borró** al terminar (las bases de datos son un artefacto prohibido).

**Deviations:** `D-FND-05-01` (el veredicto operativo no refleja el estado de la activación: publicar
lo cambiaría y es de XCT-03) · `D-FND-05-02` (clave de activación derivada, no UUID de cliente) ·
`D-FND-05-03` (coordinador sync, sin `transaction.atomic()` explícito) · `D-FND-05-04` (registro de
activadores único del proceso, no binding de DI) · `D-FND-05-05` (una fila de activación por pago
confirmado, aunque no haya activador registrado) · `D-FND-05-06` (docstring de un test de FND-04
aclarado; sus aserciones NO se tocaron).

**A0 requests (recorded, NOT applied):** `*.sqlite3` en el `.gitignore` del objetivo · sincronizar la
matriz física `00-matriz-tareas.md` (fila `T-015`) · decidir el canal de publicación del estado de
la activación (`D-FND-05-01`).

**Unresolved decisions carried forward:** `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 ·
D-A…D-E · `GOV-02-UX-01`…`05` · `GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` ·
`P-01`…`P-12` · `GOV-01-OPEN-09` · `GOV-01-OPEN-10` · `NEW-FND03-01`…`04` · `D-FND-02-01`…`09` ·
`D-FND-04-01`…`06` · **new:** `D-FND-05-01`…`08`.

**Consumers unblocked:** **DOM-02 / DOM-03 / DOM-06** (implementan `IActivadorDominioCompra` y
registran su activador; el contrato, la clave, el contexto, el resultado y el doble de prueba ya
están hechos) · **DOM-01 / DOM-04 / DOM-05 / DOM-07 / DOM-08** · **XCT-03** (la incidencia de
activación ya es visible y reintentable) · **API-03 / API-04** · **VER-01…VER-03** · **UI-01…UI-05**
(la UI del comprador puede mostrar "Pago confirmado; estamos resolviendo la activación de tu
compra" en cuanto se decida `D-FND-05-01`).

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/frontend/**` (**FND-06 /
UI-01A**) siguió avanzando durante el paquete: **no se tocó, no se revirtió y no se fusionó**, y
la fila `FND-06` del tablero **no** se editó (A0/A7 es su dueño). `modules/eventos/**` y
`modules/usuarios/**` tampoco se tocaron; sus suites se re-ejecutaron verdes dentro de V3.

**Next packet:** **DOM-02**, **DOM-03** y **DOM-06**, después de sus prerrequisitos de dominio.

---

### 2026-11-19 — DOM-04 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/dom-04-apply-progress` (packet-specific) merged into the shared topic `sdd/salesianos-fest-rebuild/apply-progress` · **Owner:** A5
**Original task IDs:** `T-040` — 1 of the 54 source-defined IDs (cumulative with GOV-00/01/02, FND-01…FND-05 and DOM-01: **18 of 54**)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)
**Freezes respected:** `FREEZE-MD-1.0.0` (FR-06) · `FREEZE-ED-1.0.0` (FR-02) · `FREEZE-PS-1.0.0` (FR-07) · `FREEZE-ENV-1.0.0` (FR-01) · `FREEZE-TC-1.0.0`

| Point | HEAD | Forbidden / frozen-root diff |
|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |

**Delivered:** el catálogo de la tienda y el **protocolo multipart corregido**.

- **`Aplicacion/backend/modules/marketplace/`** (módulo nuevo, 57 archivos): `CategoriaProducto` y
  `Producto` con alcance de `eventos.Edicion` (`PROTECT`), slug único **por edición** ·
  `ProductoImagen` con `ImageField`, `orden` canónico (`orden ASC, id ASC`), `es_principal`
  **explícito** con `UniqueConstraint` condicional y `texto_alternativo` · `precio` /
  `precio_oferta` (`Decimal`) y `oferta_inicia` / `oferta_termina` (`datetime` **tipados**) ·
  `ProductoCoreService` (escritura + proyección), `ProductoMediaService` (escritura y limpieza de
  archivos), `ProductoFlujo` (async, único lugar con `transaction.atomic()`),
  `ProductoOrchestrator` (fachada delgada) · el **puerto** `IAlcanceEdicion` (lo declara el
  dominio) con su adaptador `AlcanceEdicionEventos` en `infrastructure/services/` · el
  `ProductoHydrator` que implementa el protocolo · los cuatro presenters del ledger
  (`ProductoPresenter`, `ProductoListaPresenter`, `ProductoDetallePresenter`,
  `CategoriaListaPresenter`) con los schemas compuestos en los tres bloques de
  `SCHEMA_DRY_INTENTION` · `SCHEMA_VERSION = "1.0.0"` · `di.py` · `admin.py` · migración
  `0001_initial` · **35 tests**.
- **Rutas del ledger:** `RT-MD-01` `POST /marketplace/productos` (multipart `data` + `files`,
  permiso `Administrador`) · `RT-MK-01` `GET /marketplace/categorias` · `RT-MK-02`
  `GET /marketplace/productos` (paginación congelada) · `RT-MK-03`
  `GET /marketplace/productos/{slug}`. **Ninguna ruta provisional fue registrada** — el registro
  es de A0 (A0-03).
- **Protocolo `PROTO-MD-1.0.0`** (implementa `FREEZE-MD-1.0.0` §2.4): campo `data` con el JSON
  del payload y campo `files` con las partes `<token>___<realname>`; tokens `file_<uuid>`;
  **matching exactamente una vez** (cada token aparece una sola vez en el payload, así que la
  imagen principal y el texto alternativo viajan DENTRO del objeto de la imagen); rechazos
  `MEDIA_TOKEN_NO_RESUELTO` (400) · `MEDIA_ARCHIVO_HUERFANO` (400) · `MEDIA_TOKEN_DUPLICADO`
  (400) · `MEDIA_TIPO_NO_PERMITIDO` (400) · `MEDIA_TAMANO_EXCEDIDO` (413). El módulo **consume**
  `core/media.py` y **no** usa los helpers heredados `core/types.py` (que interpolan texto y no
  usan los códigos del catálogo).
- **UNA representación del archivo:** `ImagenProductoUploadData` viaja del borde HTTP al flujo
  dentro de `ProductoCreateData.imagenes`; no hay un segundo argumento de archivos en ninguna
  firma. Las fechas son `datetime` y el dinero es `Decimal` de punta a punta.
- **Limpieza en los TRES caminos obligatorios (FR-06 §2.5):** validación fallida (no se escribe
  nada) · rollback de transacción (los archivos escritos se borran) · reemplazo (el archivo
  anterior se borra DESPUÉS de que el nuevo quedó persistido) · borrado de entidad (se borran sus
  archivos). Residuo cero demostrado: tras cada rechazo y cada rollback el volumen queda **sin
  archivos**.
- **El precio efectivo lo decide el DOMINIO** (`precio_efectivo` + `oferta_activa` viajan en el
  result); el cliente NUNCA lo calcula. El catálogo **no inventa existencias**: `Producto` no
  declara stock (es de DOM-06).

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`; settings de
verificación `modules.marketplace.tests.settings_overlay`, SQLite en memoria):

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/marketplace/tests -q -k "producto or imagen or multipart"` | **0** | **35 passed** |
| V2 | `python -m pytest modules/marketplace/tests -q` | **0** | **35 passed** |
| V3 | `manage.py makemigrations --check --dry-run` | **0** | `No changes detected` |
| V4 | `manage.py check` | **0** | `System check identified no issues` |
| V5–V8 | `migrate` → `showmigrations marketplace` → `migrate marketplace zero` → `migrate` (replay, base SQLite en archivo) | **0** | `Applying marketplace.0001_initial... OK` · `[X] 0001_initial` · `Unapplying … OK` · `Applying … OK` |
| V9 | inspección del esquema SQLite real | **0** | 2 UNIQUE `(edicion_id, slug)` + 1 UNIQUE **parcial** `WHERE es_principal = 1` |
| V10 | `python -m pytest core/tests -q` | **0** | **100 passed** — baseline FND-01 intacto |
| V11 | `python -m pytest -q --ignore=modules/salesianos_fest` (raíz completa del objetivo) | **0** | **329 passed** (294 de FND-05 + 35 de DOM-04), 0 fallos |
| V12 | `python -m pytest -q` (raíz completa, sin `--ignore`) | **2** | `RuntimeError: … salesianos_fest … isn't in an application in INSTALLED_APPS` — **DOM-01 en curso**, NO es una regresión de este paquete (ver abajo) |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **vacío** |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **vacío** — raíces congeladas intactas |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — sin commit creado |
| R4 | `git stash` | — | **nunca invocado** |
| R5 | `Test-Path Aplicacion/backend/media` · `db.sqlite3` · `test_db.sqlite3` | **0** | `False` `False` `False` — sin residuos; el volumen real nunca se escribió |

**Known baseline failures:** unchanged — las dos puertas `manage.py` con los settings por defecto
(`config.settings.production`, sin `DB_NAME`) siguen siendo ambientales, idénticas a
FND-01…FND-05 y a DOM-01. **New:** V12 — la app `modules.salesianos_fest` (DOM-01, trabajo
concurrente) todavía no está registrada en `INSTALLED_APPS`, porque el registro permanente es una
petición a A0 (igual que la de DOM-04). Misma clase que el V2 de FND-02; **no es un defecto de este
paquete**.

**Regressions:** none. Cero archivos congelados modificados. Los archivos compartidos de A0
(`config/api.py`, `config/settings/base.py`, `core/exceptions.py`, `core/responses.py`,
`core/permissions.py`, `core/media.py`, `conftest.py`) **NO** fueron editados por este paquete: sus
`mtime` son del 2026-11-18 20:03–22:13 (paquetes anteriores), anteriores a esta sesión. No commit
creado. `git stash` no invocado.

**Byproducts removed:** la rehearsal de migraciones usó un SQLite **fuera del repositorio**
(`%TEMP%\opencode\marketplace_rehearsal.sqlite3`) y se borró; el media de test vive en
directorios temporales de pytest, que se borran solos. Ningún `*.sqlite3` ni `media/` queda bajo
`Aplicacion/backend/`.

**Changed files:** created `Aplicacion/backend/modules/marketplace/**` (57 files) and
`evidence/domains/DOM-04-marketplace-catalog-media.md`; modified `STATE.md` (this transition).
**No shared A0 file was edited** and **no file of `commerce`, `pagos`, `eventos`, `usuarios` or
`salesianos_fest` was edited**.

**A0 requests (recorded, NOT applied):** A0-01 register the app in `INSTALLED_APPS` ·
A0-02 register the DI module · A0-03 register `ProductoController` in `config/api.py` ·
**A0-04 add the `default` entry to `STORAGES`** (without it `default_storage` does not exist and
**no module can write media**: `InvalidStorageError`) · A0-05 ratify the money wire shape (the
`Decimal` travels as a decimal STRING; `ser_json_decimal_to_float` does not exist in Pydantic v2 —
the same finding as DOM-01's `D-DOM-01-01` / A0-09) · A0-06 catalog nine new public error codes ·
A0-07 retire `modules/marketplace/tests/settings_overlay.py`.

**Deviations:** `D-DOM04-01`…`D-DOM04-12` (evidence file §8) — the port/adapter for the edition
scope, the resolution level used for writes, the server-owned edition, the gallery payload shape,
the explicit principal image, the absence of stock, the four implemented routes, the non-use of the
legacy hydration helpers, the overlay replicating the `STORAGES` fix, the money wire shape, the
allowed offer above the normal price, and the absence of an HTTP route for categories.

**Open decisions carried forward:** `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 · D-A…D-E ·
`GOV-02-UX-01`…`05` · `GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` · `P-01`…`P-12` ·
`GOV-01-OPEN-09` · `GOV-01-OPEN-10` · `NEW-FND03-01`…`04` · `D-FND-02-01`…`09` · `D-FND-04-01`…`06` ·
`D-FND-05-01`…`08` · `D-DOM-01-01`…`11` · **new:** `D-DOM04-01`…`12` · **new:** `OD-DOM04-01`…`05`.

**Consumers unblocked:** **DOM-05** (pedido: catálogo, precios autoritativos, galería ordenada y
`PRODUCTO_NO_DISPONIBLE` ya existen) · **DOM-08** (patrocinadores: el mismo protocolo y los mismos
códigos de media, ya consumidos por DOM-04) · **DOM-06** (inventario: `Producto` no declara stock,
así que DOM-06 puede añadirlo con una migración aditiva) · **API-03 / API-04** (el espejo Zod
necesita el tipo del dinero ratified) · **XCT-03** (protocolo, limpieza y códigos de media
implementados y probados) · **UI-02…UI-05** (`SHOP-01` / `SHOP-02` ya tienen contrato de lectura) ·
**VER-01…VER-03**.
**Still blocked on A0:** todo consumidor que necesite las rutas servidas por la API del proyecto.

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/backend/modules/salesianos_fest/**`
(**DOM-01**) y `Aplicacion/frontend/**` (**FND-06 / UI-01A**) **no fueron tocados, revertidos ni
fusionados**. La fila `DOM-01` del tablero se conservó intacta; DOM-01 ya había registrado este
paquete como trabajo concurrente observado.

**Next packet:** **DOM-05** — `wave-02-domain-backend/DOM-05-marketplace-order.md` — después de A0-01…A0-04.

---

### 2026-11-19 — FND-01 → A0 reconciliation of DOM-01 / DOM-04 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** packet-specific topic
`sdd/salesianos-fest-rebuild/fnd-01-a0-reconciliation-dom01-dom04` · **Owner:** A0
**Nature:** **serialized A0 reconciliation** of the completed domain packets DOM-01 and DOM-04 — **NOT
a new packet**; no domain behaviour was broadened. **Full report:**
`evidence/foundations/FND-01-a0-reconciliation-dom01-dom04.md`.

**Original task IDs:** none new. It discharges the pending A0 requests of DOM-01 (`T-020`, `T-021`) and
DOM-04 (`T-040`) that live in A0's shared files, plus FND-01's own media/storage contract.

**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged;
**no commit created**, `git stash` never invoked)

| Point | HEAD | Forbidden / frozen-root diff |
|---|---|---|
| reconciliation start | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |
| reconciliation close | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |

**Delivered (A0 shared files only):**

- `config/settings/base.py` — the two completed apps registered in the order of the **migration
  graph**: `modules.eventos` → `modules.usuarios` → `modules.pagos` → `modules.commerce` →
  **`modules.salesianos_fest`** (DOM-01, after `commerce` as its A0-01 asks) → **`modules.marketplace`**
  (DOM-04) · the two DI modules `SalesianosFestModule` and `MarketplaceModule` added to
  `NINJA_EXTRA["INJECTOR_MODULES"]` · **the `STORAGES` defect FIXED**: the persistent local `default`
  backend (`django.core.files.storage.FileSystemStorage`, i.e. Django's own default over the
  persistent `MEDIA_ROOT`) now sits next to `staticfiles`. **No cloud storage, no remote path and no
  credential was invented** (DOM-04 A0-04).
- `config/api.py` — the three completed controllers registered through the FND-01 extension point:
  `registrar_controladores(EdicionController, PersonaController, PagosController, CatalogoController,
  InscripcionController, ProductoController)`. **No unfinished domain controller is registered.**
- `core/exceptions.py` — **15 safe public error codes** merged (6 DOM-01 + 9 DOM-04; DOM-04's own
  prose adopted verbatim). **No raw error leaks; no handler was weakened.**
- `core/contract_versions.py` — `"salesianos_fest": "1.0.0"` registered (the key is the **physical
  module name**, which is what the module itself documents; the ledger names the *domain*
  `inscripciones`), plus the drift test extended to the two new modules.
- `core/tests/integration/test_registration_extension.py` — the closed controller list, the allowed
  prefixes and the **exact route inventory** updated (15 domain routes), plus two new tests that
  prove **no unfinished app and no unfinished DI module is registered**.
- `core/tests/integration/test_exceptions_public_catalog.py` — parametrized tests for the 15 new
  codes: catalogued, fixed prose (no interpolation), and status matching the domain class.
- `core/tests/integration/test_media_storage.py` (**created**) — the focused persistent-media /
  `default_storage` write-and-cleanup test: the `default` entry exists, is local, resolves, writes
  inside the volume and leaves **ZERO residue** on a temporary media root. **The real volume is never
  touched**: after the whole run `Aplicacion/backend/media` does not exist.
- `modules/pagos/tests/integration/test_pago_confirmacion.py` — the **obsolete** FND-05 assertion
  `assert not apps.is_installed("modules.salesianos_fest")` replaced by the **real invariant**: the
  activation of the purchase stays `PENDIENTE` and `esta_activada is False`. **No domain behaviour
  changed** (DOM-01 A0-04 / R-DOM-01-01, closed).

**Live surface (proof):** 15 domain routes (`/api/ediciones/actual` · `/api/personas/**` ·
`/api/pagos/**` · `/api/catalogo/**` · `/api/inscripciones/**` · `/api/marketplace/**`) + the 3 JWT
routes. **Nothing else.**

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`): `check` and
`makemigrations --check --dry-run` with the **default** settings **1 (`DB_NAME` — the known
environmental baseline, identical to FND-01…FND-05, DOM-01 and DOM-04; NOT a regression)** · the
same two gates with an explicit SQLite settings module **0** (`no issues` / `No changes detected`) ·
integrated `migrate` from an empty DB **0** (incl. `marketplace.0001_initial` and
`salesianos_fest.0001_initial`) · `migrate` repeat **0** (idempotent) · `showmigrations` **0** (all
`[X]`) · `migrate <app> zero` × 6 **0** (reversible) · `migrate` replay **0** ·
**`python -m pytest -q` (whole target root) 0 (430 passed; final run 432 passed)** · `core/tests` **0 (156)** · focused
registration + OpenAPI + versions + media + catalog **0 (102)** · DOM-01 suite with its overlay
**0 (45)** · DOM-04 suite with its overlay **0 (35)** · the corrected `pagos` file **0 (14)** · the
focused media/storage test **0 (7)** · forbidden-root diff **0 (empty)** · frozen-root diff **0
(empty)** · `git rev-parse HEAD` **0 (unchanged)** · `git stash` **never invoked** · residue sweep
**0** (no `*.sqlite3`, no `db.sqlite3`, no `media/`; the rehearsal DB lived outside the repo and was
deleted).

**Known baseline failures:** unchanged — the two default-settings `manage.py` gates remain
environmental (`DB_NAME`). **New:** none. **Regressions:** none; the `R-DOM-01-01` regression
introduced by DOM-01 is **closed**.

**A0 requests accepted:** DOM-01 A0-01 · A0-02 · A0-03 · A0-04 · A0-06 · DOM-04 A0-01 · A0-02 ·
A0-03 · **A0-04** · A0-06.
**A0 requests deferred (recorded, NOT applied):** the **money wire shape** (`OD-A0R2-01` — the
contract does **not** freeze it, so it stays OPEN and nothing was guessed) · the **`RT-IN-14` ledger
ratification** (`OD-A0R2-02` — the ledger is GOV-01 contract evidence, outside the allowed roots) ·
the retirement of `modules/marketplace/tests/settings_overlay.py` (domain package, outside the
allowed roots; it is idempotent and was left untouched) · `*.sqlite3` in the target `.gitignore` ·
the physical task-matrix sync (`T-020`, `T-021`, `T-040`) · `GOV-01-OPEN-09` · `GOV-01-OPEN-10`.

**Deviations:** `D-A0R2-01`…`06` (evidence file §10) — the `salesianos_fest` overlay adapted, not
retired · the `marketplace` overlay untouched · the ledger ratification not performed ·
`core/responses.py` and `core/types.py` untouched (the money shape is an open decision) ·
`core/permissions.py` and `core/capacidades.py` untouched · the obsolete assertion replaced by a
**stronger** invariant.

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/frontend/**` (FND-06 / UI-01A
and the concurrent UI work) was **not** touched, reverted or merged, and its board rows were **not**
edited (A0/A7 owns them). The domain internals of `salesianos_fest`, `marketplace`, `commerce`,
`pagos`, `eventos` and `usuarios` were **not** edited (except the single obsolete assertion in
`pagos`, explicitly requested); their suites were re-run green.

**Consumers unblocked:** **DOM-02** · **DOM-05** · **DOM-06** · **DOM-08** · **API-02 / API-03 /
API-04** · **XCT-03** · **UI-02…UI-05** · **VER-01…VER-03**.

**Next packet:** **DOM-02** — *Capacity pool, assignment and expansion* (`T-022`, `T-023`) — and
**DOM-05** — *Marketplace order* (`RT-CM-03`).


---

### 2026-11-19 — DOM-02 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** #11279 (topic `sdd/salesianos-fest-rebuild/dom-02-apply-progress`) · **Owner:** A3
**Original task IDs:** `T-022` (pool y asignación · `RN-I03`-`RN-I05` · `FL-05`), `T-023` (ampliación y beneficios · `RN-I06` · `FL-04`) — 2 of the 54 source-defined IDs (cumulative with GOV-00/01/02, FND-01…FND-05 and DOM-01: **19 of 54**)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)
**Full report (canonical):** `evidence/domains/DOM-02-pool-asignacion-ampliacion.md`

| Point | HEAD | Forbidden / frozen-root diff |
|---|---|---|
| packet start | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |
| packet close | `f3df5401c56b41c340f257e67d5a306904a9e670` | empty |

**Delivered:** the **pool de cupos** of an inscription — the paid/assigned/available arithmetic computed by the server, the **atomic assignment** (a conditional `UPDATE`, not a read-modify-write), **add / move / remove** with eligibility, duplicate, ownership, edition and race protection, the **separate expansion purchase** (`RT-CM-01`) and the **idempotent capacity activation** through FND-05's `IActivadorDominioCompra` port.

- **New models** — `Participacion` (the pool; `edicion` and `disciplina` are REDUNDANT so the overlap constraint needs no JOIN) · `ActivacionCapacidad` (the activation record; its `clave` is UNIQUE and is the exactly-once authority) · `BeneficioConcedido` (`UNIQUE (inscripcion, beneficio)` — a `FIJO_INICIAL` benefit can only be granted once).
- **New services** — `CapacidadCoreService` (the counters) · `PoolCoreService` · `BeneficioCoreService` · `ActivadorInscripcion` · `PoolFlujo` · `CompraCuposFlujo` · `PoolOrchestrator` · `CompraCuposOrchestrator` · `PoolSelector` · `domain/referencia.py` (the CLOSED intent-reference format and its parser) · a new port `IResolucionPersonaService` with its adapter over `usuarios.PersonaSelector`.
- **New routes (frozen)** — `RT-IN-03` (GET pool) · `RT-IN-05` (POST participant) · `RT-IN-06` (DELETE participant) · `RT-CM-01` (POST expansion purchase), with `PoolPresenter` + `PoolOut` and `CompraCuposPresenter` + `CompraCreadaOut`. `SCHEMA_VERSION` of `salesianos_fest`: `1.0.0` → **`1.1.0`** (MINOR, additive).
- **57 new behaviour tests** (44 integration + 13 e2e), all green. Module suite: **102 passed** (45 of DOM-01 + 57 of DOM-02).

**The locking strategy:** the counters move with a CONDITIONAL `UPDATE` (`WHERE cupos_asignados < cupos_pagados`), not with `select_for_update` — which raises `NotSupportedError` on SQLite. The condition travels INSIDE the statement, so the database, not the application, decides who gets in (`QA-I05`). The `CHECK (cupos_asignados <= cupos_pagados)` of DOM-01 is the second line of defence. **Declared limitation (`D-DOM-02-08`):** the per-team cap is checked inside the transaction but is NOT serialized.

**Commands / exit codes** (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`):

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `python -m pytest modules/salesianos_fest/tests -q -k "cupo or asignacion or ampliacion"` | **0** | **59 passed** · 43 deselected |
| V2 | `python -m pytest modules/salesianos_fest/tests -q` | **0** | **102 passed** |
| V3 | `manage.py makemigrations --check --dry-run --settings=config.settings.test` | **1** | **`marketplace`** (DOM-05, concurrent) has pending migrations; **zero** pending for `salesianos_fest` |
| V3b | `manage.py makemigrations salesianos_fest --check --dry-run --settings=config.settings.test` | **0** | `No changes detected in app 'salesianos_fest'` |
| V4 | `manage.py check --settings=config.settings.test` | **0** | `no issues` |
| V5/V6 | `manage.py check` / `makemigrations --check --dry-run` (default settings) | **1** | `DB_NAME` — identical environmental baseline (FND-01…FND-05, DOM-01) |
| V7–V10 | `migrate` → `showmigrations` → `migrate zero` → `migrate` (replay) | **0** | `[X] 0001_initial` · `[X] 0002_pool_capacidad`; reversible and reproducible |
| V11 | SQLite schema inspection | **0** | 2 partial UNIQUE indexes on `fest_participacion` · `clave … UNIQUE` · `UNIQUE (inscripcion_id, beneficio_id)` · `CHECK (cupos_asignados <= cupos_pagados)` |
| V12 | `python -m pytest core/tests -q` | **1** | **156 passed · 2 failed** — both are A0-owned and requested (below) |
| V13–V16 | `eventos` / `usuarios` / `commerce`+`pagos` / `marketplace` suites | **0** | 63 · 35 · 96 · 35 passed — every baseline intact |
| V17 | `python -m pytest -q` (whole target root) | **1** | **487 passed · 2 failed** — the 2 are A0-owned |
| R1–R3 | frozen-root and other-owner diffs | **0** | empty |
| R4 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — no commit |
| R5 | `git stash` | — | **never invoked** |
| R6 | residue sweep under `Aplicacion/backend` | **0** | no `*.sqlite3`, no `db.sqlite3`, no `media/` |

**Known failures:** **2 A0-owned** (not defects of this packet, `core/tests/**` is a forbidden root): the frozen route inventory does not include the 4 new routes (`A0-DOM02-01`) and the global version registry still says `1.0.0` while the module declares `1.1.0` (`A0-DOM02-02`). **Environmental baseline:** the two default-settings `manage.py` gates stay `DB_NAME`. **Concurrent, not a regression:** `makemigrations --check --dry-run` fails because `modules/marketplace` (DOM-05) has models without a migration — that migration belongs to DOM-05 and this package did NOT generate it.

**Regressions:** none. Zero frozen files modified. No commit created. `git stash` not invoked.

**Changed files (this packet — 43 paths, all inside the allowed edit roots):** created 24 files under `Aplicacion/backend/modules/salesianos_fest/**` (3 models + 1 reference module + 1 selector + 3 core services + the activator + 2 flows + 2 orchestrators + 1 result module + 1 DTO module + 2 HTTP schema modules + 2 presenters + the generated migration + 4 integration test files + 1 e2e test file) and `evidence/domains/DOM-02-pool-asignacion-ampliacion.md`; modified 18 files of the same module (the vocabulary, the exceptions, the port, the re-exports, `apps.py`, `admin.py`, `di.py`, the controller, the presenters' index, the schema version, the adapters, the fixtures) and `STATE.md` (this transition). **No shared A0 file was edited** — `core/**`, `config/**` and the frozen ledger are requested by evidence (A0-DOM02-01…A0-DOM02-10).

**A0 requests:** A0-DOM02-01 frozen route inventory (+4) · A0-DOM02-02 version registry `1.1.0` (+ its two assertions) · A0-DOM02-03 public error catalog (8 codes) · A0-DOM02-04 ratify `RT-CM-01` in the ledger · A0-DOM02-05 ratify the presenter equivalence of `RT-IN-03`/`05`/`06` · A0-DOM02-06 register those routes in `SH-05` · A0-DOM02-07 `*.sqlite3` in `.gitignore` · A0-DOM02-08 sync `00-matriz-tareas.md` (`T-022`, `T-023`) · A0-DOM02-09 whether `RegistroActivadoresCompra.limpiar()` must restore the domain registrations · A0-DOM02-10 confirm the `MAX_CUPOS_POR_AMPLIACION` number with product.

**Physical task matrix still unsynced:** `00-matriz-tareas.md` rows `T-022` and `T-023` still read `pending` — the matrix is outside every packet's allowed edit roots (same precedent as DOM-01 and DOM-04). **A0 must sync it explicitly.**

**Review slices:** 16 autonomous slices, ≈ 5 367 lines (316 of generated migration, ≈ 1 392 of tests). Rollback order: WU-16 → WU-1. No slice mixes an unrelated domain.

**Rollback:** `manage.py migrate salesianos_fest zero` → delete the created files and revert the modified ones → restore `STATE.md` and the Engram topics. Rollback point `f3df5401c56b41c340f257e67d5a306904a9e670` (no commit; do not revert or reset it). **The commercial and payment history is preserved**: this rollback never deletes a purchase, an order or a transaction. **Already-audited facts are not deleted**: `ActivacionCapacidad` and `BeneficioConcedido` are the acts of what was applied — a live-data rollback compensates with a new entry, it does not erase history (`RN-C08`, `DEC-06`).

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/backend/modules/marketplace/**` (**DOM-05**) was ACTIVE during this packet — **not touched, not reverted, not merged**; its models have a pending migration (which is why V3 exits 1) and its suite was re-run green (35 passed); **its board row was deliberately NOT edited** (A5 owns it). `Aplicacion/frontend/**` (FND-06 / UI-01A and the concurrent UI work) was **not touched** and **its board rows were not edited** (A0/A7 owns them). The domain internals of `commerce`, `pagos`, `eventos` and `usuarios` were **not** edited; their suites were re-run green.

**Consumers unblocked:** **DOM-07** (T-050…T-052) · **API-02 / API-04** (four live routes to mirror: `PoolOut`, `CompraCreadaOut`; they need the 1:1 Zod mirror of `SCHEMA_VERSION = 1.1.0`) · **API-05** · **XCT-03** (T-084, depends on T-023) · **UI-02 / UI-03 / UI-04** (the paid/assigned/available trio and the impediment list are published by the backend) · **DOM-03 / DOM-06** (the per-origin activator pattern with a reference implementation) · **VER-01…VER-03**.

**Next packet:** **DOM-07** — *Competencias* (`T-050`…`T-052`) — and **API-02**, which already has the four routes to mirror. The presenter and schema freeze of DOM-02 is RECORDED (`1.1.0`).

---

### 2026-11-19 — DOM-05 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/dom-05-apply-progress` (packet-specific) · **Owner:** A5
**Original task IDs:** `T-041` — 1 of the 54 source-defined IDs (cumulative with GOV-00/01/02, FND-01…FND-05, DOM-01, DOM-02 and DOM-04: **20 of 54**)
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (HEAD al inicio de la ronda; **no commit created**, `git stash` never invoked)
**Full report (canonical):** `evidence/domains/DOM-05-marketplace-order.md`
**Freezes respected:** `FREEZE-CM-1.0.0` (FR-04) · `FREEZE-MD-1.0.0` (FR-06) · `FREEZE-ED-1.0.0` (FR-02) · `FREEZE-PS-1.0.0` (FR-07) · `FREEZE-ENV-1.0.0` (FR-01) · `FREEZE-TC-1.0.0`

| Point | HEAD | Forbidden / frozen-root diff |
|---|---|---|
| packet start | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` | empty |
| packet close | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` | empty |

**Delivered:** the **marketplace order** — the `Pedido` aggregate with its
`PedidoDetalle`, the FROZEN price snapshot, the commerce adapter and the typed
presenters.

- **New models** — `Pedido` (edition scope `PROTECT`, buyer `Persona` `PROTECT`,
  `compra` FK → `commerce.Compra` `PROTECT`+null, `estado`
  `PENDIENTE|PAGADO|CANCELADO`, `estado_entrega` `PENDIENTE|ENTREGADO`, frozen
  `total`, `moneda`, unique private `token`, `huella` of the INTENT, stable
  `referencia`) · `PedidoDetalle` (concept, quantity, `precio_unitario` and
  `precio_aplicado` frozen at order time) · migration `0002_pedido_pedidodetalle_and_more`.
- **Three DISTINCT facts** (`RN-M07`, `QA-M04`, `RN-C08`): the ORDER state, the PAYMENT state (projected from `commerce.Compra`, never stored twice) and the DELIVERY state (owned by `DOM-06`, NEVER touched here). **Paid is NOT delivered**: `marcar_estado` writes only `["estado", "updated_at"]`.
- **Immutable history** (`RN-M03`): the detail freezes the catalogue price and the applied price; a later offer changes neither the detail nor the total. The purchase is opened from the SAME frozen lines, never from the current catalogue.
- **Server-validated quantities/prices** (`RN-C02`): the payload carries NO amount and NO edition; the price is resolved against the catalogue and frozen; the total is DERIVED (`Σ cantidad × precio_aplicado`) with the same expression `commerce` uses, so the two totals cannot diverge.
- **Rejections** — `PEDIDO_ITEMS_MIXTOS` (mixed pass/registration items) · `PEDIDO_ITEM_NO_PERMITIDO` (a pass or an enrolment) · `PEDIDO_CANTIDAD_INVALIDA` (quantity out of range; the DOMAIN owns the rule, not the wire) · `PRODUCTO_NO_ENCONTRADO` (404) · `PRODUCTO_NO_DISPONIBLE` (409, other edition or retired product) · `MODULO_NO_HABILITADO` (409) · `COMPRADOR_SIN_PERSONA` (422) · `PEDIDO_NO_AUTORIZADO` (403) · `PEDIDO_NO_ENCONTRADO` (404).
- **Idempotency** (`RN-C03`, `RN-C04`, FR-04 I-4): the INTENT is the SHA-256 fingerprint of (type, product, quantity) — NOT of the price. A retry RECOVERS the same order with its frozen snapshot; the partial UNIQUE `(comprador, edicion, huella) WHERE estado='PENDIENTE'` is the authority.
- **The commerce boundary** — the port `ICommerceMarketplaceService` (create-or-reuse + read the purchase facts) with the adapter `CommerceMarketplaceAdapter`, which TRANSLATES `PENDIENTE|PAGADA|CANCELADA` into `PENDIENTE|CONFIRMADO|NO_COMPLETADO`. The domain never imports `commerce`; the adapter is built by a lazy DI factory that consumes `commerce`'s own injector bindings.
- **Routes** — `RT-CM-03` `POST /marketplace/pedidos` (`JWTAuth` + `IsAuthenticated`) · `RT-MK-04` `GET /marketplace/pedidos/{token}` (public; the token IS the credential). Presenters `PedidoPresenter` / `PedidoSeguimientoPresenter` with `PedidoCreadoOut` / `PedidoSeguimientoOut`; they expose the three states and a SAFE next action, and NO provider internals (no technical reference, no attempt, no evidence).
- **`SCHEMA_VERSION` of `marketplace`: `1.0.0` → `1.1.0`** (additive MINOR: two routes, five wrappers).

**Static review (18 checks, §4 of the evidence):** the order and the purchase
totals use the SAME expression; the commerce DTOs match field by field; the
scope resolution returns the `Edicion` MODEL (which owns `modulo_habilitado`);
the selectors return lists (F-26); the `IntegrityError` is caught OUTSIDE the
atomic block; `update_fields` never touches `estado_entrega`; the field
lengths fit their sources; the subclass code of `PedidoNoAutorizadoError` is the
one that travels; a broken credential answers 401 (and NOT `OptionalJWTAuth`'s
silent downgrade to "guest").

**Corrections applied (7, §4.1):** the quantity range moved from the wire to
the domain · `POST /pedidos` declares `auth`+`permissions` explicitly ·
`_actor_opcional` uses `core.security.JWTAuth` once · `SCHEMA_VERSION` bumped
· the test URLconf registers `PedidoController` · the orchestrator fixture
declares `db` · two new fixtures for the `COMPRADOR_SIN_PERSONA` and
`MODULO_NO_HABILITADO` scenarios.

**Commands / exit codes:** **NONE.** Runtime verification is **DEFERRED BY
EXPLICIT USER INSTRUCTION** for this packet and every future apply:
tests may be written but not executed; no `pytest`, no `manage.py check`, no
`makemigrations`, no `migrate`, no typecheck, no lint; no global Python and no
`.venv` Python; any later Python verification needs explicit authorisation and
**must use `uv run`**. The future commands are listed in §6.1 of the evidence
(`uv run python -m pytest modules/marketplace/tests -q`, `uv run python manage.py
makemigrations --check --dry-run`, `uv run python manage.py check`, the
migrate/showmigrations/replay rehearsal on a SQLite file OUTSIDE the repo, the
`core`/`commerce`/`pagos` baseline suites, the whole-root suite, and the
forbidden-root/HEAD/stash diff checks) — **none of them was executed**.

**The SQLite lock observed in the interrupted round was NOT debugged.** It was
not reproduced, not instrumented and **no code change was made to satisfy
it**. A static observation is recorded (the shared `config/settings/test.py`
uses `"isolation_level": None`, i.e. autocommit, on the test SQLite) as a
HYPOTHESIS for A0 and for the verification phase, not as a diagnosis: that
file is a shared root this package may not edit.

**Known baseline failures:** unchanged — the two default-settings `manage.py`
gates stay environmental (`DB_NAME`), identical to FND-01…FND-05, DOM-01,
DOM-02 and DOM-04. **New:** A0-02 — the module declares `SCHEMA_VERSION =
1.1.0` while the global registry still says `1.0.0`, so A0's drift test will
fail until the registry is updated. **Same class as DOM-02's A0-DOM02-02**:
`salesianos_fest` already declares `1.1.0` with the registry at `1.0.0`, so a
single registry update (`"salesianos_fest": "1.1.0"` + `"marketplace":
"1.1.0"`) closes both.

**Regressions:** none. Zero frozen files modified. No commit created.
`git stash` never invoked.

**Changed files (this packet):** created `Aplicacion/backend/modules/marketplace/tests/integration/test_pedido_reglas.py`, `…/tests/e2e/test_pedido_controller.py`, `…/tests/fixtures/pedido_fixtures.py`, `…/tests/integration/test_pedido_snapshot.py` (preserved from the interrupted round) and `evidence/domains/DOM-05-marketplace-order.md`; modified `…/di.py`, `…/infrastructure/services/comercio_adapter.py`, `…/domain/schemas/pedido_schemas.py`, `…/presentation/controllers/pedido_controller.py`, `…/presentation/schemas/{__init__,pedido_schemas}.py`, `…/tests/{conftest,factories,urls_marketplace}.py` and `STATE.md` (this transition). **No shared A0 file was edited by this packet.**

**A0 requests (recorded, NOT applied):** A0-01 register `PedidoController` in `config/api.py` (BLOCKING) · A0-02 `SCHEMA_VERSIONS["marketplace"] = "1.1.0"` (BLOCKING for the drift test) · A0-03 catalogue 5 new public error codes · A0-04 ratify `RT-MK-04` in the ledger + `SH-05` · A0-05 ratify the scope of `RT-CM-03` (`autenticado_o_invitado` vs `autenticado`) · A0-06 add the two routes to the frozen route inventory (15 → 17) · A0-07 `*.sqlite3` in `.gitignore` · A0-08 sync `00-matriz-tareas.md` (`T-041`).

**Physical task matrix still unsynced:** `00-matriz-tareas.md` row `T-041` still reads `pending` — the matrix is outside every packet's allowed edit roots (same precedent as DOM-01, DOM-02 and DOM-04). **A0 must sync it explicitly.**

**Review slices:** 1 autonomous slice (the DOM-05 order slice), ≈ 1 500 lines of production code and ≈ 900 lines of test source. The rollback boundary is the whole `DOM-05` slice: revert the marketplace `DOM-05` files and the migration `0002_*`; `commerce`, `pagos`, `eventos` and `usuarios` are never touched.

**Rollback:** `uv run python manage.py migrate marketplace zero` (only if A0 authorises it) → delete the migration `0002_*` and the `DOM-05` files of `modules/marketplace/` → revert the modified module files → restore `STATE.md` and the Engram topics. Rollback point `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (no commit; do not revert or reset it). **The commercial and payment history is preserved**: this rollback never deletes a purchase, a payment order or a transaction.

**Concurrent overlap observed (untouched, not merged):** `Aplicacion/backend/modules/salesianos_fest/**` (**DOM-02**, A3) and `Aplicacion/frontend/**` (FND-06 / UI-01A, another agent) were **not touched, reverted or merged**, and **their board rows were deliberately NOT edited** (DOM-02 and A0/A7 own them). The domain internals of `commerce`, `pagos`, `eventos` and `usuarios` were **not** edited: this package CONSUMES them through the port and the adapter. During this packet the tree also gained **concurrent work from other agents** — a new auth module in `modules/usuarios/**` (FND-03A: `AuthController`, `auth_flujo`, `auth_orchestrator`, `auth_schemas`, its fixtures and three integration test files) registered in `config/api.py`, plus `Aplicacion/frontend/src/**` changes. **None of it was touched, reverted or merged by DOM-05**, and the `usuarios` and frontend board rows were not edited.

**Consumers unblocked:** **DOM-06** (the frozen order interface, the `estado_entrega` field and the `EstadoEntregaPedido` vocabulary; PROVISIONAL — pending verification) · **API-03** (the two new wrappers to mirror, needing the ratified `SCHEMA_VERSION = 1.1.0`) · **UI-02 / UI-03 / UI-04** (the paid/pending-delivery distinction and the safe next action) · **XCT-01 / XCT-03** · **VER-01…VER-03**.

**Next packet:** **DOM-06** — *Reserva de inventario y entrega* — after the deferred verification of DOM-05 (`uv run`, §6.1 of the evidence) is authorised and executed.

---

### 2026-11-19 — DOM-03 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/dom-03-apply-progress` (packet-specific) · **Owner:** A4
**Original task IDs:** `T-030`, `T-031`, `T-032` — 3 of the 54 source-defined IDs
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (unchanged; **no commit created**, `git stash` never invoked)

**ESTADO: `verification_required`** — la verificación en runtime está **DIFERIDA por instrucción explícita del usuario** (preferencia `workflow/salesianos-sdd-apply-verification-deferred`): las pruebas se ESCRIBEN pero **NO se ejecutan**; prohibido `pytest` / `manage.py check` / `makemigrations` / `migrate` / typecheck / lint; prohibido el Python global y el de `.venv`; toda verificación Python posterior exige **autorización explícita** y **debe usar `uv run`**. **Comandos ejecutados: NINGUNO.** Los comandos futuros con `uv run` están listados en el informe canónico §6.1.

**Delivered:** the pass/benefit domain in `Aplicacion/backend/modules/salesianos_fest/**` — **six new models** (`Pase`, `PasePrecio`, `CompraPase`, `PaseBeneficiario`, `CortesiaPase`, `ActivacionPase`), the edition-scoped pass catalog, the guest purchase (`RT-CM-02`, FROZEN), beneficiary assignment and revocation (`RT-PS-03`…`RT-PS-05`, `RT-RT-03`, FROZEN), the audited courtesy (`RT-PS-08`) and the admin listings (`RT-PS-06`, `RT-PS-07`), plus the migration `0003_pases_derechos`.

**The central design — ONE right, TWO origins.** `PaseBeneficiario` is the effective right and its `origen` column discriminates `COMPRA` / `CORTESIA` (`RN-P02`), so the "no duplicate right" rule is a SINGLE partial unique constraint (`UNIQUE (edicion, pase, persona) WHERE estado='ACTIVO'`) that covers BOTH origins: a courtesy cannot duplicate a purchase, by construction.

**The three rules that were frozen and honoured.** `RN-P02` — a `PENDIENTE` purchase grants NOTHING: the lot is only assignable after the FND-05 activation. `RN-P05` — `CortesiaPase` has **no column at all** towards `commerce.Compra`, `pagos.OrdenPago` or `pagos.TransaccionPago`: the ABSENCE of the link is the guarantee that no S/ 0 charge is simulated. `RN-P04` — buyer and attendee are different columns and can be different people. `RN-P08` — revocation is permanent, audited and idempotent.

**The activation (FND-05) without touching the coordinator.** `ActivadorPase` implements the FROZEN port `IActivadorDominioCompra` for `OrigenCompra.PASE` and is registered in `apps.py::ready()` next to DOM-02's activator. `commerce`'s internals (`CoordinadorActivacionCompra`, `ActivacionCompra`, `RegistroActivadoresCompra`) were **NOT edited**: the package CONSUMES the port.

**The credential of the guest link.** The token is generated with `secrets`, compared in constant time, scoped to ONE purchase, carried in the `X-Pase-Token` header (never in the query string, never in a listing) and revocable/expirable. A missing or invalid credential is **401**, an insufficient one is **403**. The DNI is NEVER a credential (`RN-U04`).

**Tests:** **41 new test functions** (10 purchase + 14 beneficiary + 8 courtesy + 5 activation + 14 e2e) — **WRITTEN, NOT executed**. No doubles: the production services are resolved by the real injector.

**Static source review:** 33 checks (§5 of the evidence) + 5 corrections applied. **No runtime command was executed**; the review is the substitute for the runtime while the execution is deferred.

**A new fact (F-60):** `Q.__init__` SORTS the `kwargs` and does NOT sort the positional arguments. A `Q` written in a migration with positional tuples has its children in a different order than the model's `Q`, and the autodetector reads that as an ALTERED constraint (it emits `RemoveConstraint` + `AddConstraint` and the drift never settles). **The correct form in a migration is to write the `Q` with keyword arguments.**

**Concurrent change observed and reconciled (NOT merged, NOT reverted):** during the packet a background process ran `makemigrations` and generated a `0004` from this package's models. It contradicted the hand-written `0003` (it re-added the constraints `0003` already creates and renamed two indexes to the names the models already use). It was **reconciled into `0003`** and the intermediate file removed (`D-DOM03-08`) — two contradictory migrations would have broken `migrate`. **The reconciliation is static reasoning and is NOT runtime-verified** (§6.2 of the evidence, point 1). `Aplicacion/backend/modules/marketplace/**` (**DOM-05**, A5), `Aplicacion/frontend/**` (FND-06 / UI-01A / concurrent work) and the internals of `commerce`, `pagos`, `eventos` and `usuarios` were **not touched, reverted or merged**, and **their board rows were not edited**. The DOM-01/DOM-02 code inside `salesianos_fest` was **preserved**: every change is additive.

**A0 requests (recorded, NOT applied):** A0-01 register `PaseController` + `AdminPaseController` in `config/api.py` (BLOCKING) · A0-02 `SCHEMA_VERSIONS["salesianos_fest"] = "1.2.0"` (BLOCKING for the drift test) · A0-03 catalogue 9 new public error codes · A0-04 catalogue 5 more (auth/authorization/courtesy) · A0-05 ratify `RT-PS-01`…`RT-PS-08` in the ledger + `SH-05` · A0-06 ratify the `X-Pase-Token` channel · A0-07 route inventory +8/+10 · A0-08 `*.sqlite3` in `.gitignore` · A0-09 add a courtesy-revocation route to the ledger (`FL-07` paso 4 has none) · A0-10 sync `00-matriz-tareas.md` (`T-030`, `T-031`, `T-032`) · A0-11 unify the TWO definitions of "administrator" in the project.

**Open decisions left OPEN (never guessed):** `PD-01` (BOX — **not modelled at all**) · `PD-02` / `GOV-01-OPEN-08` (revocation policy — the INTERFACE is frozen, the unit is **not** released and **not** reassignable) · `PD-03` (ticket unit vs partial consumption — the quantity fields exist so the frozen shape does not change) · `GOV-01-OPEN-05` (the exact expiry policy; a conservative declared value) · which pass types admit courtesy (**not invented**) · the courtesy-revocation route (**not invented**).

**Rollback:** `uv run python manage.py migrate salesianos_fest 0002_pool_capacidad --settings=…` (only if A0 authorises it) → delete the 26 created files and revert the 13 modified ones → restore `STATE.md` and the Engram topics. Rollback point `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (no commit; do not revert or reset it). **The commercial and payment history is preserved**: `ActivacionPase` and `CortesiaPase` are ACTAS and are never deleted.

**Consumers unblocked:** **API-03** (the eight pass routes + `RT-CM-02` + `RT-RT-03` and their wrappers) · **XCT-01** (`PaseBeneficiario` as the right that `validaciones` consults) · **XCT-03** (payment / delivery / consumption kept apart) · **UI-02 / UI-03 / UI-04** · **API-05**. All **PROVISIONAL** — pending the deferred verification.

**Next packet:** **API-03** and **XCT-01** — after the deferred verification of DOM-03 with `uv run` is authorised and executed.

---

### 2026-11-19 — DOM-07 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/dom-07-apply-progress` (packet-specific) · **Owner:** A6
**Original task IDs:** `T-050`, `T-051`, `T-052` — 3 of the 54 source-defined IDs
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (unchanged; **no commit created**, `git stash` never invoked)
**Freezes respected:** `FREEZE-ENV-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-TC-1.0.0` · `FREEZE-PS-1.0.0`

**ESTADO: `verification_required`** — la verificación en runtime está **DIFERIDA por instrucción explícita del usuario** (preferencia `workflow/salesianos-sdd-apply-verification-deferred`): las pruebas se ESCRIBEN pero **NO se ejecutan**; prohibido `pytest` / `manage.py check` / `makemigrations` / `migrate` / typecheck / lint; prohibido el Python global y el de `.venv`; toda verificación Python posterior exige **autorización explícita** y **debe usar `uv run`**. **Comandos ejecutados: NINGUNO.** Los comandos futuros con `uv run` están listados en el informe canónico §7.

**Delivered:** the competitions domain in `Aplicacion/backend/modules/competencias/**` (73 Python files) — `Competencia` (edición + disciplina + nombre + estado + fecha), `CompetenciaEquipo` (participación con semilla MANUAL), `Ronda`, `Encuentro` (participantes, horario, bye, marcador, ganador autoritativo, enlace + slot, ganador propagado) and `AuditoriaOperacion` (el ACTA), all with the `version` counter of the optimistic lock.

**THE CENTRAL DESIGN — ONE operational source and ONE presenter.** `frontend/05` §1/§3 and `FL-11` step 6 require that the list, the agenda and the bracket share ONE source: `domain/selectors/proyeccion.py` is the ONLY place where a model is projected, `EncuentroResult`/`EncuentroOut` is the CANONICAL shape of an encounter, and `CompetenciasPresenter` is the ONLY presenter. The e2e test asserts that the encounter of the detail and the one of the bracket have the SAME keys.

**THE ELEGIBILITY IS CONSUMED BY PORT, NOT REIMPLEMENTED (`RN-K01`, `QA-K01`).** `modules.salesianos_fest` owns the inscription, the team, its discipline and the roster pool. The `IEquipoElegibleService` port (already present in this packet's prior partial work, PRESERVED untouched) is implemented by `EquipoElegibleAdapter`, which READS the owner's models and TRANSLATES their verdict: the verdict carries the `MotivoNoElegibilidad` CODE and the domain turns it into an exception with a public code — the client never guesses the reason. Precedence is fixed and documented: `EQUIPO_NO_ENCONTRADO` → `EDICION_DISTINTA` → `DISCIPLINA_DISTINTA` → `DISCIPLINA_INACTIVA` → `INSCRIPCION_CANCELADA` → `EQUIPO_NO_ACTIVO` → `SIN_PLANTILLA` → `PLANTILLA_INCOMPLETA` → `ELEGIBLE`.

**NO OVERLAP (`RN-K03`, `QA-K02`).** A team never plays two encounters at the same time, not even in two competitions of the same edition (it is the same physical team). Intervals are SEMI-OPEN, a CANCELLED encounter does not reserve the window, and the concurrency control is the OPTIMISTIC LOCK (`expected_version`) — NOT `select_for_update`, which SQLite does not support (`F-55`).

**THE PREVIEW NEVER WRITES (`QA-K04`).** `previsualizar_avance` and `previsualizar_correccion` are simulations: no transaction, no write, no version bump. Only the confirmation writes, inside its own atomicity, with its audited motive and its optimistic lock.

**THE CORRECTION DECLARES ITS IMPACT (`QA-K03`).** The correction computes a PLAN over the chain of descendants and publishes, per descendant, what happens to it (`reemplaza`, `limpia_slot`, `limpia_resultado`, `bloqueado`). A descendant that already elapsed BLOCKS the cascade: without an explicit `override` AND the acceptance of the calculated impact, NOTHING is written. The correction NEVER overwrites a MANUAL placement: it only touches slots whose value was PROPAGATED (`ganador_propagado`).

**Routes (16).** Five reads (`/competencias`, `/competencias/agenda`, `/competencias/{id}`, `/competencias/{id}/cuadro`, `/competencias/{id}/equipos-elegibles`) and eleven writes. The permissions use the centralised authority (`RequireAdminVer` to read, `RequireCompetenciasEscribir` to write); the JWT answers BEFORE the authorization (401 before 403).

**Presenter version:** `CompetenciasPresenter` (`presentation/presenters/competencias_presenter.py`) · `SCHEMA_VERSION` of `competencias` = **`1.0.0`** (the module's FIRST contract). The global registry `core.contract_versions.SCHEMA_VERSIONS["competencias"]` does NOT exist yet → A0 request and a pending drift.

**Tests:** **43 new test functions** (9 eligibility + 6 overlap + 5 bye + 4 preview + 5 progression + 4 stale-version + 6 correction + 8 e2e) — **WRITTEN, NOT EXECUTED**. No doubles: the production services are resolved through the real injector, and the eligibility adapter reads the owner's REAL models.

**Static source review:** 33 checks (§6 of the evidence) + **7 corrections applied** (the optimistic lock is taken ONCE per edit command; the `estado` field was added to `EncuentroActualizarData`; `ESTADO` and `CANCELACION` were added to the audited-actions vocabulary; `CompetenciaEquipoNoEncontradaError` was added; `_validar_orden` now excludes the participation and not the competition; the result flow compares the state BEFORE mutating it; the de-scheduling has a "nothing to remove" guard). **No runtime command was executed**: the review is the substitute for the runtime while the execution is deferred.

**Migration:** `migrations/0001_initial.py` — **HAND-WRITTEN** (the verification is deferred, so `makemigrations` could not be run). It reproduces the models exactly and respects the `F-60` learning: the `Q` objects with several arguments are written with NAMED arguments and the `Lower` is imported by its full path. **Its equivalence with the models is STATICALLY reasoned and NOT runtime-verified**: `pytest.ini` uses `--nomigrations`, so the suite does not exercise it (V4 of §7 of the evidence is the command that would settle it).

**A0 requests (recorded, NOT applied):** A0-01 register `modules.competencias` in `LOCAL_APPS` (after `salesianos_fest`) · A0-02 register `CompetenciasModule` in `INJECTOR_MODULES` · A0-03 register `CompetenciasController` in `config/api.py` (until then NO route exists) · A0-04 `SCHEMA_VERSIONS["competencias"] = "1.0.0"` · A0-05 catalogue the 21 new public codes in `core/exceptions.py` (while they are not catalogued the global catalogue returns the GENERIC per-status message: safe, but it does not explain the reason) · A0-06 ratify the 16 routes in the ledger and in `SH-05` · A0-07 sync `00-matriz-tareas.md` (`T-050`…`T-052`) · A0-08 `*.sqlite3` in `.gitignore`.

**Deviations:** `D-DOM07-01`…`09` (evidence §10) · **open decisions:** `OD-DOM07-01`…`05` (evidence §11) — the state transition of the COMPETITION, the INVALIDATION of a round, the PUBLIC bracket route, the audited `detalle` surface and the duration/format of the bracket are **NOT invented**.

**Rollback:** `uv run python manage.py migrate competencias zero --settings=…` (only if A0 authorises it) → delete the 73 created files and the evidence → restore `STATE.md` and the Engram topics. Rollback point `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (no commit; do not revert or reset it). **The audited history is preserved**: an acta is a FACT, and a corrected advance stays in the history as a compensating, versioned operation.

**Concurrency recorded.** `Aplicacion/backend/modules/marketplace/**` (**DOM-05**, A5), `Aplicacion/backend/modules/salesianos_fest/**` (**DOM-01/DOM-02/DOM-03**, A3/A4) and `Aplicacion/frontend/**` (**FND-06 / UI-01A**, A0/A7) were **not touched, reverted or merged**, and **their board rows were deliberately NOT edited**. The internals of `commerce`, `pagos`, `eventos` and `usuarios` were **not** edited: this packet CONSUMES them through the ports. The prior partial work of this packet (the `IEquipoElegibleService` port, the models, the constants, the exceptions and the DTOs) was **PRESERVED**: every change is ADDITIVE.

**Consumers unblocked:** **API-05** (the 16 routes and their wrappers, the single presenter, the single encounter shape and the eligibility verdict) · **UI-05** (the operational detail, the agenda and the bracket read from the same source) · **XCT-01 / XCT-03** · **VER-01…VER-03**. All **PROVISIONAL** — pending the deferred verification and A0's permanent registration.

**Next packet:** **API-05** — after DOM-07's deferred verification with `uv run`, which today requires the user's explicit authorisation.

---

### 2026-11-19 — DOM-06 → completed

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/dom-06-apply-progress` (packet-specific) merged into the shared topic `sdd/salesianos-fest-rebuild/apply-progress` · **Owner:** A5
**Original task IDs:** `T-042`, `T-043` — 2 de los 54 IDs del plan (acumulado con GOV-00/01/02, FND-01…FND-05 y DOM-01…DOM-05: **22 de 54**)
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (HEAD al inicio de la ronda; **no commit created**, `git stash` never invoked)
**Full report (canonical):** `evidence/domains/DOM-06-inventory-reservation-delivery.md`
**Freezes respetados:** `FREEZE-CM-1.0.0` (FR-04) · `FREEZE-MD-1.0.0` (FR-06) · `FREEZE-ED-1.0.0` (FR-02) · `FREEZE-PS-1.0.0` (FR-07) · `FREEZE-ENV-1.0.0` (FR-01) · `FREEZE-TC-1.0.0`

> **ESTADO: `completed`.** A diferencia de `DOM-03` y `DOM-05`, este paquete
> **SÍ ejecutó** la verificación en runtime: la instrucción vigente del
> usuario para esta ronda pide pruebas FOCALIZADAS con `uv run` y descarta la
> preferencia antigua de "verificación diferida" (`#11299`). La suite del
> módulo es **VERDE** (97 passed) y las puertas de Django son verdes.

**Delivered:** el **inventario** de la tienda en
`Aplicacion/backend/modules/marketplace/**` — la bitácora INMUTABLE de
movimientos, las reservas que sostienen la anti-sobreventa, el efecto de stock
de un pago confirmado y el acta de entrega.

- **`PD-05` DECIDIDO: el stock es POR EDICIÓN.** El inventario vive en el
  producto, y el producto pertenece a UNA edición (`Producto.edicion`
  obligatoria, slug único por edición). El clave es el **producto** y,
  transitivamente, la **edición**: no existe pool compartido entre ediciones.
- **TRES hechos separados (`RN-M06`):** `stock` (físico) · `reservado`
  (apartado por pedidos pendientes) · `disponible = stock − reservado`. El
  servidor los calcula; el cliente no inventa disponibilidad.
- **BITÁCORA INMUTABLE (`RN-M04`):** `MovimientoInventario` con producto,
  cantidad CON SIGNO, motivo, referencia de origen **ÚNICA** y actor. Ni
  `save()` ni `delete()` los modifican: una corrección es una **REVERSA**
  compensatoria (`REVERSION` con el signo contrario y `compensatorio`).
- **UNA SALIDA SIN VENTA NO ES UNA COMPRA (`RN-M05` · `QA-M02`):** la
  operación administrativa ajusta el stock y escribe el movimiento; **no**
  crea `Compra`, ni `OrdenPago`, ni `Pedido` (lo comprueba la prueba
  contando las filas de `commerce` y `pagos`: 0 y 0).
- **ANTI-SOBREVENTA (`RN-M06` · `QA-M01`):** reserva temporal con la
  SENTENCIA CONDICIONAL de `DOM-02` (`F-55`): `UPDATE … SET reservado =
  reservado + N WHERE id = ? AND stock >= reservado + N`. Si actualiza cero
  filas, no hay disponibilidad y el pedido se rechaza con
  `STOCK_INSUFICIENTE` (409). La reserva se crea **dentro de la misma
  transacción** que el alta del pedido. **NO** se usa `select_for_update`.
- **EL PAGO DESCUENTA UNA SOLA VEZ (`FR-04` I-2, I-3):**
  `ActivadorMarketplace` implementa el puerto **CONGELADO** de `commerce`
  (`IActivadorDominioCompra`) para `OrigenCompra.MARKETPLACE` y se registra en
  `apps.py::ready()`. Doble red: la transición `ACTIVA → CONFIRMADA` de la
  reserva es CONDICIONAL, y el movimiento de venta tiene una REFERENCIA
  ÚNICA. **Los interiores de `commerce` y de `pagos` NO se editaron**: el
  paquete CONSUME el puerto.
- **LA ENTREGA ES UN HECHO POSTERIOR (`RN-M07` · `QA-M04`):** exige un pedido
  PAGADO, mueve **SÓLO** `estado_entrega`, crea **UN** acta (UNIQUE por
  pedido) con actor, cantidad y detalle, **no vuelve a mover el stock** y es
  **IDEMPOTENTE y REINTENTABLE** (confirmar dos veces devuelve el mismo
  acta). Entrega **COMPLETA**, no parcial: `PD-03` sigue ABIERTO.
- **Rutas (5, PROVISIONALES):** `RT-MK-08` (inventario) · `RT-MK-09`
  (movimiento) · `RT-MK-12` (reversa) · `RT-MK-10` (cola de entregas) ·
  `RT-MK-11` (confirmar entrega). Las tres primeras vienen de `SH-05` §1.6;
  las dos últimas son **nuevas** y se piden como ratificación (A0-04,
  A0-05). **NO se registran en `config/api.py`** (es de A0): se registran
  SÓLO en el URLconf de test, como hizo `DOM-03`.
- **`SCHEMA_VERSION` de `marketplace`: `1.1.0` → `1.2.0`** (MINOR aditivo).

**Commands / exit codes (workdir `Aplicacion/backend`, siempre `uv run --group dev`):**

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V0 | `pytest modules/marketplace/tests -q` (LÍNEA BASE) | **0** | **69 passed** — el baseline de `DOM-04`/`DOM-05` |
| V1 | `pytest modules/marketplace/tests -q` (tras el paquete) | **0** | **97 passed** (69 previos + 28 nuevos) — **sin regresiones** |
| V2 | `manage.py makemigrations marketplace` | **0** | generó `0003_*` (la migración coincide con los modelos **por construcción**) |
| V3 | `manage.py makemigrations marketplace --check --dry-run --settings=…overlay` | **0** | `No changes detected in app 'marketplace'` |
| V4 | `USE_SQLITE=true SQLITE_PATH=:memory: manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| V5 | `manage.py migrate --settings=…overlay` (SQLite en fichero FUERA del repo) | **0** | `Applying marketplace.0003_… OK` |
| V6 | `manage.py showmigrations marketplace` | **0** | `[X] 0001_initial` · `[X] 0002_…` · `[X] 0003_…` |
| V7 | `manage.py migrate marketplace zero` → `migrate marketplace` | **0** | reversible y reproducible |
| V8 | inspección del esquema SQLite real | **0** | CHECK `reservado <= stock` · UNIQUE `(pedido_id, producto_id)` · UNIQUE `pedido_id` (entrega) · UNIQUE `referencia` (movimiento) |
| R1 | `git status --short -- Aplicacion/backend/modules/marketplace` | **0** | sólo ficheros de `marketplace` |
| R2 | `git rev-parse HEAD` | **0** | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — sin commit |
| R3 | `git stash` | — | **never invoked** |
| R4 | hash de `db.sqlite3` antes/después de `manage.py check` | **0** | **sin cambios** (es un artefacto preexistente de trabajo concurrente) |

**Baseline conocido (NO es una regresión de este paquete):**
`makemigrations --check --dry-run` **sin** filtro de app falla porque
`modules/salesianos_fest` tiene un cambio de modelo pendiente de `DOM-03`
(`0004_alter_comprapase_token_revocado_en`). Esa raíz es PROHIBIDA para este
paquete: se reporta como **A0-07** sin tocar nada.

**Regressions:** none. Zero frozen files modified. No commit created.
`git stash` never invoked.

**Hechos nuevos** (`F-70`…`F-74`; `F-65`…`F-69` ya las usó DOM-07 el mismo
día): la sentencia condicional con la ARITMÉTICA de dos columnas propias
extiende el patrón de `DOM-02` · un `CheckConstraint` con `F()` es válido en
Django 5.2 y genera `CHECK ("reservado" <= ("stock"))` en SQLite · `auto_now`
NO dispara en `QuerySet.update()` (hay que fijar `updated_at` a mano) · el
`SELECT` puede filtrar por `stock__gte=F("reservado") + N` · `makemigrations`
es más seguro que la migración a mano (el autodetector la hace coincidir con
los modelos POR CONSTRUCCIÓN), con el límite de los 30 caracteres del nombre
de índice (`models.E034`).

**Changed files (this packet):** created **20** files under
`Aplicacion/backend/modules/marketplace/**` (3 models + 1 migration + 1 DTO
module + 1 result module + 1 selector + 2 core services —incluido el
activador— + 1 flow + 1 orchestrator + 1 HTTP schema module + 1 presenter +
1 controller + 1 fixture module + 5 test files) and
`evidence/domains/DOM-06-inventory-reservation-delivery.md`; modified **17**
files of the same module (the vocabulary, the exceptions, the re-exports,
`Producto`, the selectors, the order core/flow/orchestrator, `apps.py`,
`admin.py`, `di.py`, the presenters' index, the schema version, the fixtures,
the factories and the test URLconf) and `STATE.md` (this transition).
**No shared A0 file was edited** — `config/api.py`, `core/**`,
`modules/commerce/**`, `modules/pagos/**`, `modules/salesianos_fest/**` and
`modules/competencias/**` are requested by evidence or forbidden.

**A0 requests (recorded, NOT applied):** A0-01 register `InventarioController`
(and `PedidoController`) in `config/api.py` (BLOCKING) · A0-02
`SCHEMA_VERSIONS["marketplace"] = "1.2.0"` (the registry already read `1.2.0`
when the suite ran — it was updated in parallel; confirm it corresponds to
this packet) · A0-03 catalogue the 8 new public codes (`STOCK_INSUFICIENTE`
409 · `MOVIMIENTO_INVENTARIO_NO_ENCONTRADO` 404 · `MOVIMIENTO_INVENTARIO_INVALIDO`
422 · `MOVIMIENTO_INVENTARIO_INMUTABLE` 409 · `PEDIDO_NO_PAGADO` 409 ·
`PEDIDO_NO_ENTREGABLE` 409 · `PEDIDO_SIN_RESERVA` 409 ·
`RESERVA_NO_CONFIRMABLE` 409) · A0-04 ratify `RT-MK-08`…`RT-MK-12` in the
ledger and in `SH-05` · A0-05 reconcile with `RB-07` (the shared validation
service owns the ticket consumption; this packet freezes the store-scoped
delivery contract) · A0-06 add the routes to the frozen route inventory ·
A0-07 **`modules/salesianos_fest` has a pending model change** (DOM-03) ·
A0-08 `*.sqlite3` in `.gitignore` · A0-09 sync `00-matriz-tareas.md` (`T-042`,
`T-043`) · A0-10 the reservation-expiry policy.

**Physical task matrix still unsynced:** `00-matriz-tareas.md` rows `T-042` and
`T-043` still read `pending` — the matrix is outside this packet's allowed
edit roots (same precedent as DOM-01, DOM-02, DOM-04 and DOM-05). **A0 must
sync it explicitly.**

**Review slices:** **1** autonomous slice (the DOM-06 inventory slice), ≈
**3 460 changed lines** (≈ 2 656 in new files, of which ≈ 1 200 are tests and
≈ 330 are the generated migration, plus ≈ 780 in modified files). **The packet
artifact carries NO `Review Workload Forecast`**, so it required no chain or
size decision; the ACTUAL size nevertheless exceeds the 400-line review
budget by ≈ 8× and is reported to A0 as a finding (§7 of the evidence). The
review boundary is the whole slice; the rollback boundary is the migration
`0003_*` plus the 20 created and 17 modified module files.

**Rollback:** `uv run python manage.py migrate marketplace 0002_pedido_pedidodetalle_and_more --settings=…` (only if A0 authorises it) → delete the 20 created files and revert the 17 modified ones → restore `STATE.md` and the Engram topics. Rollback point `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (no commit; do not revert or reset it). **The commercial and payment history is preserved**: this rollback never deletes a purchase, a payment order or a transaction. **The audit ledger is never deleted by a code rollback**: with live data, a rollback is a COMPENSATING entry, not an erasure (`RN-M04`).

**Concurrency recorded.** `Aplicacion/backend/modules/competencias/**`
(**DOM-07**, A6) and `Aplicacion/frontend/**` (FND-06 / UI-01A) were ACTIVE
during this packet: **not touched, not reverted, not merged**, and **their
board rows were deliberately NOT edited**. The internals of `commerce`,
`pagos`, `eventos` and `usuarios` were **not** edited: this package CONSUMES
them through the port. `core/contract_versions.py` (A0-owned) was updated to
`marketplace: 1.2.0` **in parallel** by another actor during the packet
window: the drift test came out GREEN without this package editing it.

**Consumers unblocked:** **API-03** (the inventory and delivery wrappers to
mirror) · **XCT-01** (the delivery acta and the ticket consumption, `T-081`)
· **XCT-03** (payment, delivery and consumption kept apart) ·
**UI-02 / UI-03 / UI-04** (the "paid / pending delivery / delivered" trio) ·
**UI-05** · **VER-01…VER-03**.

**Next packet:** **API-03** and **XCT-01** — after A0 ratifies the provisional
routes (A0-01, A0-04) and the delivery presenter is frozen.

---

### 2026-11-19 — Reconciliación formal del estado (A0 · coordinador) → FND-06 `verification_required` · DOM-08 `verification_required` · DOM-06 `completed` (confirmado)

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/apply-progress` (#11227, upsert) · **Owner:** A0 (coordinador)
**Nature:** **reconciliación formal de estado y evidencia** — NO es un paquete nuevo, NO implementa comportamiento, NO toca código. Sólo confirma o corrige el estado de los paquetes **ya entregados** (FND-01…FND-06 · DOM-01…DOM-08) contra la evidencia de runtime ya registrada. **Full report:** `evidence/reconciliation/2026-11-19-state-reconciliation.md`.
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (`betha 5`, HEAD sin cambios) · **no commit created**, `git stash`/`reset`/`checkout` **nunca invocados**

**Regla aplicada:** el estado se determina **exclusivamente** por evidencia de runtime ya registrada. **Ninguna fila se promovió a `completed` sin una suite verde ejecutada.** Los paquetes con evidencia de runtime ausente o diferida se mantienen en `verification_required` y se listan abajo.

#### Transiciones de estado (exactas)

| Packet | Antes | Después | Base de la decisión |
|---|---|---|---|
| FND-06 | `pending` (evidencia: `none`) | **`verification_required`** | Pasada de implementación aplicada (#11303, 26 ficheros en `Aplicacion/frontend/**`). Único comando de runtime: `npx tsc --noEmit` exit **0**. **Vitest, Biome, `next build`, sonda HTTP y auditoría de navegador de cinco anchos NO se ejecutaron**; 4 pruebas ESCRITAS, NO EXECUTADAS. La divergencia formal #11283 se cierra **hacia `verification_required`**, nunca hacia `completed`. |
| DOM-08 | `pending` (evidencia: `none`) | **`verification_required`** | Implementación entregada (#11347): `Aplicacion/backend/modules/patrocinadores/**` (57 ficheros, 3 363 líneas). **53 pruebas ESCRITAS, NO EJECUTADAS**; comandos ejecutados: NINGUNO (revisión estática de 22 comprobaciones + 5 correcciones). |
| DOM-06 | `completed` | **`completed` (confirmado)** | #11361: suite de `modules/marketplace/tests` **97 passed** (69 previos + 28 nuevos) con `uv run`; `makemigrations --check` 0 · `check` 0 · migrate/showmigrations/rollback/replay 0 · esquema SQLite real inspeccionado (CHECK `reservado <= stock`, UNIQUE de reserva, de acta y de referencia). |
| DOM-03 | `verification_required` | **`verification_required` (confirmado)** | 41 pruebas ESCRITAS, NO EJECUTADAS. Se le añade la reconciliación de cableado de A0 (`evidence/foundations/A0-reconciliation-dom03.md`, comandos NINGUNO): registra `PaseController` + `AdminPaseController`, `SCHEMA_VERSIONS["salesianos_fest"] = 1.2.0`, 17 códigos públicos nuevos, inventario vivo de 31 paths y 86 casos parametrizados ESCRITOS y NO EJECUTADOS. |
| DOM-05 | `verification_required` | **`verification_required` (confirmado)** | 32 pruebas ESCRITAS, NO EJECUTADAS (34 casos colectados, una parametrizada ×3). |
| DOM-07 | `verification_required` | **`verification_required` (confirmado)** | 43 pruebas ESCRITAS, NO EJECUTADAS; migración `0001_initial` escrita A MANO y **sin verificar en runtime** (`pytest.ini` usa `--nomigrations`). |
| FND-01…FND-05 · DOM-01 · DOM-02 · DOM-04 | `completed` | **`completed` (confirmado)** | Suites verdes en su propia ventana: core 156 · eventos 63 · usuarios 35 · commerce+pagos 96 · `salesianos_fest` 102 · marketplace 35 (→ 97 tras DOM-06). |
| UI-01A | **fila ausente** | **`completed` (fila añadida)** | Filas ausentes en este tablero pero presentes en el topic de estado (#11228) y en el índice acumulado (#11227): sub-lote correctivo de UI-01, apply-progress #11256 + bugfix #11257. **UI-01 sigue `pending`** (le faltan los route briefs, la tabla shadcn, los `PROVISIONAL_CONTRACT_FIXTURE`, los diez estados por ruta, los page IDs restantes y la auditoría de navegador). |

#### Test totals (los de cada paquete, en SU propia ventana — no inventados)

| Suite | Resultado | Estado de la evidencia |
|---|---|---|
| `core/tests` | 156 passed | verde |
| `modules/eventos/tests` | 63 passed | verde |
| `modules/usuarios/tests` | 35 passed | verde |
| `modules/commerce/tests` + `modules/pagos/tests` | 96 passed | verde |
| `modules/salesianos_fest/tests` | 102 passed (45 DOM-01 + 57 DOM-02) | verde · **+41 de DOM-03 SIN ejecutar** → 143 funciones escritas |
| `modules/marketplace/tests` | 97 passed (69 DOM-04/05 + 28 DOM-06) | verde (última medición en runtime: DOM-06) |
| `modules/competencias/tests` | 43 funciones ESCRITAS | **NO ejecutadas** |
| `modules/patrocinadores/tests` | 53 funciones ESCRITAS | **NO ejecutadas** |
| `core/tests` (reconciliación A0 de DOM-03) | 86 casos parametrizados ESCRITOS + 7 modificados | **NO ejecutados** |
| Frontend `Aplicacion/frontend` | UI-01A: `vitest` 248 passed / **5 failed** (fallos de token-guard preexistentes, luego corregidos por FND-06 y **nunca re-ejecutados**) · `tsc` 0 · `biome` 0 · `next build` 0 · sonda HTTP todas 200 | la auditoría de navegador de cinco anchos sigue **ABIERTA** |

**Balance en la raíz de destino `Aplicacion/backend`:** **549** funciones de prueba ejecutadas y verdes en su propia ventana · **137** funciones ESCRITAS y NO ejecutadas (41 DOM-03 + 43 DOM-07 + 53 DOM-08) · **86** casos parametrizados compartidos ESCRITOS y NO ejecutados. **686** funciones escritas en total. La suite de la raíz completa **NO se midió** en la ventana de DOM-06 (sólo la suite del módulo): la última cifra global conocida es de la 2ª reconciliación A0 de FND-01 (**432 passed**) y la de DOM-02 (**487 passed · 2 failed**, ambos de A0) — **ninguna de las dos es una medición actual**.

#### Outstanding warnings (open, NOT fixed by this reconciliation)

1. **`modules/salesianos_fest` tiene un cambio de modelo pendiente** (`0004_alter_comprapase_token_revocado_en`) → la puerta global `makemigrations --check --dry-run` **falla** (DOM-06 A0-07). No es regresión de DOM-06, pero bloquea una puerta global verde.
2. **Rutas no registradas (A0-01/A0-02, BLOQUEANTES):** `InventarioController` + `PedidoController` (DOM-06) · `CompetenciasController` (DOM-07) · `PatrocinadorController` (DOM-08). Hasta entonces esas rutas **no existen** en la API del proyecto.
3. **Versiones de contrato sin registrar:** `competencias` (`1.0.0`) y `patrocinadores` (`1.0.0`) — el registro global no las conoce (DOM-07 A0-04, DOM-08 A0-06).
4. **Códigos públicos sin catalogar** (el catálogo devuelve el mensaje genérico por status, que es seguro pero no explica el motivo): 8 de DOM-06 · 21 de DOM-07 · 4 de DOM-08.
5. **Ledger y `SH-05` sin ratificar** (`RT-PS-01`…`RT-PS-08`, `RT-MK-08`…`RT-MK-12`, las 16 de DOM-07, `RT-MD-02`) — son evidencia de contrato congelada de GOV-01/GOV-02: fuera de las raíces permitidas (`OD-A0R3-01`, `OD-A0R2-02`).
6. **`OD-A0R3-03`** (ruta de revocación de CORTESÍA: el ledger no la declara, **no se inventó**) · **`OD-A0R3-02`** (canal `X-Pase-Token` provisional) · **`OD-A0R3-04`** (las DOS definiciones de "administrador") · **`OD-A0R3-05`** (prosa heredada de `PASE_NO_TRANSFERIBLE`).
7. **H-01** (`reconciliación A0 de DOM-03` §8): `PaseNoTransferibleError` está DEFINIDA pero **no se lanza en ninguna parte** — hallazgo de DOMINIO, no tocado.
8. **`core.media.limpiar_archivos_media` deja directorios vacíos** (DOM-08 A0-08) — raíz de A0.
9. **`*.sqlite3` en el `.gitignore` del objetivo** — pendiente desde FND-01 (A0-08 de DOM-06, A0-07 de DOM-07).
10. **Matriz física `00-matriz-tareas.md` sin sincronizar** (`T-010`…`T-060`) — fuera de las raíces de todo paquete; **A0 debe sincronizarla explícitamente**.
11. **FND-06 sin cerrar:** 5 puertas de verificación sin ejecutar + `FND-06-IMP-R-02` (el panel de auth **nunca se vio en un navegador**) + `FND-06-IMP-R-03` (el `GET` de logout muta estado).

#### Divergencias formales cerradas

- **#11283** (FND-06 marcado `completed` en el índice acumulado pero `pending` en el estado): cerrada. El índice acumulado y el topic de estado **ya no** afirma `completed`; FND-06 queda en `verification_required` con la evidencia que la sostiene.
- **DOM-06** figuraba como `pending` en el topic de estado (#11228) pese a estar `completed` en el tablero físico: corregido en el topic.
- **DOM-08** figuraba como `pending` con evidencia `none` en ambos tableros pese a tener informe canónico (#11347) y fichero de evidencia: corregido.
- **UI-01A** no tenía fila en el tablero físico: añadida.

#### Reported, NOT changed (fuera del alcance autorizado)

- **`FND-03A`** (autenticación: `AuthController` registrado en `config/api.py` + 4 paths vivos en el inventario de A0, módulo `modules/usuarios/**`): existe en el árbol y en la evidencia de la reconciliación de DOM-03, pero **NO tiene fila en el tablero ni artefacto de apply-progress**. **No se le asigna estado**: hacerlo sería inventar. **A0 debe abrir su fila y su artefacto.**
- **La matriz física `00-matriz-tareas.md`** y el ledger `route-to-wrapper-ledger.csv`: raíces prohibidas.
- **El árbol congelado** `backend/**`, `frontend/**`, `worker/**`, `proxy/**`, `.opencode/**`, `contract/**`, `Aplicacion/plan/**`: **no se tocaron** (verificado con `git diff --name-only` → vacío).

#### Changed files (this reconciliation — 2 paths, both inside the allowed edit roots)

| File | Action |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | modified (board rows FND-06 / DOM-03 / DOM-06 / DOM-08 / UI-01 / UI-01A + this transition) |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/reconciliation/2026-11-19-state-reconciliation.md` | created (the concise reconciliation record) |

**Engram:** `sdd/salesianos-fest-rebuild/state` (#11228, upsert) · `sdd/salesianos-fest-rebuild/apply-progress` (#11227, upsert). **Ningún otro topic se escribió.**

#### Commands / exit codes

**Comandos de VERIFICACIÓN ejecutados: NINGUNO.** No se ejecutó `pytest`, `manage.py check`, `makemigrations`, `migrate`, `showmigrations`, typecheck, lint, `vitest`, `biome` ni `next build`: la instrucción vigente para esta ronda es la **verificación diferida** (preferencia `workflow/salesianos-sdd-apply-verification-deferred`, #11299) y esta reconciliación **no** pide autorización para ejecutarla. Los estados se deducen **sólo** de la evidencia de runtime ya registrada por cada paquete.

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| C1 | `git rev-parse --show-toplevel` | **0** | raíz del workspace |
| C2 | `git rev-parse HEAD` | **0** | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — **sin commit creado** |
| C3 | `git status --short` | **0** | 251 líneas (árbol sucio preexistente de los paquetes concurrentes) |
| C4 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion .opencode backend frontend worker proxy` | **0** | **vacío** — las raíces prohibidas están intactas |
| C5 | `git stash` / `git reset` / `git checkout` | — | **nunca invocados** |

**Known baseline failures:** sin cambios — las dos puertas `manage.py` con los settings por defecto siguen fallando con `DB_NAME` (fallo ambiental conocido, idéntico desde FND-01) y la puerta global `makemigrations --check --dry-run` sigue fallando por el cambio pendiente de `modules/salesianos_fest` (punto 1 de las advertencias). **Esta reconciliación no ejecutó ninguna suite, luego no introduce ni cierra ninguna.**
**Regressions:** none. Cero ficheros de código modificados. No commit. `git stash` never invoked.

**Rollback:** borrar `evidence/reconciliation/2026-11-19-state-reconciliation.md` · revertir las filas del tablero de este transition log · restaurar los topics #11228 y #11227 a su contenido anterior. Punto de rollback `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit; **no revertir ni resetear** ese commit). **El historial comercial, de pagos y de inventario se preserva**: esta reconciliación no borra ninguna compra, orden, transacción, acta ni movimiento de bitácora.

**Next packet:** **API-03** y **XCT-01** — tras la ratificación de las rutas provisionales (A0-01, A0-04) y el congelamiento del presenter de entrega. En paralelo, y **sólo con autorización explícita del usuario**, la verificación diferida con `uv run` de **DOM-03**, **DOM-05**, **DOM-07** y **DOM-08**, y el apply **sólo-verificación** de **FND-06** (que es lo que cierra formalmente ese paquete).

---

### 2026-11-19 — FND-08 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/apply-progress` (upsert del índice acumulado) · **Owner:** A0 + A7
**Original task IDs:** `T-017` (heredada de FND-06, compartida: "cliente API" + "claves de caché por recurso") — el artefacto del paquete no lleva ID propio de plan.
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit creado; `git stash`/`reset`/`checkout` **nunca invocados**)
**Full report (canonical):** `evidence/foundations/FND-08-query-cache-consolidation.md`
**Freezes respetados:** `FREEZE-ENV-1.0.0` (FR-01) · `FREEZE-ED-1.0.0` (FR-02) · `FREEZE-TC-1.0.0` (FR-01 §7.2) · `FREEZE-PS-1.0.0` (FR-07)

> **ESTADO: `verification_required`** — la pasada de **implementación** está aplicada; el paquete **NO se promueve a `completed`** porque la verificación en runtime está diferida por la instrucción vigente del usuario (preferencia `#11299`): las pruebas se **escriben** pero **no se ejecutan**. El ÚNICO comando de runtime fue `npx tsc --noEmit` (exit **0**).

**Delivered:** la consolidación de la base de datos del frontend en `Aplicacion/frontend/**` — **un** dueño de transporte, **una** factoría de keys por dataset, **una** forma de paginación y **una** política de caché con forma segura.

- **Dueño del transporte:** `src/lib/api.ts` conserva **la única** instancia axios de todo `src/**` y gana `apiSend()` + `ApiResult<T>`: el **204 No Content** se resuelve **en el dueño del transporte** (`data: null`) y un cuerpo vacío **jamás** se parsea.
- **Factorías de keys:** `src/shared/utils/query-keys.ts` — `createDatasetQueryKeys(scope)` da **una raíz por dataset** (`["<dataset>"]`), la familia de listas (`["<dataset>","list"]`), una lista con **todos** los parámetros que cambian la respuesta (`["<dataset>","list",{params}]`, con los `undefined` descartados) y un detalle (`["<dataset>","detail",id]`). La raíz es el blanco de invalidación de ese dataset y de ningún otro.
- **Política de staleness:** `src/shared/utils/query-options.ts` — `STALE_TIME` por tipo de dataset (catálogo 10 min · listados admin 30 s · comercial 15 s · vivo 0), `gcTime >= staleTime` y `gcTime >= 5 min` (el dinero y la elegibilidad no desaparecen de la caché), y `datasetQueryOptions()` como el **único** `queryOptions` de las lecturas. `useApiQuery` expone además `apiQueryOptions()` con la **misma** key y la **misma** política.
- **La única forma de paginación:** `src/shared/schemas/pagination.schema.ts` — `PaginatedResult<T>` = `{ items, total, page, page_size, total_pages }` (la forma congelada por `FREEZE-ENV-1.0.0` §4.3), su espejo Zod parametrizado por el item y el guard de runtime `isPaginatedResult()`.
- **Escrituras con forma segura:** `src/shared/utils/cache-policy.ts` — `invalidateDatasets` (invalida **sólo** lo declarado), `updateCachedList` (escribe **sólo** sobre un array plano), `updateCachedPage` (escribe **sólo** sobre un envelope paginado y conserva su forma), `updateCachedDetail` (escribe **sólo** sobre un detalle que ya existía) y `removeCachedEntry` (borra **exacto**, nunca por prefijo).
- **Primitivas inseguras retiradas:** `useGenericOptimisticUpdate` reescrito (forma genérica `TData → TData`, snapshot + rollback **incondicional**, eliminación de la entrada creada cuando no había caché — sin huérfanos — e invalidación al liquidar) · `useGenericUpdateMutation` reescrito (sin escritura de array sobre un envelope, **sin** escritura de detalle huérfano en `[...listKey, id]`, con `detailKey` declarado por el dataset) · `useGenericDeleteMutation` reescrito (sin `old?.filter(...) ?? []`, borrado exacto) · `useGenericCreateMutation` reescrito (**no escribe nada**: el servidor decide la posición, la página y el total; el `setQueriesData` por prefijo metía el item en **todas** las páginas e inflaba el `total` en cada una) · **`useGenericCacheSync` ELIMINADA** (cero consumidores; sus tres operaciones eran suposiciones de array y creación de huérfanos, y duplicaba a los dueños de las mutaciones).
- **Invalidación explícita:** `useApiCreate` / `useApiUpdate` / `useApiDelete` aceptan `invalidateKeys`. Una mutación que no declara claves **no** ensucia nada. La invalidación corre **dentro** de la `mutationFn` (no en `onSettled`): un componente que se desmonta durante la mutación dejaría la caché con la respuesta vieja para siempre.

**Commands / exit codes:**

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio (sin salida) |
| V2 | `git status --short -- Aplicacion/frontend/src` | raíz | 0 | inspección: los cambios de este paquete **y** los del agente concurrente (FND-06: `src/lib/routes.test.ts`, `src/lib/__tests__/route-map.guard.test.ts`, `src/hooks/system/use-gsap.ts`) — **ninguno fue tocado, revertido ni fusionado** |
| V3 | `git diff --stat -- Aplicacion/frontend/src/lib Aplicacion/frontend/src/hooks` | raíz | 0 | inspección: 618 inserciones / 218 borrados en ficheros versionados (+ ~560 líneas nuevas sin versionar) |
| V4 | `git ls-files --others --exclude-standard -- …` | raíz | 0 | inspección: ningún fichero ajeno overwritten |

**NADA MÁS se ejecutó.** `vitest`, `biome`, `next build`, `npm install`, servidores y navegadores **NOT RUN**.

**Pruebas ESCRITAS, NO EJECUTADAS (6 suites):** `src/shared/schemas/__tests__/pagination.schema.test.ts` · `src/shared/utils/__tests__/query-keys.test.ts` · `src/shared/utils/__tests__/query-options.test.ts` · `src/hooks/cache/__tests__/cache-policy.test.ts` · `src/hooks/cache/__tests__/generic-cache-mutations.test.tsx` · `src/hooks/callsApi/__tests__/useApiQuery.test.tsx` (key · invalidación · rollback · forma paginada · error con status HTTP).

**Deviations:** `D-FND08-01`…`07` (evidencia §7): `staleTime` por defecto 5 s → 15 s (la política del contrato no contempla 5 s) · `useGenericCreateMutation` pierde `insertPosition`/`listShape` (eran la escritura de arrays en envelopes paginados) · hooks de caché genéricos sobre las variables · invalidación dentro de la `mutationFn` · `useGenericCacheSync` eliminada · `useApiUpdate` deja de tener el `TPayload` sin ligar en la firma de implementación (el fichero **no compilaba**: TS2304) · la regla de la skill `salesianos-feature-architecture` que dice "edit `frontend/src`, never `Aplicacion/frontend`" está **desfasada** para este rebuild (aquí `Aplicacion/frontend` es el destino y `frontend/**` es la evidencia congelada).

**Duplicación diferida (raíces de feature prohibidas en este paquete):** los namespaces `["landing","disciplinas"|"categorias"|"paquetes"]` de `features/portada/fixtures/**` duplican el namespace `["inscripcion","catalogo",…]` del **mismo** dataset · `features/inscripciones/**` habla el backend **congelado** · `src/app/api/auth/refresh/route.ts` habla con el backend con `fetch` crudo · `PaginatedResponse<T>` (`src/types/api.types.ts`) es el **segundo** tipo de paginación del frontend. Todas van a A0 (A0-01…A0-04 de la evidencia).

**Concurrency recorded.** `Aplicacion/frontend/src/lib/routes.test.ts`, `src/lib/__tests__/route-map.guard.test.ts` y `src/hooks/system/use-gsap.ts` (trabajo concurrente de FND-06/UI-01A) y el árbol backend de los paquetes de dominio **no fueron tocados, revertidos ni fusionados**, y **sus filas del tablero no se editaron**.

**Regressions:** none (a falta de ejecución de la suite, la única puerta ejecutada — `tsc` — está verde). No commit. `git stash` never invoked.

**Rollback:** borrar `src/shared/**` y `src/hooks/cache/__tests__/**` y `src/hooks/callsApi/__tests__/**` → restaurar `src/lib/api.ts`, `src/lib/query-client.ts`, `src/hooks/callsApi/useApi{Query,Create,Update,Delete}.ts`, `src/hooks/cache/useGeneric{OptimisticUpdate,UpdateMutation,DeleteMutation,CreateMutation}.ts`, `src/hooks/cache/useGenericCacheSync.ts` y `src/hooks/cache/index.ts` desde el checkpoint `fd1c4c12` → revertir la fila de FND-08 de este tablero y el topic `sdd/salesianos-fest-rebuild/apply-progress`. **NO** revertir ni resetear `fd1c4c12`.

**Consumers unblocked:** **API-01…API-05** (un dueño de key y un cliente por dataset antes de escribir cualquier espejo Zod) · **UI-01…UI-05** (las lecturas ya tienen `queryOptions` con la política de staleness) · **XCT-01…XCT-03** (las mutaciones declaran la invalidación que ensucian) · **VER-01…VER-03** (el `QueryClient` no repite un 4xx y las mutaciones no se repiten solas).

**Siguen bloqueados (no dependen de FND-08):** el registro de los 4 controllers no registrados · la migración pendiente `0004_alter_comprapase_token_revocado_en` · los 33 códigos públicos sin catalogar · el espejo de las rutas provisionales. Son de A0 y de los paquetes de API.

**Next packet:** **FND-07** (raíces disjuntas: `genericForm`, `errors`, `lib/forms`, `utils/payload-builder`) y, en paralelo, **API-01…API-05** — que ya pueden escribir su espejo Zod, su factoría de keys y su `queryOptions` sobre la base consolidada por este paquete.

---

### 2026-11-19 — FND-07 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/apply-progress` (upsert del índice acumulado) + `sdd/salesianos-fest-rebuild/fnd-07-apply-progress` (packet-specific) · **Owner:** A0 + A7
**Original task IDs:** ninguno — el artefacto del paquete no lleva ID propio de plan (paquete de divergencia de construcción).
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit creado; `git stash`/`reset`/`checkout` **nunca invocados**)
**Full report (canonical):** `evidence/foundations/FND-07-forms-lifecycle-errors-payloads.md`
**Freezes respetados:** `FREEZE-ENV-1.0.0` (FR-01 — `error.field_errors[]` como único canal de error por campo) · `FREEZE-MD-1.0.0` (FR-06 — allowlist MIME y tope de 5 MiB en el campo de archivo)

> **ESTADO: `verification_required`** — la pasada de **implementación** está aplicada; el paquete **NO se promueve a `completed`** porque la verificación en runtime está diferida (preferencia `#11299`): las pruebas se **escriben** pero **no se ejecutan**. El ÚNICO comando de runtime fue `npx tsc --noEmit` (exit **0**).

**Delivered:** el ciclo de vida del formulario, los errores de campo del backend y la semántica de payload, en `Aplicacion/frontend/**` (12 ficheros creados + 9 modificados, **todas** las raíces permitidas del paquete).

- **Errores de campo 422 (el canal que NO existía):** `src/errors/field-errors.ts` (nuevo) lee las CUATRO formas del canal — `error.field_errors[]` (el congelado: `{field, code, message}` con ruta punteada) · `detail[]` (Django Ninja/Pydantic: `loc: ["body","beneficiarios",0,"documento"]` → `beneficiarios.0.documento`) · `errors{}` (DRF) · `details{}` (mapa plano heredado) — y las normaliza a `Record<string, string>`. `non_field_errors` **nunca** es un campo. `handleApiError` adjunta `fieldErrors` a **todo** error parseado y `GenericForm` llama `setError` **exactamente una vez por campo**.
- **Dos mapeos de payload, separados y exactos:** `buildCreatePayload` (mapeo completo validado) y `buildUpdatePayload` (mapeo estricto, consciente de `initialData`) — `undefined` omitido · `null` incluido (limpieza explícita) · `File` incluido · URL de un campo de archivo omitida (no hay nada que subir) · campo NO declarado por el schema omitido. `buildUpdatePayload` **ya funciona**: antes declaraba `initialData`/`strict` y no los usaba, y su docstring describía la semántica invertida.
- **Zod es el dueño de la coerción:** se eliminó la re-coerción por `FieldConfig.type` (`Number()`/`Boolean()`), que sólo podía corromper el valor ya validado y destruía el `null` explícito de un campo numérico. Se conserva la IDENTIDAD de la opción de un `select`/`radio` (`"3"` ES la opción `3`), que no es coerción.
- **Re-hidratación determinista:** `reset(initialData)` cuando cambia el **CONTENIDO** de `initialData` (`stableSerialize`), nunca por su referencia → un padre que reconstruye el objeto en cada render no resetea nunca; no interrumpe un envío en vuelo; no resetea cuando los valores vivos del formulario SON los nuevos datos. `resetOnInitialDataChange={false}` conserva lo que el usuario escribió.
- **`submitMode`** (prop nueva): `"create"` por defecto (preserva la forma del cable de HOY para todos los consumidores existentes) y `"update"` para el mapeo estricto. Una creación **nunca** usa semántica de diff.
- **Dependencias:** `FormField.dependsOn` (nuevo) + `src/components/genericForm/visibility.tsx`: un campo que declara sus dependencias lee SOLO esos campos con `useWatch`. `GenericForm` ya **no** llama a `watch()` sobre el formulario entero (prohibido por `contract/smart.md` §5.2).
- **UX del campo de archivo:** la previsualización sigue el **valor** del formulario (antes leía `field.defaultValue` y el formulario de edición no mostraba la imagen ya almacenada) · acciones **siempre visibles** (antes sólo al hacer hover: inalcanzables con teclado y en táctil) · input `sr-only` alcanzable con teclado con `focus-within` visible · `aria-label`/`aria-invalid`/`aria-describedby` · `accept` y límite de 5 MiB tomados del **contrato de media del backend** (`image/jpeg`/`image/png`/`image/webp`).
- **Hand-off de archivos:** el token de la parte multipart se genera con `crypto.getRandomValues` (disponible en contexto no seguro, donde `crypto.randomUUID` no) en lugar de `Math.random`; la detección de `File` está protegida (`typeof File !== "undefined"`), porque el transporte también corre en el servidor. El protocolo `PROTO-MD-1.0.0` (`data` + `files` con `<token>___<realname>`) **no se tocó**.

**Commands / exit codes:**

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio (2 passes: tras la primera tanda y tras el refinamiento del reset) |
| V2 | `git diff --name-only -- <raíces prohibidas>` | raíz | 0 | vacío para los cambios de este paquete |
| V3 | `git diff --stat -- <raíces permitidas>` | raíz | 0 | 449 inserciones / 304 borrados en versionados + ~1 250 líneas nuevas sin versionar |
| V4 | `git rev-parse HEAD` | raíz | 0 | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — sin commit |

**NADA MÁS se ejecutó.** `vitest`, `biome`, `next build`, `npm install`, servidores y navegadores **NOT RUN**.

**Pruebas ESCRITAS, NO EJECUTADAS (4 suites):** `src/errors/__tests__/field-errors.test.ts` · `src/errors/__tests__/error-handler.test.ts` · `src/lib/forms/__tests__/payload-mapping.test.ts` · `src/components/genericForm/__tests__/generic-form.lifecycle.test.tsx` (jsdom) — cubren hidratación y reset (incluido el "no reset si el contenido no cambió"), forma exacta create/update (ausente/`null`/create/update/archivo), 422 (`field_errors`, `detail[]`, `errors{}`, `details{}`, `non_field_errors`), coerción de Zod, hand-off del `File` y `setError` una vez por campo.

**Deviations:** `D-FND07-01`…`08` (evidencia §6): `submitMode` por defecto `"create"` (preserva la forma del cable de HOY) · una sección con `hidden` por función puede quedar vacía con su título (el salto exacto de sección exigiría leer el formulario entero) · se conserva la identidad de la opción de un `select`/`radio` · se eliminó la coerción por `FieldConfig.type` · `strict` de `buildUpdatePayload` ahora significa lo que su nombre dice y vale `true` por defecto · **NO** se creó `src/components/smartField/**` (la raíz no existe en el objetivo y las raíces permitidas del paquete no la incluyen; el ecosistema Smart Field del contrato vive en `components/genericForm/**`) · `imageField()` y su convención (Symbol) NO se tocaron (`imageField().schema.optional()` perdería el Symbol: trampa documentada) · `src/components-app/**` está EXCLUIDO de `tsconfig.json`, así que sus consumidores no los cubre el `tsc` (revisados a mano: ambos siguen siendo compatibles).

**Hechos nuevos:** `F-71` (el backend entrega la ruta del campo YA punteada; la conversión desde `loc` sólo hace falta para el backend congelado heredado) · `F-72` (`zodResolver` entrega la salida parseada de Zod: por eso la coerción del formulario era redundante o corruptora) · `F-73` (`useWatch` con un array de nombres devuelve un array **en el mismo orden**) · `F-74` (`src/components-app/**` excluido de `tsconfig.json`) · `F-75` (el allowlist de media del backend es la fuente de verdad del `accept` y del texto del límite).

**Review slices:** **4** rodadas autónomas (WU-1 errores 422 · WU-2 mapeo de payload y hand-off · WU-3 ciclo de vida, hidratación y dependencias · WU-4 UX del campo de archivo + suite del ciclo de vida). El artefacto del paquete **NO lleva `Review Workload Forecast`**, así que NO exigía una decisión de cadena/tamaño (mismo precedente que DOM-06); el tamaño **real** (~1 700 líneas cambiadas) excede el presupuesto de 400 líneas por ≈ 4× y **se reporta a A0** como hallazgo. Orden de rollback: WU-4 → WU-3 → WU-2 → WU-1.

**Concurrency recorded.** El árbol de trabajo ya traía modificaciones de otros agentes en `src/app/**`, `src/features/**`, `src/components/shell/**`, `src/components/ui/**`, `src/hooks/**`, `src/lib/api.ts`, `src/lib/query-client.ts` y `src/shared/**` (FND-06 / UI-01A / FND-08 / trabajo concurrente de rutas): **no fueron tocados, revertidos ni fusionados**, y **sus filas del tablero no se editaron**. Las raíces permitidas de este paquete estaban **limpias** al inicio del paquete (verificado con `git status --short`), así que no hubo conflicto con escrituras concurrentes.

**Regressions:** none (la única puerta ejecutada — `tsc` — está verde). No commit. `git stash` never invoked.

**Rollback:** revertir los 9 ficheros modificados (`src/components/genericForm/{GenericForm,GenericInput}.tsx`, `src/components/genericForm/inputs/{InputImage,index,types}.ts`, `src/errors/{error-handler,index}.ts`, `src/lib/forms/buildUpdatePayload.ts`, `src/utils/payload-builder.ts`) y borrar los 12 creados (`src/errors/field-errors.ts` + sus 2 suites, `src/lib/forms/{schemaShape,valueEquality,stableSerialize,buildCreatePayload,index}.ts` + su suite, `src/components/genericForm/{formDefaults,visibility}.tsx` + su suite) desde el checkpoint `fd1c4c12` → revertir la fila de FND-07 de este tablero y de los topics. **NO** revertir ni resetear `fd1c4c12`.

**Consumers unblocked:** **UI-02 / UI-03 / UI-04 / UI-05** (los formularios de ruta ya tienen re-hidratación determinista, errores de campo que llegan al control y dos mapeos de payload separados) · **API-01…API-05** (el canal de errores de campo y la forma del payload están cerrados) · **XCT-01…XCT-03** · **VER-01…VER-03**.

**Next packet:** **UI-01** (briefs de ruta, candidatos shadcn, `PROVISIONAL_CONTRACT_FIXTURE`, los diez estados por ruta, los page IDs restantes y la auditoría de navegador de cinco anchos) y, en paralelo, **API-01…API-05**. En paralelo y **sólo con autorización explícita del usuario**, la verificación diferida de **FND-06**, **FND-07**, **FND-08**, **DOM-03**, **DOM-05**, **DOM-07** y **DOM-08**.

---


### 2026-11-19 - UI-01 -> verification_required

**Timestamp:** 2026-11-19 (local) - **Apply-progress observation:** `sdd/salesianos-fest-rebuild/ui-01-apply-progress` - **Owner:** A7
**Paquete:** `wave-02-frontend-skeletons/UI-01-public-account-shells.md` - **Rama:** `master` - **Punto de rollback:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit)

**ESTADO: `verification_required`** - la pasada de **implementacion** esta aplicada; el paquete **NO** se promueve a `completed` porque la verificacion en runtime esta **DIFERIDA** (preferencia #11299): las pruebas se **escriben** pero **no se ejecutan**, y la auditoria de navegador de cinco anchos no se ha hecho. El UNICO comando de runtime fue `npx tsc --noEmit` (exit **0**). `vitest`, `biome`, `next build`, `npm install`, servidores y navegadores **NOT RUN**.

**Alcance realmente aplicado (6 de los 9 page IDs del paquete):** `PUB-02` (`/informacion`), `REC-01` (`/recuperar-compra`), `ACCOUNT-01` (`/mi-cuenta`), `ACCOUNT-02` (`/mis-inscripciones`), `ACCOUNT-04` (`/mis-compras`), `ACCOUNT-05` (`/mis-compras/[id]`). **`PUB-01` (`/`) vive en `app/(portada)/**` + `features/portada/**`, y `AUTH-01` / `AUTH-02` viven en `app/(auth)/**` + `features/auth/**`: ninguna de esas raices esta en las raices permitidas de este paquete, asi que NO se tocaron** (evidencia seccion 10). `ACCOUNT-03` y `SPORT-01` son de **UI-02**.

**Delivered:** las seis rutas con su proposito, sus acciones y sus estados, sobre el shell compartido y el sistema visual actuales.
- **La regla que decidio la composicion (`D-UI01-01`):** una fixture provisional puede renderizar la **configuracion del producto**; **nunca** los **datos personales de quien esta autenticado**. Las cuatro rutas de cuenta muestran de verdad el estado honesto (`sin-datos`) y las composiciones pobladas (lista, tabla, tarjetas, filtros, chips de veredicto, estado parcial) quedan implementadas, tipadas y ejercitadas por las suites.
- **Diez estados (`SH-03`):** S-01 carga (skeletons con la geometria real por ruta), S-02 vacio, S-03 vacio filtrado (`SinResultadosConFiltros`: conserva los filtros, dice cuantos oculta y ofrece quitarlos), S-04 error recuperable, S-05 validacion (resumen con `role="alert"` + foco + `aria-invalid`/`aria-describedby`), S-06 permiso (`ShellPermissionDenied`), S-07 respuesta neutra de la recuperacion, S-08 en curso, S-09 parcial/indeterminado (`EstadoIndeterminado`: el pago confirmado con el derecho todavia no habilitado). **S-10 NO aplica a estas rutas** y queda declarado, no omitido en silencio.
- **REC-01 honesto:** el formulario (`GenericForm` Modo 1 + Zod) valida, y **sin transporte NO finge un envio**: dice por que el correo todavia no sale (`PD-08`). La respuesta neutra ("exista o no la compra") es el contrato de la ruta.
- **PUB-02:** indice de anclas REAL (`nav` con nombre accesible, cada ancla resuelve a una seccion que existe, `aria-current` en la seccion leida), revelacion en movil y rail fijo desde 768.
- **shadcn:** la comparacion se RE-EJECUTO por MCP para esta familia (registro `@shadcn`, 61 items `registry:ui`, busquedas de table/pagination/accordion) y quedo registrada ANTES de componer (evidencia seccion 3). **No se anadio ningun componente y no se toco ningun fichero de `components/ui/**`.** El chip de veredicto se COMPUSO en la capa de feature (el `badge` local no tiene variantes de veredicto y arrastra un typo), y el `accordion` se descarto porque `components/ui/**` es raiz prohibida.

**Ficheros (34 creados + 2 modificados, todos dentro de las raices permitidas):** creados 9 de presentacion de ruta (`app/(public)/informacion/loading.tsx`, `app/(public)/recuperar-compra/{loading,error}.tsx`, `app/(cuenta)/mis-inscripciones/{loading,error}.tsx`, `app/(cuenta)/mis-compras/{loading,error}.tsx`, `app/(cuenta)/mis-compras/[id]/{loading,error}.tsx`), 10 de `features/cuenta` (`types/cuenta.types.ts`, `fixtures/cuenta.fixture.ts`, 5 componentes de estado, el indice del barrel, 2 suites) y 8 de `features/public` (`components/{IndiceInformacion,RecuperarCompraForm}.tsx`, `components/index.ts`, `fixtures/edicion.fixture.ts`, `schemas/recuperar-compra.schema.ts`, 2 vistas, 2 suites); modificados `app/(cuenta)/mis-inscripciones/page.tsx` y `app/(cuenta)/mis-compras/page.tsx` (leen `searchParams` y entregan los filtros a la vista). **Ninguna raiz prohibida fue tocada**: ni `src/components/shell/**`, ni `src/components/ui/**`, ni `globals.css`, ni providers, ni `src/lib/**`, ni `src/hooks/**`, ni `src/shared/**`, ni `features/{auth,portada,inscripciones,admin,theme}/**`, ni el backend, ni `contract/**`, ni el `frontend/**` de la raiz.

**Comandos / exit codes:**

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 3 errores: `ShellPermissionDenied` se llamaba sin el `title` obligatorio |
| V2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio |
| V3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | limpio (tras los limites `Suspense` de la barra de filtros) |
| V4 | `git status --short -- Aplicacion/frontend` | raiz | 0 | 123 lineas en la linea de base (arbol ya sucio por FND-06 / FND-07 / FND-08 / UI-01A) |
| V5 | `git diff --numstat` (las 2 rutas modificadas) | raiz | 0 | 38 inserciones / 20 borrados |

**NADA MAS se ejecuto.** `vitest`, `biome`, `next build`, `npm install`, servidores, navegadores, `git stash`, `git commit`, `git reset`, `git checkout`: **NOT RUN**.

**Pruebas ESCRITAS, NO EJECUTADAS (4 suites):** `src/features/cuenta/__tests__/cuenta-estados.test.tsx` (jsdom) - `src/features/cuenta/__tests__/cuenta-responsive.test.ts` (node, auditoria estatica: sin color literal, `scope="col"`, tabla desde 1024, 44 px, sin vocabulario del proveedor) - `src/features/public/__tests__/recuperar-compra-form.test.tsx` (jsdom) - `src/features/public/__tests__/informacion-indice.test.tsx` (jsdom) - `src/features/public/__tests__/public-responsive.test.ts` (node).

**Deviations:** `D-UI01-01`.`10` (evidencia seccion 12): la fixture renderiza configuracion de producto y NUNCA datos personales - el cubo de veredicto viaja CON el veredicto (el componente no ramifica sobre codigos) - se creo `features/cuenta/types/` (tipos TS, NO espejos Zod: los espejos de wire estan prohibidos en esta etapa) - el detalle tecnico de `ACCOUNT-05` se OMITIO (mostrarlo exigiria un estado del proveedor, prohibido por `GOV-02-RB-01d`) - no se anadio `accordion` ni se compuso `pagination` - el bloque "Mis entradas" de `ACCOUNT-01` se omitio (no hay ruta: seria un enlace muerto) - el schema del formulario es de validacion de cliente, no un espejo de wire - el formulario NO finge un envio - los filtros viven en la URL.

**Hechos nuevos:** `F-76` (una fixture provisional puede renderizar configuracion de producto, pero renderizar datos personales de un usuario autenticado es inventar datos de pagina) - `F-77` (el cubo presentacional de un veredicto debe viajar con el veredicto: el componente nunca debe ramificar sobre `estado_operativo.codigo`, porque 33 codigos publicos siguen sin catalogar) - `F-78` (`ShellPermissionDenied` declara `title` como obligatorio: un permiso sin titulo no es explicable) - `F-79` (el `badge` local tiene un typo en su variante secundaria y no tiene variantes de veredicto; el chip de veredicto se compone en la capa de feature) - `F-80` (con `useSearchParams` en un subarbol cliente, la pagina que lo aloja debe leer `searchParams` y/o envolver el subarbol en `Suspense`).

**A0 requests:** `A0-UI01-01` (los tonos `--success` / `--warning` no llegan a 3:1 como icono sobre la superficie clara: hace falta un rol `--success-strong` / `--warning-strong`) - `A0-UI01-02` (el typo del `badge` local) - `A0-UI01-03` (los 33 codigos publicos sin catalogar) - `A0-UI01-04` (ampliar las raices de UI-01 a `(auth)` y `(portada)`, o abrir un paquete propio) - `A0-UI01-05` (sincronizar `00-matriz-tareas.md`: la matriz es raiz prohibida).

**Workload:** el artefacto del paquete **NO lleva `Review Workload Forecast`**, asi que NO exigia una decision de cadena/tamano (mismo precedente que DOM-06, FND-07 y FND-08). El tamano **REAL** (~2 990 lineas cambiadas) excede el presupuesto de 400 lineas por ~**7.5x** y **se reporta a A0** como hallazgo. **8 unidades autonomas** (WU-1 tipos y fixtures - WU-2 estados - WU-3 listas y filtros - WU-4 vistas de cuenta - WU-5 indice y formulario - WU-6 vistas publicas - WU-7 presentacion de ruta - WU-8 suites). Orden de rollback: WU-8 -> WU-1.

**Concurrency recorded.** El arbol traia modificaciones de otros agentes en `src/app/**`, `src/features/**`, `src/components/shell/**`, `src/components/ui/**`, `src/hooks/**`, `src/lib/**` y `src/shared/**`: **no fueron tocados, revertidos ni fusionados**, y **sus filas del tablero NO se editaron**. `features/portada/fixtures/festival.ts` se leyo (configuracion del producto) y **no se modifico**.

**Regressions:** none (la unica puerta ejecutada - `tsc` - esta verde). No commit. `git stash` never invoked.

**Rollback:** revertir los 2 modificados (`app/(cuenta)/mis-inscripciones/page.tsx`, `app/(cuenta)/mis-compras/page.tsx`) y borrar los 34 creados desde el checkpoint `fd1c4c12` -> revertir la fila de UI-01 de este tablero y de los topics. **NO** revertir ni resetear `fd1c4c12`. El shell compartido y el resto del producto quedan intactos.

**Consumers unblocked:** **API-01** (las costuras, la lista de borrado de fixtures y el handoff estan en la evidencia, seccion 11) - **UI-02 / UI-03 / UI-04 / UI-05** (el patron de estado, el chip de veredicto y la barra de filtros ya existen y se pueden reutilizar) - **XCT-01..XCT-03** - **VER-01..VER-03**.

**Next packet:** **API-01** (`wave-03-api-integration/API-01-public-account-integration.md`) y, en paralelo, **UI-02..UI-05**. En paralelo y **solo con autorizacion explicita del usuario**, la verificacion diferida de **FND-06**, **FND-07**, **FND-08**, **DOM-03**, **DOM-05**, **DOM-07**, **DOM-08** y **UI-01**.

---

### 2026-11-19 — DOM-03 / DOM-05 / DOM-07 / DOM-08 → completed (cierre de validación en runtime)

**Timestamp:** 2026-11-19 (local) · **Owner:** A0 (coordinador) · **Naturaleza:** apply **sólo-verificación** — **NO** es un paquete de funcionalidad nuevo: **no** se amplió ningún dominio.
**Original task IDs:** ninguno propios — cierra DOM-03 (`T-030`…`T-032`), DOM-05 (`T-041`), DOM-07 (`T-050`…`T-052`) y DOM-08 (`T-060`).
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit; `git stash` never invoked)
**Full report (canonical):** `evidence/domains/DOM-03-05-07-08-runtime-verification.md`
**Freezes respetados:** `FREEZE-ENV-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-MD-1.0.0` · `FREEZE-TC-1.0.0` · `FREEZE-ED-1.0.0`

> **ESTADO: los CUATRO paquetes pasan a `completed`.** Cada uno tiene una suite **EJECUTADA y verde** con `uv run --group dev`, las puertas de Django verdes y el **replay de migraciones** verde sobre una base SQLite de archivo. Hasta ahora los cuatro tenían las pruebas **ESCRITAS pero NO EJECUTADAS**: esta ronda es la **evidencia de ejecución** que faltaba.

**Entorno:** workdir `Aplicacion/backend` · `uv 0.10.9` · CPython 3.10.0 · Django 5.2.11 · comando base `uv run --group dev python …` · `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`, `addopts = --tb=short --nomigrations`, `asyncio_mode = auto`) — **prevalece** sobre `[tool.pytest.ini_options]` de `pyproject.toml`.

**Overlays usados (uno por módulo, dentro de la raíz permitida del paquete):** `modules.salesianos_fest.tests.settings_overlay` · `modules.marketplace.tests.settings_overlay` · `modules.competencias.tests.settings_overlay` · `modules.patrocinadores.tests.settings_overlay`.

**Commands / exit codes:**

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V1 | `uv run --group dev python -m pytest modules/salesianos_fest/tests -q` (overlay `salesianos_fest`) | **0** | **161 passed**, 144 warnings (39.87 s) |
| V2 | `uv run --group dev python -m pytest modules/marketplace/tests -q` (overlay `marketplace`) | **0** | **97 passed**, 125 warnings (59.98 s) |
| V3 | `uv run --group dev python -m pytest modules/competencias/tests -q` (overlay `competencias`) | **0** | **55 passed**, 131 warnings (12.84 s) |
| V4 | `uv run --group dev python -m pytest modules/patrocinadores/tests -q` (overlay `patrocinadores`) | **0** | **53 passed**, 59 warnings (13.39 s) |
| V5 | `manage.py check` (settings por defecto = `config.settings.production`) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **baseline ambiental idéntico** a FND-01…FND-05 y DOM-06. **NO** es regresión. |
| V6 | `manage.py makemigrations --check --dry-run` (settings por defecto) | **1** | mismo `DB_NAME` — baseline idéntico |
| V7 | `manage.py check --settings=config.settings.development` | **0** | `no issues` |
| V8 | `manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| V9–V16 | `manage.py check` + `makemigrations --check --dry-run` con el overlay de **cada** módulo | **0** ×8 | `no issues` + `No changes detected` en los cuatro |
| V17–V20 | `manage.py migrate --no-input --settings=<overlay>` sobre SQLite **de archivo** temporal | **0** ×4 | cadena completa aplicada: `salesianos_fest.0003_pases_derechos… OK` · `marketplace.0003_…… OK` · `competencias.0001_initial… OK` · `patrocinadores.0001_initial… OK` |
| V20b | `manage.py showmigrations <app> --settings=<overlay>` | **0** ×4 | todas las migraciones `[X]` (`usuarios` 2 · `eventos` 1 · `pagos` 1 · `commerce` 2 · `salesianos_fest` 3 · `marketplace` 3 · `competencias` 1 · `patrocinadores` 1) |
| V21 | `uv run --group dev python -m pytest --collect-only -q` (raíz, settings por defecto) | **2** | **722 collected, 6 errores de colección** — `modules.competencias` y `modules.patrocinadores` **NO** están en `INSTALLED_APPS` → ver `A0-RTV-01` |
| V22 | `pytest core/tests modules/{eventos,usuarios,commerce,pagos,salesianos_fest,marketplace}/tests -q` (settings por defecto) | **0** | **722 passed** (antes de la corrección de §D-RTV-01) |
| V23 | el mismo comando, **después** de la corrección | **0** | **725 passed** (+3 = las pruebas nuevas de la guarda de regresión) |
| V24 | suite completa con los **ocho** módulos de dominio registrados (overlay temporal **fuera del repositorio**) | **1** | **831 passed, 2 failed** (833 collected) — los 2 fallos son **de A0** (`A0-RTV-04`) |

**Test totals:** DOM-03 **59** casos (41 funciones) · DOM-05 **34** casos (32 funciones) · DOM-06 **28** (control) · DOM-07 **55** casos (43 funciones) · DOM-08 **53** casos (53 funciones). Barrido de regresión del backend: **725 passed**. Suite con los ocho módulos registrados: **833 collected → 831 passed + 2 failed** (de A0).

**Defecto reproducible y de alcance propio — CORREGIDO (`D-RTV-01`):** `modules/salesianos_fest` declaraba la versión congelada de su contrato HTTP **en dos sitios con dos valores distintos** — `modules/salesianos_fest/__init__.py` con `SCHEMA_VERSION = "1.0.0"` (OBSOLETO: congelado en DOM-01, nunca actualizado en DOM-02 `1.1.0` ni DOM-03 `1.2.0`) y la fuente canónica `modules/salesianos_fest/presentation/schemas/__init__.py` con `"1.2.0"`. `FR-07` §1.1 exige **una sola fuente de verdad** por módulo: con dos literales, `from modules.salesianos_fest import SCHEMA_VERSION` devolvía la versión equivocada **sin ningún aviso**, y `salesianos_fest` era el **único** módulo de dominio con esa copia en la raíz del paquete. **Corrección:** la raíz del paquete pasa a **reexportar** la fuente canónica (`from modules.salesianos_fest.presentation.schemas import SCHEMA_VERSION`); el nombre público se conserva y devuelve el valor correcto. **Cero** cambio de comportamiento (nadie leía la copia obsoleta). **Guarda de regresión:** `modules/salesianos_fest/tests/integration/test_contrato_schema_version.py` (3 casos) fija (1) coincidencia con `SCHEMA_VERSIONS["salesianos_fest"]` **y** ausencia de drift — hueco que `salesianos_fest` **no** tenía y que `marketplace`/`patrocinadores` sí tienen —, (2) ausencia de copia en la raíz del paquete y (3) **unicidad del literal** en el paquete (una reexportación no casa con el patrón, así que la guarda detecta la reintroducción de cualquier segunda copia).

**Hallazgos CERRADOS por esta ronda:** `C-RTV-01` (**A0-07 de DOM-06**: `modules/salesianos_fest` con cambio de modelo pendiente `0004_alter_comprapase_token_revocado_en` → **no existe**; V8 y V10 verdes) · `C-RTV-03` (DOM-07: la migración `0001_initial` escrita a mano queda **verificada en runtime** por V14 + V19) · `C-RTV-04` (DOM-03: la `0003_pases_derechos` reconciliada estáticamente queda **verificada** por V10 + V17) · `C-RTV-05` (DOM-03: los 86 casos parametrizados + 7 ficheros de `core/tests/**` escritos y NO ejecutados → **ejecutados** dentro de V22/V23) · `C-RTV-02` (**NO REPRODUCIBLE**: la hipótesis de DOM-05 sobre el `isolation_level: None` de `config/settings/test.py` **no se sostiene** — las 34 pruebas de DOM-05 y las 97 de `marketplace` pasan sin tocar `config/**`; **no** se cambió código para satisfacerla).

**Bloqueos escalados a A0 (raíces prohibidas — reportados, NO tocados):** `A0-RTV-01` **BLOQUEANTE** (`modules.competencias` y `modules.patrocinadores` NO están en `INSTALLED_APPS` → el `pytest` de la raíz se INTERRUMPE con exit 2 y la puerta global de migraciones es ciega para ellas) · `A0-RTV-02` **BLOQUEANTE** (cuatro controllers existen y NO están registrados en `config/api.py`: `PedidoController` (DOM-05), `InventarioController` (DOM-06), `CompetenciasController` (DOM-07), `PatrocinadorController` (DOM-08) → sus rutas NO existen) · `A0-RTV-03` **BLOQUEANTE** (`SCHEMA_VERSIONS` no tiene `"competencias"` → sin registro de versión ni test de drift para DOM-07; **no** se añadió el test porque fallaría mientras el registro no exista) · `A0-RTV-04` **BLOQUEANTE** (el guardián `core/tests/integration/test_registration_extension.py` fija listas **CERRADAS** de apps y módulos de DI: al registrar las dos apps de `A0-RTV-01` fallan sus dos tests — hay que ampliar **AMBAS** listas en el **mismo** cambio) · `A0-RTV-05` (**33 códigos públicos** de DOM-05/DOM-07/DOM-08 sin catalogar en `core/exceptions.py::PUBLIC_ERROR_MESSAGES` — `marketplace` 13 · `competencias` 16 · `patrocinadores` 4; `salesianos_fest` 0 — el `error.code` estable **sí** se conserva, pero la prosa pública cae al mensaje genérico del status y se registra un `WARNING "HttpError no catalogado"` en cada ocurrencia) · `A0-RTV-06` (`core.media` deja directorios vacíos) · `A0-RTV-07` (`*.sqlite3` en `.gitignore`) · `A0-RTV-08` (`00-matriz-tareas.md` sin sincronizar).

**Decisiones abiertas: NO se cerró ninguna y NO se inventó ninguna.** `H-01` (`PaseNoTransferibleError` definida y nunca lanzada) queda **ABIERTA**: la política de liberación del cupo y de reemplazo del titular tras una revocación está explícitamente ABIERTA (`PD-02` / `GOV-01-OPEN-08`), y lanzarla sería **inventar política comercial**; su propio docstring dice «Código REQUESTED a A0». También quedan abiertas `PD-01` (BOX), `OD-DOM05-01`…`03`, `OD-DOM06-01`, `OD-DOM07-01`…`05` y `OD-DOM08-01`…`06`. `R-RTV-04` (datetimes sin `tzinfo` en las fixtures de `competencias`): warning de las **fixtures de prueba**, no de la lógica de dominio — **reportado, no tocado**.

**Changed files (4 paths, todos dentro de las raíces permitidas):** creado `Aplicacion/backend/modules/salesianos_fest/tests/integration/test_contrato_schema_version.py` (guarda de regresión, 3 casos) · modificado `Aplicacion/backend/modules/salesianos_fest/__init__.py` (reexportación de la versión canónica) · creado `Aplicacion/task/salesianos-fest-rebuild/evidence/domains/DOM-03-05-07-08-runtime-verification.md` · modificado `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (esta transición). **Fuera del repositorio** (temporal, no versionado): `%TEMP%\opencode\fest-replay\settings_all_overlay.py` (overlay combinado de verificación) y las cuatro bases SQLite de archivo del replay.

**Concurrency recorded.** El árbol traía modificaciones de otros agentes en `Aplicacion/frontend/**`, `Aplicacion/backend/config/**`, `Aplicacion/backend/core/**`, `Aplicacion/backend/modules/usuarios/**`, `Aplicacion/backend/modules/marketplace/**` y `Aplicacion/backend/modules/salesianos_fest/**`: **no fueron tocadas, revertidas ni fusionadas**, y **sus filas del tablero NO se editaron**. `Aplicacion/backend/db.sqlite3` (porproducto preexistente, `M` en el árbol) **NO** fue tocado por esta ronda: se escribió por última vez a las 09:39:29 y la ronda termina a las 17:03; `manage.py check` y `makemigrations --check` no abren la base de datos.

**Regressions:** none — el barrido de regresión del backend está **verde** (725 passed) y las puertas de Django también. No commit. `git stash` / `git reset` / `git checkout` **nunca invocados**.

**Rollback:** revertir `Aplicacion/backend/modules/salesianos_fest/__init__.py` desde `fd1c4c12` → borrar `modules/salesianos_fest/tests/integration/test_contrato_schema_version.py` → borrar `evidence/domains/DOM-03-05-07-08-runtime-verification.md` → revertir las filas de DOM-03/DOM-05/DOM-07/DOM-08 y esta transición en el `STATE.md` y en los topics. **NO** revertir ni resetear `fd1c4c12`.

**Consumers unblocked:** **API-03** (los diez wrappers de DOM-03, los dos de DOM-05 y los cinco de DOM-06) · **API-05** (las dieciséis rutas de DOM-07 y las de DOM-08) · **XCT-01** · **XCT-03** · **VER-01…VER-03**.

**Next packet:** **API-03** y **API-05** — **después** de que A0 aplique `A0-RTV-01`…`A0-RTV-04` (los espejos Zod 1:1 necesitan las rutas ratificadas y registradas). Con autorización explícita del usuario, y en paralelo: la verificación diferida de **FND-06**, **FND-07**, **FND-08** y **UI-01** (frontend, propiedad de otro agente).

---

### 2026-11-19 - UI-02 -> verification_required

**Timestamp:** 2026-11-19 (local) - **Apply-progress observation:** `sdd/salesianos-fest-rebuild/ui-02-apply-progress` - **Owner:** A7
**Paquete:** `wave-02-frontend-skeletons/UI-02-inscription-shells.md` - **Rama:** `master` - **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit; `git stash` nunca invocado)
**Informe canonico:** `evidence/ui/UI-02-inscription-shells.md`

> **ESTADO: `verification_required`** - la pasada de **implementacion** esta aplicada; el paquete **NO** se promueve a `completed` porque la verificacion en runtime esta **DIFERIDA** (preferencia `#11299`): las pruebas se **escriben** pero **no se ejecutan**, y la auditoria de navegador de cinco anchos no se ha hecho.

**Reconciliacion (2026-11-19, DESPUES de la ejecucion concurrente de UI-03):** este bloque de transicion y la fila del tablero se corrigieron para que digan la verdad actual. Las **raices de este paquete dieron 0 errores en todas las corridas** (V1 a V5). La puerta global solo estuvo ROJA por arboles **concurrentes y ajenos** (`features/pases/**` y `features/marketplace/**`, de UI-03), ya reparados por sus duenos; la **corrida global final** de `npx tsc --noEmit` salio **0** tras cerrar UI-03 (exit code reportado por la evidencia de UI-03, **NO medido por este paquete**). **UI-02 NO se promueve a `completed`**: sus 3 suites siguen ESCRITAS y NO EJECUTADAS y la auditoria de navegador de cinco anchos sigue sin hacer. **No se toco nada de UI-03.**

**Alcance realmente aplicado (2 de los 2 page IDs del paquete):** `SPORT-01` (`/inscripcion`) y `ACCOUNT-03` (`/mis-inscripciones/[id]`). Ambos viven en `app/(cuenta)/**` y en `features/inscripciones/**`, las raices permitidas del paquete.

**Delivered:**

- **`SPORT-01` - el asistente de cuatro pasos** (paquete, equipos, resumen, confirmacion). El paso vive en la URL (`?paso=`), asi que un paso es recuperable. Los hooks de red del asistente congelado (`POST /inscripciones/completa/`, `POST /cotizaciones/`) **NO** se usan: el backend objetivo no sirve esas rutas y son raiz prohibida (no se editaron; quedan sin referencias). El paso de declaraciones y el stepper de cantidad se **eliminaron**: el alta objetivo (`InscripcionInicialIn`) no acepta aceptaciones ni cantidad.
- **`ACCOUNT-03` - el detalle en cinco secciones** (Pool, Equipos, Participantes, Compras, Beneficios) sobre el shell compartido. Los TRES numeros del pool, la causa y los impedimentos se imprimen **verbatim** del servidor; el navegador **no resta** cupos ni multiplica precios (la auditoria estatica lo prohibe).
- **Estados honestos:** sin catalogo, error recuperable, permiso, recuperacion de la operacion pendiente, envio sin transporte, pago pendiente y confirmacion irreversible (S-10 del asistente). El chip de veredicto de UI-01 **NO** se reutilizo: ningun wrapper del dominio de inscripciones publica `EstadoOperativo` (`D-UI02-01`).
- **Fixture provisional** unica y marcada (`PROVISIONAL_CONTRACT_FIXTURE`), con `as const satisfies` sobre los espejos de los presenters reales del backend objetivo (`CatalogoPaquetesOut`, `InscripcionDetalleOut`, `PoolOut`, `CompraOut`, `CompraCreadaOut`, `InscripcionInicialOut`). Importe de ejemplo `0.00`.

**Ficheros (18 creados + 9 reescritos, todos dentro de las raices permitidas):** creados `features/inscripciones/{types/inscripcion.types.ts,schemas/alta-inscripcion.schema.ts,fixtures/inscripcion.fixture.ts}`, `components/{PasoResumen,PasoConfirmacion,PanelPool,PanelEquipos,PanelParticipantes,PanelCompras,PanelBeneficios}.tsx`, `views/MisInscripcionDetalleView.tsx`, `__tests__/{inscripcion-estados.test.tsx,inscripcion-detalle.test.tsx,inscripcion-responsive.test.ts}`, `app/(cuenta)/inscripcion/{loading,error}.tsx`, `app/(cuenta)/mis-inscripciones/[id]/{loading,error}.tsx`; reescritos `app/(cuenta)/inscripcion/page.tsx`, `app/(cuenta)/mis-inscripciones/[id]/page.tsx`, `components/{WizardStepper,PaqueteCard,PasoPaquete,PasoEquipos,index}.ts(x)`, `views/{InscripcionWizardView,index}.tsx`. **Ninguna raiz prohibida fue tocada**: ni `components/shell/**`, ni `components/ui/**`, ni `globals.css`, ni providers, ni `src/lib/**`, ni `src/hooks/**`, ni `src/shared/**`, ni `features/cuenta/**` (UI-01), ni `features/pases/**` (concurrente), ni el backend, ni `contract/**`, ni el `frontend/**` de la raiz. `components/PasoDeclaraciones.tsx` queda en disco **sin referenciar** (el arbol de la feature no esta versionado y este paquete no hace operaciones git).

**Comandos / exit codes:**

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 2 errores **de este paquete**: `PanelBeneficios` ausente y un typo `impediment` en `PanelPool` |
| V2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 6 errores, **ninguno en las raices de este paquete**: `src/features/pases/components/**` con `TS2304: Cannot find name '__USE_CLIENT__'` |
| V3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | los mismos 6 errores de `features/pases`: **trabajo concurrente** de otro agente, raiz **prohibida** para este paquete, **NO tocado** |
| V4 | `git status --short -- .../features/pases .../features/inscripciones` | raiz | **0** | ambos arboles **sin versionar** (`??`), lo que prueba que `features/pases` es concurrente y no una regresion de este paquete |
| V5 | `npx tsc --noEmit` (final de UI-02) | `Aplicacion/frontend` | **1** | la puerta global estaba ROJA por un OTRO fichero concurrente, `src/features/marketplace/components/TarjetaProducto.tsx` (de UI-03); **0 errores en las raices de este paquete** |
| V6 | `npx tsc --noEmit` (final global, **despues de que UI-03 completara**; exit code **reportado por la evidencia de UI-03**, no medido por este paquete) | `Aplicacion/frontend` | **0** | la puerta global del proyecto queda **VERDE**: UI-03 reparo sus propios errores concurrentes. **Las raices de este paquete nunca tuvieron errores.** UI-02 sigue en `verification_required` |

**NADA MAS se ejecuto.** `vitest`, `biome check`, `next build`, `npm install`, servidores, navegadores, `git stash`, `git commit`, `git reset`, `git checkout`: **NOT RUN**.

**Pruebas ESCRITAS, NO EJECUTADAS (3 suites):** `features/inscripciones/__tests__/inscripcion-estados.test.tsx` (jsdom) - `features/inscripciones/__tests__/inscripcion-detalle.test.tsx` (jsdom) - `features/inscripciones/__tests__/inscripcion-responsive.test.ts` (node; sin color literal, sin ancho fijo, `scope="col"`, tabla desde 1024 y tarjetas por debajo, 44 px, sin vocabulario del proveedor y **sin aritmetica de cupos ni de dinero en el navegador**).

**Baseline conocido (NO es una regresion de este paquete):** los errores de los arboles **concurrentes** `src/features/pases/**` y `src/features/marketplace/**` (ambos de UI-03), fuera de las raices permitidas y **ya reparados por sus duenos**. **Las raices de este paquete dieron 0 errores en todas las corridas** y la puerta global quedo **VERDE** tras la corrida final de UI-03.

**Regressions:** none. Cero archivos congelados modificados. No commit. `git stash` never invoked.

**Rollback:** revertir las 9 rutas y borrar los 18 creados desde el checkpoint `fd1c4c12` -> revertir la fila de UI-02 de este tablero y el topic `sdd/salesianos-fest-rebuild/ui-02-apply-progress`. **NO** revertir ni resetear `fd1c4c12`. El shell compartido y el resto del producto quedan intactos.

**Deviations:** `D-UI02-01`..`D-UI02-10` (informe canonico seccion 12): el chip de veredicto de UI-01 no se reutilizo - el asistente nunca calcula un valor de negocio - se creo `types/` - se elimino el paso de declaraciones - se elimino la cantidad - los hooks del asistente congelado no se usan - la disciplina es un `<select>` nativo - la confirmacion de retirada de ACCOUNT-03 (S-10 del detalle) se difiere a API-02 - el detalle vive en `features/inscripciones/views/` - las fixtures usan `as const satisfies` con arreglos `readonly`.

**A0 requests:** `A0-UI02-01`..`A0-UI02-09` (informe canonico seccion 12) - **destacado** `A0-UI02-09`: dos arboles **concurrentes** rompieron el typecheck del proyecto durante el paquete (ya reparados por sus duenos; la puerta global quedo verde al cerrar UI-03); ambas raices son **prohibidas** para este paquete.

**Consumers unblocked:** **API-02** (las costuras, el handoff y la lista de borrado de fixtures estan en el informe canonico, seccion 11) - **UI-03..UI-05** (el patron de estado y la banda del pool ya existen) - **XCT-01..XCT-03** - **VER-01..VER-03**.

**Next packet:** **API-02** (`wave-03-api-integration/API-02-inscription-integration.md`) - y, en paralelo, **UI-04** y **UI-05** (**UI-03** ya se aplico y quedo en `verification_required`). En paralelo y **solo con autorizacion explicita del usuario**, la verificacion diferida de **FND-06**, **FND-07**, **FND-08**, **DOM-03**, **DOM-05**, **DOM-07**, **DOM-08**, **UI-01**, **UI-02** y **UI-03**.

---


---

### 2026-11-19 — UI-03 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/ui-03-apply-progress` · **Owner:** A7
**Original task IDs:** none (the packet is a preparatory slice for `API-03`) · **Branch:** `master` · **Rollback point:** unchanged (no commit created)

**Delivered:** the five commercial routes of the packet — `PASS-01` `/pases`,
`PASS-02` `/pases/gestionar/[token]`, `SHOP-01` `/tienda`, `SHOP-02`
`/tienda/[slug]` and `SHOP-03` `/tienda/pedidos/[token]` — in TWO new
features (`features/pases/**`, `features/marketplace/**`) that did not exist
before this packet. Two independent checkouts, **no mixed cart**
(`GOV-02-RB-02a`).

**The rule that decided the honesty (`D-UI03-02`):** a provisional fixture
never reaches a route. Every route renders the honest state by default; the
populated compositions are typed, implemented and exercised by the suites.

**Diez estados:** S-01 (shell) · S-02 vacío · S-03 vacío filtrado (conserva el
filtro, ofrece "Quitar el filtro") · S-04 error recuperable · S-05 validación
(resumen `role="alert"` con foco + `aria-invalid`/`aria-describedby`) · S-06
permiso y **denegación NEUTRAL** (el mismo mensaje para un enlace caducado,
ajeno o con un documento equivocado: sin oráculo de existencia) · S-07
respuesta · S-08 en curso (sin ETA inventado) · S-09 parcial (el pago
confirmado con el derecho todavía no habilitado) · S-10 **irreversible** (el
diálogo de revocación nombra el efecto). Los **cinco** estados presentables
del pago (`SH-03` §3) se dibujan con la etiqueta del backend, nunca con el
código.

**Pago y entrega son DOS hechos:** `SHOP-03` los muestra como dos filas
rotuladas; un pedido pagado y no entregado nunca lee como "Entregado"
(`QA-M04`).

**Shadcn:** la comparación se **RE-EJECUTÓ por MCP** para esta familia:
`@shadcn`, búsquedas de `card` / `carousel` / `dialog`. **Ningún componente
añadido; ningún fichero de `components/ui/**` tocado.** El `carousel` local se
**rechazó** para la galería porque trae etiquetas de lector en inglés y
`components/ui/**` es raíz prohibida (A0 request).

**Ficheros:** 32 creados + 5 modificados (las cinco rutas), todos dentro de
las raíces permitidas. **Ninguna raíz prohibida fue tocada** (ni
`components/shell/**`, ni `components/ui/**`, ni `globals.css`, ni providers,
ni `src/lib/**`, ni `src/hooks/**`, ni `src/shared/**`, ni
`features/{auth,portada,inscripciones,admin,theme,cuenta,public}/**`, ni el
backend, ni `contract/**`, ni el `frontend/**` raíz).

**Pruebas ESCRITAS, NO EJECUTADAS (2 suites):**
`features/pases/__tests__/pases-estados.test.tsx` ·
`features/marketplace/__tests__/marketplace-estados.test.tsx`.

**Comandos / códigos de salida (workdir `Aplicacion/frontend`):**
`npx tsc --noEmit` **1** (15 errores de estructura JSX en
`ProductoDetalleView.tsx`, introducidos por este paquete) → **0** (limpio) →
**0** (limpio, tras las dos suites). `git status --short` 0. **NOT RUN:**
`vitest`, `biome check`, `next build`, `npm install`, servidores, navegadores,
`git stash`, `git commit`, `git reset`, `git checkout`.

**Regressions:** none. No commit. `git stash` never invoked.

**Deviations:** `D-UI03-01`…`09` · **A0 requests:** `A0-UI03-01`…`06`.

**Workload:** el artefacto del paquete **NO lleva `Review Workload Forecast`**
→ NO exigía decisión de cadena/tamaño (mismo precedente que DOM-06, FND-07,
FND-08 y UI-01); el tamaño **REAL** (~2 100 líneas) excede el presupuesto de
400 por ≈ **9x** y **se reporta a A0**. **9 slices autónomos** (WU-1 … WU-9);
rollback WU-9 → WU-1.

**Concurrency:** los cambios de los otros agentes en `src/app/**` y
`src/features/**` (en particular `features/inscripciones/**`, de **UI-02**)
**no fueron tocados, revertidos ni fusionados**, y sus filas del tablero no se
editaron.

**Consumers unblocked:** **API-03** · **XCT-01** (pagos/entrega) ·
**VER-01…VER-03**.

**Next packet:** **API-03** (`wave-03-api-integration/API-03-commercial-integration.md`),
que hereda las costuras y la lista de borrado de fixtures de §11 de la
evidencia.

---

### 2026-11-19 — A0 · validación del cableado global → `BLOCKED` (NO se promueve a `completed`)

**Timestamp:** 2026-11-19 (local) · **Owner:** A0 (coordinador) · **Naturaleza:** apply **sólo-verificación** — **NO** es un paquete de funcionalidad: **no** se tocó ningún fichero de `Aplicacion/backend/**`.
**Paquetes reconciliados:** `DOM-03` (A4) · `DOM-05` (A5) · `DOM-06` (A5) · `DOM-07` (A6) · `DOM-08` (A8) — el objeto de esta pasada es el **cableado global** que los habilita.
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit; `git stash`/`reset`/`checkout` never invoked)
**Informe canónico:** `evidence/foundations/A0-wiring-validation.md`
**Apply-progress observation:** `sdd/salesianos-fest-rebuild/apply-progress` (upsert) · `sdd/salesianos-fest-rebuild/state` (upsert)

> **ESTADO: `BLOCKED`.** La premisa «el cableado global de A0 ya está implementado» **NO se sostiene** contra el árbol actual. La validación en runtime la contradice en los **siete** ejes exigidos. **No** se promueve a `completed`: los bloqueos `A0-RTV-01`…`A0-RTV-05` **se conservan**, ahora **re-confirmados con prueba de ejecución**. Esta pasada **NO repara nada** (`Aplicacion/backend/**` es raíz prohibida para un apply de validación); **detiene y reporta**.

**Entorno:** workdir `Aplicacion/backend` · `uv 0.10.9` · CPython 3.10.0 · Django 5.2.11 · comando base `uv run --group dev python …` · `pytest.ini` (`DJANGO_SETTINGS_MODULE = config.settings.test`, `--nomigrations`, `asyncio_mode = auto`).

**Commands / exit codes:**

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| R1 | `uv run --group dev python -m pytest --collect-only -q` (raíz, settings por defecto) | **2** | **725 collected, 6 errores de colección** — `RuntimeError: Model class modules.competencias… isn't in an application in INSTALLED_APPS` (y los 5 de `patrocinadores`). **La raíz NO se puede recolectar.** |
| R2 | `uv run --group dev python manage.py check` (settings por defecto) | **1** | `DB_NAME` — **baseline ambiental** idéntico, **NO** regresión |
| R3 | `uv run --group dev python manage.py check --settings=config.settings.development` | **0** | `no issues` |
| R4 | `uv run --group dev python manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` — **pero CIEGA** para `competencias`/`patrocinadores` (Django no las conoce) |
| R5 | `uv run --group dev python -m pytest core/tests -q` | **0** | **244 passed** — el guardián de registro VERDE **hoy**, y sólo porque sus listas cerradas siguen reflejando el estado **sin cablear** |
| R6 | sonda de registro (script **fuera del repo**) | **0** | 6 apps de dominio · 6 módulos de DI · 10 controllers · **34** rutas OpenAPI · **2** controllers **NO importables** |
| R7 | `uv run --group dev python -m pytest --collect-only -q` (**overlay de 8 apps**, fuera del repo) | **0** | **833 collected** — la recolección de la raíz deja de estar interrumpida |
| R8 | `uv run --group dev python -m pytest core/tests -q` (**overlay de 8 apps**) | **1** | **2 failed, 242 passed** — los 2 fallos son del guardián (`A0-RTV-04`) |
| R9 | `uv run --group dev python -m pytest -q` (**overlay de 8 apps**, suite completa) | **1** | **2 failed, 831 passed** (833 collected), 597 warnings, 212.10 s — **reproduce exactamente** el V24 del cierre anterior |
| R10 | inventario de códigos públicos (script **fuera del repo**) | **0** | catálogo **120** · códigos lanzados **78** · **33 sin catalogar** |
| G1 | `git rev-parse HEAD` | **0** | `fd1c4c123df3767ef6e86908565edf2d4c27c00a` — sin commit |
| G2 | `git status --short -- Aplicacion/backend` | **0** | **122 líneas, idénticas** al estado de entrada — **cero** ficheros del backend creados, modificados o borrados |
| G3 | SHA-256 de `Aplicacion/backend/db.sqlite3` antes/después de R2…R4 | **0** | **sin cambios** — las puertas de Django no abren la base (`USE_SQLITE` no fijado) |

**Veredicto por eje exigido:**

| # | Eje | Veredicto |
|---:|---|---|
| 1 | `settings/base.py` registra globalmente las apps de DOM-03…DOM-08 (incl. `competencias` y `patrocinadores`) | **FALLA** — 6 de 8 apps y 6 de 8 módulos de DI (`modules.competencias` / `modules.patrocinadores` ausentes) |
| 2 | `config/api.py` registra `PedidoController`, `InventarioController`, `CompetenciasController`, `PatrocinadorController` | **FALLA** — 0 de 4 (y 2 de ellos **ni siquiera importables**) |
| 3 | Registro de versiones del contrato | **FALLA** — `SCHEMA_VERSIONS` **no tiene `"competencias"`** (el módulo declara `1.0.0` y **no** tiene test de drift) |
| 4 | Catálogo público de errores | **FALLA** — **33** de **78** códigos sin catalogar (`marketplace` 13 · `competencias` 16 · `patrocinadores` 4) |
| 5 | Recolección de la raíz | **FALLA** — exit **2**, 725 collected + **6** errores de colección |
| 6 | Puertas de migración / `check` | **PARCIAL** — verdes por defecto, **ciegas** para las dos apps no registradas |
| 7 | Guardián de registro / guardián OpenAPI | **FALLA de alineación** — verde hoy; **rojo reproducible** en cuanto se cablea |

**Hallazgo NUEVO de esta pasada — dependencia de orden (probada en runtime):** `PedidoController` e `InventarioController` **importan** bien (`modules.marketplace` **sí** está registrada), pero `CompetenciasController` y `PatrocinadorController` **fallan al importar** con `RuntimeError: Model class modules.competencias.domain.models.auditoria.AuditoriaOperacion doesn't declare an explicit app_label and isn't in an application in INSTALLED_APPS` (y el equivalente de `patrocinadores`). ⇒ **el registro de las apps es PRECONDICITO del registro de los controllers**, no un cambio paralelo.

**Prueba fallida, enunciada exactamente:** *«`Aplicacion/backend/config/settings/base.py` registra globalmente las apps completadas de DOM-03…DOM-08, incluidas `competencias` y `patrocinadores`»* → **FALLA**, `INSTALLED_APPS` contiene 6 apps de dominio y **no** contiene `modules.competencias` ni `modules.patrocinadores` (R6, exit 0), y la recolección de la raíz se **interrumpe** con exit **2** (R1). *«`Aplicacion/backend/config/api.py` registra `PedidoController`, `InventarioController`, `CompetenciasController` y `PatrocinadorController`»* → **FALLA**, `controllers_registrados()` devuelve **10** controllers y **ninguno** de los cuatro (R6), y el esquema OpenAPI expone **34** rutas, **cero** de las **24** que aportarían (R6).

**Lo que NO se hizo y por qué:** no se registró ninguna app, ni ningún controller, ni se ampliaron las listas del guardián, ni se añadió `"competencias"` al registro de versiones, ni se catalogaron los 33 códigos, ni se añadió el test de drift de `competencias` (un test rojo no es evidencia), ni se tocó `Aplicacion/backend/db.sqlite3`. Todo eso cae en `Aplicacion/backend/**`, **raíz prohibida** para esta pasada, y el encargo fue explícito: *si la validación revela un cambio de código ausente, detener y reportarlo; no repararlo en esta pasada*.

**Cambios de estado:** **ningún** paquete cambia de estado. `DOM-03` (cableado **aplicado**: `modules.salesianos_fest` registrada, `PaseController` + `AdminPaseController` registradas), `DOM-05`, `DOM-06`, `DOM-07` y `DOM-08` **siguen `completed`** porque sus **paquetes** están verdes y ejecutados; el bloqueo es del **cableado de A0**, una fila de estado distinta. Lo que cambia es la **evidencia** de sus filas (se apunta al informe nuevo y se nombra el bloqueo vigente). `FND-06`/`FND-07`/`FND-08`/`UI-01`/`UI-02`/`UI-03` **sin tocar**.

**Changed files (2, ambos dentro de las raíces permitidas):** creado `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/A0-wiring-validation.md` · modificado `Aplicacion/task/salesianos-fest-rebuild/STATE.md` (esta transición + las 4 filas de DOM-05/06/07/08). **Fuera del repositorio** (temporal, no versionado): `%TEMP%\opencode\{a0_wiring_probe,a0_catalog_probe,a0_all_apps_overlay}.py`.

**Regressions:** none — el barrido del backend está verde (244 passed en `core/tests`; 831 passed + 2 fallos **de A0** con las ocho apps registradas). No commit. `git stash` / `git reset` / `git checkout` / `git commit`: **nunca invocados**.

**Concurrencia preservada (ACTIVA durante la pasada):** otros agentes escribieron **en paralelo** en `Aplicacion/frontend/src/features/{auth,inscripciones,pases,public,marketplace}/**` (mtimes 17:32–18:15, **simultáneos** a esta pasada) y en `evidence/ui/{UI-02,UI-03}-*.md` (17:41 / 17:48). **Ninguno de esos ficheros lo escribió esta pasada**: las únicas dos escrituras de la pasada son `STATE.md` y `evidence/foundations/A0-wiring-validation.md`. `Aplicacion/backend/**` quedó con las **mismas 122 líneas** de `git status` que tenía a la entrada (**cero** ficheros del backend creados, modificados o borrados) y `db.sqlite3` con el **mismo SHA-256**. `contract/**` y `Aplicacion/plan/**`: **sin tocar**. Nada se revirtió, nada se fusionó.

**Rollback:** borrar `evidence/foundations/A0-wiring-validation.md` → revertir las 4 filas de DOM-05/06/07/08 y esta transición en el `STATE.md` y en los topics de Engram → los tres scripts de `%TEMP%\opencode\` se pueden borrar sin efecto. **NO** revertir ni resetear `fd1c4c12`.

**Consumers unblocked:** **ninguno nuevo**. **Sigue bloqueado:** **API-03** · **API-05** · **XCT-01** · **XCT-03** · **VER-01…VER-03** — todos dependen del registro de las rutas.

**Next packet:** **el cableado global de A0** (`A0-RTV-01` → `A0-RTV-05`) sobre `Aplicacion/backend/config/**` + `Aplicacion/backend/core/**`, en **un solo cambio coordinado**: (1) `LOCAL_APPS` + `INJECTOR_MODULES` con las dos apps y sus dos módulos de DI; (2) `config/api.py` con los cuatro controllers, **en ese orden**; (3) `SCHEMA_VERSIONS["competencias"] = "1.0.0"`; (4) las **cinco** listas cerradas del guardián, **en el mismo cambio**; (5) los **33** códigos en `PUBLIC_ERROR_MESSAGES`; (6) el test de drift de `competencias`, **después** de (3). **Puertas de aceptación:** raíz `pytest --collect-only` exit **0** · suite completa **833 collected → 833 passed** · `check` y `makemigrations --check` verdes **en el registro permanente** · **24** rutas nuevas en el esquema OpenAPI.

**Decisiones abiertas: NO se cerró ninguna y NO se inventó ninguna.** `H-01` · `PD-01`/`PD-02`/`GOV-01-OPEN-08` · `OD-DOM05-01`…`03` · `OD-DOM06-01` · `OD-DOM07-01`…`05` · `OD-DOM08-01`…`06` · `R-RTV-04` (datetimes sin `tzinfo` en las fixtures de `competencias` — warning de las **fixtures**, no de la lógica de dominio) · `A0-RTV-06` (`core.media` deja directorios vacíos) · `A0-RTV-07` (`*.sqlite3` en `.gitignore`) · `A0-RTV-08` (`00-matriz-tareas.md` sin sincronizar) · `FND-03A` (la autenticación: existe en el árbol, **sin fila ni artefacto** — **A0 debe abrirlos**).

---

### 2026-11-19 — API-01 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/api-01-apply-progress` (topic packet-específico) + `sdd/salesianos-fest-rebuild/apply-progress` (índice acumulativo, upsert) · **Owner:** A7
**Original task IDs:** `T-070`, `T-071` (2 de los 54 IDs del plan) · **Branch:** `master` · **Rollback point:** sin commit creado (`git stash`/`reset`/`checkout`/`commit` **nunca** invocados)
**Informe canónico:** `evidence/api/API-01-public-account-integration.md`

> **ESTADO: `verification_required`.** La pasada de **implementación** está aplicada; el paquete **NO** se promueve a `completed` porque la verificación en runtime está **DIFERIDA**: las pruebas se **escriben** pero **no se ejecutan**, y la auditoría de navegador de cinco anchos no se ha hecho. El ÚNICO comando de runtime fue `npx tsc --noEmit`.

**La regla que decidió el paquete (`D-API01-01`):** **sólo se ligation las rutas REGISTRADAS.** El paquete se abrió leyendo la verdad del backend — `Aplicacion/backend/config/api.py` (la lista cerrada de `registrar_controladores`) y `Aplicacion/backend/core/tests/integration/test_registration_extension.py` (la lista cerrada `RUTAS_DE_DOMINIO_CONGELADAS`) — y **no** el plan. De los nueve page IDs del paquete sólo **tres** datasets tienen ruta registrada con presenter congelado: **edición** (`RT-ED-01`), **identidad** (`RT-ID-01/02/03`) y **sesión** (`GET /auth/me`). **Cinco** no tienen NINGUNA ruta: `RT-ID-04` (`/mi-cuenta/resumen`), `RT-ID-05` (`/mi-cuenta/compras`), `RT-ID-06` (`/mi-cuenta/compras/{compra_id}`), `RT-RC-01` (`/recuperar-compra`) y el registro de cuenta de `AUTH-02`. Esos **no** se ligation: no se inventó ninguna URL, no se ató ningún controller no registrado y no se escribió un espejo Zod de un wrapper que no tiene presenter. El área de cuenta y la recuperación **conservan su estado honesto** y la ruta que necesitan queda como petición a A0.

**Delivered:** el espejo Zod 1:1 de `EdicionActualOut` + servicio + factoría de claves + `queryOptions` + hook + un panel cliente con los estados honestos (`S-01` esqueleto, `S-02` vacío en `404`, `S-04` error recuperable con reintento) ligado a `PUB-02`; el espejo Zod 1:1 de `DocumentoConsultaOut`/`PersonaResueltaOut`/`PersonaOut` y de `SesionUsuarioOut` + los tres servicios de identidad + el servicio de sesión + sus hooks con invalidación **dirigida**; la guardia `S-06` de sesión expirada de `ACCOUNT-01` leída del backend (`GET /auth/me`), porque la cookie puede sobrevivir al token.

**Ficheros (16 creados + 12 modificados + 3 eliminados, todos dentro de las raíces permitidas):** creados `features/public/{schemas/edicion.schema.ts, services/edicion.service.ts, utils/edicion.claves.utils.ts, hooks/useEdicionActual.ts, components/EdicionActualPanel.tsx, __tests__/edicion-integration.test.ts}`, `features/auth/{schemas/{identidad,sesion}.schema.ts, services/{identidad,sesion}.service.ts, utils/auth.claves.utils.ts, hooks/{useIdentidad,useSesionActual}.ts, __tests__/identidad-sesion-integration.test.ts}`, `features/cuenta/{components/PanelSesion.tsx, __tests__/cuenta.ejemplos.ts}`; modificados `features/public/{views/InformacionView.tsx, components/index.ts, components/RecuperarCompraForm.tsx, schemas/recuperar-compra.schema.ts}`, `features/auth/{hooks/index.ts, hooks/useDocumentoLookup.ts, schemas/index.ts, services/index.ts}`, `features/cuenta/{components/index.ts, types/cuenta.types.ts, __tests__/cuenta-estados.test.tsx}`, `app/(cuenta)/mi-cuenta/page.tsx`; eliminados `features/public/fixtures/edicion.fixture.ts`, `features/cuenta/fixtures/cuenta.fixture.ts` y `features/auth/services/documento.service.ts` (doble dueño de `RT-ID-01` con la forma desviada `razon_social`). **Ninguna raíz prohibida fue tocada** (ni `components/shell/**`, ni `components/ui/**`, ni `globals.css`, ni providers, ni `src/lib/**`, ni `src/hooks/**`, ni `src/shared/**`, ni `src/types/**`, ni `src/errors/**`, ni `features/{portada,inscripciones,pases,marketplace,admin,theme}/**`, ni `app/(portada)/**`, ni `app/(auth)/**`, ni el backend, ni `contract/**`, ni el `frontend/**` raíz).

**Pruebas ESCRITAS, NO EJECUTADAS (2 suites):** `features/public/__tests__/edicion-integration.test.ts` · `features/auth/__tests__/identidad-sesion-integration.test.ts`.

**Comandos / códigos de salida (workdir `Aplicacion/frontend`):** `npx tsc --noEmit` **2** → **2** → **2** → **0** → **2** → **2** → **1** (7 corridas; 4 errores sintacticos en `features/inscripciones/__tests__/inscripcion-transporte.test.ts`, **concurrentes y ajenos** de API-02; despues 3 errores en `features/pases/views/{PaseGestionarRuta,PaseGestionarView}.tsx`, **concurrentes y ajenos** de API-03; y las dos ultimas volvieron a estar ROJAS solo por el arbol concurrente y ajeno de API-03). **0 errores en las raíces de este pacote en todas las corridas.** `git status --short` 0. **NOT RUN:** `vitest`, `biome check`, `next build`, `npm install`, servidores, navegadores, la auditoría de cinco anchos, `git stash`, `git commit`, `git reset`, `git checkout`.

**Borrado de fixtures (prueba):** el token `PROVISIONAL_CONTRACT_FIXTURE` **no** sobrevive en `features/public/**`, `features/cuenta/**` ni `features/auth/**` (**0 coincidencias**); **0** referencias a `cuenta.fixture`/`edicion.fixture`/`documento.service` en todo `src`; ningún módulo de producción importa un fixture; ninguna rama `catch` cae a un fixture; ninguna ruta oculta. El token **sigue** en `features/pases/**` y `features/marketplace/**` (API-03) y en `features/portada/fixtures/**` (**PUB-01**, fuera de las raíces de este paquete) — petición a A0, no tocados.

**Regressions:** none. No commit. `git stash` never invoked.

**Deviations:** `D-API01-01`…`09` · **A0 requests:** `A0-API01-01`…`07` (`A0-API01-01`: las tres rutas de cuenta **no existen**; `A0-API01-02`: la recuperación **no existe**; `A0-API01-03`: el registro de cuenta **no existe**; `A0-API01-04`: el catálogo de la portada sigue apuntando a rutas inexistentes; `A0-API01-05`: el espejo de error compartido no acepta `details: null` ni lleva `field_errors[]`; `A0-API01-06`: el hogar canónico del dataset de edición es `features/edition/**`; `A0-API01-07`: `ApiQueryError` vive en un módulo de hooks).

**Workload:** el artefacto del paquete **NO lleva `Review Workload Forecast`** → NO exigía decisión de cadena/tamaño (mismo precedente que DOM-06, FND-07/08, UI-01, UI-02 y UI-03); el tamaño **REAL** (~1 100 líneas) excede el presupuesto de 400 por ≈ **2.7x** y **se reporta a A0**. **4 slices autónomos** (WU-1 edición · WU-2 identidad y sesión · WU-3 guardia de cuenta y borrado de fixtures · WU-4 suites); rollback WU-4 → WU-1.

**Concurrency preservada:** otros agentes escribieron **en paralelo** en `src/features/{inscripciones,pases,auth}/**`; **sus árboles no fueron tocados, revertidos ni fusionados** y **sus filas del tablero no se editaron**. De `features/auth/**` sólo se tocaron los cinco ficheros que este paquete necesitaba.

**Rollback:** revertir WU-4 → WU-1 (borrar los 16 creados y revertir los 12 modificados y los 3 eliminados) → revertir la fila de API-01 y esta transición del `STATE.md` y de los topics. **NO** revertir ni resetear ningún commit previo.

**Consumers unblocked:** **API-02** (el patrón de dataset, la invalidación dirigida y el espejo de `EstadoOperativo` ya tienen dueño) · **API-03** (el espejo de `EdicionActualOut` es reutilizable por el catálogo y por la tienda) · **XCT-01**…**XCT-03** · **VER-01**…**VER-03**.

**Next packet:** **API-02** (`wave-03-api-integration/API-02-inscription-integration.md`) y, en paralelo, **API-03** y **UI-04**/**UI-05**. `XCT-02` sigue bloqueado hasta cerrar API-02…API-05 y XCT-01.
---

### 2026-11-19 - API-02 -> verification_required

**Timestamp:** 2026-11-19 (local) - **Apply-progress observation:** `sdd/salesianos-fest-rebuild/api-02-apply-progress` (topic packet-especifico) + `sdd/salesianos-fest-rebuild/apply-progress` (indice acumulativo, upsert) - **Owner:** A7
**Original task IDs:** `T-072` (1 de los 54 IDs del plan) - **Paquete:** `wave-03-api-integration/API-02-inscription-integration.md` - **Rama:** `master` - **Punto de rollback:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit creado; `git stash`/`reset`/`checkout`/`commit` **nunca** invocados)
**Informe canonico:** `evidence/api/API-02-inscription-integration.md`
**Freezes respetados:** `FREEZE-ENV-1.0.0` (FR-01) - `FREEZE-PS-1.0.0` (FR-07) - `FREEZE-CM-1.0.0` - `FREEZE-ED-1.0.0` (FR-02)

> **ESTADO: `verification_required`.** La pasada de **implementacion** esta aplicada; el paquete **NO** se promueve a `completed` porque la verificacion en runtime esta **DIFERIDA** (preferencia `#11299`): las pruebas se **escriben** pero **no se ejecutan**, y la auditoria de navegador de cinco anchos no se ha hecho. El UNICO comando de runtime fue `npx tsc --noEmit` (exit **0**).

**Reconciliacion (2026-11-19, DESPUES de la ejecucion concurrente de API-01 y API-03):** las **raices de este paquete dieron 0 errores en TODAS las corridas** (V1 a V4) - el unico error propio (V1) fue corregido en esa misma corrida. La puerta global **solo** estuvo ROJA en **dos** corridas (V2 y V3) y **las dos** por arboles **concurrentes y ajenos** (`src/features/pases/**` y `src/features/marketplace/views/**`, de **API-03**): **no fueron tocados, revertidos ni fusionados** y sus duenos los repararon. La **propia corrida final de este paquete (V4) salio 0** y la **ULTIMA corrida global registrada** -la verificacion final de **API-03** (`V4`, exit **0**)- deja la **puerta global del proyecto VERDE**. Ese ultimo exit code lo **reporta la evidencia de API-03** y **NO lo midio este paquete**: esta reconciliacion **no ejecuto ningun comando**. **API-02 NO se promueve a `completed`**: sus 6 suites siguen **ESCRITAS y NO EJECUTADAS** y su auditoria de navegador de cinco anchos sigue sin hacer. **No se toco nada de API-01 ni de API-03**: ni sus ficheros, ni sus filas del tablero, ni sus evidencias.


**La regla que decidio el paquete (`D-API02-01`):** **solo se ligan rutas REGISTRADAS, y el espejo es 1:1 con el presenter que las publica.** El paquete se abrio leyendo la verdad del backend - `Aplicacion/backend/config/api.py` (la puerta `registrar_controladores`), los controllers `catalogo_controller.py` e `inscripcion_controller.py`, los schemas `catalogo_schemas.py` / `inscripcion_schemas.py` / `pool_schemas.py` / `compra_cupos_schemas.py`, los presenters `catalogo_presenter.py` / `inscripcion_presenter.py` / `pool_presenter.py` / `compra_cupos_presenter.py` y las suites e2e del modulo - y **no** el plan. **Ninguna URL inventada, ningun controller no registrado atado, ningun espejo Zod de un wrapper sin presenter.** La exploracion `#11377` ya habia registrado que la capa copiada de `features/inscripciones` hablabla el dialecto **congelado** (`/catalogo/paquetes/`, `/catalogo/promociones/`, `/cotizaciones/`, `/inscripciones/completa/`) y no podia parsear **una sola** respuesta real.

**Delivered:** el espejo Zod 1:1 de los wrappers del backend objetivo (`CatalogoPaquetesOut`, `CatalogoDisciplinasOut`, `PaqueteOut`, `DisciplinaOut`, `PrecioOut`, `BeneficioOut`, `InscripcionDetalleOut`, `EquipoOut`, `EquiposInscripcionOut`, `CompraOut`, `InscripcionInicialOut`, `InscripcionInicialIn`, `EquipoIn`, `PoolOut`, `ParticipacionOut`, `ImpedimentoOut`, `ParticipanteAsignarIn`, `ComprarCuposIn`, `CompraCreadaOut`); tres servicios sobre el **unico** dueño de transporte (`src/lib/api.ts::apiSend`); una factoría de claves con **cuatro** namespaces; cuatro lecturas y cuatro escrituras con invalidacion dirigida; y las dos vistas del area ligadas a las rutas reales.

**Reglas decisivas:** `D-API02-02` **el importe viaja como CADENA** (cadena probada: `success_response` -> `model_dump(mode="json")` -> `ninja/operation.py` revalida y dumpea en modo python -> `NinjaJSONEncoder` (hijo de `DjangoJSONEncoder`) renderiza el `Decimal` con `str(o)`); cierra `OD-A0R2-01` / `A0-UI02-01` a nivel de cable. `D-API02-03` **cuatro datasets, cuatro namespaces**: la EDICION viaja en la clave del catalogo y la INSCRIPCION en la del detalle y del pool; **no** viaja ningun filtro ni pagina porque **ninguna** ruta registrada del area filtra ni pagina (`RT-IN-01` no esta implementada) y un `page` en la clave crearia una segunda entrada para la MISMA respuesta. `D-API02-04` **se ESCRIBE cuando la forma exacta se preserva y se INVALIDA cuando no**: las tres rutas del pool responden con el `PoolOut` ACTUALIZADO, asi que el pool se escribe en su entrada (solo si la entrada ya existe: sin huerfanos) y el detalle se invalida; la compra de cupos responde con `CompraCreadaOut`, que **NO** es un pool, asi que invalida; el alta responde con una inscripcion **nueva**, asi que invalida y no crea la entrada de una inscripcion que nadie leyo. `D-API02-05` **el navegador nunca deriva un valor de negocio**: los TRES numeros del pool se imprimen como los publica el servidor y la auditoria estatica prohibe la aritmetica en los componentes, en las vistas, **en los hooks, en los servicios y en las utilidades**. `D-API02-06` el **422 original** vuelve a subir y el `GenericForm` de FND-07 marca cada control una vez; los fallos se ramifican por **STATUS HTTP**, nunca por el codigo. `D-API02-07` la recuperacion alcanzable es el **alta idempotente** (el reintento devuelve la inscripcion que ya existe y el asistente deja de ofrecer el formulario): la costura `pendiente` se CONSERVA pero **ninguna ruta puede llenarla** (`RT-IN-01` no esta implementada). `D-API02-08` `RT-IN-04` existe y esta registrada pero **NO** se liga: `InscripcionDetalleOut.equipos` ya publica los equipos y ligar los dos les daria dos duenos en la cache (FND-08, regla 1).

**UI que este paquete es dueno:** `SeccionParticipantes` y `FormularioParticipante` (nuevos) - las dos escrituras del pool (`RT-IN-05`, `RT-IN-06`) y la **confirmacion S-10** de la retirada, que nombra el efecto (libera el cupo de ESA inscripcion; NO cancela la compra, NO devuelve dinero y NO toca el inventario); la persona se asigna **POR DOCUMENTO** y la resuelve el servidor, de modo que el navegador no resuelve personas ni inventa identificadores. `PanelCompras` dice la verdad: el backend **no publica** un listado de las compras, asi que la seccion lo dice en vez de mostrar una lista vacia que se leeria como "no hay compras". `PaqueteCard` y `PasoResumen` imprimen `nombre` de la disciplina: el `DisciplinaOut` del objetivo tiene `slug`, **no** la `sigla` del arbol congelado.

**Ficheros (17 creados + 17 modificados + 7 eliminados, todos dentro de las raices permitidas `Aplicacion/frontend/src/features/inscripciones/**`):** creados `schemas/{catalogo,compra-cupos,pool,participante}.schema.ts`, `schemas/inscripcion.schema.ts` (reescrito), `services/{catalogo,inscripcion,respuesta}.service.ts` + `services/index.ts`, `hooks/{useInscripcion,useInscripcionMutaciones}.ts`, `utils/{inscripcion.errores,inscripcion.payloads}.utils.ts`, `components/{FormularioParticipante,SeccionParticipantes}.tsx`, `__tests__/{inscripcion-mirrors,inscripcion-transporte}.test.ts` + `__tests__/inscripcion-participantes.test.tsx`; modificados `schemas/{index,alta-inscripcion}.schema.ts`, `types/inscripcion.types.ts` (los modelos de vista ahora se DERIVAN de los espejos), `hooks/{useCatalogo,index}.ts`, `utils/inscripcion.claves.utils.ts`, `components/{index,PanelCompras,PanelParticipantes,PaqueteCard,PasoResumen}.ts(x)`, `views/{InscripcionWizardView,MisInscripcionDetalleView}.tsx`, `__tests__/{inscripcion-estados.test.tsx,inscripcion-detalle.test.tsx,inscripcion-responsive.test.ts}`; eliminados `fixtures/inscripcion.fixture.ts` (y el directorio `fixtures/`), `hooks/{useCotizacion,useCrearInscripcion}.ts`, `schemas/{cotizacion,paquete}.schema.ts`, `utils/inscripcion.utils.ts`, `components/PasoDeclaraciones.tsx`. **Las dos rutas del paquete NO se tocaron** (`app/(cuenta)/inscripcion/page.tsx` y `app/(cuenta)/mis-inscripciones/[id]/page.tsx`): UI-02 ya las dejo componiendo las vistas y API-02 ligo el transporte DENTRO de la feature, asi que las paginas siguen funcionando sin cambios. **Ninguna raiz prohibida fue tocada**: ni `src/app/**`, ni `src/lib/**`, ni `src/hooks/**`, ni `src/shared/**`, ni `src/errors/**`, ni `components/{shell,ui,genericForm}/**`, ni `features/{cuenta,public,auth,portada,admin,pases,marketplace}/**`, ni el backend, ni `contract/**`, ni `Aplicacion/plan/**`, ni `frontend/**` de la raiz.

**Pruebas ESCRITAS, NO EJECUTADAS (6 suites):** `__tests__/inscripcion-mirrors.test.ts` (node) - `__tests__/inscripcion-transporte.test.ts` (jsdom) - `__tests__/inscripcion-estados.test.tsx` (jsdom) - `__tests__/inscripcion-detalle.test.tsx` (jsdom) - `__tests__/inscripcion-participantes.test.tsx` (jsdom) - `__tests__/inscripcion-responsive.test.ts` (node). El doble vive en el **limite del transporte** (`apiSend`), no en el servicio ni en el schema: la ruta, el envelope y la politica de cache quedan bajo prueba y ningun modulo de produccion lleva un mock.

**Comandos / exit codes:**

| # | Comando | Workdir | Exit | Resultado |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | **3 errores de este paquete**: `enabled` no es una propiedad de `DatasetQueryOptionsInput` (x2) y `obtenerEquipos` seguia exportado por el barrel tras quitarlo. Los tres se corrigieron. |
| V2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | **0 errores en las raices de este paquete.** La puerta global estaba ROJA por un arbol **concurrente y ajeno**: `src/features/pases/**`. **NO** tocado, revertido ni fusionado; su dueno lo reparo. |
| V3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | **0 errores en las raices de este paquete.** La puerta global estaba ROJA por otro arbol **concurrente y ajeno**: `src/features/marketplace/views/**`. **NO** tocado; su dueno lo reparo. |
| V4 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | **LIMPIO, puerta global VERDE.** |
| V5 | `git status --short -- .../features/inscripciones` | raiz | **0** | el arbol entero sigue `??` (sin versionar), como lo dejo UI-02. Este paquete **no** hizo ninguna operacion git. |
| V6 | grep `PROVISIONAL_CONTRACT_FIXTURE` en `features/inscripciones/**` | raiz | **0** | **0 coincidencias.** El token sobrevive en `features/pases/**` y `features/marketplace/**` (API-03) y en `features/portada/fixtures/**` (PUB-01, fuera de las raices). |
| V7 | grep `/inscripciones/completa`, `/cotizaciones`, `/catalogo/promociones`, `/catalogo/categorias` en `src/**` | raiz | **0** | **0 llamadas de produccion.** Las unicas apariciones son las aserciones **negativas** de las suites. |

**NADA MAS se ejecuto.** `vitest`, `biome check`, `next build`, `npm install`, servidores, navegadores, la auditoria de cinco anchos, `git stash`, `git commit`, `git reset`, `git checkout`: **NOT RUN**.

**Borrado de fixtures (prueba):** la fixture provisional, sus cuatro hooks congelados y sus dos schemas congelados son **GONE**; **0** coincidencias del token provisional en `features/inscripciones/**`; **0** referencias a los ficheros eliminados en todo `src`; ningun modulo de produccion importa un fixture; ninguna rama `catch` cae a un fixture.

**Regressions:** none (la unica puerta ejecutada - `tsc` - esta VERDE, V4). No commit. `git stash` never invoked.

**Deviations:** `D-API02-01`...`11` (evidencia seccion 11): solo rutas registradas - el importe es una cadena - cuatro namespaces y ningun filtro ni pagina - escribir/invalidar segun la forma - el navegador no deriva nada - el 422 original sube - la costura `pendiente` no tiene ruta - `RT-IN-04` no se liga (un solo dueno de los equipos) - la validacion de cliente se CONSERVA junto al espejo de cable - la disciplina se imprime por `nombre` y no por `sigla` - se quito el re-export de `Veredicto`/`EstadoOperativo` (acoplamiento con el area de cuenta que nadie usaba). **A0 requests:** `A0-API02-01`...`08` (`A0-API02-01`: `RT-IN-01` - el listado de las inscripciones del responsable - no esta implementado, sin el el asistente no puede saber que hay una inscripcion pendiente ANTES del alta; `A0-API02-02`: no hay ruta que liste las compras de una inscripcion; `A0-API02-03`: ningun presenter publica `BeneficioConcedido`; `A0-API02-04`...`06`: ratificacion de las rutas provisionales y de los nombres de los presenters; `A0-API02-07`: sincronizar `00-matriz-tareas.md`; `A0-API02-08`: el catalogo provisional de la portada sigue siendo el congelado y duplica el dataset de `inscripcion.catalogo.paquetes`).

**Workload:** el artefacto del paquete **NO lleva `Review Workload Forecast`**, asi que NO exigia una decision de cadena/tamano (mismo precedente que DOM-06, FND-07/08, UI-01, UI-02, UI-03 y API-01); el tamano **REAL** (~4 400 lineas cambiadas) excede el presupuesto de 400 lineas por ~**11x** y **se reporta a A0** como hallazgo. **8 unidades autonomas** (WU-1 espejos - WU-2 transporte y claves - WU-3 lecturas - WU-4 escrituras y politica de cache - WU-5 asistente y detalle - WU-6 personas del pool - WU-7 borrado de la capa congelada - WU-8 suites). Orden de rollback: WU-8 -> WU-1. Sin commit, sin `git stash`.

**Concurrency recorded.** `src/features/pases/**` y `src/features/marketplace/**` (trabajo concurrente de API-03), `src/features/{cuenta,public,auth,portada}/**` (UI-01, API-01) y el resto de `src/app/**` **no fueron tocados, revertidos ni fusionados**, y **sus filas del tablero NO se editaron**. Solo se toco `features/inscripciones/**` y esta transicion del `STATE.md`.

**Rollback:** revertir WU-8 -> WU-1 (borrar los 17 creados, revertir los 17 modificados y restaurar los 7 eliminados desde el checkpoint `fd1c4c12`) -> revertir la fila de API-02 de este tablero y de los topics. **NO** revertir ni resetear `fd1c4c12`. El shell compartido, los providers, el tema y las demas areas quedan intactos.

**Consumers unblocked:** **API-04** (la superficie admin de las inscripciones lee los mismos wrappers) - **API-03** (la decision del importe en cable ya esta tomada) - **XCT-02** (con la tabla de readiness de la evidencia, seccion 14) - **XCT-03** - **VER-01...VER-03**.

**Next packet:** **XCT-02** (depende de **API-04**, **API-05** y **XCT-01**; **API-03 ya se aplico** tras este paquete) y, en paralelo, **API-04** y **API-05**. Con autorizacion explicita del usuario, y en paralelo, la verificacion diferida de **FND-06**, **FND-07**, **FND-08**, **UI-01**, **UI-02**, **UI-03**, **API-01**, **API-02** y **API-03**.

---

### 2026-11-19 — API-03 → verification_required (implementation applied, NOT closed)

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** topic `sdd/salesianos-fest-rebuild/api-03-apply-progress` · **Owner:** A7
**Original task IDs:** `T-073`, `T-074` (2 of the 54 source-defined IDs) · **Branch:** `master` · **Rollback point:** unchanged · **No commit created. `git stash` never invoked.**

**Delivered:** the commercial data layer of `PASS-01`, `PASS-02`, `SHOP-01` and `SHOP-02` against the **REGISTERED** controllers only — `PaseController` (`RT-PS-01`…`RT-PS-05`, `RT-CM-02`, `RT-RT-03`) and `ProductoController` (`RT-MK-01`…`RT-MK-03`). Zod mirrors 1:1 of the presenters, one service per feature, one query-key factory per dataset, `queryOptions` reads, create-only payloads, exact invalidation and the deletion of the two `PROVISIONAL_CONTRACT_FIXTURE` modules. **25 files created + 21 modified + 2 fixtures deleted** in `Aplicacion/frontend/**` (~5 000 changed lines).

**Registration truth (re-verified):** `PaseController`, `AdminPaseController`, `ProductoController` and `PagosController` ARE registered in `Aplicacion/backend/config/api.py`. **`PedidoController` and `InventarioController` are STILL NOT registered** (`A0-RTV-02`, blocking): `POST /marketplace/pedidos`, `GET /marketplace/pedidos/{token}` and the whole inventory/delivery surface **do not exist**. **NOTHING of that surface was bound**: `SHOP-02` cannot create the order, `SHOP-03` cannot show it, and the mirrors of the order shapes exist as a **seam only** (`features/marketplace/schemas/pedido.schema.ts`, banner "NOT REGISTERED · NOT BOUND · NOT CALLED").
**Commands / exit codes (workdir `Aplicacion/frontend`):** `npx tsc --noEmit` **1** (1 own error: `CompraPases.beneficiarios` without `estado_etiqueta`) → **0** → **0** → **0** (final, clean). `git status --short` 0 · `git diff --stat` 0 · grep of `PROVISIONAL_CONTRACT_FIXTURE` and of the fixture imports in the two features → **0 matches**. **NOT RUN:** vitest, biome, `next build`, npm install, servers, browsers, the five-width audit, git stash/commit/reset/checkout.

**Tests WRITTEN, NOT EXECUTED (4 suites):** `features/pases/__tests__/pases-estados.test.tsx` · `features/pases/__tests__/pase.service.test.ts` · `features/marketplace/__tests__/marketplace-estados.test.tsx` · `features/marketplace/__tests__/marketplace.service.test.ts`. The data of the suites is now the **contract parsed by the same Zod mirror** the service uses — no provisional fixture remains.

**Regressions:** none (the only gate executed, `tsc`, is GREEN). No commit. `git stash` never invoked.

**Deviations:** `D-API03-01`…`07` (evidence §7.1) — the guest link carries the token in the path **and** the batch id in the query (`?compra=`) because the backend needs both and the token may never travel in the query; the category slug of the URL is resolved to the `categoria_id` the server filters by; the **labels** of the machine codes are resolved by a feature adapter because the `DOM-03` presenters publish codes and no wording (`A0-UI03-04`); a `cargando` state was added; the **assignment form of `PASS-02`** was built (owed by `UI-03`, `D-UI03-05`).
**A0 requests:** `A0-API03-01` **register `PedidoController`** (otherwise the store checkout and `SHOP-03` cannot work) · `A0-API03-02` **register `InventarioController`** (stock/reservation/delivery) · `A0-API03-03` **ratify `P-01`**: the guest link needs the batch id next to the token, or a route that resolves a token → batch · `A0-API03-04` **publish the wording of the codes** (`PENDIENTE`/`PAGADA`/`ANULADA`, `ACTIVO`/`REVOCADO`) so the frontend adapter can be deleted · `A0-API03-05` **publish a currency** for the catalogue of the store and for the pass catalogue · `A0-API03-06` **sync `00-matriz-tareas.md`** (rows `T-073`/`T-074` still read `pending`; the matrix is outside every packet's edit roots).

**Blocked and reported (evidence §7):** `B-03-01` order creation · `B-03-02` order tracking · `B-03-03` inventory/delivery · `B-03-04` the payment verdict (`estado_operativo`) belongs to `features/pagos` (**XCT-03**) and is not reachable by a guest with only a token · `B-03-05` the guest link seam · `B-03-06` the missing currency.

**Workload:** the packet artefact carries **NO `Review Workload Forecast`**, so no chain/size decision was required (same precedent as DOM-06, FND-07/08, UI-01, UI-02, UI-03, API-01, API-02). The REAL size (~5 000 changed lines) exceeds the 400-line budget by ~**12x** and is **reported to A0**. **8 autonomous work units** (WU-1 mirrors · WU-2 transport and keys · WU-3 reads · WU-4 writes and cache policy · WU-5 the two forms · WU-6 the containers and the routes · WU-7 fixture deletion · WU-8 the suites). Rollback order: WU-8 → WU-1. No commit, no `git stash`.

**Concurrency recorded.** The concurrent work of `UI-02`/`API-02` in `features/inscripciones/**`, of `UI-01`/`API-01` in `features/{cuenta,public,auth,portada}/**` and the three route files of `UI-03` that this package did **not** edit (`pases/gestionar/layout.tsx`, `tienda/pedidos/layout.tsx`, `tienda/pedidos/[token]/page.tsx`) were **NOT touched, reverted or merged**, and their rows of the board were **NOT** edited. Only `features/pases/**`, `features/marketplace/**`, the **4 assigned public routes**, this evidence file and this transition were written.

**Consumers unblocked:** **XCT-01** (the pass right and its revocation are real) · **XCT-03** (the purchase returns `orden_pago_id`; the payment verdict has a named owner) · **VER-01…VER-03** · **API-04** (the admin surface reads the same wrappers).

**Next packet:** **XCT-01** and **XCT-03** (the payment/media owner) once A0 registers `PedidoController`; in parallel, the deferred verification of **API-03** and of the already applied **FND-06/07/08, UI-01/02/03, API-01/02**.
---

### 2026-11-19 — UI-05 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/ui-05-apply-progress` (packet-specific) · **Owner:** A7
**Original plan tasks:** no direct source-plan ID (preparatory slice for `API-05` and `XCT-01`)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)

**Delivered:** the competition, validation and sponsor route shells, in **three NEW features** that did not exist before this packet — `features/competencias/**`, `features/validaciones/**`, `features/patrocinadores/**` — with the **eight** route files rewired: `ADM-10` `/administracion/competencias`, `ADM-11` `/administracion/competencias/[id]`, `ADM-12` `/administracion/competencias/[id]/cuadro`, `ADM-13` `/administracion/competencias/agenda`, `ADM-16` `/administracion/pases/validar`, `ADM-20` `/administracion/marketplace/entregas`, `ADM-21` `/administracion/patrocinadores`, `ADM-22` `/administracion/validaciones`.

**The rule that decided the honesty of the states (`D-UI05-01`):** a route NEVER draws a datum that the backend cannot return. The registration truth was re-proved against the working tree: `modules.competencias` and `modules.patrocinadores` are still out of `INSTALLED_APPS` and `CompetenciasController` / `PatrocinadorController` are still unregistered (`A0-RTV-01`/`A0-RTV-02`) ⇒ their 16 + 1 routes DO NOT EXIST; the module `validaciones` DOES NOT EXIST AT ALL (so `RT-RT-01`/`RT-RT-02` are frozen but unimplemented and `RT-VA-01` is provisional); and `InventarioController` is unregistered ⇒ `RT-MK-10`/`RT-MK-11` do not exist. Every route therefore renders the honest state by default, and the populated compositions exist, are typed and are exercised by the suites — that is the code that `API-05` binds.

**What is bound to the backend, 1:1:** `CompetenciaListadoOut`, `CompetenciaDetalleOut`, `CompetenciaEquipoOut`, `RondaOut`, `EncuentroOut`, `ParticipanteOut`, `AgendaOut`, `EquipoElegibleOut`, `AvancePreviewOut`, `CorreccionPreviewOut`, `CorreccionImpactoOut` (`DOM-07`) · `PatrocinadorOut` + `PatrocinadorLogoOut` + `PatrocinadorImagenOut` (`DOM-08`) · `PaseBeneficiarioOut` (`DOM-03`) · `EntregaPendienteOut` + `PedidoLineaOut` (`DOM-06`/`DOM-05`).

**The rules de composición:** `D-UI05-02` el vocabulario es un espejo 1:1 de los `TextChoices` del backend y de los códigos congelados del ledger; un código desconocido conserva su texto y cae en el cubo `desconocido` — nunca se adivina · `D-UI05-03` UN panel de encuentro, alcanzable desde la lista, la agenda y el cuadro (no hay un segundo editor) · `D-UI05-04` la entrada y la recogida comparten la PRESENTACIÓN de la vista previa y nada más · `D-UI05-05` el cuadro se desplaza DENTRO de sí mismo (región nativa con `tabIndex=0`), nunca la página.

**shadcn (MCP ejecutado, `GOV-02-SH-01` y `GOV-02-SH-08`):** `drawer` RECHAZADO — su dependencia `vaul` NO está en `package.json` y `npm install` está prohibido (`A0-UI05-01`); se usó el `sheet` local · `scroll-area` RECHAZADO para el cuadro — el primitivo local sólo trae barra VERTICAL y el cuadro necesita una HORIZONTAL con foco visible · `carousel` RECHAZADO — trae etiquetas en inglés · `switch` RECHAZADO — ausente en el árbol local (`A0-UI05-02`) · `timeline` NO EXISTE en el registry · `alert-dialog`, `table`, `badge`, `empty`, `skeleton`, `alert`, `input`, `label`, `textarea`, `checkbox`, `input-group` comparados. **Ningún componente añadido. Ningún fichero de `components/ui/**` creado, modificado o sobrescrito. `get_audit_checklist` llamado.**

**Changed files (this packet — 48 paths, all inside the allowed roots):** created `Aplicacion/frontend/src/features/competencias/**` (21 files), `…/features/validaciones/**` (15 files), `…/features/patrocinadores/**` (10 files) and `…/evidence/ui/UI-05-competition-validation-shells.md`; modified the **8** route files under `Aplicacion/frontend/src/app/(administracion)/administracion/**` and this `STATE.md`. **0 deleted.**

**Commands / exit codes (workdir `Aplicacion/frontend`):**

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `npx tsc --noEmit` | **1** | 6 errores **PROPIOS** (`motivo`/`mensaje`, una errata y cuatro `ShellPermissionDenied` sin `title`) — corregidos en este paquete |
| V2 | `npx tsc --noEmit` | **0** | **LIMPIO**, proyecto entero |
| V3 | `npx tsc --noEmit` | **1** | 8 errores, **0 propios**: `features/admin/inscripciones/types/inscripciones-admin.types.ts` (4), `features/admin/operaciones/components/MarcoOperativo.tsx` (2), `features/admin/operaciones/index.ts` (2) — árbol **CONCURRENTE y FUERA de alcance** (el de **UI-04**, en vuelo en ese momento) **no tocado, no revertido, no fusionado**. Los errores de este paquete **NO son reproducibles en sus raíces** |
| R1 | `git status --short -- <mis raíces>` | **0** | 3 árboles nuevos (untracked) + 8 ficheros de ruta (modified) |

**NOT RUN** (prohibido por el contrato de lanzamiento, registrado como diferido, nunca como aprobado): `vitest` · `biome check` · `next build` · `npm install` · servidores · navegadores · la auditoría de cinco anchos · `git stash` · `git commit` · `git reset` · `git checkout`.

**Known baseline failures:** ninguno introducido por este paquete. Los 8 errores de V3 pertenecen a un árbol concurrente ajeno.
**Regressions:** none. Zero forbidden files modified. No commit created. `git stash` not invoked.

**Concurrent overlap observed (NOT touched, NOT merged):** `ADM-15` (`/administracion/pases`), `ADM-17` (`/administracion/marketplace`), `ADM-18` (`/administracion/marketplace/productos/[id]`) y `ADM-19` (`/administracion/marketplace/inventario`) **NO forman parte de lo entregado por este paquete**. Sus cuatro ficheros de ruta apuntan hoy a `features/admin/views/**` (`AdminPasesView`, `AdminMarketplaceView`, `AdminProductoDetalleView`, `AdminInventarioView`), que es la raíz de **FND-06**: **UI-04 lo DESCONOCE** (su alcance son seis page IDs, modificó seis ficheros de ruta y declara `features/admin/{components,views,utils}/**` como NOT touched) y **UI-05 no lo tocó** (raíz PROHIBIDA). El árbol procede del **agente `general` lanzado manualmente** de la sesión `salesianos-ui-general-agent-prompt-2026-11-19` (#11314), que trabaja **FUERA** del sistema de paquetes: esas cuatro rutas **no tienen fila, ni apply-progress, ni fichero de evidencia**, y **no** son las composiciones de UI-05 — el paquete de UI-05 sí las enumera entre sus plan IDs, así que **siguen debidas** a este alcance (`D-UI05-06`, `A0-UI05-08`). Los ocho shells de FND-06 que este paquete superó (`AdminCompetenciasView` y sus siete hermanos) quedan **sin referencia** y **NO se borraron** (`D-UI05-07`, `A0-UI05-04`).

**Desviaciones declaradas:** `D-UI05-01`…`13` (highlighted: `D-UI05-06` las cuatro rutas de ADM siguen debidas a este paquete (ver la transición de reconciliación); `D-UI05-08` la barra de filtros de `ADM-22` ofrece SÓLO el veredicto, porque los otros siete filtros necesitan los nombres de parámetro de `RT-VA-01`, que sigue PROVISIONAL; `D-UI05-12` los campos de `TicketPreviewOut`/`TicketConfirmadoOut` son PROVISIONALES porque no hay módulo `validaciones`).
**A0 requests:** `A0-UI05-01`…`08`.

**Consumers unblocked:** **API-05** (competitions, sponsors, validation and delivery binding) · **XCT-01** (the DERECHO and the acta of the delivery) · **XCT-02** · **VER-01…VER-03**.

**Next packet:** **API-05** (`wave-03-api-integration/API-05-competition-admin-integration.md`) — dependency satisfied — and, in parallel, **XCT-01**. The five-width browser audit and the execution of the three suites stay DEFERRED to the verification phase.

---

### 2026-11-19 — UI-04 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/ui-04-apply-progress` · **Owner:** A7
**Original task IDs:** none — the packet declares "No direct source-plan ID. Preparatory slice for downstream `API-04`."
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit created)

**Delivered:** the six administrative route shells of the operations area — `ADM-05` `/administracion/inscripciones`, `ADM-06` `/administracion/inscripciones/[id]`, `ADM-07` `/administracion/equipos`, `ADM-08` `/administracion/equipos/[id]`, `ADM-09` `/administracion/participantes` and `ADM-14` `/administracion/pagos` — in **five new domain-specific subfolders** under `Aplicacion/frontend/src/features/admin/**` (`operaciones` · `inscripciones` · `equipos` · `participantes` · `pagos`) plus the **6 route files** re-pointed.

**The rules that decided the composition:**

- `D-UI04-01` **ONE admin list pattern, not six** (`GOV-02-RB-03a`): `ListaOperativa` answers at every width with the SAME data — a card per row at 360/390 and a table from 768 with priority columns.
- `D-UI04-02` **a provisional fixture never reaches a route**: every route renders the honest state (`sin-datos`) by default; the populated compositions are exercised by the suites and are the code that API-04 binds.
- `D-UI04-03` **the verdict travels with its bucket** (`D-UI01-02`): the view model carries `estado_operativo` AND `rol`; a component NEVER branches on a business code. The adapter knows the EIGHT frozen codes of `EstadoOperativoPago` and neutralises the unknown ones.
- `D-UI04-04` **the filters live in the URL** (`GOV-02-RB-03b` · `D-UI01-10`): the page reads the query string, the filter bar and the search write it back, and the page number travels in the URL too.
- `D-UI04-06` / `D-UI04-07` **the cupos are three facts and the roster is three numbers**: neither is ever a balance nor an inference; the readiness is the verdict of the presenter.

**Registration truth (read in `Aplicacion/backend/config/api.py`):** **NONE** of the administrative routes of this area is registered — `RT-IN-07`, `RT-IN-08`, `RT-IN-09`, `RT-IN-10`, `RT-IN-11`, `RT-PG-04`, `RT-PG-05`, `RT-PG-06`, `RT-PG-07`, `RT-ID-07` and `RT-ID-08` **DO NOT EXIST**. Every route therefore keeps its HONEST state, every sensitive action is DISABLED with a written reason, and **no endpoint, payload, field or business rule was invented**. Every vocabulary of the interfaces comes from the REAL target backend (`EstadoInscripcion`, `EstadoEquipo`, `EstadoParticipacion`, `RolParticipante`, `EstadoOperativoPago`, `OrigenCompra`, `EstadoCompra`, `EstadoOrdenPago`, `OrigenPago`, `IntentoPagoOut`, `PoolOut`, `CompraOut`).

**shadcn (MCP executed para esta familia):** `shadcn_get_project_registries` (`@shadcn`) · `shadcn_list_items_in_registries` (**61** items de `registry:ui`) · búsquedas `table`, `sheet`, `tabs`. **Reutilizados:** `table` · `sheet` · `tabs` · `collapsible` · `alert-dialog` · `pagination` · `empty` · `skeleton` · `input`/`label` · `select`. **RECHAZADOS:** `drawer` (ausente y `components/ui/**` es raíz PROHIBIDA, sin install) · `accordion` (ausente) · `badge` (sin variantes de veredicto, así que el chip se COMPONE en la feature) · `item` (`ItemTitle` trunca) · `sidebar` (la navegación es de A0) · `field`/`form` (`GOV-02-SH-03`). **Ningún componente añadido. Ningún fichero de `components/ui/**` creado, modificado o sobrescrito. Ningún install ejecutado.**

**Changed files (this packet — 54 paths, all inside the allowed roots):** created **48** ficheros — `Aplicacion/frontend/src/features/admin/operaciones/**` (19), `./features/admin/inscripciones/**` (9), `./features/admin/equipos/**` (9), `./features/admin/participantes/**` (6), `./features/admin/pagos/**` (10) and `./evidence/ui/UI-04-admin-operations-shells.md`; modified the **6** route files under `Aplicacion/frontend/src/app/(administracion)/administracion/**` and this `STATE.md`. **0 deleted.**

**Commands / exit codes (workdir `Aplicacion/frontend`):**

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `npx tsc --noEmit` | **1** | 9 errores **PROPIOS** — el tipo `VeredictoOperativo` chocaba con el componente homónimo y `ShellErrorState` / `ShellPermissionDenied` exigen `title` explícito |
| V2 | `npx tsc --noEmit` | **0** | **LIMPIO**, tras renombrar el tipo a `Veredicto` y dar los `title` explícitos |
| V3 | `npx tsc --noEmit` | **0** | **LIMPIO**, tras las seis rutas y las cinco suites |
| V4 | `npx tsc --noEmit` | **0** | **LIMPIO**, corrida final del paquete (puerta global VERDE) |
| R1 | `git status --short -- <mis raíces>` | **0** | 6 ficheros de ruta modificados + 5 árboles nuevos; las demás líneas ya estaban modificadas por agentes concurrentes y **NO** se tocaron |

**NOT RUN** (prohibido por el contrato de lanzamiento, registrado como diferido, nunca como aprobado): `vitest` · `biome check` · `next build` · `npm install` · servidores · navegadores · la auditoría de cinco anchos · `git stash` · `git commit` · `git reset` · `git checkout`.

**Known baseline failures:** ninguno introducido por este paquete. Los 9 errores de V1 fueron propios y se corrigieron aquí.
**Regressions:** none. Zero forbidden files modified. No commit created. `git stash` not invoked.

**Concurrent overlap observed (NOT touched, NOT merged):** `features/admin/{components,views,utils}/**` (raíz de **FND-06**) y las shells concurrentes `AdminPasesView` / `AdminMarketplaceView` / `AdminProductoDetalleView` / `AdminInventarioView` **no se tocaron, no se revirtieron y no se fusionaron**. UI-05 corrió en paralelo y registró en su propia corrida V3 los 8 errores que **este** paquete tenía en those moments; UI-05 los dejó intactos y este paquete los reparó (V2/V3/V4 exit 0).

**Desviaciones declaradas:** `D-UI04-08` (el motivo del S-10 es un `Textarea` con etiqueta y NO un `GenericForm`: el esquema no existe) · `D-UI04-09` (el formulario de «agregar jugador» de `ADM-08` NO se construyó) · `D-UI04-10` (la paginación se compone pero no se ejerce) · `D-UI04-11` (`fecha` es una extensión de `AdminPagoListItemOut`, no una alteración de la forma canónica de `FR-08` §2.4) · `D-UI04-12` (el drawer de `ADM-14` es un `sheet` en todos los anchos) · `D-UI04-13` (la elegibilidad es una lista de veredictos, no un formulario) · `D-UI04-14` (no se creó `loading.tsx`: S-01 pertenece al límite de grupo del shell, raíz PROHIBIDA).

**A0 requests:** `A0-UI04-01` (registrar los controllers administrativos: `RT-IN-07…11`, `RT-PG-04…07`, `RT-ID-07/08` — **`RT-PG-04` y `RT-PG-05` ya están CONGELADOS en GOV-01 y sólo esperan el registro**) · `A0-UI04-02` (publicar el presenter del drilldown de equipo: `EquipoOut` NO publica el roster, el mínimo, el máximo ni el veredicto) · `A0-UI04-03` (publicar la prosa de los códigos administrativos de equipo, inscripción y participación) · `A0-UI04-04` (publicar la ruta administrativa que retira a una persona de CUALQUIER inscripción: la registrada `DELETE /inscripciones/{id}/participantes/{pid}` es del RESPONSABLE) · `A0-UI04-05` (el filtro por disciplina sigue sin catálogo publicado) · `A0-UI04-06` (sincronizar la fila de UI-04 en `00-matriz-tareas.md`) · `A0-UI04-07` (el chip de veredicto se compone en la feature porque el `badge` local no tiene variantes de veredicto: un primitivo compartido lo desduplicaría).

**Workload:** el artefacto del paquete **NO lleva `Review Workload Forecast`**, así que NO exigía decisión de cadena/tamaño (mismo precedente que DOM-06, FND-07/08, UI-01, UI-02, UI-03, API-01, API-02, API-03 y UI-05). El tamaño **REAL** (~5 400 líneas cambiadas) excede el presupuesto de 400 por ≈ **13x** y se **reporta a A0**. **7 unidades autónomas** (WU-1 capa operativa · WU-2 inscripciones · WU-3 equipos · WU-4 participantes · WU-5 pagos · WU-6 rutas · WU-7 suites); rollback WU-7 → WU-1. Sin commit, sin `git stash`.

**Consumers unblocked:** **API-04** (las costuras de los once seams están documentadas con su ruta, su presenter y su forma) · **XCT-02** (transversal de administración) · **VER-01…VER-03**.

**Next packet:** **API-04** (`wave-03-api-integration/API-04-admin-operations-integration.md`) — su dependencia `UI-04` queda satisfecha. La auditoría de navegador de cinco anchos, el recorrido de tecnologías de asistencia y la ejecución de las cinco suites siguen **DIFERIDOS** a la fase de verificación.

---

### 2026-11-19 — Reconciliación concurrente UI-04 ↔ UI-05 (A7) — sólo-verificación

**Timestamp:** 2026-11-19 (local) · **Owner:** A7 · **Alcance:** **reconciliación estrecha** — **NINGÚN** fichero de `Aplicacion/frontend/**` modificado · **NINGÚN** comando de runtime ejecutado · **NINGÚN** cambio en los artefactos de UI-04 (su fichero de evidencia, su apply-progress y su fila del tablero quedan **VERBATIM**)

**Por qué:** UI-04 y UI-05 corrieron **en paralelo**. UI-05 cerró su corrida project-wide con la puerta en ROJO a causa del árbol **concurrente y ajeno** de UI-04, y UI-04 terminó **después**. La fila de UI-05 en este tablero decía «the last project-wide run was RED», lo que es cierto de SU corrida pero **no** refleja el estado final del proyecto.

**Hechos reconciliados (leídos de la evidencia y de los artefactos actuales):**

| # | Hecho | Evidencia |
|---|---|---|
| `R-UI05/04-01` | **Las raíces de UI-05 fueron limpias en TODAS sus corridas.** Los 8 errores de su V3 estaban **exclusivamente** en `features/admin/inscripciones/**` y `features/admin/operaciones/**` — el árbol **en vuelo de UI-04** — y **cero** en `features/competencias/**`, `features/validaciones/**` o `features/patrocinadores/**` | `evidence/ui/UI-05-competition-validation-shells.md` §8 (corridas V1–V3) |
| `R-UI05/04-02` | **La ÚLTIMA corrida project-wide registrada es la `V4` de UI-04 y salió `0`** ⇒ la **puerta global está VERDE** | `evidence/ui/UI-04-admin-operations-shells.md` §8 (fila `V4`: *«clean — FINAL run of the packet; the global gate is GREEN»*) |
| `R-UI05/04-03` | UI-04 declara explícitamente que los 8 errores que UI-05 registró en su V3 **eran suyos**, que UI-05 los dejó intactos y que **UI-04 los reparó** (V2/V3/V4 exit 0) | `sdd/salesianos-fest-rebuild/ui-04-apply-progress` (§9, #11434) |

**La verdad unificada de la puerta global** (mismo patrón que API-01 + API-02 + API-03): los dos paquetes corrieron en paralelo, **ninguno tuvo errores en sus propias raíces**, la puerta project-wide osciló **sólo** por el árbol **concurrente y ajeno** del otro — que el escritor ajeno **no tocó, no revirtió y no fusionó** — y la **última corrida project-wide registrada sale `0`**, de modo que la **puerta global del proyecto está VERDE**. El exit code lo **reporta** la evidencia de UI-04 (`V4`); UI-05 **no lo midió** y no lo afirma por cuenta propia.

**Aclaración de la propiedad de `ADM-15` / `ADM-17` / `ADM-18` / `ADM-19` (`D-UI05-06` → `A0-UI05-08`):**

La primera nota de UI-05 decía que las cuatro rutas «fueron entregadas **CONCURRENTEMENTE** por otro agente». La evidencia actual muestra que **no** es así: el agente concurrente era **UI-04**, y la evidencia de UI-04 **DESCONOCE** esas cuatro vistas (§9 de #11434: *«the concurrent shells `AdminPasesView` / `AdminMarketplaceView` / `AdminProductoDetalleView` / `AdminInventarioView` … NOT touched, NOT merged»*). Las cuatro rutas apuntan a `features/admin/views/**`, que es la raíz de **FND-06**, y ese árbol procede del **agente `general` lanzado manualmente** de la sesión `salesianos-ui-general-agent-prompt-2026-11-19` (**#11314**), cuyo encargo era la política de tema, las transiciones GSAP y la **estandarización visual de las rutas administrativas**, con la instrucción explícita «*No crear, modificar ni ejecutar tests; sólo `npx tsc --noEmit`*»; esa pasada también **borró** `components/shell/RoutePlaceholder.tsx`, que es la razón por la que las cuatro rutas ya no renderizan el placeholder de FND-06.

⇒ Esas cuatro rutas **no tienen fila, ni apply-progress, ni fichero de evidencia**: su propiedad es **NO ATRIBUIDA** dentro del sistema de paquetes. **UI-05 no las construyó** (raíz PROHIBIDA, ni tocadas, ni revertidas, ni fusionadas) y el paquete de UI-05 **sí** las enumera entre sus plan IDs, de modo que **siguen debidas** al alcance de UI-05. Se abre **`A0-UI05-08`** para que el coordinador abra fila de esa pasada no-SDD o las incorpore al próximo paquete que las reclame. **La aclaración NO modificó ningún fichero de código fuente.**

**Cambios de esta reconciliación (sólo UI-05):**

| Artefacto | Cambio |
|---|---|
| `evidence/ui/UI-05-competition-validation-shells.md` | cabecera «Reconciled»; §1 nota de propiedad reescrita con la tabla de evidencia + «Correction of an earlier wording»; **§8.1 nuevo** (reconciliación con UI-04, tabla de las dos filas); `D-UI05-06` reescrita; `A0-UI05-08` añadido; §12 nota de reconciliación; §13 dos criterios nuevos |
| `STATE.md` | fila de **UI-05** actualizada (puerta global VERDE + `A0-UI05-01…08` + la propiedad NO ATRIBUIDA); V3 de la transición de UI-05 atribuida al árbol de UI-04; nota de propiedad de la transición de UI-05; `A0 requests` de UI-05 → `A0-UI05-01…08`; **esta transición de reconciliación** |
| `sdd/salesianos-fest-rebuild/ui-05-apply-progress` (#11432) | §8.1 (reconciliación + puerta global VERDE), `D-UI05-06`/`A0-UI05-08`, nota de propiedad |
| `sdd/salesianos-fest-rebuild/apply-progress` (#11227) | fusionado: fila y digest de **UI-04** + digest de UI-05 actualizado + recuento corregido (47 creados) |
| `sdd/salesianos-fest-rebuild/state` (#11228) | fusionado: filas de **UI-04** y de **UI-05** + ambos digests + recuento corregido |
| `sdd/salesianos-fest-rebuild/ui-05-count-correction` (#11433) | cerrado: la fusión de los índices compartidos ya lleva el recuento correcto |

**Preservado VERBATIM:** `evidence/ui/UI-04-admin-operations-shells.md` · `sdd/salesianos-fest-rebuild/ui-04-apply-progress` (#11434) · la fila de **UI-04** del tablero · la transición de **UI-04** de este `STATE.md` · las filas, digests, evidencias y ficheros de GOV-00…02, FND-01…08, DOM-01…08, UI-01…03 y API-01…03.

**Comandos:** **NINGUNO**. **Regressions:** none. **Cero ficheros de `Aplicacion/frontend/**` modificados.** Sin commit, sin `git stash`.

**Siguiente paquete:** **API-04** y **API-05** (ambas dependencias ya satisfechas) y, en paralelo, **XCT-01**.

---

### 2026-11-19 — API-05 → verification_required (implementation applied, NOT closed)

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** topic `sdd/salesianos-fest-rebuild/api-05-apply-progress` · **Owner:** A0 + A7
**Original task IDs:** `T-077`, `T-078`, `T-082` (3 de los 54 source-defined IDs)
**Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (sin commit; `git stash` nunca invocado)

| Point | HEAD | Estado del árbol | Raíces prohibidas |
|---|---|---|---|
| packet start | `fd1c4c1…` | 322 líneas (árbol sucio preexistente de los paquetes concurrentes) | intactas |
| packet close | `fd1c4c1…` | 331 líneas (+ las 10 creadas + las 11 modificadas + las 3 eliminadas de este packet) | intactas |

**Entregado:** los **tres espejos Zod 1:1** de los presenters que **existen** en las tres áreas
(`features/competencias/schemas/competencia.schema.ts` — 13 wrappers + 10 entradas de `DOM-07` ·
`features/patrocinadores/schemas/patrocinador.schema.ts` — la composición de los tres bloques +
logo + galería + 2 entradas de `DOM-08` · `features/validaciones/schemas/validacion.schema.ts` —
`EntregaPendienteOut` + `EntregaConfirmadaOut` de `DOM-06`, **reutilizando** `PaseBeneficiarioOut`
del dueño `features/pases` y `PedidoLineaOut` del dueño `features/marketplace`); la **eliminación de
las TRES fixtures provisionales** del alcance y la reescritura de las tres suites para que sus datos
salgan del espejo (`schema.parse(...)`); tres correcciones de honestidad del contrato (`url` nullable
del logo y de la pieza; `MEDIA_TOKEN_DUPLICADO` en la unión de la familia de media; cabeceras de los
tipos de vista); **tres suites de contrato nuevas** (una por área) y **la auditoría de cierre** de
las tres features.

**CERO rutas ligadas — y por qué:** `CompetenciasController` (16 rutas), `PatrocinadorController`
(1 ruta) e `InventarioController` (5 rutas) **NO están registrados** en `config/api.py`;
`modules.competencias` y `modules.patrocinadores` **NO** están en `LOCAL_APPS` (y sin ellas sus
controllers **ni siquiera se importan**: el registro de las apps es **precondición** del registro de
los controllers) y el módulo **`validaciones` NO EXISTE** en el objetivo ⇒ de las **tres** superficies
del alcance (`ADM-10…13`, `ADM-16`, `ADM-20`, `ADM-21`, `ADM-22`) **ninguna** tiene ruta registrada.
**Ligar una ruta que no existe sería inventar un contrato**; es el mismo veredicto que took `API-01`
(`RT-ID-04/05/06`), `API-02` (`RT-IN-01`) y `API-03` (`PedidoController`/`InventarioController`).
**El espejo se escribe AUNQUE la ruta no exista**: transcribe un presenter **existente y congelado**
(no inventa nada) y hace que la liaison del futuro sea **un cliente y cero reescrituras de vistas**.

**Changed files (this packet — 24 paths):**

| Fichero | Acción |
|---|---|
| `Aplicacion/frontend/src/features/competencias/schemas/competencia.schema.ts` | **creado** |
| `Aplicacion/frontend/src/features/competencias/__tests__/datos.contract.ts` | **creado** |
| `Aplicacion/frontend/src/features/competencias/__tests__/competencia-mirrors.test.ts` | **creado** |
| `Aplicacion/frontend/src/features/validaciones/schemas/validacion.schema.ts` | **creado** |
| `Aplicacion/frontend/src/features/validaciones/__tests__/datos.contract.ts` | **creado** |
| `Aplicacion/frontend/src/features/validaciones/__tests__/validacion-mirrors.test.ts` | **creado** |
| `Aplicacion/frontend/src/features/patrocinadores/schemas/patrocinador.schema.ts` | **creado** |
| `Aplicacion/frontend/src/features/patrocinadores/__tests__/datos.contract.ts` | **creado** |
| `Aplicacion/frontend/src/features/patrocinadores/__tests__/patrocinador-mirrors.test.ts` | **creado** |
| `…/features/competencias/types/competencia.types.ts` | **modificado** (cabecera) |
| `…/features/competencias/__tests__/competencias-estados.test.tsx` | **modificado** (datos por el espejo) |
| `…/features/validaciones/types/validacion.types.ts` | **modificado** (cabecera) |
| `…/features/validaciones/__tests__/validaciones-estados.test.tsx` | **modificado** (datos por el espejo) |
| `…/features/validaciones/components/TablaAuditoriaValidaciones.tsx` | **modificado** (referencia de la petición) |
| `…/features/validaciones/utils/validaciones.estados.utils.ts` | **modificado** (ídem) |
| `…/features/patrocinadores/types/patrocinador.types.ts` | **modificado** (`url` nullable + `CodigoErrorMedio` re-exportado) |
| `…/features/patrocinadores/__tests__/patrocinadores-estados.test.tsx` | **modificado** (datos por el espejo) |
| `…/features/patrocinadores/components/FormularioPatrocinador.tsx` | **modificado** (redacción de `MEDIA_TOKEN_DUPLICADO`) |
| `…/features/patrocinadores/components/LogoPatrocinador.tsx` | **modificado** (hueco sin URL) |
| `…/features/patrocinadores/components/GaleriaPatrocinador.tsx` | **modificado** (hueco sin URL) |
| `…/features/competencias/fixtures/competencias.fixture.ts` | **ELIMINADO** |
| `…/features/validaciones/fixtures/validaciones.fixture.ts` | **ELIMINADO** |
| `…/features/patrocinadores/fixtures/patrocinadores.fixture.ts` | **ELIMINADO** |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/api/API-05-competition-admin-integration.md` | **creado** |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | **modificado** (esta transición) |

**Raíces tocadas:** `Aplicacion/frontend/src/features/{competencias,validaciones,patrocinadores}/**` ·
`Aplicacion/task/salesianos-fest-rebuild/evidence/api/**` · `STATE.md`.
**Raíces prohibidas NO tocadas:** `src/lib/**` · `src/shared/**` · `src/hooks/**` · `src/errors/**` ·
`src/components/**` · `src/providers/**` · `src/utils/**` · `src/types/**` · `src/app/**` ·
`src/features/{admin,auth,cuenta,inscripciones,marketplace,pases,portada,public,theme}/**` ·
`Aplicacion/backend/**` · `contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**`.

**Commands / exit codes (workdir `Aplicacion/frontend`):**

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V1 | `npx tsc --noEmit` | **1** | 5 errores: **1 PROPIO** (faltaba la redacción de `MEDIA_TOKEN_DUPLICADO` tras unificar la unión de la familia de media) — **corregido** — y **4 AJENOS** en `features/admin/{equipos,inscripciones,pagos,participantes}/__tests__/**`: los `fixtures/*.fixture.ts` de ese árbol **habían desaparecido** mientras el otro agente lo reescribía. **No tocados, no revertidos, no fusionados** |
| V2 | `npx tsc --noEmit` | **1** | 8 errores, **TODOS ajenos** y **TODOS** en `features/admin/**` (árbol concurrente en vuelo). **CERO** en las raíces de este packet |
| V3 | `npx tsc --noEmit` | **0** | **LIMPIO — el proyecto entero** (el agente concurrente reparó su árbol durante este packet) |
| V4 | `npx tsc --noEmit` | **0** | **LIMPIO — verificación final** |

**Known baseline failures:** ninguno introducido por este packet. **Regressions:** none. **Cero
ficheros de `Aplicacion/backend/**` modificados.** Sin commit, sin `git stash`, sin `git reset`.

**NOT RUN** (fuera del permiso del packet): `vitest` · `biome check` · `next build` · `npm install` ·
servidor · navegador · la auditoría de los cinco anchos (360 · 390 · 768 · 1024 · 1440) ·
`python manage.py check` · `pytest`. **6 suites ESCRITAS, NO EJECUTADAS.**

**A0 requests:** `A0-API05-01` (**registrar `modules.competencias` y `modules.patrocinadores` en
`LOCAL_APPS` + sus módulos de DI, y **después** `CompetenciasController` y `PatrocinadorController`
en `config/api.py`**) · `A0-API05-02` (**ratificar los tres wrappers de `validaciones`**: el módulo
**tiene que existir**) · `A0-API05-03` (**no hay ruta de LECTURA de patrocinadores**: el ledger sólo
declara el alta) · `A0-API05-04` (`SCHEMA_VERSIONS["competencias"]` + test de drift) ·
`A0-API05-05` (**atribuir `ADM-15/17/18/19`**) · `A0-API05-06` (deuda de fixtures provisionales en
`features/portada/**` y `features/admin/**`, **fuera** de las raíces de este packet) ·
`A0-API05-07` (sincronizar `00-matriz-tareas.md`).

**Propiedad de `ADM-15` / `ADM-17` / `ADM-18` / `ADM-19` (`A0-API05-05`):** sigue **NO ATRIBUIDA**.
`features/admin/**` está **FUERA** de las raíces permitidas de este packet y su árbol estaba en vuelo,
así que **no se tocó, no se revirtió ni se fusionó**. La reconciliación de `UI-05` (`A0-UI05-08`) sigue
vigente y API-05 la **re-eleva**, sin tocar ninguna raíz ajena.

**Concurrencia preservada:** durante este packet, otro agente reescribió
`features/admin/{equipos,inscripciones,pagos,participantes}/**` (borró sus `fixtures/*.fixture.ts` y
creó sus propios módulos de datos de suite). Sus errores de typecheck fueron **ajenos** y quedaron
**intactos**; su dueño los reparó durante este packet y la **última** corrida project-wide salió **0**.
Ninguna fila del tablero de otro paquete fue editada por este packet.

**Siguiente paquete:** **XCT-01** (tickets y validación), y después **XCT-02** y **XCT-03** por
dependencia. El **cableado global de A0** (`A0-API05-01`) es el camino crítico de las tres.

---

### 2026-11-19 — API-04 → verification_required

**Timestamp:** 2026-11-19 (local) · **Apply-progress observation:** `sdd/salesianos-fest-rebuild/api-04-apply-progress` · **Owner:** A7
**Original task IDs:** `T-075`, `T-076`
**Packet:** `Aplicacion/task/salesianos-fest-rebuild/wave-03-api-integration/API-04-admin-operations-integration.md`
**Rollback:** revertir los ficheros de §7 de la evidencia (no hay commit creado; `git stash` nunca invocado)

**Veredicto: CERO rutas ligadas.** Ninguna ruta administrativa del alcance existe en el backend de
destino: `AdminInscripcionController` (`RT-IN-07`, `RT-IN-08`), `AdminEquipoController` (`RT-IN-09`,
`RT-IN-10`), `AdminParticipanteController` (`RT-IN-11`), `AdminPagoController` (`RT-PG-04`, `RT-PG-05`,
`RT-PG-07`) y `AdminPersonaController` (`RT-ID-07`, `RT-ID-08`) **NO están registrados** en
`Aplicacion/backend/config/api.py`; y `PagosController` no expone `/intentos` (`RT-PG-06`). Ligar una ruta
inexistente sería **inventar un contrato** (prohibido por el packet): mismo veredicto que `API-01`
(`RT-ID-04/05/06`), `API-02` (`RT-IN-01`), `API-03` (`PedidoController`/`InventarioController`) y `API-05`
(cero rutas ligadas).

**Delivered:** (1) **cuatro espejos Zod** del contrato declarado de los presenters administrativos
(`features/admin/{inscripciones,equipos,participantes,pagos}/schemas/*.schema.ts`) con su **proyección** al
modelo de la vista; (2) **el ledger con la verdad de registro** `RUTAS_ADMIN` (12 rutas con `ledger`,
`metodo`, `ruta`, `presentador`, `wrapper`, `registrado`, `motivo` y `permiso`) y **el guard** que rechaza
una ruta no registrada **antes del transporte**: es imposible emitir una petición a una URL que responde
404; (3) **cuatro factorías de claves** con la edición, el filtro, la página, el registro y la **versión**
dentro de la clave, y un parámetro `undefined` descartado; (4) **ocho hooks** con `queryOptions` y con el
`enabled` atado a la verdad de registro; (5) **la política de estados y de errores** en un fichero (401/403 →
`sin-permiso`; 409/422/500 → `error`; el `422` con `error.field_errors[]` → mapa de campo; el texto
**verbatim** del servidor); (6) **la invalidación dirigida** que vive **dentro** de la `mutationFn` y
declara **exactamente** el dataset que ensucia; (7) **los seis contenedores** (`*Ruta`) con la cadena
**página → contenedor → vista → componentes → hooks → servicios → esquemas**; (8) **los dos S-10** atados a
su mutación, con el **motivo obligatorio**, el botón **deshabilitado desde el mismo registro** que usa el
servicio y el error del backend anunciado; (9) **las cuatro fixtures provisionales ELIMINADAS** y las
cuatro suites reescritas para que sus datos salgan del **mismo espejo Zod** que usa el servicio.

**Decisiones:** `D-API04-01` cero rutas ligadas · `D-API04-02` el guard es el mecanismo, no una convención ·
`D-API04-03` un solo lugar decide la existencia de una ruta (`RUTAS_ADMIN`) · `D-API04-04` el wire
publica el `EstadoOperativo` congelado y el cubo visual lo añade el adaptador (el backend no publica una
decisión de la interfaz) · `D-API04-05` el `enabled` de cada lectura es la verdad de registro ·
`D-API04-06` la invalidación vive dentro de la `mutationFn` y declara exactamente su dataset ·
`D-API04-07` los datos de las suites salen de `schema.parse(...)` y viven en `__tests__/` ·
`D-API04-08` el motivo del S-10 sigue siendo un control etiquetado (el esquema del wire **no existe**);
API-04 aporta el constructor del payload y el mapa de errores de campo.

**Commands / exit codes (workdir `Aplicacion/frontend`):**

| # | Comando | Exit | Resultado |
|---:|---|---:|---|
| V1 | `npx tsc --noEmit` | **1** | 5 errores: **4 PROPIOS** (`ParamsListaAdmin` no satisfacía `Record<string, unknown>` — un `interface` sin índice — y un import mal nombrado; **corregidos**) + **1 AJENO** (`src/features/patrocinadores/components/FormularioPatrocinador.tsx`, árbol **concurrente** de API-05, **NO tocado**) |
| V2 | `npx tsc --noEmit` | **1** | **0 errores propios**; queda **1 ajeno** (el mismo de API-05) |
| V3 | `npx tsc --noEmit` | **0** | **LIMPIO — el proyecto entero** ⇒ **puerta global VERDE** |
| V4 | `npx tsc --noEmit` (final) | **0** | **LIMPIO** ⇒ **puerta global VERDE** |
| V5 | `npx tsc --noEmit` (tras exportar los hooks de las cuatro features desde sus barrels) | **0** | **LIMPIO** ⇒ **puerta global VERDE** |

**Known baseline failures:** ninguno introducido. **Regressions:** none. **Cero** ficheros de
`Aplicacion/backend/**` modificados. Sin commit, sin `git stash`, sin `git reset`.

**NOT RUN** (fuera del permiso del packet): `vitest` · `biome check` · `next build` · `npm install` ·
servidor · navegador · la auditoría de los cinco anchos (360 · 390 · 768 · 1024 · 1440) ·
`python manage.py check` · `pytest`. **5 suites ESCRITAS, NO EJECUTADAS** (1 nueva de integración + las
cuatro reescritas).

**Escaneo de cierre:** `PROVISIONAL_CONTRACT_FIXTURE` → **0** en `features/admin/**` · imports de
`fixtures/` → **0** · carpetas `fixtures/` → **0**.

**Bloqueos reportados:** `B-04-01`…`B-04-08` (nueve rutas administrativas inexistentes · el módulo
`pagos` sin `/intentos` · **el ledger contradice al módulo** sobre quién puede leer el pool de una
inscripción · sin preset de paginación ratified fuera de `RT-PG-04`).

**A0 requests:** `A0-API04-01` (**BLOQUEANTE**: registrar los cinco controllers administrativos;
`RT-PG-04` y `RT-PG-05` ya están **CONGELADOS** en GOV-01) · `A0-API04-02` (publicar el wrapper
`AdminPagoAprobarManualOut`) · `A0-API04-03` (unificar el envelope de error: el `apiErrorSchema` compartido
no declara `field_errors` y rechaza un `details: null`) · `A0-API04-04` (ratificar el **tipo del importe**:
el plan lo declara como cadena y `CompraOut` lo manda como `float`) · `A0-API04-05` (reconciliar los
espejos con los presenters reales al registrar) · `A0-API04-06` (**BLOQUEANTE** para `ADM-06`/`ADM-08`:
publicar la ruta administrativa de retirada) · `A0-API04-07` (sincronizar `00-matriz-tareas.md`) ·
`A0-API04-08` (atribuir `ADM-15/17/18/19`, que **sí** tienen rutas registradas y siguen **NO ATRIBUIDAS**).

**Concurrencia preservada:** durante este packet, el árbol concurrente de **API-05**
(`features/patrocinadores/**`) tuvo **1** error de typecheck **ajeno**: **no se tocó, no se revirtió ni se
fusionó**; su dueño lo reparó durante este packet y la corrida final (V4) salió **0**. Ninguna fila del
tablero de otro paquete fue editada por este packet.

**Siguiente paquete:** **XCT-02** (admin transversal), cuyas dependencias (API-02…API-05) quedan
satisfechas en cuanto A0 registre los controllers. **Ver también** `XCT-01`, ya desbloqueado por API-05.

---

### 2026-11-20 — XCT-01 → verification_required

**Timestamp:** 2026-11-20 (local) · **Apply-progress observation:** topic `sdd/salesianos-fest-rebuild/apply-progress` · **Owner:** A8 + A4 + A5
**Original task IDs:** `T-080`, `T-081` (2 of the 54 source-defined IDs)
**Branch:** `master` · **Rollback point:** `f3df5401c56b41c340f257e67a5a306904a9e670` (unchanged, no commit created)

**Delivered:** el módulo `validaciones` **COMPLETO** — `Ticket` (la credencial que REFERENCIA un derecho existente, nunca lo duplica) y `ValidacionTicket` (el acta de cada intento, permitido o denegado) · el puerto CONGELADO `IVerificadorDerecho` (`FR-05` §5) · DOS adaptadores de dueño (`PaseVerificadorDerecho` en `salesianos_fest`, `PedidoVerificadorDerecho` en `marketplace`) que son los ÚNICOS que deciden si un derecho se puede canjear · `PreviewTicketFlujo` (lectura pura, NO consume, `RN-P06`) · `ConfirmarTicketFlujo` (UNA transacción: idempotencia → bloqueo de la credencial → revalidación y consumo BAJO BLOQUEO en el dueño → acta) · `TicketPreviewPresenter` / `TicketConfirmPresenter` con las formas CONGELADAS de `FR-05` §3.1 y §3.2 · `ValidacionController` con `RT-RT-01` y `RT-RT-02` · el comando `emitir_ticket` · la migración `0001_initial` con TRES restricciones CHECK que son la autoridad de las reglas · y en el frontend: los espejos Zod reales, el cliente único, los hooks, el adaptador y DOS contenedores (`ValidarPaseRuta` para el INGRESO y `ValidarEntregaRuta` para la ENTREGA) con el código MANUAL como camino de reserva.

**Un solo ciclo de vida:** el contador de consumo vive en el DERECHO (`PaseBeneficiario.cantidad_consumida`), no en la credencial. `validaciones` no concede, no modifica y no reimplementa ningún derecho: lo PREGUNTA a su dueño.

**Changed files (this packet — 44 product paths, all inside the allowed edit roots):** created `Aplicacion/backend/modules/validaciones/**` (30 files) · created `Aplicacion/backend/modules/salesianos_fest/domain/services/core/verificador_derecho_pase.py` · created `Aplicacion/backend/modules/marketplace/domain/services/core/verificador_derecho_pedido.py` · created 12 files in `Aplicacion/frontend/src/features/validaciones/**` and in the two administrative route pages · modified 5 frontend files · modified `STATE.md` (this transition) · created `evidence/cross-cutting/XCT-01-tickets-validation.md`. **ZERO** shared A0 file was edited (`config/api.py`, `config/settings/base.py`, `core/exceptions.py`, `core/contract_versions.py`): the requests are filed as evidence.

**Commands / exit codes (workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe`):** `ast.parse` over the 45 new/changed Python files **0** (`AST OK 45`) · `manage.py makemigrations --check --dry-run --settings=modules.validaciones.tests.settings_overlay` **0** (`No changes detected`) — **run TWICE**: the first run reported drift (the `to=` of the self-reference and the order/shape of the `Q` children of the constraints) and the drift was CORRECTED; the intermediate `0002_*.py` that Django generated for the diagnosis was DELETED · `manage.py check --settings=…overlay` **0** (`no issues`) · import check of the conftest and of BOTH owner adapters **0** (`IMPORTS OK`) · `npx tsc --noEmit` (workdir `Aplicacion/frontend`) **0** — **the project-wide gate is GREEN**.

**Deferred by the standing apply restriction (NOT run, NOT claimed):** `python -m pytest modules/validaciones/tests -q` (20 cases WRITTEN, NOT EXECUTED) · `npx vitest run src/features/validaciones src/app` (1 suite WRITTEN, NOT EXECUTED) · `npx biome check` · `next build` · the browser · the five-width audit (`360`, `390`, `768`, `1024`, `1440`).

**Known baseline failures:** unchanged — none of them was re-run and none was touched. **Regressions:** none in the roots of this packet; the type gate is GREEN project-wide. **Known risk:** the concurrency case asserts the invariant of `QA-V02` against SQLite, where `select_for_update` is a NO-OP: `VER-01` has to run it on a database with real row locks before the packet can be signed off.

**A0 requests:** `A0-XCT01-01` (`INSTALLED_APPS`) · `A0-XCT01-02` (`INJECTOR_MODULES`) · `A0-XCT01-03` (**BLOQUEANTE**: registrar `ValidacionController` ⇒ `RT-RT-01` y `RT-RT-02` NO EXISTEN hasta entonces) · `A0-XCT01-04` (los cuatro códigos `TICKET_NO_ENCONTRADO`, `TICKET_YA_CONSUMIDO`, `CANTIDAD_EXCEDIDA`, `DERECHO_REVOCADO` en el catálogo público) · `A0-XCT01-05` (la emisión automática de la credencial al otorgar el derecho) · `A0-XCT01-06` (`PD-03` y `PD-04`) · `A0-XCT01-07` (el grupo de los operadores de validación).

**Rollback:** borrar `Aplicacion/backend/modules/validaciones/**` y los dos adaptadores de dueño, revertir los 5 ficheros de frontend modificados y borrar los 12 creados, revertir `STATE.md` y la evidencia. **La historia de las validaciones NUNCA se borra en un rollback en vivo** (`RN-P08`). La migración es reversible con `migrate validaciones zero`, pero sólo ANTES de que el área esté en uso.

**Next packet:** **XCT-02** (admin transversal) — sus dependencias (API-02..API-05) quedan satisfechas en cuanto A0 registre los controllers; **XCT-01** ya está aplicado y en `verification_required`.

