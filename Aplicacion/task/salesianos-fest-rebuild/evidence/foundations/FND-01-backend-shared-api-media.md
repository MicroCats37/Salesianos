# FND-01 — Backend shared API, permissions and media foundations

**Artifact:** `evidence/foundations/FND-01-backend-shared-api-media.md` · **Packet:** `FND-01-backend-shared-api-media`
**Change:** `salesianos-fest-rebuild` · **Project:** Salesianos · **Owner:** A0
**Original plan tasks:** `T-016` (media contract), `T-018` (auth/permissions contract)
**Status:** completed · **Date:** 2026-11-19 (local) · **Mode:** Standard (implementation packet, product code)

---

## 1. Packet Result

**status:** ok

**executive_summary:** FND-01 established the serialized shared backend surface of the target
(`Aplicacion/backend`): **one frozen HTTP envelope** (success / error / pagination) with a safe
public error catalog that never returns raw exception text; **the permission and authentication
authority** with an explicit 401-before-403 rule; **the local persistent media contract** (root,
URL, MIME allowlist, size cap, content-signature check, single storage path, multipart token
protocol and cleanup helpers); **the A0 registration extension point** in `config/api.py` with no
unfinished domain controllers; and **the contract-version registry** (`ENVELOPE_VERSION` +
per-module `SCHEMA_VERSION`). 89 focused behavior-first tests were added under `core/tests/` and
all pass. The frozen roots, `contract/**`, `Aplicacion/plan`, `Aplicacion/documentacion` and
`Aplicacion/frontend` were **not** modified; the two `manage.py` baseline failures remain
environmental and identical to the pre-packet baseline (`DB_NAME` missing).

---

## 2. Cumulative Task State (merged across all packets)

| Packet | Original task IDs | Status | Evidence |
|---|---|---|---|
| GOV-00 | `T-000` | completed (prior batch) | `evidence/checkpoint/GOV-00-checkpoint-summary.md` |
| GOV-01 | `T-003`…`T-007` | completed (prior batch) | `evidence/contracts/GOV-01-contract-freeze-summary.md` + 9 FR files + `route-to-wrapper-ledger.csv` |
| GOV-02 | `T-001`, `T-002` | completed (prior batch) | `evidence/routes/**` (15) + `evidence/baseline/**` (5) |
| **FND-01** | **`T-016`, `T-018`** | **completed (this batch)** | `evidence/foundations/FND-01-backend-shared-api-media.md` (this file) + `Aplicacion/backend/core/tests/**` |

**9 of the 54 source-defined task IDs are now closed** (1 + 5 + 2 + 2).

### 2.1 Where the completion is marked

