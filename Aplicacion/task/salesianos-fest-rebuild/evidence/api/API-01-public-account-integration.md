# API-01 - Integrate Public, Identity, Account And Recovery Routes

**Artifact:** `evidence/api/API-01-public-account-integration.md` - **Packet:** API-01 (`wave-03-api-integration`)
**Owner:** A7 - **Status:** `verification_required` (implementation applied, runtime verification deferred)
**Date:** 2026-11-19 - **Target:** `Aplicacion/frontend/**` only (allowed roots of the packet)
**Original task IDs:** `T-070`, `T-071` (2 of the 54 source-defined IDs)

---

## 1. The decision that shaped this packet

The packet asks to replace the UI-01 provisional fixtures with **registered** real endpoints. The
first thing this packet did was to read the truth of the backend instead of the plan:

- `Aplicacion/backend/config/api.py` — the closed list of `registrar_controladores(...)`.
- `Aplicacion/backend/core/tests/integration/test_registration_extension.py` — the closed list
  `RUTAS_DE_DOMINIO_CONGELADAS`, the authoritative ledger of the routes that EXIST.

**Consequence:** of the nine page IDs of the packet (`PUB-01/02`, `AUTH-01/02`, `ACCOUNT-01/02/04/05`,
`REC-01`), only **three datasets** have a registered route with a frozen presenter:

| Dataset | Registered route | Bound in API-01 |
|---|---|---|
| Current edition | `GET /api/ediciones/actual` (`RT-ED-01`) | **YES** |
| Identity (document / resolve / confirm) | `GET /api/personas/busqueda/{documento}`, `POST /api/personas/resolver`, `POST /api/personas/confirmar` (`RT-ID-01/02/03`) | **YES** |
| Session | `GET /api/auth/me` | **YES** |

and **five datasets have NO route at all**:

| Dataset | Proposed route | State |
|---|---|---|
| Account summary | `GET /api/mi-cuenta/resumen` (`RT-ID-04`) | **does not exist** |
| Account purchases (list) | `GET /api/mi-cuenta/compras` (`RT-ID-05`) | **does not exist** |
| Account purchase (detail) | `GET /api/mi-cuenta/compras/{compra_id}` (`RT-ID-06`) | **does not exist** |
| Purchase recovery | `POST /api/recuperar-compra` (`RT-RC-01`) | **does not exist** |
| Account registration | `POST /api/auth/registro` (AUTH-02) | **does not exist** |

Those five live only in `evidence/routes/SH-05-provisional-endpoint-and-presenter-register.md` as
**provisional** proposals; they are NOT in the frozen ledger of GOV-01 and they have NO controller.

**Therefore this packet binds what exists and declares what does not.** It did not invent a URL, it
did not bind an unregistered controller and it did not write a Zod mirror of a wrapper that has no
presenter. The account area keeps its HONEST state, and the missing routes are an A0 request with
the exact route, presenter and wrapper each one needs.

---

## 2. Endpoint / controller / presenter / schema ledger

Source of truth: `Aplicacion/backend/config/api.py` + the registered controllers + the frozen ledger
`RUTAS_DE_DOMINIO_CONGELADAS` (`core/tests/integration/test_registration_extension.py`).

| Route ID | Method | Path | Controller | Presenter | Wrapper (backend) | Registered | API-01 |
|---|---|---|---|---|---|---|---|
| `RT-ED-01` | GET | `/api/ediciones/actual` | `EdicionController` | `EdicionPresenter` | `EdicionActualOut` | **YES** | **bound** |
| `RT-ID-01` | GET | `/api/personas/busqueda/{documento}` | `PersonaController` | `PersonaBusquedaPresenter` | `DocumentoConsultaOut` | **YES** | **bound** |
| `RT-ID-02` | POST | `/api/personas/resolver` | `PersonaController` | `PersonaResolverPresenter` | `PersonaResueltaOut` | **YES** | **bound** |
| `RT-ID-03` | POST | `/api/personas/confirmar` | `PersonaController` | `PersonaConfirmarPresenter` | `PersonaOut` | **YES** | **bound** |
| — | POST | `/api/auth/login/username\|dni\|email` | `AuthController` | `AuthPresenter` | `LoginTokenOut` | **YES** | already bound by `features/auth` |
| — | GET | `/api/auth/me` | `AuthController` | `AuthPresenter` | `SesionUsuarioOut` | **YES** | **bound** |
| `RT-ID-04` | GET | `/api/mi-cuenta/resumen` | — | `MiCuentaPresenter` | `MiCuentaOut` | **NO** | **unbound** |
| `RT-ID-05` | GET | `/api/mi-cuenta/compras` | — | `MisComprasPresenter` | `PaginatedData[MisComprasListItemOut]` | **NO** | **unbound** |
| `RT-ID-06` | GET | `/api/mi-cuenta/compras/{compra_id}` | — | `CompraDetallePresenter` | `CompraDetalleOut` | **NO** | **unbound** |
| `RT-RC-01` | POST | `/api/recuperar-compra` | — | `RecuperarCompraPresenter` | `RecuperarCompraOut` | **NO** | **unbound** |
| — | POST | `/api/auth/registro` | — | — | — | **NO** | **unbound** |

