# FND-03 — Identity, Roles And RENIEC Resolution

**Packet:** `FND-03` · **Original plan tasks:** `T-011`, `T-012` · **Owner:** A1
**Freeze:** `FREEZE-ID-1.0.0` (`FR-03`) + `FREEZE-PS-1.0.0` (`FR-07`)
**Status:** **completed** (implementation + verification), with **one A0 dependency open** (app registration)
**Date:** 2026-11-19 · **Branch:** `master` · **HEAD:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged, no commit)

---

## 1. Executive summary

The `usuarios` module was created from scratch in the target backend
(`Aplicacion/backend/modules/usuarios/**`): civil identity (`Persona`), optional
accounts (`Usuario`), the two functional Django groups (`Normal`,
`Administrador`), the frozen titularidad interface (four titularidades, no
central service), and a local-first resolver to the external document source
with typed external states and deferred persistence.

Key delivered behaviours:

- `Persona` exists **without** an account; `Usuario` exists **without** a
  `Persona` (technical accounts). The relation is 1:1 and **optional** in both
  directions (`FR-03` §1.1, §1.2, `RN-U01`).
- The resolver is **local-first**: a local hit never touches the external
  source (`FR-03` §3.2 regla 1).
- The external source answers with **five typed states** (`ENCONTRADO`,
  `NO_ENCONTRADO`, `DATOS_INCOMPLETOS`, `TIMEOUT`,
  `FUENTE_NO_DISPONIBLE`); the four failure states are distinguishable at the
  domain level and the retryable/non-existent distinction reaches HTTP
  (`FR-03` §3.3).
- External identities are persisted **only** when the real operation is
  confirmed (`FR-03` §3.2 regla 2).
- Duplicate creation is protected by the database `UniqueConstraint` plus a
  **controlled retry** on `IntegrityError` — never a silent `get_or_create`
  (`FR-03` §3.2 regla 3, `RN-U03`).
- Knowing a document never authorizes another person's operation: the subject
  of a titularidad check can only be the `Persona` linked to the
  authenticated account (`RN-U04`).
- Three frozen HTTP routes (`RT-ID-01`, `RT-ID-02`, `RT-ID-03`) with the
  frozen wrapper and presenter names of the `FR-07` ledger.

**Verification:** 35 behaviour tests pass; `makemigrations --check` and
`manage.py check` exit 0; the migrations replay cleanly on a file SQLite and
create the two functional groups; the shared suite (`core/tests`) is
unchanged at 89 passing; the frozen roots show an empty diff.

---

## 2. Scope and ownership

