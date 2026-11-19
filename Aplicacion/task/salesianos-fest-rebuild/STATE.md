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
| FND-06 | pending | GOV-02 | A0 + A7 | none |
| FND-07 | pending | FND-06 | A0 + A7 | none |
| FND-08 | pending | FND-06,FND-07 | A0 + A7 | none |
| DOM-01 | completed | FND-02,FND-03,FND-04 | A3 | `evidence/domains/DOM-01-inscripcion-catalogo-compra.md` · `Aplicacion/backend/modules/salesianos_fest/**` (45 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-01-apply-progress`) |
| DOM-02 | completed | DOM-01,FND-05 | A3 | `evidence/domains/DOM-02-pool-asignacion-ampliacion.md` · `Aplicacion/backend/modules/salesianos_fest/**` (102 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-02-apply-progress`) |
| DOM-03 | pending | FND-02,FND-03,FND-04,FND-05 | A4 | none |
| DOM-04 | completed | FND-02,FND-01 | A5 | `evidence/domains/DOM-04-marketplace-catalog-media.md` · `Aplicacion/backend/modules/marketplace/**` (35 tests, all pass) · apply-progress (topic `sdd/salesianos-fest-rebuild/dom-04-apply-progress`) |
| DOM-05 | pending | DOM-04,FND-04 | A5 | none |
| DOM-06 | pending | DOM-04,DOM-05,FND-05 | A5 | none |
| DOM-07 | pending | FND-02,DOM-02 | A6 | none |
| DOM-08 | pending | FND-02,FND-01 | A8 | none |
| UI-01 | pending | GOV-02,FND-06 | A7 | none |
| UI-02 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| UI-03 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| UI-04 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| UI-05 | pending | GOV-02,FND-06,FND-07 | A7 | none |
| API-01 | pending | UI-01,FND-02,FND-03,FND-08 | A7 | none |
| API-02 | pending | UI-02,DOM-01,DOM-02,FND-08 | A7 | none |
| API-03 | pending | UI-03,DOM-03..DOM-06,FND-08 | A7 | none |
| API-04 | pending | UI-04,DOM-01,DOM-02,FND-04,FND-08 | A7 | none |
| API-05 | pending | UI-05,DOM-03,DOM-07,DOM-08,FND-08 | A0 + A7 | none |
| XCT-01 | pending | DOM-03,DOM-06,API-03,API-05 | A8 + A4 + A5 | none |
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