**Path convention.** The transport owner (`Aplicacion/frontend/src/lib/api.ts`) already carries the
`/api` namespace, so the services write the path **without** it (`/ediciones/actual`,
`/personas/resolver`). The trailing-slash drift of the frozen tree (`/catalogo/paquetes/`) is not
repeated.

---

## 3. Service / hook / key owners

One dataset, one owner. The literals of a key live in ONE file and never travel to a component.

| Dataset | Service (owner) | Key factory (owner) | Hook | `queryOptions` |
|---|---|---|---|---|
| Edition | `features/public/services/edicion.service.ts` | `features/public/utils/edicion.claves.utils.ts` (`["edicion","actual"]`) | `features/public/hooks/useEdicionActual.ts` | `edicionActualQueryOptions` |
| Identity | `features/auth/services/identidad.service.ts` | `features/auth/utils/auth.claves.utils.ts` (`["auth", …]`) | `features/auth/hooks/useIdentidad.ts` | — (mutations) |
| Session | `features/auth/services/sesion.service.ts` | `features/auth/utils/auth.claves.utils.ts` (`["auth","sesion"]`) | `features/auth/hooks/useSesionActual.ts` | `sesionActualQueryOptions` |

**The edition namespace is `edicion`, not `public`.** The edition is one dataset of the whole
product: the catalogue, the store and the inscription wizard read the same edition and must share
this namespace. The factory lives in the feature that consumes it first; when the roots are widened
to a dedicated `features/edition/**` the move is a one-file change because the literals are here and
nowhere else.

### Stale times

| Read | Kind | `staleTime` | `gcTime` |
|---|---|---|---|
| Current edition | `catalogo` | 10 min | 10 min (`gcTime >= staleTime`, ≥ 5 min) |
| Session | `comercial` | 15 s | 5 min |

### Targeted invalidation

| Mutation | Invalidates | Does NOT touch |
|---|---|---|
| `useConfirmarPersona` | `["auth","sesion"]` and `["auth","identidad","confirmar",tipo,numero]` | the catalogue, the account lists, the edition |
| `useResolverPersona` | `["auth","identidad","resolver",tipo,numero]` | everything else |

### Error policy (branch on the HTTP status, never on the code)

The shared error handler (`@/errors` → `handleApiError`) is the ONE reader of the frozen error
envelope: it reads `error.message` and the `error.field_errors[]` channel, and it returns the
HTTP status. The reads wrap it into `ApiQueryError` (the canonical "API failure with status" type)
so the components can branch on the status:

| Status | Meaning in this packet | State drawn |
|---|---|---|
| 401 | no session | `S-06` — session expired, with the way back (sign in again) |
| 403 | not allowed | `S-06` — permission denied |
| 404 | no published edition | `S-02` — empty, **not** an error |
| 409 | ambiguous edition / duplicated identity | `S-04` — the message of the backend, verbatim |
| 422 | invalid payload | the field error reaches its control through `field_errors[]` |
| 5xx / network | the server or the connection failed | `S-04` — recoverable error with the retry |

The machine code is treated as **opaque text**: 33 public codes are still uncatalogued, so the
frontend never branches on them.

---

## 4. Files changed (16 created, 12 modified, 3 deleted)

Every path is inside the allowed roots of the packet (`features/public/**`, `features/cuenta/**`,
`features/auth/**`, `app/(cuenta)/**`).

### Created — edition dataset (5)

