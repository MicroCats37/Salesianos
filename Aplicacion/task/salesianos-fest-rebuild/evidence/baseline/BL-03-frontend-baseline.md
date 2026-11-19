# BL-03 — Frontend Frozen-Source Baseline (workdir `frontend`) And Repository State

**Artifact:** `evidence/baseline/BL-03-frontend-baseline.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A0 · **Status:** RECORDED — nothing fixed
**Date:** 2026-11-19 (local)
**Frozen root:** `frontend/` — **read-only during this packet**

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 4 | `npx tsc --noEmit` | `frontend` | **0** | **PASS** — no output, no errors |
| 5 | `npx vitest run` | `frontend` | **1** | `Test Files 1 failed \| 33 passed (34)` · `Tests 2 failed \| 274 passed (276)` · duration 80.38 s |
| 6 | `npx biome check .` | `frontend` | **1** | `Checked 566 files in 669ms` · `Found 105 errors` · `Found 93 warnings` |
| 7 | `git status --short` | repo root | **0** | 17 lines at capture time (see §4) |

---

## 1. `npx tsc --noEmit` — PASS

**Exit 0, zero diagnostics.** The frozen frontend typechecks cleanly against its own `tsconfig`.

**Why this matters for the rebuild:** the frozen tree is a *type-clean* baseline. Any type error appearing in the target root is therefore a **regression introduced by the rebuild**, not inherited debt — with one documented exception: `Aplicacion/frontend/src` is a **184-file subset** of the 559 frozen files (GOV-01 fact `D-1`), so a file that does not exist in the subset cannot produce an inherited error either.

**Caveat carried forward:** `frontend/src/components-app/**` (18 files) is **CAM-era residue excluded by `tsconfig.json` yet still imported** (`GOV-00` quarantine list; `07-guia-para-ui-ux.md` §3.3 lists it as a live defect). The clean typecheck therefore does **not** cover it. The target root must not inherit it.

---

## 2. `npx vitest run` — 1 red file, 2 red tests

| Metric | Value |
|---|---|
| Test files | **34** total → 33 passed, **1 failed** |
| Tests | **276** total → 274 passed, **2 failed** |
| Duration | 80.38 s (transform 7.73 s · setup 55.03 s · collect 277.71 s · tests 43.24 s · environment 131.79 s) |

### 2.1 The failing file

`src/features/admin/schemas/admin.catalogos.schema.test.ts`

| # | Test | Error |
|---:|---|---|
| 1 | *"acepta el catálogo con los vocabularios publicados"* | `ZodError: expected array, received undefined` at path `["estados","estado_capacidad_equipo"]` (line 85) |
| 2 | *"acepta un veredicto desconocido para poder renderizarlo neutro"* | `AssertionError: expected false to be true` on `resultado.success` (line 116) |

**Root cause:** the frontend mirror `admin.catalogos.schema` expects the vocabulary `estado_capacidad_equipo` inside `estados`, and the fixture no longer publishes it. The test's own intent — *"acepta un veredicto desconocido para poder renderizarlo neutro"* — is precisely the contract `SH-01` §3.2 and `SH-03` §2 require: **an unknown verdict must render neutrally, not crash**.

**This is the documented stable red file.** `07-guia-para-ui-ux.md` §7.5: *"🔴 La línea base actual tiene **1 archivo rojo estable** (`admin.catalogos.schema.test.ts`, por la deriva `estado_capacidad_equipo`)"*. The measured baseline **matches the documented one exactly**, and the drift field is identical.

### 2.2 The unstable file — **passed** in this run

`src/features/admin/competencias/components/editors/CompetenciaEncuentroEditors.test.tsx` — documented as *"1 archivo rojo inestable (dependiente del orden)"*. It **passed** here. It is therefore an **order-dependent** baseline, not a stable one.

**Consequence for the target matrix:** a single full-suite run is **not sufficient** to declare the target green. `BL-05` therefore requires the unstable file to be run **both** in isolation **and** in the full race (a rule already written in `07-guia-para-ui-ux.md` §7.5: *"La prueba nueva … pasa en ejecución aislada **y** en la carrera completa"*).

### 2.3 Non-failing stderr warnings (recorded, not failures)

| Warning | File | Count | Assessment |
|---|---|---:|---|
| `Encountered two children with the same key, '11111111-1111-4111-8111-111111111111-2026-09-30T09:00:00Z'` | `src/features/admin/components/AdminPagosLista.test.tsx` | 4 occurrences (across 4 tests) | **A real defect in the fixture, not in the suite.** The same purchase/transaction key is rendered twice, so React may duplicate or omit rows. The affected component is **the admin payments list** — precisely the surface `ADM-14` rebuilds. Recorded as `GOV-02-BL-07`. |

---

## 3. `npx biome check .` — 105 errors / 93 warnings

| Metric | Value |
|---|---|
| Files checked | **566** |
| Errors | **105** |
| Warnings | **93** |
| Duration | 669 ms |
| Diagnostics shown before truncation | ~186 of ~198 (the tool's own limit: *"Diagnostics not shown: 179"*) |

**This matches the documented baseline exactly.** `07-guia-para-ui-ux.md` §7.5: *"`npx biome check .` no aumenta el número de errores por encima de la línea base actual (**105 errores, 93 avisos**)"*.

### 3.1 Representative diagnostic classes observed

| Class | Example | Note |
|---|---|---|
| **Formatter** | `src/components/event/EventHero.tsx` — the `style={{ fontFamily: … }}` object literal must be expanded over multiple lines | The bulk of the 105. Pure formatting debt. |
| **A11y-class rule** | A diagnostic citing **WCAG 2.4.4** and **WCAG 4.1.2** | Present in the frozen tree. Any rule the rebuild must not regress. |
| Lint | various | — |

### 3.2 The hardcoded-colour rule is a *rebuild-time* obligation, not a frozen-debt item

`Aplicacion/frontend/src/app/globals.css` (the frozen file) contains **15+ literal `rgba()`/`#hex` values inside `@utility` blocks** (`hero-gradient`, `card-elevated`, `discipline-card`, `btn-brand-gradient`, `text-gradient-*`, `btn-login`, `vp-panel` …). `salesianos-shadcn` Hard Rule 8 rejects literal colours in **components**; the frozen theme file is the single place where literals are acceptable *as source values*, but they must be **converted into semantic roles** by FND-06 (`SH-01` §2.3 lists every one of them).

**Baseline statement:** the Biome error count is a **format/lint** number and does **not** measure hardcoded colours. Therefore the target root needs a **separate hardcoded-colour audit** (`GOV-02-SH-08` / `salesianos-shadcn` Execution Step 8: *"Search the changed presentation files for hardcoded colors"*), because Biome's 105/93 number will not detect a `bg-[#312e8e]` regression on its own.

---

## 4. `git status --short` (repository root)

Command: `git status --short` · workdir: repository root · exit **0**.

Output captured at baseline time (17 lines):

```
 M .atl/.skill-registry.cache.json
 M .atl/skill-registry.md
 M Aplicacion/frontend/components.json
 M Aplicacion/task/salesianos-fest-rebuild/STATE.md
 M Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/excluded-generated-trees.csv
 M Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/manifest-aplicacion.csv
 M opencode.json
 M skills-lock.json
?? .agents/skills/gsap-core/
?? .agents/skills/gsap-performance/
?? .agents/skills/gsap-plugins/
?? .agents/skills/gsap-react/
?? .agents/skills/gsap-scrolltrigger/
?? .agents/skills/gsap-timeline/
?? Aplicacion/frontend/doc_dev/shadcn-registry-inventory.md
?? Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/GOV-00-checkpoint-summary.md
?? Aplicacion/task/salesianos-fest-rebuild/evidence/checkpoint/GOV-00-classification-and-rollback.md
?? Aplicacion/task/salesianos-fest-rebuild/evidence/contracts/
```

### 4.1 Classification of every line

| Line(s) | Owner | Disposition |
|---|---|---|
| `Aplicacion/task/…/STATE.md`, `evidence/checkpoint/**`, `evidence/contracts/**` | **This change** (GOV-00, GOV-01) | Kept and extended by this packet |
| `.atl/.skill-registry.*`, `opencode.json`, `skills-lock.json` | Concurrent user activity | **Untouched.** Not reverted, not staged. |
| `Aplicacion/frontend/components.json` | Concurrent user activity | **Untouched** — but *read*, because it defines the target shadcn registry (`SH-04` §2). |
| `.agents/skills/gsap-*/` (6 directories) | Concurrent user activity | **Untouched.** |
| `Aplicacion/frontend/doc_dev/shadcn-registry-inventory.md` | Concurrent user activity | **Untouched.** |

**Zero** frozen product paths (`backend/**`, `frontend/**`, `worker/**`, `proxy/**`, `contract/**`, `Aplicacion/plan/**`, `Aplicacion/documentacion/**`, `.opencode/**`) appear in the status. **This is the zero-modification proof for the frozen roots.**

### 4.2 Rollback point

`f3df5401c56b41c340f257e67d5a306904a9e670` — unchanged since GOV-00/GOV-01. This packet creates **no commit** and does not move HEAD.

---

## 5. Obligations Issued By The Frontend Baseline

| ID | Obligation | Owner | Blocking scope |
|---|---|---|---|
| `GOV-02-BL-07` | The duplicate-key defect in `AdminPagosLista` must not be inherited by the rebuilt `ADM-14` list: row keys must be unique and stable. | A7 | ADM-14, FND-08 |
| `GOV-02-BL-08` | The `estado_capacidad_equipo` drift is a **Zod-mirror-vs-backend** drift. The rebuild's catalogue mirror must follow the frozen envelope exactly (`GOV-02-BL-01`), and the "unknown verdict renders neutrally" case must be **kept** as a test. | A7 + A0 | FND-07, ADM-05/07/09/14 |
| `GOV-02-BL-09` | The Biome budget is **105 errors / 93 warnings**. A target packet must not raise either number. This is a **ceiling**, not a target: no packet is required to reduce it. | A7 + A9 | Every UI-0x packet |
| `GOV-02-BL-10` | Because one frontend file is **order-dependent**, the target matrix must run the unstable file both in isolation and in the full race. | A9 | `BL-05`, VER-01 |
| `GOV-02-BL-11` | The frozen `tsconfig` excludes `components-app/**` yet still imports it. The target root must **not** carry a tsconfig-excluded but imported tree. | A7 | FND-06, FND-08 |
| `GOV-02-BL-12` | The hardcoded-colour audit is a **separate gate** from Biome; the 105/93 ceiling does not detect `bg-[#…]` regressions. | A7 | Every UI-0x packet |

---

## 6. Acceptance Criteria For This Document

- [x] Each frontend command is recorded with workdir, exit code and result.
- [x] The failing file and both failing tests are named with their errors.
- [x] The stable-vs-unstable distinction is preserved and the unstable file's pass is recorded honestly.
- [x] The 105/93 Biome figure is reconciled with the documented baseline.
- [x] The stderr key-collision warnings are recorded as a defect, not as noise.
- [x] `git status --short` is recorded verbatim and every line is classified by owner.
- [x] Zero frozen product paths appear in the status output.
- [x] No frozen frontend file was modified.