| Item | Value |
|---|---|
| Packet | `FND-03` (wave 01 — foundations) |
| Original task IDs | `T-011` (`Persona`/`Usuario`/roles/titularidad), `T-012` (resolver local→RENIEC + confirmed persistence) |
| Owner | A1 (`usuarios` module) |
| Dependencies | `GOV-01` (frozen), `GOV-02` (route briefs), `FND-01` (A0 shared API/permissions/media) — all satisfied |
| Allowed edit roots used | `Aplicacion/backend/modules/usuarios/**` only |
| Forbidden roots touched | **none** (empty `git status` diff for `backend/`, `frontend/`, `worker/`, `proxy/`, `contract/`, `Aplicacion/plan/`, `Aplicacion/documentacion/`) |
| A0 shared files edited | **none** — `config/api.py`, `config/settings/**`, `core/responses.py`, `core/exceptions.py`, `core/permissions.py` are untouched by this packet (their current diff is FND-01's) |
| Commits | none (`git stash` and `git commit` were never used) |

---

## 3. Mandatory context read

| Source | Used for |
|---|---|
| `contract/django-app-architecture-contract.md` | Module layout, sync/async chain, controller/orchestrator/flow/core rules, atomic placement, exceptions, naming |
| `contract/PLAN_REFACTORIZACION.md` | "Sagrados" controllers, `BaseSchema` obligation, absolute imports (§1.E), atomic only in the flow (§4), presenter rules |
| `contract/api-wrapper-presenter-contract.md` | Typed module wrappers, presenter ≠ selector, public message contract, error ownership |
| `contract/TEST_ARCHITECTURE_CONTRACT.md` | Test tree, `factories.py`, fixtures, no `unittest.mock.patch`, client matrix |
| `contract/SCHEMA_DRY_INTENTION.md` | Three-block schema composition (General / Specific / Identity) |
| `Aplicacion/plan/.../00-decisiones-y-alcance.md` | `DEC-02`, `DEC-03`, `DEC-04` |
| `Aplicacion/plan/.../funcional/02-reglas-de-negocio.md` | `RN-U01`, `RN-U02`, `RN-U03`, `RN-U04` |
| `Aplicacion/plan/.../funcional/04-flujos-end-to-end.md` | `FL-02` (resolver persona por documento) |
| `Aplicacion/plan/.../contratos/02-autenticacion-y-permisos.md` | Identity/account, auth vs authorization matrix, groups, local→RENIEC flow, guest purchase |
| `Aplicacion/plan/.../contratos/03-integraciones-y-eventos-internos.md` | RENIEC integration, failure/recovery table, rate limiting note |
| `evidence/contracts/FR-03-identity-titularidad.md` | The frozen identity/titularidad contract (authoritative) |
| `evidence/contracts/FR-07-presenter-schema-versions.md` + `route-to-wrapper-ledger.csv` | Route ids, HTTP verbs, wrapper names, presenter names, error codes |
| `evidence/contracts/FR-01/FR-05/FR-06` (as needed) | Envelope, rights actor shape, media rules (not applicable here) |
| `Aplicacion/documentacion/01-arquitectura-y-runtime.md`, `04-datos-y-dominio.md`, `02a/02b` | External document service contract (`worker/scraper`: `GET {SCRAPER_URL}/consultar/{documento}`), identity endpoints and their current behaviour |
| `.opencode/skills/salesianos-feature-architecture/SKILL.md` | Layer boundaries, read-contract-before-edit discipline |
| `.opencode/skills/salesianos-api-data/SKILL.md` | Typed wire schemas, endpoint traceability, no invented endpoints |

---

## 4. What was implemented

### 4.1 Identity model (`FREEZE-ID-1.0.0` §1)

| Rule | Where | Evidence |
|---|---|---|
| `Persona` unique by `(tipo_documento, numero_documento)` | `domain/models/persona.py` → `UniqueConstraint("unique_tipo_numero_documento")` | `test_persona_es_unica_por_tipo_y_numero` |
| Document normalized (no separators, upper case) → case-insensitive comparison | `domain/schemas/persona_schemas.py::normalizar_numero_documento` | `test_documento_se_normaliza_para_la_comparacion` |
| Closed document vocabulary (`DNI`, `CE`, `PAS`) | `domain/constants.py::TipoDocumentoChoices` | `test_resolver_rechaza_tipo_documento_invalido` |
| `Persona` exists without account | `domain/models/persona.py` (no FK to `Usuario`) | `test_persona_puede_existir_sin_cuenta` |
| `Usuario` → `Persona` 1:1 **optional** | `domain/models/usuario.py::persona_fk` (`null=True, blank=True`) | `test_cuenta_puede_existir_sin_persona` |
| Exactly two functional groups | `domain/constants.py::GrupoFuncionalChoices` + `migrations/0002_grupos_funcionales.py` | `test_solo_existen_dos_grupos_funcionales` |
| `is_superuser` is the technical tier, not a business role | `domain/services/core/grupo_service.py` | `test_superusuario_es_nivel_tecnico_no_rol_de_negocio` |
| No account is born from resolving a document | resolver never touches `Usuario` | `test_resolver_no_nace_una_cuenta` |
| Origin and date of recovered data are kept | `Persona.origen_datos`, `Persona.datos_obtenidos_en` | `test_confirmar_persiste_la_identidad` |

### 4.2 Titularidad interface (`FREEZE-ID-1.0.0` §2)

`domain/services/core/titularidad_service.py` exposes the frozen vocabulary
(`TITULARIDAD_RESPONSABLE`, `TITULARIDAD_COMPRADOR`,
`TITULARIDAD_BENEFICIARIO`, `TITULARIDAD_ADMIN`) and **resource-agnostic**
primitives:

- `RecursoTitularidad` — the minimal view each owning module contributes
  (`responsable_id`, `persona_id`, `derecho_revocado`). The identity module
  never imports another module's models (`FR-03` §2.1 regla 1).
- `TitularidadService.persona_del_actor(usuario)` — the **only** admissible
  source of the subject: the `Persona` linked to the authenticated account.
  This is what makes `RN-U04` structural rather than documentary.
- `TitularidadService.verificar(...)` — returns a typed verdict
  (`titularidad`, `permitida`, `motivo`).

Rules proven by tests: the group does **not** replace titularidad (an
`Administrador` is not the responsable of somebody else's inscription); a
group `Administrador` holds `TITULARIDAD_ADMIN`; a revoked right denies
`TITULARIDAD_BENEFICIARIO`; an account without a linked `Persona` cannot hold
a personal titularidad; **knowing a document grants nothing**.

### 4.3 Local-first resolver (`FREEZE-ID-1.0.0` §3, `FL-02`)

`domain/services/flujos/persona_resolucion_flujo.py`

1. `buscar_local` — exact match on the normalized `(tipo, numero)` pair.
2. `consultar_externa` — only when the local lookup misses.
3. `resolver` — returns `PersonaResolucionResult` with an **explicit origin**
   (`LOCAL`, `EXTERNO`, `NO_ENCONTRADO`, `FUENTE_NO_DISPONIBLE`) plus the fine
   external `estado`.
4. `confirmar` — the **only** write path; opens `transaction.atomic()` (the
   flow is the only place with `@transaction.atomic`, per
   `PLAN_REFACTORIZACION.md` §4) and retries on `IntegrityError`.

`domain/services/orchestrators/persona_orchestrator.py` translates a failed
origin into the typed domain exception with a stable code — the controller
never builds an error response.

### 4.4 External adapter behaviour

`infrastructure/services.py::ConsultaDocumentoClient` implements the port
`IConsultaDocumentoClient` against the **already existing** document service
(`worker/scraper`); no provider payload and no credential was invented:

| Provider answer | Typed state | HTTP |
|---|---|---|
| `200 {tipo_documento, numero_documento, razon_social}` with a name | `ENCONTRADO` | 200 |
| `200` without a usable name | `DATOS_INCOMPLETOS` | 422 `PERSONA_DATOS_INCOMPLETOS` |
| `404` | `NO_ENCONTRADO` | 404 `PERSONA_NO_ENCONTRADA` |
| `422` | `DATOS_INCOMPLETOS` | 422 `PERSONA_DATOS_INCOMPLETOS` |
| `504` / read or connect timeout | `TIMEOUT` | 504 `FUENTE_EXTERNA_TIMEOUT` |
| `500`, `502`, `503`, other | `FUENTE_NO_DISPONIBLE` | 503 `FUENTE_EXTERNA_NO_DISPONIBLE` |
| network error | `FUENTE_NO_DISPONIBLE` | 503 `FUENTE_EXTERNA_NO_DISPONIBLE` |
| source not configured (`SCRAPER_URL` absent) | `FUENTE_NO_DISPONIBLE` | 503 `FUENTE_EXTERNA_NO_DISPONIBLE` |

The adapter never fabricates an identity, never propagates the provider body
to the client and never leaks the provider payload to the logs (only the HTTP
status is logged).

Name handling: the source delivers `"APELLIDOS, NOMBRES"`. When the comma is
missing the split is **not** invented: the full name goes to `nombres` and
`apellidos` stays empty (`Persona.apellidos` is `blank=True`).

Base URL resolution: `settings.SCRAPER_URL` first, then the `SCRAPER_URL`
environment variable; **no default address** — without a configured source the
resolver answers `FUENTE_NO_DISPONIBLE` instead of guessing.

### 4.5 Frozen HTTP surface (`FR-07` ledger)

| Route id | Method | Route | Presenter | Out | In | Auth | Errors |
|---|---|---|---|---|---|---|---|
| `RT-ID-01` | GET | `/personas/busqueda/{documento}` | `PersonaBusquedaPresenter` | `DocumentoConsultaOut` | — | public | `PERSONA_NO_ENCONTRADA` 404, `PERSONA_DATOS_INCOMPLETOS` 422, `FUENTE_EXTERNA_*` 503/504 |
| `RT-ID-02` | POST | `/personas/resolver` | `PersonaResolverPresenter` | `PersonaResueltaOut` | `PersonaResolverIn` | session | `PERSONA_NO_ENCONTRADA` 404, `TIPO_DOCUMENTO_INVALIDO` 422, `FUENTE_EXTERNA_*` 503/504 |
| `RT-ID-03` | POST | `/personas/confirmar` | `PersonaConfirmarPresenter` | `PersonaOut` | `PersonaConfirmarIn` | session | `PERSONA_DUPLICADA` 409, `TIPO_DOCUMENTO_INVALIDO` 422 |

`modules/usuarios/presentation/schemas/__init__.py` declares
`SCHEMA_VERSION = "1.0.0"`, matching `core/contract_versions.py`
(`SCHEMA_VERSIONS["usuarios"] = "1.0.0"`). Wrappers are composed from the
three `SCHEMA_DRY_INTENTION` blocks (`PersonaDatosOut` = General,
`PersonaIdentidadOut` = Identity, the wrapper adds the case-specific block).
Every schema inherits `core.types.BaseSchema` (`PLAN_REFACTORIZACION.md`
§1.C).

Success messages are fixed, contextual prose; errors come from the global
catalog and the stable `error.code` — never from the controller.

---

## 5. Files and migrations

All files are **new** under `Aplicacion/backend/modules/usuarios/**`
(53 files; 2 592 code lines + 829 docstring lines + 58 comment lines;
`migrations/0001_initial.py` alone is 406 generated code lines).

| Area | Files | Content |
|---|---|---|
| Domain | `domain/{constants,exceptions}.py`, `domain/models/{persona,usuario}.py`, `domain/ports/__init__.py`, `domain/results/persona_resolucion_results.py`, `domain/schemas/persona_schemas.py`, `domain/selectors/persona_selector.py`, `domain/services/core/{persona_core_service,usuario_core_service,grupo_service,titularidad_service}.py`, `domain/services/flujos/persona_resolucion_flujo.py`, `domain/services/orchestrators/persona_orchestrator.py` | Model, vocabulary, typed errors, DTOs, port, selectors, sync core services, async flow, async facade |
| Infrastructure | `infrastructure/services.py` | HTTP adapter of the document source (states, no fabrication) |
| Presentation | `presentation/schemas/{__init__,persona_schemas}.py`, `presentation/presenters/persona_presenter.py`, `presentation/controllers/persona_controller.py` | Typed wrappers, three presenters, one thin controller |
| Wiring | `apps.py`, `models.py`, `admin.py`, `di.py` | AppConfig, pure re-export, Django admin, injector module |
| Migrations | `migrations/0001_initial.py`, `migrations/0002_grupos_funcionales.py` | Schema + the two functional groups |
| Tests | `tests/**` | 35 behaviour tests + fixtures + package verification settings |

### Migrations

- `0001_initial` — `Usuario` (custom auth user), `Persona`, `HistoricalPersona`,
  the `persona_fk` 1:1 and the non-empty-email unique constraint. Its only
  dependency is `("auth", "0012_alter_user_first_name_max_length")`; the
  swappable `history_user` FK does **not** create a self-referential
  dependency.
- `0002_grupos_funcionales` — data migration that creates exactly `Normal` and
  `Administrador` (`auth.Group`), and removes them on reverse.

---

## 6. Tests and commands

### 6.1 Exact environment

Workdir: `C:\Users\Usuario\Desktop\Aplicaciones\CST\Salesianos\Aplicacion\backend`
Interpreter: `Aplicacion/backend/.venv/Scripts/python.exe` (Python 3.10.0,
Django 5.2.11, pydantic 2.12.5, pytest 8.3.4)

The module is not yet registered in `INSTALLED_APPS` (A0 dependency, §8), so
the package tests run against the **package verification settings**, which
replicate the three settings lines A0 has to apply:

```powershell
$env:PYTEST_ADDOPTS = "--ds=modules.usuarios.tests.settings_usuarios"
```

`modules/usuarios/tests/settings_usuarios.py` extends
`config.settings.test` (SQLite in memory) with `INSTALLED_APPS += "modules.usuarios"`,
`AUTH_USER_MODEL = "usuarios.Usuario"` and
`NINJA_EXTRA["INJECTOR_MODULES"] += "modules.usuarios.di.UsuariosModule"`.
It also accepts `USUARIOS_SQLITE_PATH` to point at a **file** SQLite, used
for the migration replay.

### 6.2 Results

| # | Command (workdir `Aplicacion/backend`) | Exit | Output |
|---|---|---|---|
| 1 | `python -m pytest modules/usuarios/tests -q` with `PYTEST_ADDOPTS=--ds=modules.usuarios.tests.settings_usuarios` | **0** | `35 passed, 1 skipped, 40 warnings` |
| 2 | `python -m pytest modules/usuarios/tests -q` (project settings, app **not** registered) | **0** | `1 skipped` + explicit stderr notice — the 35 tests are *omitted*, not silently passed |
| 3 | `python manage.py makemigrations --check --dry-run --settings=modules.usuarios.tests.settings_usuarios` | **0** | `No changes detected` |
| 4 | `python manage.py check --settings=modules.usuarios.tests.settings_usuarios` | **0** | `System check identified no issues (0 silenced).` |
| 5 | `python manage.py migrate --settings=modules.usuarios.tests.settings_usuarios` (file SQLite) | **0** | `Applying usuarios.0002_grupos_funcionales... OK` |
| 6 | `manage.py shell` after the replay | **0** | `GRUPOS: ['Administrador', 'Normal']` · tables `usuarios_persona`, `usuarios_usuario`, `usuarios_historicalpersona`, `usuarios_usuario_groups`, `usuarios_usuario_user_permissions` |
| 7 | `python -m pytest core/tests -q` (project settings) | **0** | `89 passed` — **unchanged** from the FND-01 baseline |
| 8 | `python manage.py check --settings=config.settings.development` | **0** | `System check identified no issues` (baseline re-check) |
| 9 | `python manage.py check` / `makemigrations --check --dry-run` with the **default** settings | **1** | pre-existing environmental baseline (default settings are `production`, which needs `DB_NAME`); identical to the FND-01 baseline, untouched by this packet |
| 10 | `git status --short -- backend frontend worker proxy contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** — frozen roots unchanged |
| 11 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — unchanged, no commit |

### 6.3 Stability

The suite was executed **12 consecutive times** after the last fix: `35
passed` on every run (see §8.2, D-3). The earlier intermittency was a real
defect of the test harness, not of the module, and it is fixed.

### 6.4 Behaviour coverage (behaviour-first)

| Behaviour | Test |
|---|---|
| success (local hit) | `test_resolver_local_no_consulta_la_fuente_externa` |
| success (external hit, not persisted) | `test_resolver_externo_no_persiste` |
| success (confirmed persistence) | `test_confirmar_persiste_la_identidad` |
| rejection (invalid document type) | `test_resolver_rechaza_tipo_documento_invalido` |
| rejection (document already linked to an account) | `test_confirmar_rechaza_documento_ya_vinculado_a_cuenta` |
| failure (not found) | `test_resolver_falla_con_no_encontrado` |
| failure (source down) | `test_resolver_falla_con_fuente_no_disponible` |
| failure (timeout — a distinct state) | `test_resolver_distingue_el_timeout` |
| failure (incomplete data — a distinct state) | `test_resolver_distingue_los_datos_incompletos` |
| recovery (retry after a source failure) | `test_el_fallo_de_la_fuente_es_recuperable` |
| concurrency (database authority) | `test_la_base_de_datos_rechaza_el_documento_duplicado` |
| concurrency (loser of the race reuses the winner's row) | `test_la_carrera_perdida_reutiliza_la_fila_ganadora` |
| concurrency (idempotent confirmation) | `test_confirmar_dos_veces_no_duplica` |
| concurrency (two simultaneous confirmations) | `test_confirmaciones_simultaneas_no_duplican` |
| titularidad (the four frozen titularidades) | `test_el_responsable_es_titular_de_su_recurso`, `test_el_comprador_es_titular_de_su_compra`, `test_el_beneficiario_con_derecho_revocado_no_es_titular`, `test_el_grupo_administrador_da_titularidad_de_administracion` |
| titularidad (group does not replace titularidad) | `test_el_grupo_no_sustituye_la_titularidad` |
| titularidad (knowledge of a document authorizes nothing) | `test_conocer_un_documento_no_autoriza_la_operacion_de_otro` |
| identity (independence of `Persona` and `Usuario`) | `test_persona_puede_existir_sin_cuenta`, `test_cuenta_puede_existir_sin_persona` |
| identity (no account born from a document lookup) | `test_resolver_no_nace_una_cuenta` |
| authorization (401 before 403) | `test_resolver_exige_sesion` |

---

## 7. Decisions and deviations

| # | Decision / deviation | Why | Owner to ratify |
|---|---|---|---|
| D-1 | **The app registration was NOT applied.** `INSTALLED_APPS`, `AUTH_USER_MODEL` and `NINJA_EXTRA["INJECTOR_MODULES"]` live in `config/settings/base.py`, an A0-owned file. The packet implements the module and **requests** the registration (§8). The package ships its own verification settings so the work is verifiable today. | `00-contrato-global-de-apply.md` — "Shared Files: A0 exclusively owns and serializes" · packet step 5 — "Request A0 registration/permission changes separately" | A0 |
| D-2 | **Three error codes are not yet in the public catalog**: `FUENTE_EXTERNA_NO_DISPONIBLE` (503), `FUENTE_EXTERNA_TIMEOUT` (504) and `PERSONA_DATOS_INCOMPLETOS` (422). `PERSONA_NO_ENCONTRADA`, `TIPO_DOCUMENTO_INVALIDO` and `PERSONA_DUPLICADA` come from the `FR-07` ledger. | The ledger lists one code for the source failure, but `FR-03` §3.3 requires the four failure states to be distinguishable so the frontend can tell "retryable" from "does not exist". Until A0 adds the prose, the codes travel in `error.code` and the public message falls back to the generic per-status prose (safe by construction). | A0 (catalog) + A1 |
| D-3 | **The package test API is session-scoped and has a unique `urls_namespace`.** | `ninja_extra` keeps the `APIController` of a controller class in **global** state. With one API per test, the registration re-points the routes to the previous API and the client intermittently fails with `Cannot resolve "/personas/resolver"` (observed 3 times in ~25 runs). One API per session removes the defect. | — (fixed in the packet) |
| D-4 | **`ninja_extra.testing.TestAsyncClient` does not merge `client.headers`** (unlike `ninja.testing.TestClient`). The package ships a 12-line subclass that merges them. | Without it the JWT header never reaches the view and every authenticated route answers 401. | — (fixed in the packet) |
| D-5 | **The HTTP tests use `django_db(transaction=True)`.** | `django-ninja` runs authentication and the operation in a worker thread. With the default `django_db` the main connection holds the write transaction and SQLite's shared in-memory cache answers `database table is locked`. With `transaction=True` the fixture data is committed and the worker thread reads it. | — (fixed in the packet) |
| D-6 | **The reverse accessor `persona.usuario` raises `RelatedObjectDoesNotExist`** for a nullable `OneToOneField`. The "already linked to an account" check therefore goes through `UsuarioSelector`. | Django semantics; documented in the flow so the next reader does not repeat the discovery. | — |
| D-7 | **`Persona.apellidos` is `blank=True`.** | The external source delivers a single `razon_social` field. When the comma is missing the split is not invented; the whole name goes to `nombres`. | A1 (already ratified by the implementation) |
| D-8 | **`Persona` carries `origen_datos` and `datos_obtenidos_en`.** | `FR-03` §3.2 regla 5 — "origen y fecha de los datos se conservan cuando se requiere control de calidad". | — |
| D-9 | **`simple_history` on `Persona` only, not on `Usuario`.** | `Usuario` is the `AUTH_USER_MODEL`; a historical model for it would add a self-referential swappable FK in the first migration. The audit of account actions (`FR-03` §5) needs an explicit audit model that no packet has frozen yet. | A1 + A0 (audit model) |
| D-10 | **`RT-ID-01` is public** (`auth=None`, `AllowAny`) exactly as the ledger states. | `FR-07` ledger, `FR-03` §4 "no exponer bases masivas de DNI". | A0 + producto (rate limiting, `contratos/03` §8) |
| D-11 | **The external source only recognises 8-digit documents (DNI).** A `CE`/`PAS` lookup answers `422 PERSONA_DATOS_INCOMPLETOS`. | The source infers the type by length (`worker/scraper`: 8 → DNI, 11 → RUC); the target vocabulary is closed to `DNI`/`CE`/`PAS`. No inference was invented for the new types. | A0 + producto + A1 |
| D-12 | **`RT-ID-01` returns the raw name of the source; `RT-ID-02` splits it.** | The ledger defines `DocumentoConsultaOut` as the source's answer and `PersonaResueltaOut` as the module's answer. | — |

---

## 8. Requests to A0

### 8.1 Registration (blocking for the project's own test/serve commands)

In `Aplicacion/backend/config/settings/base.py`:

```python
LOCAL_APPS = [
    'import_export',
    "core",
    "modules.usuarios",          # ← add
    # ...
]

AUTH_USER_MODEL = "usuarios.Usuario"   # ← add

NINJA_EXTRA = {
    "INJECTOR_MODULES": [
        "modules.usuarios.di.UsuariosModule",   # ← add
        # ...
    ]
}
```

In `Aplicacion/backend/config/api.py`:

```python
from modules.usuarios.presentation.controllers import PersonaController
registrar_controladores(PersonaController)
```

> **Order matters.** `AUTH_USER_MODEL` must be set **before** the first
> migration of the target runs. If the target database was already migrated
> with `auth.User`, the swap needs a fresh database (or an explicit
> `auth` migration surgery). The target database is empty at this point.

Once applied, delete `modules/usuarios/tests/test_registro_de_la_app_pendiente.py`
— it fails on purpose from that moment on — and re-run the package tests with
the project settings.

### 8.2 Public error catalog

In `Aplicacion/backend/core/exceptions.py` → `PUBLIC_ERROR_MESSAGES`:

| Code | Status | Proposed public prose |
|---|---|---|
| `FUENTE_EXTERNA_NO_DISPONIBLE` | 503 | "La fuente externa de documentos no está disponible. Inténtalo nuevamente." |
| `FUENTE_EXTERNA_TIMEOUT` | 504 | "La fuente externa de documentos no respondió a tiempo. Inténtalo nuevamente." |
| `PERSONA_DATOS_INCOMPLETOS` | 422 | "La fuente externa no devolvió datos suficientes para esa identidad." |

`PERSONA_DUPLICADA` (409) is in the `FR-07` ledger but not in the catalog
either; its prose is "Ese documento ya está vinculado a una cuenta."

### 8.3 Permission authority

`core/capacidades.py` resolves the administration tier from `is_staff` /
`is_superuser`. The frozen identity contract resolves the **functional** role
from the Django groups `Normal` / `Administrador`
(`domain/services/core/grupo_service.py`). Both must exist; A0 decides
whether `es_admin` should also honour the `Administrador` group, and whether
the capability map should be expressed over the groups. This packet did NOT
touch `core/capacidades.py` or `core/permissions.py`.

### 8.4 Physical task matrix

`Aplicacion/task/salesianos-fest-rebuild/00-matriz-tareas.md` rows `T-011` and
`T-012` still read `pending`: the matrix is outside every packet's allowed
edit roots. **A0 must sync them** (same as `T-016`/`T-018` for FND-01).

---

## 9. Baseline and regressions

| Item | Classification |
|---|---|
| `manage.py check` / `makemigrations --check` with the **default** settings → exit 1 | **pre-existing baseline** (default settings are `production` and need `DB_NAME`). Identical before and after this packet (FND-01 §9). |
| `core/tests` → 89 passed | **baseline preserved** |
| `pytest -q` at the target root | **collection error in `modules/eventos/tests`** — that is **FND-02's** concurrent work (the `eventos` module is not registered in `INSTALLED_APPS` either). Observed, **not touched**, and reported to A0. |
| `Aplicacion/frontend/**` changes | **FND-06's** concurrent work — observed, not touched, not merged. |
| `Aplicacion/backend/modules/eventos/**` | **FND-02's** concurrent work — observed, not touched. |
| New regressions introduced by this packet | **none** |

---

## 10. Rollback

The packet is a single self-contained work unit under
`Aplicacion/backend/modules/usuarios/**`:

1. Remove `Aplicacion/backend/modules/usuarios/` (models, migrations, services,
   presentation, tests).
2. If A0 already applied the registration, remove the three settings lines and
   the controller registration of §8.1. **The `AUTH_USER_MODEL` swap needs an
   empty target database**: reverting it against a migrated database leaves
   `auth_user` orphaned.
3. No database dump, no secret and no frozen root is involved.

---

## 11. Consumers unblocked

| Consumer | What it gets |
|---|---|
| `DOM-01` (inscripción) | `Persona`/`Usuario` models, the `Responsable` titularidad primitive and `RecursoTitularidad` |
| `DOM-03` (pases y beneficios) | `TITULARIDAD_BENEFICIARIO` (with revocation), `Persona` for the beneficiary |
| `DOM-04`/`DOM-08` | `Persona` as the buyer/sponsor identity |
| `API-01` (public account) | `RT-ID-02` (`/personas/resolver`) and `RT-ID-03` (`/personas/confirmar`) with the frozen wrappers |
| `XCT-01` (validación de tickets) | `TITULARIDAD_ADMIN` and the group authority |
| `FND-05` (derechos) | the actor shape of `FR-05` on top of `Persona`/`Usuario` |
| `FND-08` (cache) | `SCHEMA_VERSION = "1.0.0"` of `usuarios` |
| `VER-01`…`VER-03` | 35 behaviour tests, two migrations that replay, and a frozen envelope that matches `FR-01` |

**Still blocked on A0:** any consumer that needs the routes to be *served* by
the project API (the controller registration of §8.1) or that runs the project
test command without the package settings.

---

## 12. Review slices (work-unit boundary)

The packet exceeds the ~400 changed lines of the review budget
(`README.md` §"Each packet is a review unit"): **2 592 code lines** plus 829
docstring lines (of which 406 code lines are the generated migration). The
work was therefore split into four reviewable slices, all in the same
autonomous work unit and all verified together:

| Slice | Content | Approx. code lines |
|---|---|---|
| WU-A — domain | constants, exceptions, models, port, results, internal DTOs, selectors, `migrations/0001`, `0002` | ~950 |
| WU-B — behaviour | core services (persona, usuario, grupos, titularidad), flow, orchestrator, external adapter, `di.py` | ~640 |
| WU-C — surface | HTTP schemas, three presenters, controller, admin, apps, `models.py` | ~590 |
| WU-D — tests | fixtures, factories, 35 behaviour tests, package verification settings, evidence | ~520 |

No unrelated domain was mixed in to reduce the count, and no commit was made
(the packet owner / A0 decides the commits).

---

## 13. New facts established by FND-03 (carry forward)

| # | Fact | Evidence |
|---|---|---|
| F-FND03-01 | `ninja_extra.testing.TestAsyncClient.request` **ignores `client.headers`**; only per-request `headers` reach the view. A subclass that merges them is required for JWT tests. | `tests/fixtures/persona_fixtures.py::ClienteUsuarios` |
| F-FND03-02 | `ninja_extra` keeps the `APIController` of a controller class in **global** state: one API instance per test re-points the routes to the previous API and the client fails with `Cannot resolve "<ruta>"`. One API per session fixes it. | `tests/fixtures/persona_fixtures.py::api_usuarios` (session scope) |
| F-FND03-03 | `django-ninja` runs authentication and the operation in a worker thread; with SQLite's shared in-memory cache and the default `django_db` this answers `database table is locked`. `django_db(transaction=True)` is required for authenticated HTTP tests on SQLite. | all HTTP tests of the package |
| F-FND03-04 | The reverse accessor of a nullable `OneToOneField` (`persona.usuario`) raises `RelatedObjectDoesNotExist` instead of returning `None`. | `domain/services/flujos/persona_resolucion_flujo.py::_tiene_cuenta` |
| F-FND03-05 | An uncatalogued domain code still travels in `error.code`; only the public prose falls back to the generic per-status message. That is how `PERSONA_DATOS_INCOMPLETOS` stays distinguishable before A0 extends the catalog. | `core/exceptions.py::on_http_error` |
| F-FND03-06 | A `UniqueConstraint` on a swappable `AUTH_USER_MODEL` in the same app does **not** create a self-referential migration dependency: the generated `usuarios.0001_initial` depends only on `("auth", "0012_…")`. | `migrations/0001_initial.py` |
| F-FND03-07 | `pytest` sets Django up **before** the conftest files are imported, so an app cannot be added to `INSTALLED_APPS` from a conftest: the registration has to come from the settings. | `modules/usuarios/tests/conftest.py` |
| F-FND03-08 | The document source (`worker/scraper`) answers `GET {SCRAPER_URL}/consultar/{documento}` with `{tipo_documento, numero_documento, razon_social}` and infers the type by length (8 → DNI, 11 → RUC). It does not know `CE`/`PAS`. | `Aplicacion/documentacion/01-arquitectura-y-runtime.md` §8 |

---

## 14. Open items carried forward

| Id | Item | Owner |
|---|---|---|
| `GOV-01-OPEN-04` | Policy for validation operators (third group?) — untouched: the module ships exactly two groups | A0 + producto |
| `GOV-01-OPEN-05` | Expiration/rotation of guest-purchase links — not in this packet's scope | A1 + A0 + producto |
| `PD-07` | Definitive scope of the guest checkout | A1 + A7 + producto |
| NEW-FND03-01 | Audit model for sensitive account actions (`FR-03` §5) — no model frozen yet | A1 + A0 |
| NEW-FND03-02 | Rate limiting for the external document lookups (`contratos/03` §8) | A0 + producto |
| NEW-FND03-03 | External source coverage for `CE`/`PAS` (D-11) | A0 + producto + A1 |
| NEW-FND03-04 | `core.capacidades` vs the functional groups (D-3 of §8.3) | A0 |
