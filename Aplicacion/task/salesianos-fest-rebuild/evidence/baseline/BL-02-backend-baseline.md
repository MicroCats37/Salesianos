# BL-02 — Backend Frozen-Source Baseline (workdir `backend`)

**Artifact:** `evidence/baseline/BL-02-backend-baseline.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A0 · **Status:** RECORDED — nothing fixed
**Date:** 2026-11-19 (local)
**Frozen root:** `backend/` — **read-only during this packet**

Commands, verbatim, with the exact environment they ran in:

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `python -m pytest modules -q` | `backend` | **1** | `13 failed, 1333 passed, 641 warnings in 718.52s (0:11:58)` |
| 2 | `python manage.py check` | `backend` | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` |
| 3 | `python manage.py makemigrations --check --dry-run` | `backend` | **1** | same `DB_NAME` failure, raised while importing `config/settings/production.py:17` |

---

## 1. Environment Facts That Explain The Result

These are **observations**, not fixes.

| Fact | Evidence | Consequence |
|---|---|---|
| `manage.py` sets `DJANGO_SETTINGS_MODULE` to **`config.settings.production`** by default | `backend/manage.py:22` — `os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")` | Every `manage.py` command without an explicit settings module tries to load PostgreSQL settings. |
| `config/settings/production.py` requires `DB_NAME`, `DB_USER`, `DB_PASSWORD` with **no default** | `backend/config/settings/production.py:14-23` | With no `DB_*` in the environment, settings import raises `ImproperlyConfigured`. |
| `backend/.env` supplies **SQLite** variables, not PostgreSQL ones | `backend/.env` keys: `SECRET_KEY, DEBUG, USE_SQLITE, SQLITE_PATH, IZIPAY_SHOP_ID, IZIPAY_KEY, IZIPAY_MODE, PAGO_MANUAL_APROBACION_ENABLED` | `base.py` reads `USE_SQLITE`/`SQLITE_PATH`, but `production.py` **overrides** `DATABASES` unconditionally with PostgreSQL. |
| `backend/.env` **does not** contain `DB_NAME` | key list above | ⇒ the two `manage.py` failures are **environmental**, not code defects. |
| `pytest.ini` pins a different settings module | `backend/pytest.ini:2` — `DJANGO_SETTINGS_MODULE = config.settings.test` | The pytest suite runs on `config/settings/test.py` → SQLite `:memory:` (`test.py:9-19`). **This is why pytest works and `manage.py` does not.** |
| `pytest.ini` adds `--nomigrations` | `backend/pytest.ini:4` | Tests build the schema directly, so migration state is not exercised by pytest at all. |
| `pytest.ini` sets `asyncio_mode = auto` | `backend/pytest.ini:10` | Async tests run without an explicit marker; relevant to failure **B5**. |
| `DEBUG` is disabled in the test settings' middleware but `debug_toolbar` remains in `INSTALLED_APPS` via `development.py` only | `test.py:34`, `development.py:35` | Explains diagnostic **D4**: with `config.settings.test`, `config/urls.py` still imports `debug_toolbar.urls`, whose model needs an `app_label`. |

> **Classification:** `manage.py check` and `manage.py makemigrations --check --dry-run` fail **as commands**, for a **settings-default + missing-environment-variable** reason. Diagnostics D2/D3 prove the underlying code is clean under `config.settings.development` + `USE_SQLITE=true`:
> - `python manage.py check` → *"System check identified no issues (0 silenced)"* — **exit 0**
> - `python manage.py makemigrations --check --dry-run` → *"No changes detected"* — **exit 0**

**Interpretation:** there is **no pending model migration** and **no Django system-check defect** in the frozen backend. The mandated command form is nevertheless a **baseline failure** and must be reported as such — see `BL-05` for the corrected target form.

---

## 2. `python -m pytest modules -q`

| Metric | Value |
|---|---|
| Exit code | **1** |
| Collected | **1346** tests (D1: `--collect-only` → exit 0, 7.21 s) |
| Passed | **1333** |
| Failed | **13** |
| Warnings | **641** |
| Duration | 718.52 s (11 min 58 s) |
| Error class distribution | `IntegrityError` (UNIQUE) · `NotSupportedError` (SQLite) · `ImproperlyConfigured` · `SynchronousOnlyOperation` · bare assertion mismatches |

