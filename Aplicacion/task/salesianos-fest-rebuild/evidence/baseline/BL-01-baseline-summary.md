# BL-01 — Frozen-Source Baseline Summary

**Artifact:** `evidence/baseline/BL-01-baseline-summary.md` · **Packet:** GOV-02 (`GOV-02-route-ux-baseline`) · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A0 (baseline) + A9 (review) · **Status:** RECORDED — **no baseline failure was fixed**
**Date:** 2026-11-19 (local) · **Duration of the baseline capture:** ~25 min wall clock
**Frozen roots exercised:** `backend/` (718 tracked files) and `frontend/` (605 tracked files) — **read-only**

---

## 1. Purpose And Rule

> **A failure that appears in this document is a BASELINE FAILURE (evidence), not a waiver and not a defect to fix in this packet.**
> `00-olas-paralelas.md` §"Aggregate Wave Gates": *"Known baseline failures are evidence, not waivers. A failure absent from the baseline or introduced in changed scope is a regression."*

This packet therefore:
- **records** every command, workdir, exit code and result;
- **classifies** every failure and warning by command and path;
- **does not modify** a single line of frozen source to make anything green;
- keeps the **target command matrix separate** (`BL-05`).

---

## 2. Commands Executed — At A Glance

| # | Command | Workdir | Exit | Verdict | Detail file |
|---:|---|---|---:|---|---|
| 1 | `python -m pytest modules -q` | `backend` | **1** | **FAIL — 13 failed / 1333 passed** | `BL-02` §2 |
| 2 | `python manage.py check` | `backend` | **1** | **FAIL — environment (missing `DB_NAME`)** | `BL-02` §3 |
| 3 | `python manage.py makemigrations --check --dry-run` | `backend` | **1** | **FAIL — environment (same cause)** | `BL-02` §4 |
| 4 | `npx tsc --noEmit` | `frontend` | **0** | **PASS — clean** | `BL-03` §1 |
| 5 | `npx vitest run` | `frontend` | **1** | **FAIL — 1 file / 2 tests red** | `BL-03` §2 |
| 6 | `npx biome check .` | `frontend` | **1** | **FAIL — 105 errors / 93 warnings** | `BL-03` §3 |
| 7 | `git status --short` | repo root | **0** | Executed (17 lines at capture time) | `BL-03` §4 |

**Diagnostic variants** (run only to *classify* the cause — they are **not** substitutes for the mandated commands and are **not** the target contract):

| # | Command | Workdir | Exit | Purpose |
|---:|---|---|---:|---|
| D1 | `python -m pytest modules -q --collect-only` | `backend` | 0 | Prove collection is healthy: **1346 tests collected in 7.21 s** — the suite does not hang at import time |
| D2 | `$env:DJANGO_SETTINGS_MODULE='config.settings.development'; $env:USE_SQLITE='true'; python manage.py check` | `backend` | **0** | *"System check identified no issues (0 silenced)"* — the Django system check is **clean**; the mandated failure is environmental |
| D3 | `$env:DJANGO_SETTINGS_MODULE='config.settings.development'; $env:USE_SQLITE='true'; python manage.py makemigrations --check --dry-run` | `backend` | **0** | *"No changes detected"* — there is **no pending model migration**; the mandated failure is environmental |
| D4 | `$env:DJANGO_SETTINGS_MODULE='config.settings.test'; python manage.py makemigrations --check --dry-run` | `backend` | 1 | Different failure: `debug_toolbar.models.HistoryEntry doesn't declare an explicit app_label` — the *test* settings module cannot serve a URLconf for management commands either |

---

## 3. Headline Numbers

| Metric | Value |
|---|---|
| Backend tests collected | **1346** |
| Backend tests passed | **1333** |
| Backend tests failed | **13** (0.97 %) |
| Backend warnings | **641** |
| Backend suite duration | **718.52 s (11 min 58 s)** |
| Frontend typecheck errors | **0** |
| Frontend test files | 34 total → **33 passed / 1 failed** |
| Frontend tests | 276 total → **274 passed / 2 failed** |
| Frontend Vitest duration | 80.38 s |
| Biome files checked | 566 |
| Biome errors / warnings | **105 / 93** |
| Frozen files modified by this packet | **0** |
| Commits created | **0** |
| `git stash` invocations | **0** |

---

## 4. Baseline Failure Taxonomy (summary; detail in `BL-04`)