| File | What |
|---|---|
| `features/public/schemas/edicion.schema.ts` | Zod 1:1 mirror of `EdicionActualOut` (three blocks + `modulos`). No `z.any()`. |
| `features/public/services/edicion.service.ts` | `obtenerEdicionActual()` → `GET /ediciones/actual`; parses the envelope LOUDLY; never parses a `204`. |
| `features/public/utils/edicion.claves.utils.ts` | The key factory of the edition namespace. |
| `features/public/hooks/useEdicionActual.ts` | `edicionActualQueryOptions` + `useEdicionActual()`. |
| `features/public/components/EdicionActualPanel.tsx` | The client panel: `S-01` skeleton, `S-02` empty (404), `S-04` recoverable error with retry. |

### Created — identity and session dataset (7)

| File | What |
|---|---|
| `features/auth/schemas/identidad.schema.ts` | Zod 1:1 mirrors of `DocumentoConsultaOut`, `PersonaResueltaOut`, `PersonaOut` + the two input schemas. |
| `features/auth/schemas/sesion.schema.ts` | Zod 1:1 mirror of `SesionUsuarioOut` (identity + account + role blocks). |
| `features/auth/services/identidad.service.ts` | `consultarDocumento()`, `resolverPersona()`, `confirmarPersona()` — the three registered routes. |
| `features/auth/services/sesion.service.ts` | `obtenerSesionActual()` → `GET /auth/me`. |
| `features/auth/utils/auth.claves.utils.ts` | The key factory of the auth/identity namespace. |
| `features/auth/hooks/useIdentidad.ts` | The three identity mutations with their targeted invalidation. |
| `features/auth/hooks/useSesionActual.ts` | `sesionActualQueryOptions` + `useSesionActual({ enabled })`. |

### Created — account guard and test data (4)

| File | What |
|---|---|
| `features/cuenta/components/PanelSesion.tsx` | The `S-06` guard of the account area: reads `GET /auth/me` and distinguishes the expired session from a recoverable error. |
| `features/cuenta/__tests__/cuenta.ejemplos.ts` | The example values of the suites, **inside `__tests__`**: NOT a contract fixture, imported by NO production module. |
| `features/public/__tests__/edicion-integration.test.ts` | The focused suite of the edition dataset. |
| `features/auth/__tests__/identidad-sesion-integration.test.ts` | The focused suite of the identity and session datasets. |

### Modified (12)

| File | What |
|---|---|
| `features/public/views/InformacionView.tsx` | Composes `EdicionActualPanel`; the doc comment now says where the edition comes from. |
| `features/public/components/index.ts` | Exports `EdicionActualPanel`. |
| `features/public/components/RecuperarCompraForm.tsx` | The comment no longer promises a transport that cannot exist: `RT-RC-01` has no registered route. |
| `features/public/schemas/recuperar-compra.schema.ts` | The header declares that this is a client-validation schema and NOT a wire mirror, and why. |
| `features/auth/hooks/useDocumentoLookup.ts` | Consumes the new owner of `RT-ID-01` and the REAL wrapper field (`nombre_completo` instead of the frozen `razon_social`). |
| `features/auth/hooks/index.ts` | Exports the new hooks. |
| `features/auth/schemas/index.ts` | Exports the new mirrors. |
| `features/auth/services/index.ts` | Exports the new services. |
| `app/(cuenta)/mi-cuenta/page.tsx` | Renders `PanelSesion` above the hub. |
| `features/cuenta/components/index.ts` | Exports `PanelSesion`. |
| `features/cuenta/types/cuenta.types.ts` | The header states the truth: these types are NOT a mirror, because the account wrappers have no presenter. |
| `features/cuenta/__tests__/cuenta-estados.test.tsx` | Imports the example values from `__tests__/cuenta.ejemplos`. |

### Deleted (3)

| File | Why |
|---|---|
| `features/public/fixtures/edicion.fixture.ts` | The provisional mirror of `EdicionActualOut` is replaced by the real Zod mirror and the real service. |
| `features/cuenta/fixtures/cuenta.fixture.ts` | The provisional mirror of wrappers that have **no** presenter: it cannot be replaced by a mirror, only removed. |
| `features/auth/services/documento.service.ts` | The route `RT-ID-01` had **TWO** owners (this one and the new `identidad.service.ts`) and the old one carried a drifted shape (`razon_social` instead of the real `nombre_completo`). The single owner is now `identidad.service.ts`.

