# BL-04 — Failure And Warning Classification By Command And Path

**Artifact:** `evidence/baseline/BL-04-failure-classification.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A0 + A9 · **Status:** RECORDED — nothing fixed in this packet
**Date:** 2026-11-19 (local)

> **The rule this document exists to enforce** (`00-olas-paralelas.md` §"Aggregate Wave Gates"):
> *"Known baseline failures are evidence, not waivers. A failure absent from the baseline or introduced in changed scope is a regression."*

Therefore: **this table IS the regression oracle.** Every later packet compares its own failures against §3.

---

## 1. Classification By Command

| Command | Workdir | Exit | Total failures | Baseline (recorded here) | Not in this list ⇒ **regression** |
|---|---|---:|---:|---|---|
| `python -m pytest modules -q` | `backend` | 1 | **13** | the 13 ids in §3.1 | any other failing test id |
| `python manage.py check` | `backend` | 1 | 1 (environmental) | `ImproperlyConfigured: Set the DB_NAME environment variable` | any other `manage.py check` output |
| `python manage.py makemigrations --check --dry-run` | `backend` | 1 | 1 (environmental) | same `DB_NAME` failure | any "Changes detected" message |
| `npx tsc --noEmit` | `frontend` | 0 | **0** | — | **any** diagnostic is a regression |
| `npx vitest run` | `frontend` | 1 | **2** (1 file) | `admin.catalogos.schema.test.ts` → the 2 ids in §3.2 | any other failing file/test |
| `npx biome check .` | `frontend` | 1 | 105 errors / 93 warnings | the exact counts | **errors > 105 or warnings > 93 is a regression** |
| `git status --short` | root | 0 | — | the 17 lines in `BL-03` §4 | any new line outside the allowed edit roots |

**Also observed but NOT a failure:** 4 React duplicate-key warnings in `AdminPagosLista.test.tsx` (stderr), 641 pytest warnings, 179 Biome diagnostics suppressed by the tool's own display limit.

---

## 2. Classification By Cause

| Class | Definition | Count | Frozen? | Fixable later? | Owner |
|---|---|---:|---|---|---|
| **B1** | Envelope / wrapper contract drift | 1 | yes | yes — a backend change + a mirror change in the same work | A0 + A7 |
| **B2** | HTTP status-code semantics mismatch | 3 | yes | yes — freeze one convention per operation | A0 + A2 |
| **B3** | SQLite engine limitation (FK checks inside `transaction.atomic`) | 4 | yes | yes — a PostgreSQL test lane, or a targeted SQLite-safe schema path | A0 + A9 |
| **B4** | UNIQUE constraint violation in fixtures/creates | 3 | yes | yes — reconcile the target commerce model with the constraint | A2 + A0 |
| **B5** | Async/Sync boundary violation | 1 | yes | yes — the target suite is async end-to-end | A0 |
| **B6** | Count assertion (empty fixtures) | 2 | yes | yes | A2 + A0 |
| **B7** | Settings / environment (`DB_NAME`) | 2 | yes | yes — pin the settings module in the target matrix | A0 |
| **B8** | Frontend Zod mirror drift (`estado_capacidad_equipo`) | 2 (1 file) | yes | yes | A7 |
| **B9** | Biome format/lint debt | 105 / 93 | yes | not required — a ceiling | A7 |
| **B10** | React duplicate key | 4 warnings | yes | yes — must not be inherited | A7 |
| **B11** | Django deprecation warnings | 641 | yes | not in scope — disappears with `core_application` deletion | — |

### 2.1 Which classes block which rebuild packet

| Class | Blocks | Why |
|---|---|---|
| B1 | DOM-01…DOM-08, API-01…API-05 | Every presenter wrapper must expose one envelope; a drift here breaks every Zod mirror. |
| B2 | DOM-01…DOM-08 | The admin UI branches on 409 vs 200/201 for the conflict states (`SH-03` §2). |
| B3, B4, B5, B6 | XCT-01…XCT-03 | A green target suite is impossible while these persist as false regressions. |
| B7 | nothing — it is a **command** defect, fixed by the matrix | `BL-05` pins the settings module. |
| B8 | FND-07, FND-08 | The catalogue mirror must be right before the admin lists are built on it. |
| B9 | every UI-0x | Ceiling enforcement. |
| B10 | ADM-14 | The rebuilt payments list must not inherit the key collision. |

---

## 3. The Baseline Oracle — Item By Item

### 3.1 Backend — `python -m pytest modules -q` (13)

| # | Test id | Path | Class | Note |
|---:|---|---|---|---|
| 1 | `test_el_rango_de_fechas_estrcha_por_fecha_de_creacion[A5]` | `modules/administracion/tests/integration/test_admin_matriz_a1_a14.py` | B6 | `assert 0 == 5` |
| 2 | `test_el_rango_de_fechas_estrcha_por_fecha_de_creacion[A12]` | `modules/administracion/tests/integration/test_admin_matriz_a1_a14.py` | B6 | `assert 0 == 3` |
| 3 | `test_filtro_por_veredicto_sin_evidencia_y_sin_fecha` | `modules/administracion/tests/integration/test_admin_pagos.py` | B4 | UNIQUE `compra_inscripcion(inscripcion_id, tipo)` |
| 4 | `test_el_preflight_reporta_la_orden_con_multiples_intentos_vivos` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | B3 | SQLite FK / `transaction.atomic` |
| 5 | `test_el_preflight_no_modifica_ningun_intento` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | B3 | idem |
| 6 | `test_el_informe_json_del_preflight_es_estructurado` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | B3 | idem |
| 7 | `test_el_guard_de_la_migracion_rechaza_una_orden_insegura` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | B3 | idem |
| 8 | `test_obtener_precio_vigente_respeta_fechas_no_fallback` | `modules/salesianos_fest/tests/integration/test_cotizacion.py` | B2 | `assert 200 == 409` |
| 9 | `test_crear_inscripcion_completa_duplicada_devuelve_conflict` | `modules/salesianos_fest/tests/integration/test_inscripcion.py` | B2 | `assert 409 == 201` |
| 10 | `test_reconciliacion_tolera_intentos_pendientes_antiguos` | `modules/salesianos_fest/tests/integration/test_reconciliar_pagos.py` | B4 | UNIQUE `pagos_transaccionpago.orden_pago_id` |
| 11 | `test_busqueda_endpoint_devuelve_forma_contractual` | `modules/usuarios/tests/integration/test_persona_busqueda.py` | **B1** | envelope carries `message` |
| 12 | `test_los_intentos_superados_se_retiran_todos` | `modules/pagos/tests/integration/test_ciclo_vida_intentos.py` | B4 | UNIQUE `pagos_transaccionpago.orden_pago_id` |
| 13 | `test_la_identidad_de_transaccion_es_unica_por_orden` | `modules/pagos/tests/integration/test_ciclo_vida_intentos.py` | B5 | `SynchronousOnlyOperation` |

### 3.2 Frontend — `npx vitest run` (1 file / 2 tests)

| # | Test id | Path | Class | Note |
|---:|---|---|---|---|
| 1 | `admin.catalogos.schema — el espejo del catálogo > acepta el catálogo con los vocabularios publicados` | `src/features/admin/schemas/admin.catalogos.schema.test.ts:85` | B8 | `estados.estado_capacidad_equipo` → `expected array, received undefined` |
| 2 | `admin.catalogos.schema — el espejo del catálogo > acepta un veredicto desconocido para poder renderizarlo neutro` | `src/features/admin/schemas/admin.catalogos.schema.test.ts:116` | B8 | `resultado.success` is `false` |

### 3.3 Frontend — `npx biome check .`

| Metric | Baseline ceiling | Source |
|---|---:|---|
| Errors | **105** | `07-guia-para-ui-ux.md` §7.5 — measured value identical |
| Warnings | **93** | idem |
| Files checked | 566 | measured |

### 3.4 Frontend — `npx tsc --noEmit`

**Baseline: 0 diagnostics.** Any diagnostic in the target root is a regression **unless** the target root intentionally includes files the frozen `tsconfig` excluded (the `components-app/**` quarantine) — in which case the target `tsconfig` must include them properly, not exclude-and-import (`GOV-02-BL-11`).

### 3.5 Environment — the two `manage.py` commands

| Command | Baseline failure | Diagnostic proof |
|---|---|---|
| `python manage.py check` | `ImproperlyConfigured: Set the DB_NAME environment variable` (`config/settings/production.py:17`) | with `DJANGO_SETTINGS_MODULE=config.settings.development` + `USE_SQLITE=true` → *"System check identified no issues (0 silenced)"*, exit **0** |
| `python manage.py makemigrations --check --dry-run` | same | same environment → *"No changes detected"*, exit **0** |

**Interpretation:** *the code is clean; the command form is wrong for a machine without PostgreSQL variables.* This is **not** a waiver — the target matrix must use a form that works deterministically (`BL-05`).

---

## 4. Regression Decision Procedure (for every later packet)

```
1. Run the target command matrix (BL-05) in the target root.
2. For each failure, look it up in §3 by exact test id / path.
3. Found in §3   → INHERITED BASELINE. Record it. Do not call it a regression.
4. Not found, and the path is inside the packet's changed scope → REGRESSION. Fix it in this packet.
5. Not found, and the path is outside the packet's changed scope → PRE-EXISTING, newly surfaced. Report it; do not silently absorb it.
6. A failure that DISAPPEARED from §3 → IMPROVEMENT. Record it; do not count it as "fixed by me"
   unless the packet's acceptance criteria said so.
```

**Mandatory for step 4:** the packet must state the *changed scope* explicitly so step 4 is decidable. This is the concrete form of `sdd-phase-common.md` §E (400-line review budget) and `00-olas-paralelas.md` (serialise the shared files).

---

## 5. Explicit Non-Actions

| Non-action | Why |
|---|---|
| No baseline failure was fixed | Out of scope: GOV-02 edits only `evidence/routes/**`, `evidence/baseline/**`, `STATE.md` and the two Engram topics. |
| No `.env` was created or edited to make `manage.py` work | Secrets/runtime config are forbidden roots; and the fix belongs in the command matrix. |
| No `pytest.ini` change | Runtime config is a forbidden root, and `pytest.ini` belongs to the frozen backend. |
| No migration was created or squashed | `makemigrations --check` already reports **no changes**. |
| No Biome autofix was run | `biome check . --write` would touch 566 frozen files. |
| No `git stash`, no commit, no branch | Project rule + packet rule. |

---

## 6. Acceptance Criteria For This Document

- [x] Every failure is classified **by command** and **by path**.
- [x] Every failure is classified **by cause**, with the fix owner.
- [x] The baseline oracle is explicit and item-by-item.
- [x] A regression decision procedure is defined for later packets.
- [x] Every non-action is stated.
- [x] Nothing was fixed; no forbidden root was touched.
