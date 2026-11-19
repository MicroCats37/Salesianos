# BL-05 — Target Command Matrix (recorded SEPARATELY from the frozen baseline)

**Artifact:** `evidence/baseline/BL-05-target-command-matrix.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A0 + A9 · **Status:** PROPOSED — to be ratified by A0 before the wave-01 packets bind to it
**Date:** 2026-11-19 (local)

> **This file is deliberately NOT the baseline.** `BL-01`…`BL-04` record what the **frozen** roots do today. This file records what the **target** root must run, in the target root, once the rebuild starts.
> `00-olas-paralelas.md` §"Aggregate Wave Gates" states: *"Commands are future commands and must be run with the shown workdir."*

---

## 1. Target Roots

| Root | Role | State today |
|---|---|---|
| `Aplicacion/backend` | **Target** backend | `config/` (10 files) + `core/` (28) copied; **`modules/` holds only `__init__.py`**; **no migrations** |
| `Aplicacion/frontend` | **Target** frontend | `src/` is a **184-file subset** of the frozen 559; `node_modules` + `.next` present |
| `backend/` , `frontend/` | **Frozen** source of truth — read-only evidence | unchanged since `f3df540` |

---

## 2. Backend Target Commands

| Gate | Workdir | Command | Expected | Notes |
|---|---|---|---|---|
| **Backend system check** | `Aplicacion/backend` | `python manage.py check --settings=config.settings.development` | exit **0** | The **settings module is pinned explicitly**. `manage.py` defaults to `config.settings.production`, which requires `DB_NAME`/`DB_USER`/`DB_PASSWORD` and fails in any environment without PostgreSQL variables (baseline class **B7**). |
| **Backend migrations** | `Aplicacion/backend` | `python manage.py makemigrations --check --dry-run --settings=config.settings.development` | exit **0**, *"No changes detected"* | Same pinning rationale. The frozen baseline proves there is **no** pending model migration. |
| **Backend unit/integration suite** | `Aplicacion/backend` | `python -m pytest modules -q` | exit **0** | `pytest.ini` already pins `config.settings.test` → SQLite `:memory:`. The target `pytest.ini` must keep that pin and must also declare `asyncio_mode = auto` and `--nomigrations` — or, preferably, drop `--nomigrations` once the target owns real migrations. |
| **Backend suite (PostgreSQL lane)** | `Aplicacion/backend` | `python -m pytest modules -q --ds=<target postgres settings>` | exit **0** | **Required**, not optional: baseline classes **B3** (SQLite FK/`transaction.atomic`) and **B4** (UNIQUE) are engine-dependent and would otherwise appear as false regressions (`GOV-02-BL-02`). |
| **Backend route registration diff** | repository root | `git diff --name-only -- Aplicacion/backend/config/api.py` + a controller-registration inventory | every new controller registered | A route does not exist until it is registered (`FR-07` §3.1.2). |
| **Backend envelope check** | `Aplicacion/backend` | `python -m pytest modules -q -k envelope` (or the equivalent tagged subset) | exit **0** | Guards baseline class **B1**: the success envelope must include `message` (`FREEZE-ENV-1.0.0` `D-06`). |
| **Backend contract-version drift** | `Aplicacion/backend` | the `FREEZE-PS-1.0.0` drift test | exit **0** | Compares `SCHEMA_VERSION` in the registry against the frontend mirror (`FR-07` §1.3). |

---

## 3. Frontend Target Commands

| Gate | Workdir | Command | Expected | Notes |
|---|---|---|---|---|
| **Typecheck** | `Aplicacion/frontend` | `npx tsc --noEmit` | exit **0** | The frozen baseline is **0 diagnostics**; any diagnostic is a regression (`BL-03` §1). The target `tsconfig` must **not** exclude-and-import a tree (`GOV-02-BL-11`). |
| **Unit/component suite** | `Aplicacion/frontend` | `npx vitest run` | exit **0** | Baseline ceiling: the only red file is `admin.catalogos.schema.test.ts` (2 tests). |
| **Unstable-file lane** | `Aplicacion/frontend` | `npx vitest run src/features/admin/competencias/components/editors/CompetenciaEncuentroEditors.test.tsx` | exit **0** | The documented **order-dependent** file must pass **in isolation as well as** in the full race (`GOV-02-BL-10`). |
| **Lint / format** | `Aplicacion/frontend` | `npx biome check .` | exit **0** **or** ≤ **105 errors / 93 warnings** | The ceiling is the frozen baseline; it is not a target to reach zero (`GOV-02-BL-09`). |
| **Hardcoded-colour audit** | `Aplicacion/frontend` | a repository scan for `#hex`, `rgb(`, `hsl(`, `bg-[`, `text-[` outside `src/app/globals.css` | **0** new occurrences | **Separate from Biome.** The 105/93 ceiling does **not** detect `bg-[#312e8e]` regressions (`GOV-02-BL-12`). |
| **Semantic-token audit** | `Aplicacion/frontend` | a scan proving every colour utility consumed is a semantic role (`bg-primary`, `text-muted-foreground`, `border-border`, …) | 0 violations | `salesianos-shadcn` Hard Rule 8. |
| **Registry consistency** | `Aplicacion/frontend` | a check that `components.json` declares the `@shadcn` registry at style `radix-nova` | match | `Aplicacion/frontend/components.json` already does; the frozen `frontend/components.json` has an **empty** `registries` map, which is why the shadcn MCP reported no project registry (`SH-04` §1). |
| **Responsive matrix** | `Aplicacion/frontend` | manual evidence at **360 / 390 / 768 / 1024 / 1440** per route | 38/38 routes × 5 widths | `salesianos-responsive-a11y` Hard Rule 1. Not automatable today; the evidence is produced per UI packet. |
| **Accessibility audit** | `Aplicacion/frontend` | the `ui-ux-reviewer` pass | 0 critical/high findings | Format: `[severity] file:line | route | viewport | finding | remediation`. |