### NOT touched

`src/components/shell/**` · `src/components/ui/**` · `src/providers/**` · `src/lib/**` ·
`src/hooks/**` · `src/shared/**` · `src/app/globals.css` · `src/types/**` · `src/errors/**` ·
`features/{portada,inscripciones,pases,marketplace,admin,theme}/**` · `app/(portada)/**` ·
`app/(auth)/**` · `Aplicacion/backend/**` · `contract/**` · the root `frontend/**`.

---

## 5. Proof of the deletion of the provisional fixtures

| Check | Command | Result |
|---|---|---|
| The token `PROVISIONAL_CONTRACT_FIXTURE` does not survive in the roots of this packet | `grep -r "PROVISIONAL_CONTRACT_FIXTURE" features/public features/cuenta features/auth` | **0 matches** |
| No reference to the deleted fixture files survives | `grep -r "cuenta.fixture\|edicion.fixture\|documento.service" src` | **0 matches** |
| No production module imports a fixture | the only importer of the example values is `features/cuenta/__tests__/cuenta-estados.test.tsx` | **verified** |
| No `catch` falls back to a fixture | the two services throw; there is no fallback branch | **verified** |
| No hidden route | the only new paths are `/ediciones/actual`, `/personas/**`, `/auth/me` — all registered | **verified** |

**The token still exists in trees that are NOT the roots of this packet** and are owned by other
packets: `features/pases/fixtures/pase.fixture.ts` (API-03),
`features/marketplace/fixtures/marketplace.fixture.ts` (API-03) and
`features/portada/fixtures/{useCatalogo,useLandingPaquetes,paquetes.fixture}.ts` (**PUB-01**, which
is outside the allowed roots of API-01). They are reported as an A0 request, not touched.

---

## 6. Commands run, exit codes and results

**The ONLY runtime command of this packet was the typecheck.** Tests, lint, build, servers and
browsers were forbidden by the launch contract.

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | 4 errors, ALL of them SYNTACTIC and ALL in `src/features/inscripciones/__tests__/inscripcion-transporte.test.ts` — an **untracked, concurrent, out-of-scope** file of API-02 (JSX in a `.ts` file). **0 errors in the roots of API-01.** |
| 2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | 4 errors in the same concurrent file, plus 0 semantic errors anywhere. |
| 3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | 3 errors, ALL in `src/features/pases/views/{PaseGestionarRuta,PaseGestionarView}.tsx` — **concurrent, out-of-scope** (API-03). **0 errors in the roots of API-01.** |
| 4 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | **GREEN, project-wide.** The concurrent trees of API-02 (`features/inscripciones/**`) and API-03 (`features/pases/**`) were repaired by their own owners during this packet. |
| 5 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | 1 error in `src/features/marketplace/__tests__/marketplace-estados.test.tsx` — a fixture it imports was deleted in the middle of the run by API-03. **Concurrent, out-of-scope.** |
| 6 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** / **1** | 2 SYNTACTIC errors in `src/features/pases/__tests__/pases-estados.test.tsx` — **concurrent, out-of-scope** (API-03, still in flight). **0 errors in the roots of API-01.** |

**Zero errors were reported in `features/public/**`, `features/cuenta/**`, `features/auth/**` and
`app/(cuenta)/**` in EVERY run (7 runs).** The project-wide gate was GREEN in one run and RED in
the others ONLY because of the concurrent trees of API-02 (`features/inscripciones/**`) and API-03
(`features/pases/**`, `features/marketplace/**`), which are outside the allowed roots of this packet
and were NOT touched, reverted or merged. The last two runs of the packet were RED on those
concurrent trees: **the gate of this packet is green, the project-wide gate belongs to API-03
while it writes.**

**NOT RUN** (forbidden by the launch contract, and recorded as deferred, never as passed):
`vitest` · `biome check` · `next build` · `npm install` · any server · any browser · the five-width
audit · `git stash` · `git commit` · `git reset` · `git checkout`.

---

## 7. Tests written (NOT executed)