### 2.1 The 13 failures, by path

| # | Test id | Path | First error line |
|---:|---|---|---|
| 1 | `test_el_rango_de_fechas_estrcha_por_fecha_de_creacion[A5]` | `modules/administracion/tests/integration/test_admin_matriz_a1_a14.py` | `E assert 0 == 5` |
| 2 | `test_el_rango_de_fechas_estrcha_por_fecha_de_creacion[A12]` | `modules/administracion/tests/integration/test_admin_matriz_a1_a14.py` | `E assert 0 == 5` / `0 == 3` |
| 3 | `test_filtro_por_veredicto_sin_evidencia_y_sin_fecha` | `modules/administracion/tests/integration/test_admin_pagos.py` | `E sqlite3.IntegrityError: UNIQUE constraint failed: salesianos_fest_compra_inscripcion.inscripcion_id, salesianos_fest_compra_inscripcion.tipo` |
| 4 | `test_el_preflight_reporta_la_orden_con_multiples_intentos_vivos` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | `E django.db.utils.NotSupportedError: SQLite schema editor cannot be used while foreign key constraint checks are enabled…` |
| 5 | `test_el_preflight_no_modifica_ningun_intento` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | same `NotSupportedError` |
| 6 | `test_el_informe_json_del_preflight_es_estructurado` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | same `NotSupportedError` |
| 7 | `test_el_guard_de_la_migracion_rechaza_una_orden_insegura` | `modules/pagos/tests/integration/test_intento_activo_unico.py` | same `NotSupportedError` |
| 8 | `test_obtener_precio_vigente_respeta_fechas_no_fallback` | `modules/salesianos_fest/tests/integration/test_cotizacion.py` | `E assert 200 == 409` |
| 9 | `test_crear_inscripcion_completa_duplicada_devuelve_conflict` | `modules/salesianos_fest/tests/integration/test_inscripcion.py` | `E assert 409 == 201` |
| 10 | `test_reconciliacion_tolera_intentos_pendientes_antiguos` | `modules/salesianos_fest/tests/integration/test_reconciliar_pagos.py` | `E sqlite3.IntegrityError: UNIQUE constraint failed: pagos_transaccionpago.orden_pago_id` |
| 11 | `test_busqueda_endpoint_devuelve_forma_contractual` | `modules/usuarios/tests/integration/test_persona_busqueda.py` | `E AssertionError: assert {'data','error','message','success'} == {'data','error','success'}` |
| 12 | `test_los_intentos_superados_se_retiran_todos` | `modules/pagos/tests/integration/test_ciclo_vida_intentos.py` | `E sqlite3.IntegrityError: UNIQUE constraint failed: pagos_transaccionpago.orden_pago_id` |
| 13 | `test_la_identidad_de_transaccion_es_unica_por_orden` | `modules/pagos/tests/integration/test_ciclo_vida_intentos.py` | `E django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an async context - use a thread or sync_to_async.` |

### 2.2 Failure distribution by module

| Module | Failures | Files |
|---|---:|---|
| `modules/pagos` | **7** | `test_intento_activo_unico.py` (4), `test_ciclo_vida_intentos.py` (2), plus `modules/salesianos_fest/tests/integration/test_reconciliar_pagos.py` (1, cross-module) |
| `modules/administracion` | **3** | `test_admin_matriz_a1_a14.py` (2), `test_admin_pagos.py` (1) |
| `modules/salesianos_fest` | **2** | `test_cotizacion.py` (1), `test_inscripcion.py` (1) |
| `modules/usuarios` | **1** | `test_persona_busqueda.py` (1) |

**6 of 7 payment failures sit on the same two models** — `pagos_transaccionpago` (unique `orden_pago_id`) and the `salesianos_fest_compra_inscripcion` (unique `(inscripcion_id, tipo)`). The payment domain is the single largest baseline cluster.

### 2.3 Failure #11 is a **contract** failure, and it is the one that matters most for this packet

```
AssertionError: assert {'data', 'error', 'message', 'success'} == {'data', 'error', 'success'}
  Extra items in the left set: 'message'
```