| Tasks artifact | Marked? | Reason |
|---|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/00-matriz-tareas.md` (rows `T-016`, `T-018`) | **Not edited** | The matrix is **outside FND-01's allowed edit roots** (the packet permits `config/api.py`, `config/settings/**`, the four shared `core/` files, media utilities/tests under `core/**`, `**/tests/**`, the packet evidence, `STATE.md` and the two Engram topics). Its rows still read `pending`. **A0 must sync the matrix**, exactly as with GOV-00/01/02. |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | **Yes** | FND-01 row = `completed` + full transition log |
| Engram `sdd/salesianos-fest-rebuild/apply-progress` | **Yes** | §2 (cumulative table) |
| Engram `sdd/salesianos-fest-rebuild/state` | **Yes** | FND-01 transition log |

**There is no Engram `sdd/salesianos-fest-rebuild/tasks` artifact.** The physical matrix remains the
only tasks artifact and is read-only for this packet.

---

## 3. Files Changed (this packet — 12 paths, all inside the allowed edit roots)

### 3.1 Created — shared A0 files

| File | Purpose |
|---|---|
| `Aplicacion/backend/core/media.py` | The whole media contract: allowlist, size cap, signature detection, storage path, multipart token protocol, cleanup helpers. Writes nothing and opens no transaction. |
| `Aplicacion/backend/core/contract_versions.py` | `ENVELOPE_VERSION` + per-module `SCHEMA_VERSION` registry + semver comparison / drift detection (`FREEZE-PS-1.0.0`, FR-07 §5 assigns this file to FND-01 / `T-018`). |

### 3.2 Created — focused tests (`core/tests/`)

| File | Covers |
|---|---|
| `core/tests/__init__.py` · `core/tests/conftest.py` · `core/tests/fixtures/__init__.py` · `core/tests/fixtures/api_fixtures.py` | A0 shared fixtures: `api_client` (`ninja_extra.testing.TestAsyncClient`, the client `FREEZE-TC-1.0.0` mandates), `django_client` (the permitted synchronous alternative) and `api`. |
| `core/tests/integration/__init__.py` | Test package. `unit/` is not used (`contract/TEST_ARCHITECTURE_CONTRACT.md` §1). |
| `core/tests/integration/test_responses_envelope.py` | Envelope shape, one pagination shape, deprecation of the second pagination form. |
| `core/tests/integration/test_exceptions_public_catalog.py` | 401 / 403 / 404 / 409 / 422 / 500 envelopes are safe and typed; no raw exception text escapes. |
| `core/tests/integration/test_permissions_authority.py` | Capability map, tier rules, `RequireAdmin` / `RequireCapability`, authentication-before-authorization. |
| `core/tests/integration/test_media_validation.py` | MIME allowlist, size cap, signature mismatch, storage path, token absent / orphan / duplicate, cleanup. |
| `core/tests/integration/test_contract_versions.py` | Frozen versions, drift detection, semver classification. |
| `core/tests/integration/test_registration_extension.py` | The A0 registration extension point is idempotent and holds no unfinished domain controller. |

### 3.3 Modified — shared A0 files

| File | Change |
|---|---|
| `Aplicacion/backend/core/responses.py` | Added `FieldError`; `ErrorDetail.field_errors`; `paginated_response()` (the single pagination shape inside `data`); `DEFAULT_PAGE_SIZE = 25` / `MAX_PAGE_SIZE = 100`; **removed the deprecated `PaginatedApiResponse` + `PaginationMeta`** (FR-01 §4.3 rule 1 — GOV-01 §9 deviation 4 assigns this removal to FND-01); the error envelope now always declares the root `message: null`. |
| `Aplicacion/backend/core/exceptions.py` | Public catalog extended with the frozen transversal codes (`NOT_FOUND`, `PERMISSION_DENIED`, `AUTH_ERROR`, `VALIDATION_ERROR`, `CONFLICT`, `INTERNAL_ERROR`, `BUSINESS_ERROR`, `CIP_NOT_FOUND`) and the six media codes; `GENERIC_PUBLIC_MESSAGES` fallback per HTTP status; `public_message_for()`; `field_errors_from_pydantic()` / `field_errors_from_django()`; the `HttpError`, `ValueError` and `DjangoValidationError` handlers no longer return raw exception text; media exception classes with stable codes and statuses. |
| `Aplicacion/backend/core/permissions.py` | Documented the 401-before-403 authority; re-exported `AllowAny`, `IsAuthenticated`, `IsAuthenticatedOrReadOnly`, `IsAdminUser` from `ninja_extra.permissions`. **No change to the capability map** — `core/capacidades.py` was already the single authority and needed no edit. |
| `Aplicacion/backend/config/api.py` | Added the A0 extension point `registrar_controladores(*controllers)` / `controllers_registrados()`. The registration list lives on the API instance, so reloading the module does not duplicate routes. The JWT controller is registered through the extension point. **The pytest startup cleanup block (`PYTEST_CURRENT_TEST` → `sys._ninja_api_instance` → `ConfigError` fallback) was preserved verbatim.** |
| `Aplicacion/backend/config/settings/base.py` | Media settings block (`MEDIA_ALLOWED_MIME_TYPES`, `MEDIA_MAX_SIZE_BYTES`, `MEDIA_DOMAINS`, `MEDIA_MIN_DIMENSION`, `MEDIA_MAX_DIMENSION`, `MEDIA_BACKUP_ENABLED`, `MEDIA_BACKUP_ROOT`) with the `MEDIA_ROOT` / `MEDIA_URL` values unchanged; documented extension points for `LOCAL_APPS` and `NINJA_EXTRA["INJECTOR_MODULES"]`; the stale "Fase 1 / Fase 4" comments replaced. |
| `Aplicacion/backend/conftest.py` | Test-client authority: `test_sync_client` now uses `django.test.Client` and `test_async_client` uses `ninja_extra.testing.TestAsyncClient` (`ninja.testing.TestClient` is prohibited against async controllers by `FREEZE-TC-1.0.0`). The session-scoped `_cleanup_test_db` startup cleanup was preserved. |

**Nothing else was touched.** `core/capacidades.py`, `core/pagination.py`, `core/utils.py`,
`core/types.py`, `core/security.py`, `core/dependencies.py`, `core/decorators.py` and
`config/settings/{development,production,test}.py` were left byte-identical.

### 3.4 Evidence and state

| File | Action |
|---|---|
| `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/FND-01-backend-shared-api-media.md` | created (this file) |
| `Aplicacion/task/salesianos-fest-rebuild/STATE.md` | modified (FND-01 row + transition log) |

---

## 4. The frozen envelope (FREEZE-ENV-1.0.0)

### 4.1 One success shape

```json
{"success": true, "data": {"id": 1}, "error": null, "message": "…"}
```

`success_response()` keeps the frozen behavior (Decimals serialized as JSON floats, nested schemas
serialized with `mode="json"`, `message` optional and fixed).

### 4.2 One error shape

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "La solicitud no es válida.",
    "details": {"non_field_errors": "La solicitud no es válida."},
    "field_errors": [
      {"field": "email", "code": "INVALID_VALUE", "message": "Input should be a valid string"}
    ]
  },
  "message": null
}
```

- `error.code` — stable, machine-readable, catalogued. Never built by a controller.
- `error.message` — public Spanish prose **always** taken from `PUBLIC_ERROR_MESSAGES`.
- `error.details` — non-field context only.
- `error.field_errors` — the **only** field-error channel. `{field, code, message}`; the field path
  is dotted and nested (`beneficiarios.0.documento`); the transport prefix (`body`, `query`, …) is
  stripped.

### 4.3 One pagination shape

```json
{"success": true, "data": {"items": [], "total": 0, "page": 1, "page_size": 25, "total_pages": 0}, "error": null, "message": null}
```

`page` is 1-based, `page_size` defaults to 25 and is capped at 100, `total_pages` is
`ceil(total / page_size)` and is `0` when `total == 0`. **The second pagination form
(`PaginatedApiResponse` + root `meta`) was removed from the target** — no route can declare it.

### 4.4 Status → code map actually implemented

| Status | Code | Message source |
|---|---|---|
| 401 | `AUTHENTICATION_REQUIRED` | catalog |
| 403 | `ACTION_NOT_ALLOWED` / `ADMIN_REQUIRED` | catalog |
| 404 | `RESOURCE_NOT_FOUND` / domain code / `NOT_FOUND` | catalog |
| 409 | `CONFLICT` / domain code | catalog |
| 413 | `MEDIA_TAMANO_EXCEDIDO` | catalog |
| 422 | `VALIDATION_ERROR` | catalog |
| 500 | `INTERNAL_ERROR` | catalog (generic) |

### 4.5 The no-leak rule

Three handlers in the frozen code returned text that could escape to the client. They are closed:

| Frozen handler | Leak | Fix |
|---|---|---|
| `on_value_error` | `message = str(exc)` (raw text, 401) | `422 VALIDATION_ERROR` with the catalog message; the raw text goes to the log only |
| `on_http_error` (uncatalogued code) | `exc.message` returned verbatim | generic message by status; the raw message goes to the log only |
| `on_django_validation_error` | `exc.messages` / `message_dict` verbatim (Django interpolates the offending value) | `field_errors` whose prose is chosen from the Django **error code**, never from its message |

`on_unhandled_exception` (500) now returns the catalog's generic `INTERNAL_ERROR` message in
Spanish instead of the ad-hoc English string.

**Nothing in the public catalog was weakened.** The whole domain catalog (payments, passes,
competencias, identity) was preserved verbatim and only extended.

---

## 5. Permission and authentication authority

| Concern | Owner | Decision |
|---|---|---|
| Capability vocabulary and tiers | `core/capacidades.py` (unchanged) | `admin = is_staff OR is_superuser`; the break-glass tier always resolves the complete set |
| Gates | `core/permissions.py` | `RequireAdmin` + `RequireCapability` (+ the concrete gates) |
| 401 vs 403 | `config/api.py` + `core/exceptions.py` | The API declares `auth=JWTAuth()` globally, so **authentication resolves before authorization**: anonymous → 401, authenticated-but-not-permitted → 403 |
| Public denial message | `core/exceptions.py` | From the catalog; the permission class never writes prose |

`RequireCapability` accepts both a concrete subclass (`permissions=[RequirePagosAprobar]`) and an
instance with an explicit code (`permissions=[RequireCapability(CAP_PAGOS_APROBAR)]`).

`AllowAny`, `IsAuthenticated`, `IsAuthenticatedOrReadOnly` and `IsAdminUser` are re-exported from
`core/permissions.py` so that domain packets have one import site for the gates.

---

## 6. Media contract (FREEZE-MD-1.0.0)

| Aspect | Frozen rule | Where it lives |
|---|---|---|
| Root | `MEDIA_ROOT` = persistent local volume | `config/settings/base.py` (value unchanged) |
| URL | `MEDIA_URL`, no CDN | `config/settings/base.py` (value unchanged) |
| Storage path | `MEDIA_ROOT/<dominio>/<entidad_id>/<uuid><ext>` | `core.media.construir_ruta_media` |
| Name | **Never** the uploaded name; a server-side UUID | `core.media.MediaValidado.nombre_extension` |
| Extension | Derived from the **detected** MIME | `core.media.extension_for_mime` |
| MIME allowlist | `image/jpeg`, `image/png`, `image/webp` (SVG excluded) | `MEDIA_ALLOWED_MIME_TYPES` |
| Size | 5 MiB per file | `MEDIA_MAX_SIZE_BYTES` |
| Signature | Magic bytes checked against the declared MIME **before** persisting | `core.media.detect_mime_type` + `validar_archivo_media` |
| Dimensions | Hook active only when limits are configured; exact limits pending `GOV-01-OPEN-10` | `MEDIA_MIN_DIMENSION` / `MEDIA_MAX_DIMENSION` |
| Multipart | `data` (JSON with `file_<uuid>` tokens) + `files` (`<token>___<realname>`) | `core.media.parsear_archivos_media` + `resolver_tokens_media` |
| Rejections | `MEDIA_TOKEN_NO_RESUELTO`, `MEDIA_ARCHIVO_HUERFANO`, `MEDIA_TOKEN_DUPLICADO`, `MEDIA_TIPO_NO_PERMITIDO`, `MEDIA_TAMANO_EXCEDIDO` | `core/exceptions.py` catalog + exception classes |

**The orphan-file gap is closed.** FR-06 §2.4 recorded that the frozen `core/utils.py` never
rejects an orphan file part. `core.media.resolver_tokens_media()` rejects it, and the frozen
`core/utils.py` was **not** modified (it is outside the packet's edit roots) — the new module is
the contract that `marketplace` (DOM-04) and `patrocinadores` (DOM-08) must consume.

### 6.1 Persistence, backup and cleanup — expectations, without secrets

| Expectation | Status | Where |
|---|---|---|
| `MEDIA_ROOT` is a persistent volume holding durable business state | Frozen | `config/settings/base.py` |
| Nothing is written before validation | Frozen | `core.media.validar_archivo_media` returns a decision; it never writes |
| Cleanup on validation failure / rollback / replacement / deletion | Frozen | `core.media.limpiar_archivos_media` + the caller owns the transaction |
| **Backup policy of the volume** | **PENDING** `GOV-01-OPEN-09` (A0 + producto) | `MEDIA_BACKUP_ENABLED` / `MEDIA_BACKUP_ROOT` are the hooks; **no credential, remote path or window was invented**. Default: no copy, explicitly (not silently) |
| **Exact dimension limits per image type** | **PENDING** `GOV-01-OPEN-10` (A0 + A5) | `MEDIA_MIN_DIMENSION` / `MEDIA_MAX_DIMENSION` default to `0` (check inert) |

---

## 7. A0 registration extension point

`config/api.py` now exposes one door:

```python
registrar_controladores(*controllers) -> list   # registers and returns the NEW ones
controllers_registrados() -> tuple              # ordered, as registered
```

- The registry lives on the API **instance**, so reloading `config.api` (which happens under
  pytest) does not re-register routes and raise `ConfigError`.
- The extension is **idempotent**: registering the same controller twice is a no-op.
- **No unfinished domain controller is registered.** The only live controller is
  `NinjaJWTDefaultController` (the JWT token endpoints). The ledger's 19 proposed routes are all
  `provisional = sí` and none was registered.
- The pytest startup cleanup (`PYTEST_CURRENT_TEST` → `sys._ninja_api_instance` →
  `ConfigError` fallback with a UUID namespace) is preserved **verbatim**.

---

## 8. Contract versions and the route→wrapper ledger (FREEZE-PS-1.0.0)

`core/contract_versions.py` is the A0 registry required by FR-07 §1.1 and assigned to FND-01 /
`T-018` by FR-07 §5:

| Artifact | Version | State |
|---|---|---|
| Envelope (success / error / pagination) | `ENVELOPE_VERSION = "1.0.0"` | FROZEN |
| `eventos` · `usuarios` · `commerce` · `pagos` · `pases` · `beneficios` · `validaciones` · `marketplace` · `patrocinadores` | `SCHEMA_VERSION = "1.0.0"` | FROZEN |

It also provides the semver primitives the drift test needs: `comparar_versiones()`,
`tipo_de_cambio()` (MAJOR / MINOR / PATCH) and `hay_drift()`.

**The ledger was respected, not extended.** No route was registered, so no `provisional = sí` row of
`route-to-wrapper-ledger.csv` became a live endpoint.

---

## 9. Commands run, workdirs and exit codes

All backend commands run from `Aplicacion/backend` with the project virtual environment
(`.\.venv\Scripts\python.exe`, Python 3.10.19, Django 5.2.11, django-ninja 1.5.3,
django-ninja-extra 0.31.0, pytest 8.3.4, pytest-django 4.9.0, Pillow 11.1.0).

### 9.1 Pre-change baseline of the target root (captured before any edit)

| # | Command | Exit | Result |
|---:|---|---:|---|
| B1 | `.\.venv\Scripts\python.exe manage.py check` | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` |
| B2 | `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` | **1** | same `DB_NAME` failure |
| B3 | `… manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| B4 | `… manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` |
| B5 | `… -m pytest core/tests modules/usuarios/tests -q` | **4** | `ERROR: file or directory not found: core/tests` |

### 9.2 Post-change verification

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `.\.venv\Scripts\python.exe manage.py check` | **1** | `ImproperlyConfigured: Set the DB_NAME environment variable` — **identical to B1**, environmental |
| V2 | `… manage.py makemigrations --check --dry-run` | **1** | same — **identical to B2**, environmental |
| V3 | `… manage.py check --settings=config.settings.development` | **0** | `System check identified no issues (0 silenced)` |
| V4 | `… manage.py makemigrations --check --dry-run --settings=config.settings.development` | **0** | `No changes detected` — **no pending model migration** |
| V5 | `… -m pytest core/tests modules/usuarios/tests -q` | **4** | `ERROR: file or directory not found: modules/usuarios/tests` — **the target `modules/` holds only `__init__.py` by design**; the exact command was run and its failure recorded |
| V6 | `… -m pytest core/tests -q` | **0** | **89 passed in 0.60 s** (the valid focused target suite) |
| V7 | `… -m pytest -q` (whole target root) | **0** | 89 passed |
| V8 | `… -m pytest modules -q` (BL-05 backend gate) | **5** | `no tests ran` — no module tests exist yet in the target |
| V9 | `DJANGO_SETTINGS_MODULE=config.settings.test` · `… -c "import config.api, core.responses, core.exceptions, core.permissions, core.capacidades, core.media, core.contract_versions, core.utils, core.types"` | **0** | `imports OK` · `controllers vivos: (NinjaJWTDefaultController,)` |

### 9.3 Repository-root checks

| # | Command | Exit | Result |
|---:|---|---:|---|
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | **empty** — no forbidden root touched |
| R2 | `git diff --name-only -- backend frontend worker proxy` | **0** | **empty** — the frozen roots are untouched |
| R3 | `git diff --name-only -- .opencode/skills .opencode/agents` | **0** | **empty** |
| R4 | `git status --short -- Aplicacion/backend` | **0** | 6 `M` + 3 `??` — exactly the files listed in §3 |
| R5 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged) |

### 9.4 Environment used

`config.settings.development` + the SQLite variables already present in `Aplicacion/backend/.env`
(`USE_SQLITE=true`, `SQLITE_PATH=:memory:`) for the `manage.py` gates — the target command matrix
`BL-05` §2 requires the settings module to be pinned explicitly, because `manage.py` defaults to
`config.settings.production`, which needs `DB_NAME`/`DB_USER`/`DB_PASSWORD`.

**Byproduct removed.** `manage.py check --settings=config.settings.development` creates a
0-byte `Aplicacion/backend/db.sqlite3` (development.py points SQLite at `BASE_DIR / "db.sqlite3"`).
It was **deleted** after the verification runs: databases are a forbidden artifact and the file did
not exist before this packet. `*.sqlite3` is **not** in `Aplicacion/backend/.gitignore`.

---

## 10. Baseline comparison

| Item | Frozen baseline (GOV-02) | Target root before FND-01 | Target root after FND-01 | Verdict |
|---|---|---|---|---|
| `manage.py check` | exit 1 (`DB_NAME`) | exit 1 (`DB_NAME`) | exit 1 (`DB_NAME`) | **unchanged — environmental (class B7)** |
| `makemigrations --check --dry-run` | exit 1 (`DB_NAME`) | exit 1 (`DB_NAME`) | exit 1 (`DB_NAME`) | **unchanged — environmental** |
| `manage.py check --settings=config.settings.development` | exit 0 | exit 0 | exit 0 | **unchanged** |
| `makemigrations --check --dry-run --settings=config.settings.development` | exit 0 | exit 0 | exit 0 | **unchanged — no pending migration** |
| Backend suite | 13 failed / 1333 passed (frozen `backend/`) | not runnable (no `modules/`) | `core/tests` → **89 passed** | new foundation, green |
| Forbidden-root diff | empty | empty | empty | **clean** |
| Frozen-root diff | empty | empty | empty | **clean** |

**Regressions: none.** No frozen file modified. No commit created. `git stash` not invoked.

### 10.1 Baseline failures deliberately NOT fixed

The 13 frozen-backend failures are **not** in scope and were **not** touched (they live in
`backend/modules/**`, a frozen root, and belong to the domain packets):

envelope drift (1) · status-code mismatch (3) · SQLite FK limitation (4) · UNIQUE violation (3) ·
async/sync (1) · count assertion (2).

FND-01 only closed the three **FND-01-specific** risks: the raw-exception-text leak, the orphan
media file and the non-compliant HTTP test client.

---

## 11. Deviations

| # | Deviation | Why | Risk |
|---|---|---|---|
| D-FND-01-01 | `core/contract_versions.py` created, although the packet's enumerated edit roots list only `core/responses.py`, `exceptions.py`, `permissions.py`, `capacidades.py` and "media utilities/tests under `core/**`" | FR-07 §5 assigns the creation of `core/contract_versions.py` **explicitly to FND-01 (`T-018`)**, and the packet's own implementation step 6 requires respecting the presenter/schema versions. It is a **new** A0-owned file, it is **not** in the forbidden list, and no concurrent agent owns it | Low — needs A0 ratification. Alternative was to inline the registry into `core/responses.py`, which would contradict FR-07 §1.1 |
| D-FND-01-02 | The `ValueError` handler now answers **422 `VALIDATION_ERROR`** instead of 401 with the raw text | FR-01 §4.4 places validation at 422 and `contract/django-app-architecture-contract.md` §10 forbids `ValueError` as control flow. The frozen 401 was tied to the raw-text leak | Low — the target has no consumer yet; the frozen `backend/` is untouched. **A1 (login) must be aware if it reuses `ValueError` for invalid credentials** |
| D-FND-01-03 | The Django `ValidationError` handler now answers **422** (it was 400) and moves the per-field prose into `field_errors` | FR-01 §4.2 makes `field_errors` the only field channel and lists 422 as the validation status | Low — same reasoning; the target has no consumer |
| D-FND-01-04 | `Aplicacion/backend/conftest.py` was modified although it is not literally under a `tests/` root | `FREEZE-TC-1.0.0` (§7.2) forbids `ninja.testing.TestClient` against async controllers, and FR-01 §7.2 assigns the rewrite of the test-client fixture to FND-01 (A0 + A1). The alternative was leaving a known-prohibited fixture in the target | Low — needs A0 ratification; the fixture names were preserved so no consumer breaks |
| D-FND-01-05 | The deprecated `PaginatedApiResponse` + `PaginationMeta` were **removed** rather than only flagged | FR-01 §4.3 rule 1 and GOV-01 §9 deviation 4 assign the removal to FND-01 (A0). Nothing in the target imported them | None — no consumer in the target |
| D-FND-01-06 | `core/pagination.py` was **not** modified; `core/responses.py` imports `PaginatedData` from it | `core/pagination.py` is not in the packet's allowed edit roots and its `PaginatedData` already matches the frozen shape exactly | None |
| D-FND-01-07 | `core/utils.py` and `core/types.py` were **not** modified | They contain the legacy multipart helpers. FR-06 §2.4 assigns the orphan-file gap to FND-01, and it is closed in the new `core/media.py` (the contract the domain modules must consume). Editing the legacy helpers would widen the blast radius of a shared file | Medium — `core/types.py::hydrate_form` still raises raw `HttpError` texts for orphan files. **Those are now neutralised at the error boundary** (uncatalogued code → generic message), but the code-level error code is the generic one, not `MEDIA_ARCHIVO_HUERFANO`. DOM-04 / DOM-08 must use `core.media` to get the specific codes |
| D-FND-01-08 | The `EVENTO_ACTIVO_NOMBRE` setting was **kept** (only documented as legacy) | `FREEZE-ED-1.0.0` (FR-02, `D-01`) removes it as a scope assumption, but that change belongs to FND-02 (`eventos`) | Low — a comment now points FND-02 at the decision |
| D-FND-01-09 | The exact dimension limits and the backup policy were **not** invented | `GOV-01-OPEN-10` and `GOV-01-OPEN-09` are open decisions with named owners. The hooks and the settings exist; the values do not | Low — the hooks are inert by default and documented |

---

## 12. Issues Found

1. **`manage.py` defaults to `config.settings.production`.** The two gate commands of the packet
   fail on `DB_NAME` for the target root, exactly as they do for the frozen root. The fix belongs
   to `GOV-02-CM-02` (A0): pin `config.settings.development` per command, as `BL-05` §2 does.
2. **`manage.py check --settings=config.settings.development` leaves a 0-byte `db.sqlite3`** in the
   target root. `*.sqlite3` is not in `Aplicacion/backend/.gitignore`. The file was removed; the
   gap in `.gitignore` is reported to A0 (not fixed here: `.gitignore` is outside the packet's
   allowed edit roots).
3. **`contract/TEST_ARCHITECTURE_CONTRACT.md` §2 and §10.5 still mandate `ninja.testing.TestClient`**,
   which is incompatible with the async controllers of the project. The operative decision
   (`FREEZE-TC-1.0.0`) is documented and operative, but the documentary amendment
   (`GOV-01-OPEN-01`, GAP-2) is still open. `contract/**` was not modified.
4. **The frozen `core/types.py::hydrate_form` raises raw `HttpError` texts** for malformed
   multipart requests. The error boundary neutralises them (generic message, no leak), but the
   stable media codes only apply through `core/media.py`.
5. **Concurrent activity in `Aplicacion/frontend/**`.** During this packet the frontend tree
   changed substantially (route groups `(public)`, `(administracion)`, `(cuenta)`, `features/`,
   `components/shell/`, `lib/routes.ts`, `providers/AppProviders.tsx`, and a large set of
   `src/**` modifications and deletions). This is **FND-06's** work — another agent owns
   `Aplicacion/frontend`. **None of it was touched, reverted or merged by this packet.**

---

## 13. Rollback

- **Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` — unchanged; do **not** revert or
  reset it.
- **Packet rollback (code):** delete `Aplicacion/backend/core/media.py`,
  `Aplicacion/backend/core/contract_versions.py` and `Aplicacion/backend/core/tests/**`, and restore
  `Aplicacion/backend/core/{responses,exceptions,permissions}.py`,
  `Aplicacion/backend/config/api.py`, `Aplicacion/backend/config/settings/base.py` and
  `Aplicacion/backend/conftest.py` to their pre-packet content. The target root then returns
  exactly to the B1…B5 baseline.
- **Packet rollback (state):** delete
  `Aplicacion/task/salesianos-fest-rebuild/evidence/foundations/FND-01-backend-shared-api-media.md`,
  restore `STATE.md`, and in Engram restore `sdd/salesianos-fest-rebuild/apply-progress` and
  `/state` to their GOV-02 revisions.
- **No database, secret, dump or frozen file is involved**, so there is no data rollback.

---

## 14. Consumers Unblocked

| Consumer | Enabling artefact | Remaining DAG dependency |
|---|---|---|
| **FND-02** (`eventos`, `T-010`) | envelope + catalog + `core/responses.py` | none beyond FND-01 |
| **FND-03** (`usuarios`, `T-011`, `T-012`) | envelope + catalog + `core/permissions.py` + `core/capacidades.py` + `core/contract_versions.py` | none beyond FND-01 |
| **FND-04** (`commerce` / `pagos`, `T-013`, `T-014`) | envelope + `field_errors` + stable error codes | none beyond FND-01 |
| **DOM-04** (`marketplace`, `T-040`) | `core/media.py` + `MEDIA_*` settings + the media catalog | FND-02, FND-01 |
| **DOM-08** (`patrocinadores`, `T-060`) | `core/media.py` + `MEDIA_*` settings | FND-02, FND-01 |
| **DOM-01…DOM-08** (presenters) | `core/contract_versions.py` (`SCHEMA_VERSION` per module) | FND-02…FND-05 |
| **FND-07 / FND-08** (frontend Zod mirrors, query keys) | the frozen envelope shape and `ENVELOPE_VERSION` | FND-06 |
| **API-01…API-05** | the A0 registration extension point + the version registry (drift test) | UI-0x, DOM-0x, FND-08 |
| **XCT-03** (`T-085`) | the media contract + the permission authority | FND-05, DOM-02, DOM-03, DOM-06 |

**Consumption rules.** A consumer may use an interface only once its freeze entry is FROZEN. The
envelope is `FREEZE-ENV-1.0.0`, the media contract is `FREEZE-MD-1.0.0`, the versions are
`FREEZE-PS-1.0.0` and the test client is `FREEZE-TC-1.0.0` — all FROZEN as of GOV-01.

---

## 15. Next Packet

**FND-02**, **FND-03** and **FND-04** may start on disjoint roots (the packet's own "Next packet"
section). Their DAG dependency — FND-01 — is now satisfied.

**Carry-forward:** `PD-01`…`PD-10` · `GOV-01-OPEN-01`…`13` · GAP-1…GAP-4 · D-A…D-E ·
`GOV-02-UX-01`…`05` · `GOV-02-SH-01`…`08` · `GOV-02-BL-01`…`12` · `GOV-02-CM-01`…`05` ·
`P-01`…`P-12` · **`GOV-01-OPEN-09`** (backup policy) · **`GOV-01-OPEN-10`** (dimension limits).

---

## 16. Acceptance Criteria Of The Packet

- [x] Shared files have one A0 owner and a stable extension contract.
- [x] 401 / 403 / 404 / 409 / 422 / 500 envelopes are safe and typed.
- [x] The media policy uses persistent local storage and rejects invalid size / type / signature paths.
- [x] No secrets or domain rules enter the shared config.
- [x] One success, one error and one pagination shape; the second pagination form is gone.
- [x] Raw exception text never reaches a client.
- [x] The orphan-file gap and the test-client risk are closed.
- [x] A0 registration extension points exist; no unfinished domain controller is registered.
- [x] `FREEZE-ENV-1.0.0`, `FREEZE-TC-1.0.0`, `FREEZE-PS-1.0.0` and `FREEZE-MD-1.0.0` are respected.
- [x] Focused behavior-first tests exist and pass (89).
- [x] No forbidden root was touched; no commit; no `git stash`.

---

## 17. A0 Reconciliation — completed foundations (2026-11-19)

**Full report:** `evidence/foundations/FND-01-a0-reconciliation.md` (canonical detail).
**Owner:** A0 · **Mode:** serialized A0 reconciliation of the **completed** packets FND-02, FND-03
and FND-04 — **not a new packet**; no domain behaviour was broadened.

### 17.1 What the reconciliation applied

| Item | Result |
|---|---|
| Apps registered (`config/settings/base.py` → `LOCAL_APPS`) | `modules.eventos`, `modules.usuarios`, `modules.pagos`, `modules.commerce` — ordered by the **migration dependency graph** (`usuarios` → `pagos` → `commerce`; `eventos` independent) |
| `AUTH_USER_MODEL` | `"usuarios.Usuario"` — fixed **before** the target's first real migration |
| DI modules (`NINJA_EXTRA["INJECTOR_MODULES"]`) | `UsuariosModule`, `EventosModule`, `PagosModule`, `CommerceModule` — completed modules only |
| Controllers (`config/api.py`, FND-01 extension point) | `registrar_controladores(EdicionController, PersonaController, PagosController)` — **no unfinished domain controller** |
| `EVENTO_ACTIVO_NOMBRE` | **removed** from settings (FR-02 §2.4 · D-01); no replacement setting invented |
| Public error catalog | **18 codes merged** (8 `eventos` + 4 `usuarios` + 6 `commerce`/`pagos`); 503/504 added to the generic fallback map; no raw error leaks |
| Contract-version registry | verified against every completed module's declared `SCHEMA_VERSION`; drift tests added |
| Live surface | **exactly 7 domain routes** (RT-ED-01, RT-ID-01…03, RT-PG-01…03) + 3 JWT routes |

### 17.2 Requests deferred (recorded, deliberately not applied)

`*.sqlite3` in `.gitignore` and the physical task-matrix sync (rows `T-010`…`T-014`, `T-016`,
`T-018`) are **outside the allowed edit roots** of this reconciliation · `D-FND-02-08` (candidate
list in `error.details`) and `NEW-FND03-04` (`es_admin` vs the `Administrador` group) are **open
decisions** · `IZIPAY_KEY_HASH` in the target `.env` is a **forbidden root** and a release
decision.

### 17.3 Commands / exit codes

`check --settings=config.settings.development` **0** · `makemigrations --check --dry-run
--settings=config.settings.development` **0** · `check` / `makemigrations --check --dry-run`
with the default settings **1** (`DB_NAME` — **identical environmental baseline**, not a
regression) · integrated `migrate` from an empty DB **0** in the order `usuarios` → `pagos` →
`commerce` (+ `eventos`) · `migrate` repeat **0** (idempotent) · `showmigrations` **0** (all
`[X]`) · `migrate <app> zero` × 4 **0** (reversible) · `migrate` replay **0** ·
**`python -m pytest core/tests modules/eventos/tests modules/usuarios/tests modules/commerce/tests
modules/pagos/tests -q` → 0 (277 passed)** · whole target root **0 (277 passed)** · per package
`core 99` · `eventos 63` · `usuarios 35` · `commerce 15` · `pagos 64` · focused registration test
**0 (8 passed)** · the three adapted overlays **0 (63 / 35 / 79)** · forbidden-root diff **0
(empty)** · frozen-root diff **0 (empty)** · `git rev-parse HEAD` **0 (unchanged)** ·
`git stash` **never invoked**.

### 17.4 Deviations

`D-A0R-01` (the three domain overlays were **adapted** to an idempotent registration instead of
being retired — requirement 8 permits "delete **or** adapt", and deleting would drop the
file-SQLite rehearsal capability) · `D-A0R-02` (the intentional registration-pending marker
`modules/usuarios/tests/test_registro_de_la_app_pendiente.py` was **deleted**, as FND-03 §8.1
explicitly requires) · `D-A0R-03`…`D-A0R-06` (see the full report).

### 17.5 Rollback and consumers

**Rollback point** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged; no commit created);
the `AUTH_USER_MODEL` swap is only safe to undo on an empty database — the target database **is**
empty (the rehearsal `db.sqlite3` was deleted).
**Consumers unblocked:** FND-05 · DOM-01…DOM-08 · API-01…API-05 (the routes are now served by
the project API) · FND-07 / FND-08 · XCT-01…XCT-03 · VER-01…VER-03.
**Next packet:** **FND-05** — *Coordinate Exactly-Once Rights Activation* (`T-015`).
