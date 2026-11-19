# FND-01 - A0 reconciliation of DOM-01 and DOM-04

**Artifact:** `evidence/foundations/FND-01-a0-reconciliation-dom01-dom04.md`
**Change:** `salesianos-fest-rebuild` · **Packet:** `FND-01-backend-shared-api-media` (A0 reconciliation, 2nd round)
**Owner:** A0 · **Date:** 2026-11-19 · **Mode:** Standard (no `strict_tdd` active)
**Nature:** **serialized A0 reconciliation** of the completed packets **DOM-01** (`salesianos_fest`) and
**DOM-04** (`marketplace`) — **NOT a new packet**. No domain behaviour was broadened; only A0-owned
shared files were touched.

**Base artifact:** `Aplicacion/task/salesianos-fest-rebuild/wave-01-foundations/FND-01-backend-shared-api-media.md`
**Canonical report (race-proof):** `sdd/salesianos-fest-rebuild/fnd-01-a0-reconciliation-dom01-dom04` (Engram)
**Rollback point:** `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged — **no commit created**,
`git stash` never invoked)

---

## 1. What was delivered

The A0 reconciliation of packet **FND-01** applied the registration, the public-error work and the
media-storage fix that the completed domain packets **DOM-01** and **DOM-04** had requested as
explicit evidence.

| # | Delivered | File |
|---|---|---|
| 1 | The two completed apps registered in **migration-graph order** | `config/settings/base.py` |
| 2 | Their two completed DI modules registered | `config/settings/base.py` |
| 3 | Their three completed controllers registered through the FND-01 extension point | `config/api.py` |
| 4 | **15 safe public error codes** merged (6 DOM-01 + 9 DOM-04) | `core/exceptions.py` |
| 5 | The `salesianos_fest` contract version registered + the drift test extended | `core/contract_versions.py`, `core/tests/integration/test_contract_versions.py` |
| 6 | The **route inventory** of the live API updated (exact, closed) | `core/tests/integration/test_registration_extension.py` |
| 7 | The **verified `STORAGES` defect fixed**: a persistent local `default` backend next to `staticfiles` | `config/settings/base.py` |
| 8 | A focused **persistent-media / `default_storage` write-and-cleanup** test with zero residue | `core/tests/integration/test_media_storage.py` (new) |
| 9 | The **obsolete FND-05 assertion** replaced by the real invariant | `modules/pagos/tests/integration/test_pago_confirmacion.py` |

---

## 2. Exact registrations

### 2.1 Apps (`config/settings/base.py` → `LOCAL_APPS`)

```python
"modules.eventos",
"modules.usuarios",
"modules.pagos",
"modules.commerce",
"modules.salesianos_fest",   # DOM-01 · A0-01
"modules.marketplace",       # DOM-04 · A0-01
```

**Why this order is dependency-safe** (the migration graph is the authority):

| Migration | Depends on |
|---|---|
| `usuarios.0001` | `auth.0012` |
| `usuarios.0002` | `usuarios.0001` |
| `pagos.0001` | `swappable_dependency(AUTH_USER_MODEL)` → `usuarios` |
| `commerce.0001` | `pagos.0001`, `usuarios.0002`, `swappable_dependency` |
| `eventos.0001` | — (independent) |
| `marketplace.0001` | `eventos.0001` |
| `salesianos_fest.0001` | `eventos.0001`, `usuarios.0002`, `swappable_dependency` |

`salesianos_fest` is registered **after** `commerce` exactly as DOM-01 A0-01 requested. `marketplace`
depends only on `eventos`, so it may come last.

### 2.2 DI modules (`config/settings/base.py` → `NINJA_EXTRA["INJECTOR_MODULES"]`)

```python
"modules.usuarios.di.UsuariosModule",
"modules.eventos.di.EventosModule",
"modules.pagos.di.PagosModule",
"modules.commerce.di.CommerceModule",
"modules.salesianos_fest.di.SalesianosFestModule",   # DOM-01 · A0-01
"modules.marketplace.di.MarketplaceModule",           # DOM-04 · A0-02
```

### 2.3 Controllers (`config/api.py`)

```python
registrar_controladores(
    EdicionController,
    PersonaController,
    PagosController,
    CatalogoController,      # DOM-01 · A0-02
    InscripcionController,   # DOM-01 · A0-02
    ProductoController,      # DOM-04 · A0-03
)
```

### 2.4 Live surface (proof — 15 domain routes + 3 JWT routes, nothing else)

```
GET  /api/ediciones/actual                      RT-ED-01        FND-02
GET  /api/personas/busqueda/{documento}         RT-ID-01        FND-03
POST /api/personas/resolver                     RT-ID-02        FND-03
POST /api/personas/confirmar                    RT-ID-03        FND-03
GET  /api/pagos/ordenes/{orden_id}              RT-PG-03        FND-04
POST /api/pagos/ordenes/{orden_id}/confirmar    RT-PG-01        FND-04
POST /api/pagos/izipay/notificacion             RT-PG-02        FND-04
GET  /api/catalogo/paquetes                     RT-IN-12        DOM-01
GET  /api/catalogo/disciplinas                  RT-IN-13        DOM-01
POST /api/inscripciones                         RT-IN-14        DOM-01 (provisional ratificada)
GET  /api/inscripciones/{inscripcion_id}        RT-IN-02        DOM-01
GET  /api/inscripciones/{inscripcion_id}/equipos RT-IN-04       DOM-01
GET  /api/marketplace/productos                 RT-MK-02        DOM-04
POST /api/marketplace/productos                 RT-MD-01        DOM-04
GET  /api/marketplace/categorias                RT-MK-01        DOM-04
GET  /api/marketplace/productos/{slug}          RT-MK-03        DOM-04
POST /api/token/pair · /refresh · /verify        ninja_jwt
```

**No unfinished controller or app is registered.** The proof is the **live OpenAPI surface**, not the
class name: the `@api_controller` decorator rewrites `__module__`, so introspection cannot prove
ownership (F-41). The registration test asserts the surface is EXACTLY the closed set above, that
`INSTALLED_APPS` holds exactly the six completed domain apps, and that `INJECTOR_MODULES` holds
exactly the six completed DI modules.

**Why the provisional routes may be registered.** FR-07 §3.1 forbids registering a route marked
`provisional = sí` *until its module and presenter are implemented and versioned*. Both are now
implemented, verified (45 + 35 green tests) and versioned (`SCHEMA_VERSION = "1.0.0"`), which is
the condition the rule states. The ledger's provisional marking is a **status**, not a veto.

---

## 3. Public error catalog merged (15)

All prose is fixed Spanish text. None interpolates a UUID, an internal id, a slug, a price, a
filesystem path, a SQL constraint, a provider payload or a credential.

### 3.1 DOM-01 (A0-03) — 6 codes

| Code | Status | Public prose |
|---|---|---|
| `PAQUETE_NO_VIGENTE` | 409 | "El paquete seleccionado no está disponible para esta edición." |
| `DISCIPLINA_NO_PERMITIDA` | 422 | "La disciplina seleccionada no está permitida para este paquete." |
| `EQUIPO_DUPLICADO` | 422 | "No puede declarar dos equipos para la misma disciplina." |
| `INSCRIPCION_NO_ENCONTRADA` | 404 | "No se encontró la inscripción solicitada." |
| `INSCRIPCION_NO_AUTORIZADA` | 403 | "No tienes autorización para gestionar esta inscripción." |
| `COMPRADOR_SIN_PERSONA` | 422 | "La cuenta no tiene una persona vinculada." |

### 3.2 DOM-04 (A0-06) — 9 codes

The prose is the one **proposed by DOM-04 itself**, adopted verbatim.

| Code | Status | Public prose |
|---|---|---|
| `PRODUCTO_NO_ENCONTRADO` | 404 | "No se encontró el producto solicitado." |
| `PRODUCTO_SLUG_DUPLICADO` | 409 | "Ya existe un producto con ese identificador en la edición." |
| `PRODUCTO_NO_DISPONIBLE` | 409 | "El producto seleccionado no está disponible." |
| `PRODUCTO_CATEGORIA_INCOHERENTE` | 422 | "La categoría indicada pertenece a otra edición." |
| `CATEGORIA_PRODUCTO_NO_ENCONTRADA` | 404 | "No se encontró la categoría de producto solicitada." |
| `CATEGORIA_PRODUCTO_SLUG_DUPLICADO` | 409 | "Ya existe una categoría con ese identificador en la edición." |
| `PRODUCTO_IMAGEN_NO_ENCONTRADA` | 404 | "No se encontró la imagen de producto solicitada." |
| `OFERTA_INVALIDA` | 422 | "La oferta indicada no es válida." |
| `GALERIA_INVALIDA` | 422 | "La galería del producto no es válida." |

`MODULO_NO_HABILITADO` was **already** catalogued by the first A0 reconciliation (FR-02 §2.5); it
was not duplicated.

**Statuses confirmed from the domain classes** (`ConflictError` → 409, `UnprocessableEntityError` →
422, `NotFoundError` → 404, `ForbiddenError` → 403), so the status and the code cannot drift apart.
A new parametrized test asserts both.

---

## 4. The `STORAGES` defect (DOM-04 A0-04) — FIXED

**The defect, verified in the source:** `config/settings/base.py` declared `STORAGES` with **only**
the `staticfiles` entry. Django 5 requires the `default` entry too: without it `default_storage`
does not exist and the resolution raises
`InvalidStorageError: Could not find config for 'default' in settings.STORAGES`.

**It is not a business failure — it blocks every module that touches media:**

- `modules/marketplace/domain/services/core/producto_media_service.py:161` calls
  `default_storage.exists(ruta)`.
- `modules/marketplace/domain/models/producto_imagen.py:60` declares an `ImageField`, whose storage
  defaults to `default_storage`.

**The fix (no invention):**

```python
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