| Suite | Environment | What it freezes |
|---|---|---|
| `features/public/__tests__/edicion-integration.test.ts` | node | The mirror of `EdicionActualOut` is exact (it accepts the wrapper and it rejects an answer that does not match); the route is the registered one; a `204` is never parsed; the key lives in one namespace. |
| `features/auth/__tests__/identidad-sesion-integration.test.ts` | node | The mirrors of `DocumentoConsultaOut`, `PersonaResueltaOut`, `PersonaOut` and `SesionUsuarioOut` are exact; the three identity routes and the session route are the registered ones; the input schema of the confirmation declares its limits; the keys live in one namespace. |

**2 suites WRITTEN, NEVER RUN.** Nothing in this packet may be read as a green test result.

### The five widths

**NOT AUDITED.** No browser was run. The markup keeps the composition of UI-01 (the panel is a
`flex flex-col` block with `border-border bg-surface-raised p-4`, the same tokens as the rest of the
area) and adds no fixed width, no literal colour and no new interaction. The audit at 360, 390,
768, 1024 and 1440 stays OPEN.

---

## 8. Deviations, decisions and A0 requests

| ID | Type | What |
|---|---|---|
| `D-API01-01` | decision | **Only registered routes are bound.** The five datasets without a route (`RT-ID-04/05/06`, `RT-RC-01`, account registration) keep their honest state; the frontend never invents a URL nor a wrapper. |
| `D-API01-02` | decision | **The account types stay TYPES.** They are not replaced by a Zod mirror because there is no presenter to mirror: a mirror of a non-existent wrapper would be an invented contract. They are documented as the seam where the real wrappers will land. |
| `D-API01-03` | decision | **The example values of the account area moved INSIDE `__tests__`.** They are not a contract fixture any more; no production module imports them and the repo-wide token survives only in the trees of other packets. |
| `D-API01-04` | decision | **The session is read from the backend, not from the cookie.** The cookie of the session can outlive the access token; `GET /auth/me` is the authority. The account hub draws the `S-06` state from it. |
| `D-API01-05` | deviation | **`RT-ID-01` had two owners.** `features/auth/services/documento.service.ts` was deleted and its only consumer was moved to the new `identidad.service.ts`. Its shape was also drifted (`razon_social` instead of the real `nombre_completo`); the mirror is now exact. |
| `D-API01-06` | deviation | **The error of a READ is wrapped in `ApiQueryError`** (the canonical "API failure with HTTP status"), which is imported from `@/hooks/callsApi/useApiQuery`. It is the only canonical type of the project that carries the status; its natural home would be `src/errors/**` (A0-owned, forbidden root here). |
| `D-API01-07` | deviation | **`APP-01` (`/mi-cuenta`) was the only route file touched.** The `PanelSesion` guard is rendered by the page (a server component) and NOT by `MiCuentaView`, so the composition of UI-01 and its suites stay untouched. |
| `D-API01-08` | deviation | **The edition namespace is `edicion`, not `public`.** The dataset belongs to the whole product, not to one feature. |
| `D-API01-09` | deviation | **`AUTH-02` (`/registro`) was not integrated.** There is no registered route for the registration of an account, and the register flow of `features/auth/**` is a copy of the frozen one. It needs a backend route first. |

### A0 requests

| ID | Request |
|---|---|
| `A0-API01-01` | **The account routes do not exist.** `GET /api/mi-cuenta/resumen` (`MiCuentaOut`), `GET /api/mi-cuenta/compras` (`PaginatedData[MisComprasListItemOut]`), `GET /api/mi-cuenta/compras/{compra_id}` (`CompraDetalleOut`) have no controller. They are the exact wrapper of `ACCOUNT-01/02/04/05` and they are the LAST thing this packet could not deliver. |
| `A0-API01-02` | **The recovery route does not exist.** `POST /api/recuperar-compra` (`RecuperarCompraOut`) has no controller; the mail provider is also not configured (`PD-08`). Until both exist, the neutral answer of `REC-01` stays a declaration and not a transport. |
| `A0-API01-03` | **The registration of an account does not exist.** `POST /api/auth/registro` has no controller: the route `AUTH-02` cannot be integrated. |
| `A0-API01-04` | **The catalogue of the portada still points at routes that do not exist.** `features/portada/fixtures/useCatalogo.ts` calls `/catalogo/categorias/` and `/catalogo/promociones/`, which are NOT registered (`/catalogo/paquetes` and `/catalogo/disciplinas` are). The tree is outside the roots of API-01 (it belongs to `PUB-01`). |
| `A0-API01-05` | **The shared error mirror does not accept `details: null`** (`src/types/api.types.ts` → `apiErrorSchema`), and it does not carry `field_errors[]`. The shared handler (`src/errors/field-errors.ts`) does read the channel, so the behaviour is correct, but the mirror of the envelope is not exact. `src/types/**` and `src/errors/**` are outside the roots of this packet. |
| `A0-API01-06` | **The canonical home of the edition dataset is `features/edition/**`**, not `features/public/**`. The namespace is already `edicion` and the literals live in one file, so the move is mechanical. It matters when the shell needs the module filter (`FND-06-D-02`). |
| `A0-API01-07` | **`ApiQueryError` lives in a hook module.** Its natural home is `src/errors/**` (shared), so that the services do not depend on the hook layer. |
| `A0-API01-08` | **`00-matriz-tareas.md` still reads `pending` for `T-070` and `T-071`.** The physical task matrix is a **forbidden root** for every apply packet (same precedent as FND-01, FND-02, UI-01, UI-02, UI-03 and DOM-01…DOM-08): **A0 must sync it explicitly.** |