---

## 4. Wave Gates (target form of `00-olas-paralelas.md`)

| Wave | Workdir | Commands | Gate condition |
|---|---|---|---|
| **Backend wave** | `Aplicacion/backend` | `python manage.py check --settings=config.settings.development` · `python manage.py makemigrations --check --dry-run --settings=config.settings.development` · `python -m pytest modules -q` | all exit 0 |
| **Frontend wave** | `Aplicacion/frontend` | `npx tsc --noEmit` · `npx vitest run` · `npx biome check .` · hardcoded-colour audit | tsc 0 · vitest 0 · biome ≤ ceiling · colour audit 0 |
| **Integration wave** | repository root | route-registration inventory diff · backend wave gate · frontend wave gate | no unregistered controller · no provisional fixture remains in the integrated scope |
| **Final** | repository root | `VER-01` + `VER-02` commands · all 29 QA cases · the 38×5 responsive matrix | every baseline item unchanged, no new failure |

---

## 5. Baseline → Target Mapping (what the target must NOT reintroduce)

| Baseline item | Target expectation | Verified by |
|---|---|---|
| 13 backend failing tests | **0** in the target, or each one explicitly re-classified as "still baseline" with a named owner | `BL-04` §4 |
| `admin.catalogos.schema.test.ts` red | **green**, and the *"unknown verdict renders neutrally"* case **kept** | `BL-04` §3.2 + `GOV-02-BL-08` |
| Biome 105 / 93 | ≤ 105 / ≤ 93 | `GOV-02-BL-09` |
| `tsc` 0 diagnostics | 0 diagnostics | `BL-03` §1 |
| `manage.py` DB_NAME failure | **gone** — the settings module is pinned in the command | `BL-02` §1 |
| SQLite-only failures | re-run on the PostgreSQL lane | `GOV-02-BL-02` |
| `PROVISIONAL_CONTRACT_FIXTURE` in the tree | **zero** in the integrated scope | `FR-08` + integration wave gate |

---

## 6. Decisions Required Before This Matrix Is Ratified

| ID | Question | Owner | Default if unanswered |
|---|---|---|---|
| `GOV-02-CM-01` | Does the target suite run on SQLite or PostgreSQL by default? The recommendation is **both**: SQLite for speed, PostgreSQL as the authoritative lane. | A0 + A9 | PostgreSQL authoritative lane, SQLite optional |
| `GOV-02-CM-02` | Which settings module is the **target** default for `manage.py`? The recommendation: `config.settings.development` for local commands and `config.settings.test` for the suite, with `production` only in deployment. | A0 | Pin per command, as written above |
| `GOV-02-CM-03` | Does the target `pytest.ini` keep `--nomigrations`? Recommendation: **drop it** once the target owns migrations, so migration state is actually exercised. | A0 | keep until DOM packets land, then drop with a tracked change |
| `GOV-02-CM-04` | Is the hardcoded-colour audit a scripted command or a manual review step? Recommendation: a scripted scan, because Biome does not cover it. | A7 | scripted |
| `GOV-02-CM-05` | Does the target keep `frontend/` as a second, live copy during the rebuild, or is it a read-only archive from FND-06 onward? This decides whether the baseline stays meaningful. | A0 + product | read-only archive from cutover |

---

## 7. Acceptance Criteria For This Document

- [x] The target matrix is recorded **separately** from the frozen baseline, with different workdirs and different command forms.
- [x] Every target command names its **workdir**.
- [x] The settings-module pinning is explicit, with the reason.
- [x] The PostgreSQL lane is required, with the reason.
- [x] The hardcoded-colour audit is separated from Biome.
- [x] The 38×5 responsive matrix is stated as a gate.
- [x] Every baseline item has a target expectation and a verification method.
- [x] Five decisions are listed for ratification by A0.