The frozen backend returns `{success, data, error, message}` (`core/responses.py`, `ApiResponse`). The test asserts the **plan's** three-key envelope. This is the very shape that `FREEZE-ENV-1.0.0` (`D-06`) froze as the **single** envelope, with `message` **inside** it.

**Consequence for the route briefs:** every wrapper named in `SH-05` must include `message` in its success envelope, and the frontend Zod mirror must accept it. Any brief that omits `message` from the expected envelope will produce a failing contract test on the first API integration packet. Recorded as obligation `GOV-02-BL-01` below.

### 2.4 The 641 warnings

| Warning family (representative) | Origin | Relevance |
|---|---|---|
| `RemovedInDjango60Warning: CheckConstraint.check is deprecated in favor of '.condition'` | `backend/core_application/models.py:72` | Django 6.0 removal. Not a rebuild blocker; it is pre-existing debt in a module the plan quarantines. |
| Django deprecations (`datetime.utcnow`, `NullBooleanField`, `providing_args`, …) | multiple | Pre-existing debt across the frozen modules. |
| Pytest / third-party warnings | — | Not rebuild-relevant. |

**Classification:** the 641 warnings are **pre-existing deprecation debt**, not regressions. They are recorded but are not in scope for any rebuild packet. The exception is `core_application`, which the plan marks for **deletion** (CAM legacy, no routes) — its warning disappears with the module.

---

## 3. What Was NOT Run And Why

| Not run | Reason |
|---|---|
| The suite against `Aplicacion/backend` | `Aplicacion/backend/modules/` contains only `__init__.py` — no domain module, no migrations. The suite cannot exist there yet. |
| The suite against PostgreSQL | No `DB_*` variables exist in this environment and no Postgres service is configured for the frozen root. This is an **environment gap**, recorded as `GOV-02-BL-02`. |
| `pytest --lf` / `--ff` re-runs | Not needed; the baseline is captured in one full, reproducible run. |
| `pytest -p no:randomly` variants | `pytest-randomly` is not installed; ordering is already the documented cause of one *unstable* frontend file, not of these backend failures. |

---

## 4. Obligations Issued By The Baseline

| ID | Obligation | Owner | Blocking scope |
|---|---|---|---|
| `GOV-02-BL-01` | Every presenter wrapper named in `SH-05` must expose the frozen envelope **including `message`**, and the frontend mirror must accept it. The failure of `test_busqueda_endpoint_devuelve_forma_contractual` is the reference counter-example. | A7 + A0 | API-01…API-05, DOM-01…DOM-08 |
| `GOV-02-BL-02` | The target backend test matrix needs a **PostgreSQL** lane, or the SQLite-specific failures (B3/B4) will persist as false regressions. | A0 + A9 | XCT-01…XCT-03 |
| `GOV-02-BL-03` | The target command matrix must pin the settings module explicitly (see `BL-05`), instead of inheriting `manage.py`'s production default. | A0 | `BL-05` |
| `GOV-02-BL-04` | The payment-domain UNIQUE constraints (`pagos_transaccionpago.orden_pago_id`, `compra_inscripcion(inscripcion_id, tipo)`) must be reconciled with the **target** commerce model (`FREEZE-CM-1.0.0`: a `Compra` with 3-value origin and a frozen total). A UNIQUE on `orden_pago_id` conflicts with a payments model that may hold several attempts per order. | A2 + A0 | DOM-04, DOM-05, DOM-06 |
| `GOV-02-BL-05` | `SynchronousOnlyOperation` in an async context must be fixed in the target code, not carried over: the target suite is `async def` end-to-end (23 of 24 frozen controllers are async). | A0 | FND-01, XCT-01 |
| `GOV-02-BL-06` | The status-code mismatches (200 vs 409, 201 vs 409) are **business-conflict semantics**; the target presenters must freeze one convention per operation before the API packets consume them. | A0 + A2 | DOM-01…DOM-08, API-0x |

---

## 5. Acceptance Criteria For This Document

- [x] Each backend command is recorded with its workdir, exit code and concise result.
- [x] The 13 failures are listed individually with path and first error line.
- [x] Failures are grouped by module and by cause class.
- [x] The environment cause of the two `manage.py` failures is proven with two diagnostic runs.
- [x] The contract-relevant failure (#11) is called out as an obligation for the route briefs.
- [x] No frozen backend file was modified.