---

## 9. Workload and review boundary

The artefact of the packet carries **no** `Review Workload Forecast`, so no chain decision was
required before the apply (the same precedent as DOM-06, FND-07, FND-08, UI-01, UI-02 and UI-03).

The real size of this packet is **~1 100 changed lines** (16 created + 12 modified + 3 deleted),
which exceeds the 400-line review budget by roughly **2.7×**. It is reported to A0 as a finding.
There is **no commit** in this packet, so the budget is a report and not a gate.

**Autonomous work units** (each one reviewable on its own, in this order):

| WU | Scope | Files |
|---|---|---|
| WU-1 | The edition dataset (mirror, service, keys, options, hook, panel) | `features/public/{schemas,services,utils,hooks,components}/**` |
| WU-2 | The identity and session datasets | `features/auth/{schemas,services,utils,hooks}/**` |
| WU-3 | The account guard and the deletion of the fixtures | `features/cuenta/**` · `app/(cuenta)/mi-cuenta/page.tsx` |
| WU-4 | The suites | `features/{public,auth}/__tests__/**` · `features/cuenta/__tests__/**` |

**Rollback:** revert WU-4 → WU-1. The rollback is confined to the 16 created files and the 12
modified files of this packet; the shared shell, the providers, the theme and every other feature
are untouched, so reverting this packet leaves the product exactly as it was. `git stash` was never
invoked and no commit was created.

---

## 10. Concurrency observed (not touched, not merged)

During this packet the tree changed under it:

- `src/features/inscripciones/**` (API-02) — an untracked
  `__tests__/inscripcion-transporte.test.ts` with JSX in a `.ts` file broke the global typecheck for
  two runs. **Not touched, not reverted, not merged**: it is owned by API-02.
- `src/features/pases/**` (API-03) — three type errors in `views/{PaseGestionarRuta,PaseGestionarView}.tsx`.
  **Not touched, not reverted, not merged**: it is owned by API-03.
- `src/features/auth/{components,views}/**` and `src/features/auth/hooks/useRegister.ts` — modified
  by another agent. **Only the files this packet needed were touched** (`hooks/index.ts`,
  `hooks/useDocumentoLookup.ts`, `schemas/index.ts`, `services/index.ts`); the rest was read-only.

---

## 11. Acceptance criteria of the packet

- [x] Every visible data/action of the bound datasets uses a **registered** endpoint and the exact
      mirror of its presenter.
- [x] The query keys carry the identity of their dataset (edition, document, resolved person) and
      the mutations invalidate **only** the affected data.
- [x] No provisional fixture, mock or fallback survives in the roots of this packet; the account
      area and the recovery keep their **honest** state and declare the route they need.
- [x] The recovery response stays neutral: the form declares the same answer whether the purchase
      exists or not, and it does not fake a sent message.
- [ ] The suites were **WRITTEN** and **NOT EXECUTED**; the five-width browser audit and the
      assistive-technology pass were **NOT RUN**. The packet stays `verification_required`.

---

## 12. Next packet

**`API-02`** (`wave-03-api-integration/API-02-inscription-integration.md`), in parallel with
**`API-03`** (commercial) and **`UI-04`/`UI-05`**. `XCT-02` stays blocked until API-02…API-05 and
XCT-01 are closed.