`FileSystemStorage` is Django's own **local** backend and writes under `MEDIA_ROOT`, which is the
**persistent** volume of the media contract (`FREEZE-MD-1.0.0` · FR-06 §2.1). **No cloud storage,
no remote path, no credential and no new key was invented**; the only value that changed is the
backend class that Django itself declares as the default. The temporary overlay
`modules/marketplace/tests/settings_overlay.py` replicated this adjustment to let DOM-04 verify
itself; the permanent fix supersedes it.

**Verification (new file `core/tests/integration/test_media_storage.py`, 7 tests):**

- `STORAGES` declares `default` with the local backend.
- The backend is a `FileSystemStorage` subclass.
- `default_storage.location` is exactly `MEDIA_ROOT` (`BASE_DIR / "media"`).
- `storages["default"]` resolves (the original defect raised here).
- A file written through `default_storage` lands **inside** the volume at the requested path.
- `core.media.limpiar_archivos_media([...])` removes it and leaves **ZERO residue**.
- Cleaning a non-existent file is a no-op and never raises.

The write/cleanup cycle runs against a **temporary** media root (`tmp_path`), obtained by
overriding `STORAGES` — not `MEDIA_ROOT` alone — because Django only resets the storage cache when
`STORAGES`, `STATIC_ROOT` or `STATIC_URL` change. **The real volume is never touched**: after the
whole run `Aplicacion/backend/media` **does not exist**.