| Class | Count | Commanded by | Nature |
|---|---:|---|---|
| **B1 — Envelope/wrapper contract drift** | 1 | pytest | The frozen response carries `message`; the test expects the plan's envelope without it. **Directly relevant to the route briefs** (every presenter shape). |
| **B2 — Status-code contract mismatch** | 3 | pytest | Expected 409 / got 200, expected 201 / got 409. Business-conflict semantics disagree with the test expectation. |
| **B3 — SQLite engine limitation** | 4 | pytest | `NotSupportedError: SQLite schema editor cannot be used while foreign key constraint checks are enabled`. The suite runs on `:memory:` SQLite while the production target is PostgreSQL. |
| **B4 — UNIQUE constraint violation** | 3 | pytest | `compra_inscripcion(inscripcion_id, tipo)` and `pagos_transaccionpago(orden_pago_id)`. |
| **B5 — Async/Sync boundary violation** | 1 | pytest | `SynchronousOnlyOperation: You cannot call this from an async context`. |
| **B6 — Count assertion** | 2 | pytest | `assert 0 == 5`, `assert 0 == 3` — the admin matrix / admin payments fixtures produce no rows. |
| **B7 — Settings/environment** | 2 | `manage.py check`, `makemigrations --check` | `ImproperlyConfigured: Set the DB_NAME environment variable`. `manage.py` defaults to `config.settings.production`. |
| **B8 — Frontend Zod mirror drift** | 2 (1 file) | vitest | `admin.catalogos.schema.test.ts` — `estados.estado_capacidad_equipo` missing from the mirror. **Already documented as the stable red file** in `07-guia-para-ui-ux.md` §7.5. |
| **B9 — Lint/format debt** | 105 errors / 93 warnings | biome | **Exactly** the documented baseline (`07-guia-para-ui-ux.md` §7.5: *"105 errores, 93 avisos"*). Includes at least one a11y-class diagnostic (WCAG 2.4.4 / 4.1.2 references). |
| **B10 — React key collision warning** | 4 stderr warnings | vitest | `Encountered two children with the same key` in `AdminPagosLista.test.tsx` — a real defect in the fixture, not a failure. |

**Total: 13 backend failures + 1 frontend red file (2 tests) + 2 environment failures.** None is a regression introduced by this packet (zero frozen files were modified).

---

## 5. Cross-Check Against The Documented Baseline

`Aplicacion/documentacion/07-guia-para-ui-ux.md` §7.5 declares the frontend baseline. The measured values **match exactly**:

| Documented claim | Measured | Match |
|---|---|---|
| *"1 archivo rojo estable (`admin.catalogos.schema.test.ts`, por la deriva `estado_capacidad_equipo`)"* | exactly that file, exactly that field (`estados.estado_capacidad_equipo` → `expected array, received undefined`) | **YES** |
| *"1 archivo rojo inestable (`CompetenciaEncuentroEditors.test.tsx`, dependiente del orden)"* | **passed** in this run | **YES — it is order-dependent and did not reproduce**; it is an *unstable* baseline, not a stable one |
| *"`npx biome check .` … **105 errores, 93 avisos**"* | 105 errors / 93 warnings, 566 files | **YES** |
| *"`npx tsc --noEmit` pasa sin errores"* | exit 0 | **YES** |

**The backend baseline was never documented.** The 13 failures are **new evidence**, not a contradiction of any prior claim.

---

## 6. What This Baseline Does NOT Establish

- It does **not** establish that the target root (`Aplicacion/backend`, `Aplicacion/frontend`) is green. The target backend has **no domain modules yet** (`Aplicacion/backend/modules/` holds only `__init__.py`), so the backend suite cannot even be run there.
- It does **not** establish the behaviour of the 19 GOV-01 frozen routes — none of them is registered in `Aplicacion/backend/config/api.py` yet.
- It does **not** cover browser rendering, screen readers, camera/QR hardware, or 200 % zoom (declared as residual gaps in `SH-02` §5).
- It does **not** validate the 78 provisional routes of `SH-05` — none exists.

---

## 7. Acceptance Criteria For This Document

- [x] Every mandated command has a workdir, an exit code, a date and a concise result.
- [x] No test is claimed as passed unless it was actually run.
- [x] Every failure and warning is classified by command and path (`BL-04`).
- [x] Baseline failures are separated from future regressions (the classification table defines the regression test).
- [x] The target command matrix is recorded **separately** (`BL-05`).
- [x] No frozen source file was modified; no commit was created; `git stash` was not used.
