# FND-01 — A0 reconciliation of the completed foundations (FND-02, FND-03, FND-04)

**Artifact:** `evidence/foundations/FND-01-a0-reconciliation.md` · **Packet:** `FND-01-backend-shared-api-media` (A0 reconciliation)
**Change:** `salesianos-fest-rebuild` · **Project:** Salesianos · **Owner:** A0
**Status:** completed · **Date:** 2026-11-19 (local) · **Mode:** Standard (serialized A0 reconciliation — no new packet, no new domain behaviour)
**Base task artifact:** `Aplicacion/task/salesianos-fest-rebuild/wave-01-foundations/FND-01-backend-shared-api-media.md`

---

## 1. Packet Result

**status:** ok

**executive_summary:** The A0 reconciliation of packet **FND-01** applied the registration and the
public-error work that the completed foundations **FND-02 (`eventos`), FND-03 (`usuarios`) and
FND-04 (`commerce` + `pagos`)** had requested as evidence. Four completed apps are now registered
in the Django order dictated by the migration graph (`eventos` → `usuarios` → `pagos` →
`commerce`), `AUTH_USER_MODEL = "usuarios.Usuario"` is fixed **before** the target's first real
migration, the four completed DI modules are registered, the three completed controllers are
registered through the FND-01 extension point (`registrar_controladores`), the rejected global
`EVENTO_ACTIVO_NOMBRE` assumption is **removed**, the 18 safe public error codes requested by the
three packets were merged into the frozen catalog, and the contract-version registry was verified
against the declared `SCHEMA_VERSION` of every completed foundation. The live API now exposes
**exactly 7 domain routes** (the frozen ledger's `RT-ED-01`, `RT-ID-01…03`, `RT-PG-01…03`) plus
the 3 JWT routes — **no unfinished domain controller is registered**. The integrated migration
applies from an empty database, is reversible and replays in the required order; the focused
suites are green (**277 passed** in the combined run). No forbidden or frozen root was touched,
no commit was created and `git stash` was never used.

---

## 2. Scope, allowed roots and preserved freezes

| Item | Value |
|---|---|
| Target root | `Aplicacion/backend` |
| Allowed edits | `config/api.py` · `config/settings/**` · A0 `core/{responses,exceptions,permissions,capacidades,contract_versions}.py` + directly related A0 tests · packet evidence · `STATE.md` transition · shared Engram apply-progress/state |
| Narrow exception used | **Requirement 8**: intentionally temporary *registration-pending* test artefacts whose **own packet evidence explicitly requires** A0 to act on them, and only when the file is inside a domain root (see §9.3) |
| Read-only | frozen `backend/**`, `frontend/**`, `worker/**`, `proxy/**` · `contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**` · `Aplicacion/frontend/**` (owned by another agent) |
| Forbidden | domain internals under `modules/**` (except the narrow exception above) · secrets/`.env*` · databases/dumps · proxy/worker |
| Freezes preserved | `FREEZE-ENV-1.0.0` · `FREEZE-ED-1.0.0` · `FREEZE-ID-1.0.0` · `FREEZE-CM-1.0.0` · `FREEZE-PS-1.0.0` · `FREEZE-TC-1.0.0` · `FREEZE-MD-1.0.0` · GOV-01 freezes (`FR-01`…`FR-09`) |
| Git | `git stash` **never invoked** · **no commit created** · HEAD unchanged at `f3df5401c56b41c340f257e67d5a306904a9e670` |

---

## 3. A0 requests — disposition

### 3.1 Accepted and applied

| Request | Source | Disposition | Where |
|---|---|---|---|
| Register the completed apps in the correct Django order | FND-02 A0-02, FND-03 A0-01, FND-04 A0-01 | **applied** | `config/settings/base.py` → `LOCAL_APPS` |
| Fix `AUTH_USER_MODEL = "usuarios.Usuario"` before the target's first real migration | FND-03 A0-01 | **applied** | `config/settings/base.py` (Auth section) |
| Register the completed DI modules | FND-02 A0-02, FND-03 A0-01, FND-04 A0-01 | **applied** (4 modules) | `config/settings/base.py` → `NINJA_EXTRA["INJECTOR_MODULES"]` |
| Register the completed controllers through the FND-01 extension point | FND-02 A0-03, FND-03 A0-02, FND-04 A0-03 | **applied** (3 controllers) | `config/api.py` → `registrar_controladores(...)` |
| Remove `EVENTO_ACTIVO_NOMBRE` | FND-02 A0-04 (FR-02 §2.4 · D-01) | **applied** — the setting and its legacy block are gone | `config/settings/base.py` |
| Public error catalog — 8 codes (`eventos`) | FND-02 A0-01 | **applied** | `core/exceptions.py` → `PUBLIC_ERROR_MESSAGES` |
| Public error catalog — 4 codes (`usuarios`) | FND-03 A0-02 | **applied** | `core/exceptions.py` → `PUBLIC_ERROR_MESSAGES` |
| Public error catalog — 6 codes (`commerce` + `pagos`) | FND-04 A0-04 | **applied** | `core/exceptions.py` → `PUBLIC_ERROR_MESSAGES` |
| Confirm the HTTP status of the new codes | FND-04 A0-05 | **verified** — see §6.2 (no edit needed) | domain exception classes (read-only) |
| Contract-version registry covers the completed foundations | FND-01 §8, FR-07 §5 | **verified + drift test added** | `core/contract_versions.py` + `core/tests/integration/test_contract_versions.py` |

### 3.2 Deferred — recorded, deliberately NOT applied

| Request | Source | Why it was not applied | Owner to resolve |
|---|---|---|---|
| `*.sqlite3` in the target `.gitignore` | FND-01 §12.2, FND-02 A0-05, FND-04 A0-06 | `Aplicacion/backend/.gitignore` is **outside the allowed edit roots** of this reconciliation (the roots are `config/api.py`, `config/settings/**`, the A0 `core/**` files, packet evidence, `STATE.md` and the Engram topics). The byproduct was deleted again after the verification runs | A0 (next A0 packet with `.gitignore` in scope) |
| Sync the physical task matrix `00-matriz-tareas.md` (rows `T-010`…`T-014`, `T-016`, `T-018`) | FND-01 §2.1, FND-02 A0-07, FND-03 A0-04, FND-04 A0-07 | The matrix is **outside the allowed edit roots** (only *packet evidence*, the *`STATE.md` transition* and the shared Engram topics are editable) | A0 (matrix sync) |
| `D-FND-02-08` — `details` support for the `EDICION_AMBIGUA` candidate list | FND-02 A0-06 | **A product/architecture decision that is still open**, and the A0 side cannot implement it alone: the boundary would have to import the domain vocabulary (`exc.candidatas`) into the shared error layer, which is exactly the leak the frozen backend was criticised for (cf. FND-04 learned #5). The candidate list stays available, public-safe, on the domain exception; the public prose is now catalogued | A0 + producto |
| Whether `core/capacidades.py::es_admin` must honour the `Administrador` group | FND-03 A0-05 (`NEW-FND03-04`) | An **authorization-behaviour** decision that is still open. Changing it would broaden domain behaviour, which this reconciliation must not do | A0 + producto |
| Whether `IZIPAY_KEY_HASH` must be in the target `.env` before release | FND-04 A0-08 | `.env*` is a **forbidden** root (secrets) and the decision is a release/product decision. **No secret value was read, printed or copied** | A0 + producto (release) |
| `D-FND-04-03` — the manual-approval channel `RT-PG-05` | FND-04 open decisions | No route may be registered without a frozen, versioned module; the channel is still undecided | A0 |
| `commerce` has no HTTP surface | FND-04 `D-FND-04-06` | Not a request: a recorded decision. Honoured — no `CommerceController` is registered | — |

### 3.3 Requests accepted with a declared deviation

| Request | Deviation |
|---|---|
| The three verification overlays of the domain packages (`modules/{eventos,usuarios,pagos}/tests/settings_overlay.py`) are *temporary registration-pending* artefacts whose own evidence says A0 must retire them once the permanent registration exists | They were **adapted, not deleted** (idempotent registration) instead of being removed. Deleting them would also delete the file-SQLite rehearsal capability (`*_SQLITE_PATH`) and break the documented verification commands of three packets. See §9.3 and §11-D-04 |

---

## 4. Exact registrations

### 4.1 Apps — `config/settings/base.py` → `LOCAL_APPS`

```python
LOCAL_APPS = [
    'import_export',

    "core",
    "modules.eventos",
    "modules.usuarios",
    "modules.pagos",
    "modules.commerce",
]
```

**Why this order** — the order follows the **migration dependency graph**, which is the authority:

| App | Label | Migration dependency | Consequence |
|---|---|---|---|
| `modules.eventos` | `eventos` | none (independent) | may be registered first |
| `modules.usuarios` | `usuarios` | `("auth", "0012_alter_user_first_name_max_length")` + `swappable_dependency(AUTH_USER_MODEL)` | must precede `pagos` and `commerce` |
| `modules.pagos` | `pagos` | `swappable_dependency(settings.AUTH_USER_MODEL)` → `usuarios` | must precede `commerce` |
| `modules.commerce` | `commerce` | `("pagos", "0001_initial")`, `("usuarios", "0002_grupos_funcionales")`, `swappable_dependency(AUTH_USER_MODEL)` | last |

The effective migration order observed in the integrated apply is exactly
**`usuarios` → `pagos` → `commerce`**, with `eventos` applied independently.

### 4.2 `AUTH_USER_MODEL`

```python
AUTH_USER_MODEL = "usuarios.Usuario"
```

Fixed in `config/settings/base.py` **before** the target's first real migration. The target
database was empty, so the swap needed no `auth` surgery. The label is `usuarios` (not
`modules_usuarios`) because `modules/usuarios/apps.py` declares `label = "usuarios"`.

### 4.3 DI modules — `NINJA_EXTRA["INJECTOR_MODULES"]`

```python
"INJECTOR_MODULES": [
    "modules.usuarios.di.UsuariosModule",
    "modules.eventos.di.EventosModule",
    "modules.pagos.di.PagosModule",
    "modules.commerce.di.CommerceModule",
]
```

Only the **completed** DI modules. `pagos` binds the two `commerce` ports through lazy factories
(`modules/pagos/di.py`), so the module graph stays acyclic and the load order is irrelevant.

### 4.4 Controllers — `config/api.py` (FND-01 extension point)

```python
registrar_controladores(NinjaJWTDefaultController)
registrar_controladores(EdicionController, PersonaController, PagosController)
```

| Controller | Module | Routes |
|---|---|---|
| `NinjaJWTDefaultController` | `ninja_jwt` | `POST /api/token/pair`, `/api/token/refresh`, `/api/token/verify` |
| `EdicionController` | `modules.eventos` (FND-02) | `GET /api/ediciones/actual` (RT-ED-01) |
| `PersonaController` | `modules.usuarios` (FND-03) | `GET /api/personas/busqueda/{documento}` (RT-ID-01), `POST /api/personas/resolver` (RT-ID-02), `POST /api/personas/confirmar` (RT-ID-03) |
| `PagosController` | `modules.pagos` (FND-04) | `POST /api/pagos/ordenes/{orden_id}/confirmar` (RT-PG-01), `POST /api/pagos/izipay/notificacion` (RT-PG-02), `GET /api/pagos/ordenes/{orden_id}` (RT-PG-03) |

`commerce` contributes **no** controller (`D-FND-04-06`): its purchases are created in-process by
the domains.

### 4.5 Live route inventory (proof)

Extracted from the **live** API instance (`api.get_openapi_schema()`), not from a declaration:

```
GET  /api/ediciones/actual
POST /api/pagos/izipay/notificacion
GET  /api/pagos/ordenes/{orden_id}
POST /api/pagos/ordenes/{orden_id}/confirmar
GET  /api/personas/busqueda/{documento}
POST /api/personas/confirmar
POST /api/personas/resolver
POST /api/token/pair
POST /api/token/refresh
POST /api/token/verify
```

**Exactly 7 domain routes + 3 JWT routes. Nothing else exists.** No unfinished domain
(`pases`, `beneficios`, `validaciones`, `marketplace`, `patrocinadores`, `competencias`,
`administracion`, `inscripciones`) is registered — those modules do not exist in the target.

---

## 5. The rejected `EVENTO_ACTIVO_NOMBRE` assumption — removed

`FREEZE-ED-1.0.0` (FR-02 §2.4 · D-01) removes the global "active event by name" scope
assumption. The setting and its legacy comment block are **deleted** from
`config/settings/base.py`; **no replacement setting was invented** — the scope is resolved by
the frozen order in the `eventos` module (explicit edition → the actor's active edition → the
single `PUBLICADA` edition → error).

Proof: `settings.EVENTO_ACTIVO_NOMBRE` → `presente: False`.

---

## 6. Public error catalog merge

### 6.1 Codes merged (18)

| Block | Codes |
|---|---|
| `eventos` (FND-02 A0-01, 8) | `EDICION_NO_ENCONTRADA` · `EDICION_NO_PUBLICADA` · `EDICION_AMBIGUA` · `EDICION_NO_RESUELTA` · `EVENTO_NO_ENCONTRADO` · `EDICION_SLUG_DUPLICADO` · `EDICION_PUBLICADA_DUPLICADA` · `MODULO_NO_HABILITADO` |
| `usuarios` (FND-03 A0-02, 4) | `FUENTE_EXTERNA_NO_DISPONIBLE` · `FUENTE_EXTERNA_TIMEOUT` · `PERSONA_DATOS_INCOMPLETOS` · `PERSONA_DUPLICADA` |
| `commerce` + `pagos` (FND-04 A0-04, 6) | `IDEMPOTENCY_KEY_REUTILIZADA` · `IDEMPOTENCY_KEY_INVALIDA` · `ORDEN_PAGO_NO_PAGABLE` · `COMPRA_TOTAL_INCOHERENTE` · `COMPRA_REFERENCIA_INVALIDA` · `COMPRA_NO_ENCONTRADA` |

**No raw error leaks.** Every prose is fixed Spanish text; none interpolates a UUID, an internal
id, a slug, an amount, a SQL constraint, a provider payload or a credential. The three codes
proposed verbatim by FND-03 keep their proposed prose
(`FUENTE_EXTERNA_NO_DISPONIBLE`, `FUENTE_EXTERNA_TIMEOUT`, `PERSONA_DATOS_INCOMPLETOS`,
`PERSONA_DUPLICADA`).

`GENERIC_PUBLIC_MESSAGES` also gained the two statuses the completed domains actually use
(**503** and **504**), so an *uncatalogued* code with those statuses still answers with a safe,
generic, recoverable message instead of the 500 one.

### 6.2 HTTP statuses confirmed (FND-04 A0-05) — read-only verification

| Code | Status in the domain exception | Verdict |
|---|---|---|
| `PAGO_FIRMA_INVALIDA` | 400 (`ErrorPago400`) | ✅ ledger status confirmed (not the 409 of the frozen backend) |
| `PAGO_NOTIFICACION_NO_VERIFICABLE` | 400 (`ErrorPago400`) | ✅ confirmed |
| `IDEMPOTENCY_KEY_REUTILIZADA` | 409 (`ConflictError`) | ✅ confirmed |
| `IDEMPOTENCY_KEY_INVALIDA` | 409 (`ConflictError`) | ✅ confirmed |
| `COMPRA_TOTAL_INCOHERENTE` | 422 (`UnprocessableEntityError`) | ✅ confirmed |
| `ORDEN_PAGO_NO_PAGABLE` | 409 (`ConflictError`) | ✅ confirmed |
| `COMPRA_REFERENCIA_INVALIDA` | 422 (`UnprocessableEntityError`) | ✅ confirmed |
| `COMPRA_NO_ENCONTRADA` | 404 (`HttpError(404, …)`) | ✅ confirmed |
| `PERSONA_DATOS_INCOMPLETOS` | 422 | ✅ confirmed |
| `PERSONA_DUPLICADA` | 409 | ✅ confirmed |
| `FUENTE_EXTERNA_NO_DISPONIBLE` / `FUENTE_EXTERNA_TIMEOUT` | 503 / 504 | ✅ confirmed |
| `eventos` codes | 404 (`NotFoundError`) / 409 (`ConflictError`) | ✅ confirmed |

The catalog only holds prose; the status lives in the exception class, so no A0 edit was needed.
No domain file was modified to satisfy A0-05.

---

## 7. Contract-version registry

`core/contract_versions.py` already declared `eventos`, `usuarios`, `commerce` and `pagos` at
`1.0.0`. The reconciliation **verified** it against the modules themselves and made the check
executable:

* `test_el_registro_incluye_los_fundamentos_completados[eventos|usuarios|commerce|pagos]` — the
  registry contains every completed foundation at the frozen version.
* `test_no_hay_drift_entre_el_registro_y_el_modulo[eventos|usuarios|commerce|pagos]` — the
  registry version equals the `SCHEMA_VERSION` each module declares in
  `modules/<modulo>/presentation/schemas/__init__.py` (the drift test FR-07 §5 asks for).

`ENVELOPE_VERSION = "1.0.0"` and the schema semantics (MAJOR / MINOR / PATCH) are untouched.

---

## 8. Files changed (this reconciliation)

| File | Action | What was done |
|---|---|---|
| `Aplicacion/backend/config/settings/base.py` | Modified | `LOCAL_APPS` → 4 completed apps in dependency order; `AUTH_USER_MODEL = "usuarios.Usuario"` added; `EVENTO_ACTIVO_NOMBRE` + its legacy block removed; `NINJA_EXTRA["INJECTOR_MODULES"]` → 4 completed DI modules. **No other setting was touched.** |
| `Aplicacion/backend/config/api.py` | Modified | Imports of the three completed controllers; `registrar_controladores(EdicionController, PersonaController, PagosController)`; the docstring updated to state the rule that only completed controllers are registered. The pytest startup-cleanup block and the JWT registration were preserved **verbatim**. |
| `Aplicacion/backend/core/exceptions.py` | Modified | 18 public codes added to `PUBLIC_ERROR_MESSAGES`; 503/504 added to `GENERIC_PUBLIC_MESSAGES`. **No handler was weakened**: the catalog still wins over raw exception text, and the no-leak rule is unchanged. |
| `Aplicacion/backend/core/tests/integration/test_registration_extension.py` | Modified | Rewritten for the closed, explicit registry: the completed controllers are registered, the registry is idempotent, **no unfinished domain controller** is registered (asserted over the **live OpenAPI surface**), and the domain routes are **exactly** the frozen ledger's 7. |
| `Aplicacion/backend/core/tests/integration/test_contract_versions.py` | Modified | Added the registry-coverage and drift tests of §7. |
| `Aplicacion/backend/modules/eventos/tests/settings_overlay.py` | Adapted | Idempotent app + DI registration (requirement 8). |
| `Aplicacion/backend/modules/usuarios/tests/settings_usuarios.py` | Adapted | Idempotent app + DI registration (requirement 8). |
| `Aplicacion/backend/modules/pagos/tests/settings_overlay.py` | Adapted | Idempotent app + DI registration (requirement 8). |
| `Aplicacion/backend/modules/usuarios/tests/test_registro_de_la_app_pendiente.py` | **Deleted** | The intentional registration-pending marker: FND-03 §8.1 requires its deletion once A0 applies the registration ("it fails on purpose from that moment on"). It would have failed the required combined command. |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/FND-01-a0-reconciliation.md` | Created | This file. |
| `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/FND-01-backend-shared-api-media.md` | Modified | §17 — the A0 reconciliation subsection. |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | Modified | The serialized transition note. |

**`core/responses.py`, `core/permissions.py` and `core/capacidades.py` were NOT modified** — the
envelope, the gates and the capability map needed no change. `core/capacidades.py` stays the
single authority (`admin = is_staff OR is_superuser`).

---

## 9. Commands run, workdirs and exit codes

All backend commands run from `Aplicacion/backend` with the project virtual environment
(`.\.venv\Scripts\python.exe`, Python 3.10.x, Django 5.2.11, django-ninja 1.5.3,
django-ninja-extra 0.31.0, pytest 8.3.4, pytest-django 4.9.0).

### 9.1 Django gates

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| V2 | `manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` — no pending model migration |
| V3 | `manage.py check` (default = `config.settings.production`) | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **identical to the FND-01/02/03/04 baseline; environmental, not a regression** |
| V4 | `manage.py makemigrations --check --dry-run` (default settings) | **1** | same `DB_NAME` failure — **identical baseline** |

### 9.2 Integrated migration apply (empty database), replay and rollback

| # | Command | Exit | Result |
|---:|---|---:|---|
| V5 | `migrate --settings=config.settings.development` (empty DB) | **0** | `Applying usuarios.0001_initial` → `usuarios.0002_grupos_funcionales` → `pagos.0001_initial` → `commerce.0001_initial` → `eventos.0001_initial` — **the required order** |
| V6 | `migrate` (repeat) | **0** | `No migrations to apply` — idempotent |
| V7 | `showmigrations eventos usuarios pagos commerce` | **0** | `[X] 0001_initial` (eventos) · `[X] 0001_initial`, `[X] 0002_grupos_funcionales` (usuarios) · `[X] 0001_initial` (pagos) · `[X] 0001_initial` (commerce) |
| V8 | `migrate commerce zero` → `migrate pagos zero` → `migrate usuarios zero` → `migrate eventos zero` | **0** | all four `Unapplying … OK` — reversible |
| V9 | `migrate` (replay) | **0** | `Applying usuarios… → pagos… → commerce… → eventos…` — replayed in the same order |
| V10 | `py_compile` of every changed Python file | **0** | all compile |

### 9.3 Focused suites

| # | Command | Exit | Result |
|---:|---|---:|---|
| V11 | `python -m pytest core/tests modules/eventos/tests modules/usuarios/tests modules/commerce/tests modules/pagos/tests -q` (**the required combined command**) | **0** | **277 passed** |
| V12 | `python -m pytest -q` (whole target root) | **0** | **277 passed** |
| V13 | `python -m pytest core/tests -q` | **0** | **99 passed** (FND-01 baseline 89 + 10 new) |
| V14 | `python -m pytest modules/eventos/tests -q` | **0** | **63 passed** — FND-02 baseline intact |
| V15 | `python -m pytest modules/usuarios/tests -q` | **0** | **35 passed** — FND-03 baseline intact (**the pending-registration marker is gone: no more skip**) |
| V16 | `python -m pytest modules/commerce/tests -q` | **0** | **15 passed** — FND-04 baseline intact |
| V17 | `python -m pytest modules/pagos/tests -q` | **0** | **64 passed** — FND-04 baseline intact |
| V18 | `python -m pytest core/tests/integration/test_registration_extension.py -v` | **0** | **8 passed** — the focused registration/startup test |
| V19 | `python -m pytest core/tests/integration/test_contract_versions.py -v` | **0** | **31 passed** together with V18 |
| V20 | `pytest modules/eventos/tests -q --ds=modules.eventos.tests.settings_overlay` | **0** | **63 passed** — the adapted overlay still works |
| V21 | `pytest modules/usuarios/tests -q --ds=modules.usuarios.tests.settings_usuarios` | **0** | **35 passed** — the adapted overlay still works |
| V22 | `pytest modules/commerce/tests modules/pagos/tests -q --ds=modules.pagos.tests.settings_overlay` | **0** | **79 passed** — the adapted overlay still works |

### 9.4 Live-API audit (read-only)

| # | Command | Exit | Result |
|---:|---|---:|---|
| V23 | startup audit of `config.api` (controllers, apps, `AUTH_USER_MODEL`, DI modules, OpenAPI paths, catalog coverage) | **0** | 4 controllers with prefixes `/token`, `/ediciones`, `/personas`, `/pagos` · 4 apps · `usuarios.Usuario` · 4 DI modules · 10 live routes · `EVENTO_ACTIVO_NOMBRE` **absent** · **18/18** new codes catalogued |

### 9.5 Repository-root integrity

| # | Command | Exit | Result |
|---:|---|---:|---|
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** — no forbidden product root touched |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | **empty** — the frozen roots are untouched |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — **unchanged, no commit created** |
| R4 | `git stash` | — | **never invoked** |
| R5 | `git status --short -- Aplicacion/backend` | **0** | the expected set only; the `db.sqlite3` byproduct of the migration rehearsal was **deleted** |

**Note on a pre-existing working-tree change:** `evidence/checkpoint/manifest-aplicacion.csv` and
`evidence/checkpoint/excluded-generated-trees.csv` show as modified in `git status`. They were
written by the **GOV-00** checkpoint (mtime 2026-11-18 18:51, hours before this reconciliation)
and the diff is a **line-ending normalisation only**. **This reconciliation did not touch them.**

---

## 10. Baseline comparison

| Item | Before | After | Verdict |
|---|---|---|---|
| `manage.py check` (default settings) | exit 1 (`DB_NAME`) | exit 1 (`DB_NAME`) | **unchanged — environmental baseline** |
| `makemigrations --check --dry-run` (default settings) | exit 1 (`DB_NAME`) | exit 1 (`DB_NAME`) | **unchanged — environmental baseline** |
| `check --settings=config.settings.development` | exit 0 | exit 0 | unchanged |
| `makemigrations --check --dry-run --settings=config.settings.development` | exit 0 | exit 0 | unchanged |
| `core/tests` | 89 passed | **99 passed** | +10 A0 tests, green |
| `modules/eventos/tests` | 63 passed | 63 passed | intact |
| `modules/usuarios/tests` | 35 passed, **1 skipped** | **35 passed, 0 skipped** | the pending marker is gone |
| `modules/commerce/tests` | 15 passed | 15 passed | intact |
| `modules/pagos/tests` | 64 passed | 64 passed | intact |
| Combined suite | not runnable (apps unregistered) | **277 passed** | **green** |
| Forbidden / frozen-root diff | empty | empty | **clean** |
| `EVENTO_ACTIVO_NOMBRE` | present in settings | **absent** | removed (FR-02 §2.4) |

**Regressions: none.** No frozen file modified. No commit created. `git stash` not invoked.

---

## 11. Deviations

| # | Deviation | Why | Risk |
|---|---|---|---|
| D-A0R-01 | The three domain verification overlays were **adapted** (idempotent registration) instead of **deleted** as their own evidence asks | Requirement 8 permits "delete **or** adapt". Deleting would remove the file-SQLite rehearsal capability (`*_SQLITE_PATH`) and break three packets' documented verification commands. The adaptation keeps every documented command working and removes the duplicate-label failure | **Low** — behaviour identical when the permanent registration is absent |
| D-A0R-02 | `modules/usuarios/tests/test_registro_de_la_app_pendiente.py` was **deleted** | FND-03 §8.1 explicitly requires it: "it fails on purpose from that moment on". It would have failed the required combined command | **None** — the file's only purpose was to signal the pending registration |
| D-A0R-03 | `modules/commerce/tests/settings_overlay.py` was **not** touched | It only re-exports `modules.pagos.tests.settings_overlay`; the idempotency of the latter is inherited | None |
| D-A0R-04 | The `usuarios` package conftest still carries the *pending-registration* branch (now inert) | Cosmetic; editing a domain conftest is **not** required by any packet evidence, and requirement 8 only covers registration-pending **tests** | None — the branch is simply never taken |
| D-A0R-05 | `D-FND-02-08` (candidate list in `error.details`) was **not** implemented | Implementing it on the A0 side would require importing the domain vocabulary into the shared error boundary. The candidates stay on the domain exception (public-safe) and the public prose is catalogued | Low — the ambiguity is still reported as 409 `EDICION_AMBIGUA` with a safe message |
| D-A0R-06 | `core/capacidades.py` was **not** changed to honour the `Administrador` group | Open authorization-behaviour decision (`NEW-FND03-04`); changing it would broaden domain behaviour | None — the capability map stays the single authority |

---

## 12. Rollback

- **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` — unchanged; **do not revert or
  reset it**.
- **Code rollback:** restore `config/settings/base.py` and `config/api.py` to their pre-
  reconciliation content (remove the 4 apps, `AUTH_USER_MODEL`, the 4 DI modules and the 3
  controller registrations; restore the `EVENTO_ACTIVO_NOMBRE` block), remove the 18 catalog
  entries and the 503/504 generic messages from `core/exceptions.py`, restore the two A0 test
  files, re-create `modules/usuarios/tests/test_registro_de_la_app_pendiente.py` and revert the
  three overlays.
- **Data rollback:** the `AUTH_USER_MODEL` swap is only safe to undo on an **empty** target
  database. The target database is empty (the rehearsal file `Aplicacion/backend/db.sqlite3` was
  **deleted** after the verification runs), so no data rollback is needed.
- **State rollback:** restore `STATE.md` and the two Engram topics to their FND-04 revisions.
- The rollback is safe **before** the consumers below start depending on the permanent routes.

---

## 13. Consumers unblocked

| Consumer | Enabling artefact | Remaining DAG dependency |
|---|---|---|
| **FND-05** (exactly-once rights activation) | the `usuarios`, `pagos` and `commerce` apps are installed and migrated; `Compra.estado` and the payment verdict exist | none from A0 |
| **DOM-01 / DOM-02 / DOM-03 / DOM-05** (inscription, passes, marketplace) | the edition scope, the identity module and the commerce module are live in the same database | their own dependencies |
| **API-01 … API-05** | the completed routes are **served by the project API** (previously dead code) | UI-0x, DOM-0x, FND-08 |
| **FND-07 / FND-08** (frontend Zod mirrors, query keys) | the frozen envelope and the frozen error codes are catalogued | FND-06 |
| **XCT-01 … XCT-03** | one database with the four foundations migrated in the required order | DOM-0x |
| **VER-01 … VER-03** | the target boots, migrates and serves the frozen routes | all implementation packets |

**Still blocked on A0 (recorded, not applied):** the `.gitignore` entry, the physical task matrix
sync, `D-FND-02-08`, the `Administrador`-group capability decision and the `IZIPAY_KEY_HASH`
release decision — see §3.2.

---

## 14. Next packet

**FND-05** — *Coordinate Exactly-Once Rights Activation* (`T-015`) — is the next packet in
`wave-01-foundations` and is now unblocked: the payment is durable in the target database before
any activation, and the four foundations share one migrated database.

**Carry-forward:** `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 · D-A…D-E ·
`GOV-02-UX-01`…`05` · `GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` ·
`P-01`…`P-12` · `NEW-FND03-01`…`04` · `D-FND-02-01`…`09` · `D-FND-04-01`…`06` ·
**new:** `D-A0R-01` (the overlays were adapted, not retired — A0 may retire them later) ·
`D-A0R-05` (`D-FND-02-08` still open) · `D-A0R-06` (`NEW-FND03-04` still open).