---

## 5. The obsolete FND-05 assertion (DOM-01 A0-04) — FIXED

**Evidence.** `modules/pagos/tests/integration/test_pago_confirmacion.py::test_la_compra_se_marca_pagada_sin_activar_derechos`
asserted:

```python
assert not apps.is_installed("modules.salesianos_fest")
assert not apps.is_installed("modules.validaciones")
```

The assertion **merely expected the new app to be absent** — it used the ABSENCE OF THE PACKAGE as a
proxy for the ABSENCE OF THE CAPABILITY that grants rights. DOM-01 created `modules.salesianos_fest`
(the inscription catalogue — it owns **no rights table and no activator**; the `INSCRIPCION` activator
is DOM-02's), so the premise became obsolete. It failed only when the app was registered (DOM-01 V17).

**The invariant it really protected** — *payment confirmation does not directly activate domain
rights* (`RN-C08`, FR-04 §4) — is now asserted directly, on the state of the activation:

```python
activacion = ActivacionCompra.objects.get(compra=compra)
assert activacion.estado == EstadoActivacionCompra.PENDIENTE
assert activacion.esta_activada is False
```

**No domain behaviour changed.** The test file, the flow, the models and the assertions of `commerce`,
`pagos`, `eventos` and `usuarios` are otherwise untouched. The new assertion is *stronger* than the
old one: it proves the payment is recorded, the activation was requested, and **no right was
conceded** — instead of proving that a package is missing. This is the correction of D-15: *a guard
written as the absence of an app is a time bomb; assert the absence of the capability.*

---

## 6. Contract versions

`core/contract_versions.py` now registers `"salesianos_fest": "1.0.0"` (A0-06 of DOM-01). The key is
the **physical module name** (`modules/salesianos_fest`), which is what the module itself documents
in `modules/salesianos_fest/presentation/schemas/__init__.py`; the ledger names the *domain*
`inscripciones` (D-DOM-01-08). `marketplace` was already registered at `1.0.0` and was verified
against its declared `SCHEMA_VERSION`.

The drift test now covers both new modules: the registry value and the module's own declared
`SCHEMA_VERSION` must not differ.

---

## 7. Commands / exit codes

Workdir `Aplicacion/backend`, `.\.venv\Scripts\python.exe` (Python 3.10.0 · Django 5.2.11 ·
Pydantic 2.12.5 · pytest-django 4.9.0 · ninja 1.5.3 · ninja-extra 0.31.0 · injector 0.24.0 ·
Pillow 11.1.0). The rehearsal database was a SQLite **file outside the repository**
(`%TEMP%\opencode\a0r_dom01_dom04.sqlite3`) and it was deleted.

| # | Command | Exit | Result |
|---|---|---:|---|
| V1 | `manage.py check` (default = `config.settings.production`) | **1** | `DB_NAME` — **known environmental baseline**, identical to FND-01…FND-05, DOM-01 and DOM-04. Not a regression |
| V2 | `manage.py makemigrations --check --dry-run` (default) | **1** | same `DB_NAME` baseline |
| V3 | `manage.py check --settings=config.settings.base` (SQLite) | **0** | `System check identified no issues (0 silenced)` |
| V4 | `manage.py makemigrations --check --dry-run --settings=config.settings.base` | **0** | `No changes detected` |
| V5 | `manage.py migrate` (empty DB) | **0** | all 12 apps applied, incl. `marketplace.0001_initial` and `salesianos_fest.0001_initial` |
| V6 | `manage.py migrate` (repeat) | **0** | `No migrations to apply` (idempotent) |
| V7 | `manage.py showmigrations` | **0** | every domain migration `[X]` |
| V8 | `manage.py migrate <app> zero` × 6 (`commerce`, `pagos`, `marketplace`, `salesianos_fest`, `usuarios`, `eventos`, reverse dependency order) | **0** | every `Unapplying … OK` — reversible |
| V9 | `manage.py migrate` (replay) | **0** | `usuarios → pagos → commerce → eventos → marketplace → salesianos_fest` |
| V10 | `manage.py showmigrations` (after replay) | **0** | all `[X]` |
| V11 | **`python -m pytest -q`** (whole target root, project settings) | **0** | **430 passed** — the whole target is green on the project settings |
| V12 | `python -m pytest core/tests -q` | **0** | **156 passed** (FND-01 baseline 100 + 56 new) |
| V13 | `python -m pytest core/tests/integration/test_registration_extension.py core/tests/integration/test_contract_versions.py core/tests/integration/test_media_storage.py core/tests/integration/test_exceptions_public_catalog.py -q` | **0** | **102 passed** (focused registration / OpenAPI / versions / media / catalog) |
| V14 | `python -m pytest modules/salesianos_fest/tests -q` (DOM-01 overlay) | **0** | **45 passed** — DOM-01 baseline intact |
| V15 | `python -m pytest modules/marketplace/tests -q` (DOM-04 overlay) | **0** | **35 passed** — DOM-04 baseline intact |
| V16 | `python -m pytest modules/pagos/tests/integration/test_pago_confirmacion.py -q` | **0** | **14 passed** — the corrected obsolete assertion |
| V17 | `python -m pytest core/tests/integration/test_media_storage.py -q` | **0** | **7 passed** — persistent media / `default_storage` write-and-cleanup, zero residue |
| R1 | `git diff --name-only -- contract Aplicacion/plan Aplicacion/documentacion` | **0** | empty — forbidden roots intact |
| R2 | `git diff --name-only -- backend frontend worker proxy .opencode` | **0** | empty — frozen roots intact |
| R3 | `git rev-parse HEAD` | **0** | `f3df5401c56b41c340f257e67d5a306904a9e670` — **no commit created** |
| R4 | `git stash` | — | **never invoked** |
| R5 | residue sweep under `Aplicacion/backend` | **0** | no `*.sqlite3`, no `db.sqlite3`, no `media/`, no `staticfiles/` |
| V18 | **`python -m pytest -q`** (whole target root, FINAL run) | **0** | **432 passed** — the same green suite after the two extra registration tests of §2.4 were added (V11 = 430 + 2) |

### Known failure, recorded separately

**The production-environment `DB_NAME` failure (V1, V2).** `manage.py` defaults to
`config.settings.production`, which requires `DB_NAME`/`DB_USER`/`DB_PASSWORD`; the target `.env`
supplies only SQLite variables. The failure is
`django.core.exceptions.ImproperlyConfigured: Set the DB_NAME environment variable` with exit code
**1**. It is **identical to the baseline recorded by FND-01, FND-02, FND-03, FND-04, FND-05, DOM-01
and DOM-04** — it is an environmental gap of the *deployment*, not a defect introduced here, and it
is **not** a regression. The equivalent gates with an explicit SQLite settings module exit **0**
(V3, V4).

---

## 8. A0 requests — accepted and deferred

### Accepted (applied here)

| Request | Source | Applied |
|---|---|---|
| Register the app + its DI module | DOM-01 A0-01 | ✅ `config/settings/base.py` |
| Register `CatalogoController` and `InscripcionController` | DOM-01 A0-02 | ✅ `config/api.py` |
| Six public error codes | DOM-01 A0-03 | ✅ `core/exceptions.py` |
| Update the obsolete FND-05 assertion | DOM-01 A0-04 | ✅ `modules/pagos/tests/integration/test_pago_confirmacion.py` |
| Register `salesianos_fest` in the version registry + the drift test | DOM-01 A0-06 | ✅ `core/contract_versions.py` + `core/tests/integration/test_contract_versions.py` |
| Register the app + its DI module | DOM-04 A0-01 / A0-02 | ✅ `config/settings/base.py` |
| Register `ProductoController` | DOM-04 A0-03 | ✅ `config/api.py` |
| **Add the `default` entry to `STORAGES`** | DOM-04 A0-04 | ✅ `config/settings/base.py` |
| Nine public error codes | DOM-04 A0-06 | ✅ `core/exceptions.py` |

### Deferred (recorded, NOT applied — with the reason)

| Request | Source | Why deferred |
|---|---|---|
| **The money wire shape** (`Decimal` → string vs number) | DOM-01 A0-09 / DOM-04 A0-05 | **Open decision, deliberately NOT guessed.** The GOV-01/contract evidence does **not** freeze the JSON representation: `FR-04` freezes the **domain** type (`Decimal` in the model) and no contract file mentions the wire shape of an amount. The observable behaviour of the target (a decimal leaves the JSON as a string, because `success_response()` calls `model_dump(mode="json")` before `_decimal_to_float`, and the key `ser_json_decimal_to_float` does not exist in Pydantic v2) is **frozen by observation, not by contract**. Changing `core/responses.py` without a frozen decision would silently break the frontend mirrors. **Recorded as OPEN** — see §9. |
| Ratify `RT-IN-14` and the presenter names in the ledger CSV + `SH-05` | DOM-01 A0-05 | The ledger (`evidence/contracts/route-to-wrapper-ledger.csv`) and `SH-05` are **GOV-01/GOV-02 contract evidence**, outside this packet's allowed edit roots. The route **is** registered (its module and presenter are implemented and versioned), and the A0-owned route inventory now carries it explicitly. |
| Retire `modules/marketplace/tests/settings_overlay.py` | DOM-04 A0-07 | The overlay lives in a **domain** package's test tree, outside this packet's allowed edit roots. Following the precedent of `D-A0R-01`, the overlays are kept but are already **idempotent**, so the permanent registration does not conflict with them (V14, V15 prove it). Its now-redundant `STORAGES` block is a harmless no-op (`setdefault`). |
| `*.sqlite3` in the target `.gitignore` | DOM-01 A0-08, FND-01, FND-02, FND-04, FND-05 | Outside the allowed edit roots. **No `.sqlite3` was left in the repository** (R5); the rehearsal DB lived outside the repo and was deleted. |
| Sync the physical task matrix `00-matriz-tareas.md` (`T-020`, `T-021`, `T-040`) | DOM-01 A0-07 | Outside the allowed edit roots. |
| `GOV-01-OPEN-09` (media backup policy) and `GOV-01-OPEN-10` (exact dimension limits) | FR-06 | Still open decisions of A0 + product; the switch/lines already exist in settings and **no policy was invented**. |

---

## 9. Open decisions carried forward

**`OD-A0R2-01` — the wire shape of money (DOM-01 A0-09 / DOM-04 A0-05).** OPEN. The contract does
not freeze it. The observable behaviour of the target today is the **decimal string** (`"3.50"`),
shared by `pagos`, `salesianos_fest` and `marketplace`. The frontend mirrors expect `z.number()`.
Whoever decides must change it **once**, in `core/responses.py`, and the modules must not fork the
convention. No code was changed here.

**`OD-A0R2-02` — `RT-IN-14` in the frozen ledger.** OPEN (GOV-01 owner). The route works and is
registered; only the ledger row and the presenter names are pending ratification.

---

## 10. Deviations

- `D-A0R2-01` — the `salesianos_fest` overlay was **adapted, not retired**: it is already idempotent
  (it checks `if "modules.salesianos_fest" not in INSTALLED_APPS`), so the permanent registration does
  not produce "Application labels aren't unique" (F-39). Retiring it would drop the documented
  file-SQLite rehearsal command `SALESIANOS_FEST_SQLITE_PATH`. Same precedent as `D-A0R-01`.
- `D-A0R2-02` — the `marketplace` overlay was **left untouched**: it is outside the allowed edit
  roots, it is idempotent, and its `STORAGES` block is now a harmless no-op.
- `D-A0R2-03` — the ledger ratification of `RT-IN-14` was **not** performed: the ledger is GOV-01
  contract evidence and outside the allowed edit roots. The A0-owned route inventory carries the
  route explicitly instead.
- `D-A0R2-04` — `core/responses.py` and `core/types.py` were **not** modified: the money wire shape
  is an open decision and the contract does not freeze it.
- `D-A0R2-05` — `core/permissions.py` and `core/capacidades.py` were **not** modified: no permission
  or capability change was requested, and `NEW-FND03-04` (the `Administrador` group) stays open.
- `D-A0R2-06` — the regression `R-DOM-01-01` was resolved by **strengthening the invariant**, not by
  deleting the test: the obsolete app-absence proxy became an assertion on the activation state.

---

## 11. Changed files

| File | Action | What was done |
|---|---|---|
| `Aplicacion/backend/config/settings/base.py` | Modified | `LOCAL_APPS` += `modules.salesianos_fest`, `modules.marketplace` (migration-graph order) · `NINJA_EXTRA["INJECTOR_MODULES"]` += the two DI modules · `STORAGES` += the persistent local `default` backend |
| `Aplicacion/backend/config/api.py` | Modified | The three completed controllers registered through `registrar_controladores(...)`; the docstring updated |
| `Aplicacion/backend/core/exceptions.py` | Modified | **15** safe public error codes merged (6 DOM-01 + 9 DOM-04) |
| `Aplicacion/backend/core/contract_versions.py` | Modified | `"salesianos_fest": "1.0.0"` registered |
| `Aplicacion/backend/core/tests/integration/test_registration_extension.py` | Modified | Closed controller list, allowed prefixes, **exact route inventory** (15 routes), plus two new tests: no unfinished app registered, no unfinished DI module registered |
| `Aplicacion/backend/core/tests/integration/test_contract_versions.py` | Modified | The drift test now covers `salesianos_fest` and `marketplace` |
| `Aplicacion/backend/core/tests/integration/test_exceptions_public_catalog.py` | Modified | Parametrized tests: the 15 new codes are catalogued, their prose is fixed text, and their status matches the domain class |
| `Aplicacion/backend/core/tests/integration/test_media_storage.py` | **Created** | 7 tests: the `default` entry exists, is local, is the persistent volume, resolves, writes, and leaves **zero residue** on cleanup |
| `Aplicacion/backend/modules/pagos/tests/integration/test_pago_confirmacion.py` | Modified | The obsolete `apps.is_installed` proxy replaced by the real invariant (activation `PENDIENTE`, `esta_activada is False`) |

**NOT edited:** any domain internals of `salesianos_fest`, `marketplace`, `commerce`, `pagos`,
`eventos` or `usuarios`; the frontend; `contract/**`; `Aplicacion/plan/**`;
`Aplicacion/documentacion/**`; the frozen roots `backend/**`, `frontend/**`, `worker/**`, `proxy/**`,
`.opencode/**`; secrets; databases; user media.

---

## 12. Rollback

Rollback point `f3df5401c56b41c340f257e67d5a306904a9e670` (unchanged; no commit created; **do not
revert or reset it**).

1. `manage.py migrate marketplace zero` and `manage.py migrate salesianos_fest zero` (both verified
   reversible) — only if the target database is to be returned to its pre-registration state.
2. `config/settings/base.py`: remove `"modules.salesianos_fest"` and `"modules.marketplace"` from
   `LOCAL_APPS`; remove the two DI modules from `INJECTOR_EXTRA["INJECTOR_MODULES"]`; remove the
   `"default"` entry from `STORAGES`.
3. `config/api.py`: remove the three controller imports and the three names from the
   `registrar_controladores(...)` call.
4. `core/exceptions.py`: remove the 15 catalog entries.
5. `core/contract_versions.py`: remove `"salesianos_fest"`.
6. `core/tests/integration/test_registration_extension.py`: restore the previous controller list,
   prefixes and route inventory (7 domain routes) and remove the two new app/DI tests.
7. `core/tests/integration/test_contract_versions.py`: restore the previous module lists.
8. `core/tests/integration/test_exceptions_public_catalog.py`: remove the new parametrized block.
9. Delete `core/tests/integration/test_media_storage.py`.
10. `modules/pagos/tests/integration/test_pago_confirmacion.py`: restore the previous
    `apps.is_installed` assertions.
11. Restore `STATE.md` and the shared Engram topics.

**The commercial and payment history is preserved**: this rollback never deletes a purchase, an
order or a transaction.

---

## 13. Concurrency

`Aplicacion/frontend/**` (FND-06 / UI-01A / the concurrent UI work) kept advancing and was **not
touched, not reverted and not merged**; its board rows were **not** edited (A0/A7 owns them). The
modules of `salesianos_fest`, `marketplace`, `commerce`, `pagos`, `eventos` and `usuarios` were
**not** edited (except the single obsolete assertion in `pagos`, which was explicitly requested);
their suites were re-run green (V14, V15, V16 and the whole-root V11).

---

## 14. Consumers unblocked

- **DOM-02** — the inscription app and its routes are now served by the project API; the
  `INSCRIPCION` activator is still DOM-02's.
- **DOM-05** — the marketplace catalogue, its routes and the **media storage** are available; the
  product creation route now works against a real `default_storage`.
- **DOM-06 / DOM-08** — `default_storage` exists again: media can be written and cleaned.
- **API-02 / API-04** — the inscription wrappers have live routes to mirror.
- **API-03** — the marketplace wrappers have live routes to mirror (still waiting on `OD-A0R2-01`
  for the money shape).
- **XCT-03** — the multipart protocol can now be exercised end to end against the real storage.
- **UI-02…UI-05 / VER-01…VER-03** — the public and administrative surfaces of the catalogue, the
  inscriptions and the store exist.

---

## 15. Next packet

**DOM-02** — *Capacity pool, assignment and expansion* (`T-022`, `T-023`) — now with the inscription
app registered, its routes served and its catalogue reachable. **DOM-05** — *Marketplace order*
(`RT-CM-03`) — now with the store app, its routes and a working persistent media storage.

The A0 requests that remain open for the next A0 round are `OD-A0R2-01` (money wire shape),
`OD-A0R2-02` (`RT-IN-14` ledger ratification), the `.gitignore` entry, the physical task-matrix sync
and the two open media decisions (`GOV-01-OPEN-09`, `GOV-01-OPEN-10`).
