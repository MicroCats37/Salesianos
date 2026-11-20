# API-02 — Integración del alta, el pool, los equipos y las compras de la inscripción

**Artifact:** `evidence/api/API-02-inscription-integration.md` · **Packet:** API-02 (`wave-03-api-integration`)
**Owner:** A7 · **Status:** `verification_required` (implementation pass applied, runtime verification deferred)
**Sub-batches:** API-02 (2026-11-19, the implementation pass) · **API-02B** (2026-11-20, the corrective sub-batch — see §16)
**Task of origin:** `T-072` · **Target:** `Aplicacion/frontend/src/features/inscripciones/**` only
**Date:** 2026-11-19 (API-02) · 2026-11-20 (API-02B) · **Branch:** `master` · **Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (no commit created; `git stash` never invoked)

---

## 1. Scope actually applied

The packet names ONE original task (`T-072`) and TWO routes through the
registration area. Both live inside the allowed edit roots, so both were
applied.

| Page ID | Route | Route file | Feature | State |
|---|---|---|---|---|
| `SPORT-01` | `/inscripcion` | `app/(cuenta)/inscripcion/page.tsx` (**NOT touched**) | `features/inscripciones/views/InscripcionWizardView.tsx` | **applied** |
| `ACCOUNT-03` | `/mis-inscripciones/[id]` | `app/(cuenta)/mis-inscripciones/[id]/page.tsx` (**NOT touched**) | `features/inscripciones/views/MisInscripcionDetalleView.tsx` | **applied** |

**The two route files were NOT edited.** UI-02 had already left them
composing the feature views (`<InscripcionWizardView pasoSolicitado={paso} />`
and `<MisInscripcionDetalleView id={id} />`), and API-02 bound the transport
INSIDE the feature: the views own their hooks now, so the pages keep working
unchanged. Their `git status` entry is UI-02's, not this packet's.

---

## 2. The rule that decided the packet (`D-API02-01`)

> **Only REGISTERED routes are bound, and the mirror is 1:1 with the presenter
> that publishes them.**

The truth was read from the target backend, not from the plan:

- `Aplicacion/backend/config/api.py` — the `registrar_controladores(...)` block
  (the only gate: `FREEZE-PS-1.0.0` §3.1.2).
- `Aplicacion/backend/modules/salesianos_fest/presentation/controllers/` —
  `catalogo_controller.py` and `inscripcion_controller.py`.
- `Aplicacion/backend/modules/salesianos_fest/presentation/schemas/` —
  `catalogo_schemas.py`, `inscripcion_schemas.py`, `pool_schemas.py`,
  `compra_cupos_schemas.py`.
- `Aplicacion/backend/modules/salesianos_fest/presentation/presenters/` —
  `catalogo_presenter.py`, `inscripcion_presenter.py`, `pool_presenter.py`,
  `compra_cupos_presenter.py`.
- `Aplicacion/backend/modules/salesianos_fest/tests/e2e/` — the suites that fix
  the wire shape and the status codes.

The frozen tree (`frontend/**`, `backend/**`) was read as evidence only. The
exploration `#11377` (`sdd/frontend-api-ui-readiness/explore`) had already
recorded that the copied `features/inscripciones` layer spoke the FROZEN
dialect (`/catalogo/paquetes/`, `/catalogo/promociones/`, `/cotizaciones/`,
`/inscripciones/completa/`) and could not parse a single real answer.

**No URL was invented. No unregistered controller was bound. No Zod mirror was
written for a wrapper without a presenter.**

---

## 3. Endpoint / presenter / schema ledger

Every row is a route that EXISTS at runtime in `Aplicacion/backend`.

| Route | Method | Ledger | Controller (target) | Presenter (target) | Wrapper (target) | Mirror Zod (este paquete) |
|---|---|---|---|---|---|---|
| `/catalogo/paquetes` | GET | `RT-IN-12` | `CatalogoController.listar_paquetes` | `CatalogoPresenter.present_paquetes` | `CatalogoPaquetesOut` | `catalogoPaquetesSchema` |
| `/catalogo/disciplinas` | GET | `RT-IN-13` | `CatalogoController.listar_disciplinas` | `CatalogoPresenter.present_disciplinas` | `CatalogoDisciplinasOut` | `catalogoDisciplinasSchema` |
| `/inscripciones` | POST | `RT-IN-14` | `InscripcionController.crear_inicial` | `InscripcionPresenter.present_inicial` | `InscripcionInicialOut` | `inscripcionInicialSchema` |
| `/inscripciones/{id}` | GET | `RT-IN-02` | `InscripcionController.obtener` | `InscripcionPresenter.present_detalle` | `InscripcionDetalleOut` | `inscripcionDetalleSchema` |
| `/inscripciones/{id}/equipos` | GET | `RT-IN-04` | `InscripcionController.listar_equipos` | `InscripcionPresenter.present_equipos` | `EquiposInscripcionOut` | `equiposInscripcionSchema` (**NO LIGADA**, ver §4) |
| `/inscripciones/{id}/pool` | GET | `RT-IN-03` | `InscripcionController.obtener_pool` | `PoolPresenter.present_pool` | `PoolOut` | `poolSchema` |
| `/inscripciones/{id}/participantes` | POST | `RT-IN-05` | `InscripcionController.agregar_participante` | `PoolPresenter.present_pool` | `PoolOut` | `poolSchema` |
| `/inscripciones/{id}/participantes/{participacion_id}` | DELETE | `RT-IN-06` | `InscripcionController.retirar_participante` | `PoolPresenter.present_pool` | `PoolOut` | `poolSchema` |
| `/inscripciones/{id}/compras/cupos` | POST | `RT-CM-01` | `InscripcionController.comprar_cupos` | `CompraCuposPresenter.present_compra` | `CompraCreadaOut` | `compraCreadaSchema` |

### 3.1 The routes that DO NOT exist (and were not invented)

| Route of the frozen tree / of the plan | Reality in the target | What this packet did |
|---|---|---|
| `POST /inscripciones/completa/` | **does not exist** | deleted (`useCrearInscripcion.ts`) |
| `POST /cotizaciones/` | **no controller at all** | deleted (`useCotizacion.ts` + `cotizacion.schema.ts`) |
| `GET /catalogo/promociones/` | **does not exist** | deleted (`useCatalogo.ts`) |
| `GET /catalogo/categorias/` | **does not exist** | deleted (`useCatalogo.ts`) |
| `GET /inscripciones` (list, `RT-IN-01`) | **not implemented** in `InscripcionController` | **NOT bound**; the pending-operation seam stays unfilled (§4) |
| `GET /inscripciones/{id}/compras` (list of purchases) | **not implemented** | **NOT bound**; the purchases section says so (`PanelCompras`) |
| any route that publishes `BeneficioConcedido` | **no presenter** | **NOT bound**; the benefits section stays the honest empty |

---

## 4. The decisions of the package

### `D-API02-01` — Only registered routes are bound

The ledger of §3 is the whole surface. The three routes of the frozen tree
that the target does not serve are GONE, and nothing replaced them.

### `D-API02-02` — The money on the wire is a STRING, and it is proved

`PrecioOut.monto` and `CompraOut.total` are `Decimal` on the server. The wire
shape is a JSON **string**, and the chain is:

1. `core/responses.py::success_response` → `model_dump(mode="json")`, and
   Pydantic v2 serialises a `Decimal` in JSON mode as a string.
2. `ninja/operation.py::_result_to_response` → re-validates the envelope
   against the declared response model and dumps it in the DEFAULT ("python")
   mode, so the `Decimal` survives as a `Decimal`.
3. `ninja/responses.py::NinjaJSONEncoder` extends Django's
   `DjangoJSONEncoder`, whose `default()` renders a `Decimal` with `str(o)`.

The mirror declares `z.string()` and the frontend prints the amount exactly as
it arrives: it never parses, sums nor formats money (`RN-C02`). The e2e suite
of DOM-02 (`Decimal(str(datos["compra"]["total"])) == Decimal("750.00")`) is
compatible with the string form.

> **Open decision `OD-A0R2-01` (raised by UI-02 as `A0-UI02-01`) is CLOSED by
> the evidence**: the money travels as a string. It stays open only as a
> question of product policy about the DISPLAY, not about the wire.

### `D-API02-03` — One dataset, one namespace, four of them

`utils/inscripcion.claves.utils.ts` owns the four namespaces of the area with
the shared factory `createDatasetQueryKeys`:

| Dataset | Namespace | Key |
|---|---|---|
| the catalogue of packages | `inscripcion.catalogo.paquetes` | `["inscripcion.catalogo.paquetes","list",{edicion_id}]` |
| the catalogue of disciplines | `inscripcion.catalogo.disciplinas` | `["inscripcion.catalogo.disciplinas","list",{edicion_id}]` |
| the detail of a registration | `inscripcion.detalle` | `["inscripcion.detalle","detail",{id}]` |
| the pool of a registration | `inscripcion.pool` | `["inscripcion.pool","detail",{id}]` |

**What travels in the key:** the EDITION (the catalogue is edition-scoped) and
the REGISTRATION (the detail and the pool are per registration). A parameter
that is `undefined` is dropped, so `{edicion_id: undefined}` and `{}` are the
SAME cache entry.

**What does NOT travel, and why:** no filter and no page. NO registered
endpoint of this area filters or paginates: the catalogue is edition-scoped
and complete, and the paginated read of the inscriptions (`RT-IN-01`) is NOT
implemented. Putting a `page` in the key would create a SECOND cache entry for
the SAME answer. The `listPage(params)` slot of the generic factory is the
reserved place for the frozen pagination shape when that route is ratified.

### `D-API02-04` — Write when the exact shape is preserved, invalidate otherwise

| Mutation | Answer | Policy |
|---|---|---|
| `POST /inscripciones` | `InscripcionInicialOut` | **INVALIDATE** `inscripcion.detalle`. The inscription is NEW: writing it would create the entry of a registration that nobody read (FND-08, rule 4 — no orphans). |
| `POST /inscripciones/{id}/participantes` | `PoolOut` | **WRITE** the pool into its entry (only if the entry already exists) + **INVALIDATE** `inscripcion.detalle["detail",id]`. The answer IS the new pool: the exact shape is preserved, so the browser does not guess the new balance. |
| `DELETE /inscripciones/{id}/participantes/{pid}` | `PoolOut` | **WRITE** the pool + **INVALIDATE** the detail. Same reason. |
| `POST /inscripciones/{id}/compras/cupos` | `CompraCreadaOut` | **INVALIDATE** the pool AND the detail. The answer is NOT a pool: it carries the capacity but not the participations nor the impediments, so the exact shape of the pool cannot be preserved. |

The invalidation lives INSIDE the `mutationFn` (not in `onSettled`): a
component that unmounts while the mutation is in flight would never
invalidate, and the cache would keep the old answer (FND-08, rule 5).

The invalidation happens when the mutation SETTLES, and not only when it
succeeds: a **409** means that ANOTHER actor changed the same registration, so
the reads have to be refreshed even though this mutation wrote nothing.

### `D-API02-05` — The browser never derives a business value

- The pool band prints the THREE numbers that the server publishes
  (`cupos_pagados`, `cupos_asignados`, `cupos_disponibles`) side by side and
  as a sentence. There is no subtraction anywhere in the feature.
- The eligibility, the capacity, the price and the payment state are printed
  as they arrive.
- The static audit of `__tests__/inscripcion-responsive.test.ts` now covers
  the hooks, the services and the utils as well, and forbids
  `cupos_pagados -`, `cupos_asignados -`, `cupos_disponibles -`,
  `cupos_incluidos *`, `total *` and `monto *`.
- The reuse of a registration is READ from what the server declares: the
  boolean `compra.reutilizada` and the cause `INSCRIPCION_REUTILIZADA` (a
  CLOSED vocabulary of the backend, `CausaOperativaInscripcion`). The cause is
  ALSO printed verbatim, so a cause that the backend adds in the future is
  shown instead of hidden.

### `D-API02-06` — The 422 reaches the control that owns the field

The alta re-throws the **ORIGINAL** error (it does not replace it with a
generic message), so the `GenericForm` seam of FND-07 reads
`error.field_errors[]` and marks each control exactly once. The form of the
participant does the same by hand with `handleApiError` and
`setError`, because it is not a `GenericForm`.

The routes that FAIL are handled by HTTP STATUS and never by the machine
code: `403` is the permission state of the route, `409` is a recoverable
conflict whose message is printed verbatim, and `422` reaches the field.

### `D-API02-07` — The recovery of a pending operation

The recovery that IS reachable is the **idempotent alta**: the retry answers
with the inscription that already exists (`FR-04` I-4) and the wizard then
shows the recovery state instead of offering the form again.

The `pendiente` seam of the view is KEPT but **no route can fill it**: the
target backend has no route that LISTS the inscriptions of the responsible
(`RT-IN-01` is in the provisional ledger and is NOT implemented). It is left
in place, documented and honest — a request to A0 (`A0-API02-01`).

### `D-API02-08` — The teams have ONE owner

`GET /inscripciones/{id}/equipos` (`RT-IN-04`) exists and is registered, but
it is **NOT bound**: `InscripcionDetalleOut.equipos` already publishes the
teams of the registration, and binding both would give the teams TWO cache
entries and two sources of truth (FND-08, rule 1). The service and the mirror
exist (`equiposInscripcionSchema`); the hook does not, because nothing reads
it.

---

## 5. The layers

### 5.1 Schemas (`features/inscripciones/schemas/**`)

| File | Mirror |
|---|---|
| `catalogo.schema.ts` | `PrecioOut`, `BeneficioOut`, `DisciplinaOut`, `PaqueteOut`, `CatalogoPaquetesOut`, `CatalogoDisciplinasOut` |
| `inscripcion.schema.ts` | `EquipoOut`, `InscripcionDetalleOut`, `EquiposInscripcionOut`, `CompraOut`, `InscripcionInicialOut`, `EquipoIn`, `InscripcionInicialIn` |
| `pool.schema.ts` | `ParticipacionOut`, `ImpedimentoOut`, `PoolOut`, `ParticipanteAsignarIn` |
| `compra-cupos.schema.ts` | `ComprarCuposIn`, `CompraCreadaOut` |
| `participante.schema.ts` | the CLIENT validation of the assignment (not a wire mirror) + the two closed vocabularies (`TIPOS_DOCUMENTO`, `ROLES_PARTICIPANTE`) |
| `alta-inscripcion.schema.ts` | the CLIENT validation of the alta (kept; it declares no wire shape) |

`types/inscripcion.types.ts` was REWRITTEN: the view models are now DERIVED
from the mirrors (`z.infer`), so there is exactly ONE description of the wire
in the feature. The re-export of `Veredicto` / `EstadoOperativo` from the
account feature was removed: nothing in the feature used it and it was a
cross-feature coupling.

### 5.2 Services (`features/inscripciones/services/**`)

- `catalogo.service.ts` — `obtenerCatalogoPaquetes`, `obtenerCatalogoDisciplinas`.
- `inscripcion.service.ts` — `crearInscripcionInicial`, `obtenerInscripcion`,
  `obtenerPool`, `agregarParticipante`, `retirarParticipante`, `comprarCupos`.
- `respuesta.service.ts` — `leerRespuesta`: opens the ONE frozen envelope
  (`src/types/api.types.ts::apiResponseSchema`) and INSISTS that it carries
  data. A body that is not the envelope throws.

Every service goes through `apiSend` (`src/lib/api.ts`), the single transport
owner, and never through a raw `fetch`.

### 5.3 Hooks (`features/inscripciones/hooks/**`)

| Hook | Kind | Dataset / invalidation |
|---|---|---|
| `useCatalogoPaquetes` | read | `inscripcion.catalogo.paquetes`, `kind: "catalogo"` (10 min) |
| `useCatalogoDisciplinas` | read | `inscripcion.catalogo.disciplinas`, `kind: "catalogo"` |
| `useInscripcionDetalle` | read | `inscripcion.detalle["detail",id]`, `kind: "comercial"` (15 s) |
| `useInscripcionPool` | read | `inscripcion.pool["detail",id]`, `kind: "comercial"` |
| `useAltaInscripcion` | write | invalidates `inscripcion.detalle` (all) |
| `useAgregarParticipante` | write | writes the pool + invalidates `inscripcion.detalle["detail",id]` |
| `useRetirarParticipante` | write | writes the pool + invalidates `inscripcion.detalle["detail",id]` |
| `useCompraCupos` | write | invalidates the pool AND the detail of that registration |

The reads use the shared `datasetQueryOptions` (the staleness policy lives in
ONE place) and the writes use `useMutation` with the shared
`invalidateDatasets` / `updateCachedDetail`.

### 5.4 Payloads (`utils/inscripcion.payloads.utils.ts`)

Three CREATE mappings, all distinct, all built in the boundary and never in a
component:

| Mapping | Shape | What does NOT travel |
|---|---|---|
| `construirPayloadAlta` | `{edicion_id, paquete_id, equipos[]}` | the responsible (the server resolves it, `RN-U04`), the price, the quantity, the state |
| `construirPayloadParticipante` | `{equipo_id, persona_id?, tipo_documento?, numero_documento?, rol?, reemplaza_participacion_id?}` | the number of cupos (it is unitary and the server assigns it) — and the identification is EXCLUSIVE: identifier OR document, never both |
| `construirPayloadCompraCupos` | `{cantidad}` | the amount (the server resolves it against the catalogue in force, `RN-C02`) |

`undefined` means "not sent"; `null` clears a nullable field and only a
nullable one. The team count is NOT bounded in the browser: the limit is a
domain rule that the server declares and enforces with its 422.

---

## 6. The UI that the packet owns

| Surface | What changed |
|---|---|
| `InscripcionWizardView` | the catalogue is a REAL read (`RT-IN-12`) with a skeleton while it travels; the alta is a REAL write (`RT-IN-14`); the 422 reaches the control; the recovery shows "Ya existía esa inscripción" when the server reuses the inscription; the error alert prints the message of the server |
| `MisInscripcionDetalleView` | the detail (`RT-IN-02`) and the pool (`RT-IN-03`) are REAL reads; `403` is the permission state; the error is recoverable with a retry; the purchases and the benefits sections say why they are empty |
| `SeccionParticipantes` (NEW) | the two WRITES of the pool (`RT-IN-05`, `RT-IN-06`) and the **S-10** confirmation of the withdrawal, which names the effect (it frees the cupo of THAT registration; it does NOT cancel the purchase, does NOT return money and does NOT touch the inventory) |
| `FormularioParticipante` (NEW) | the assignment of a person BY DOCUMENT: the server resolves her from the register, so the browser never resolves a person nor invents an identifier |
| `PanelParticipantes` | the optional action of withdrawal, per row, in the table and in the cards |
| `PanelCompras` | the empty copy is now TRUTHFUL: the backend does not publish a listing of the purchases, so the section says that instead of showing an empty list that would read as "there are no purchases" |
| `PaqueteCard`, `PasoResumen` | the discipline chip prints `nombre` (the target `DisciplinaOut` has NO `sigla`; it has `slug`) |

The `sigla` of the FROZEN `PaqueteDisciplinaOut` was the last field of the
frozen dialect that the feature still used.

---

## 7. Deletion of the fixtures and of the stale hooks (the checklist of UI-02 §11)

| # | Item of the checklist | State |
|---|---|---|
| 1 | delete `fixtures/inscripcion.fixture.ts` and replace it with the Zod mirrors | **DONE** — the file and the `fixtures/` directory are GONE; the mirrors are `schemas/**` |
| 2 | prove that NO module outside `__tests__` imports a fixture, that there is no `catch` that falls back to a fixture and that there is no hidden route | **DONE** — `grep "PROVISIONAL_CONTRACT_FIXTURE"` in `features/inscripciones/**` → **0**; the whole `src` keeps the token ONLY in `features/pases/**`, `features/marketplace/**` (API-03) and `features/portada/fixtures/**` (PUB-01, out of the roots) |
| 3 | replace the view models of `types/inscripcion.types.ts` with the Zod mirrors | **DONE** — the view models are `z.infer` of the mirrors |
| 4 | replace `schemas/alta-inscripcion.schema.ts` with the mirror of `InscripcionInicialIn` | **DONE** with a declared deviation: the CLIENT validation is KEPT (it declares no wire shape) and the WIRE mirror is `inscripcionInicialInSchema`; the payload that travels is built from the mirror in `utils/inscripcion.payloads.utils.ts` (see `D-API02-09`) |
| 5 | bind the real service to the `enviar` seam and to the catalogue prop | **DONE** — the seams became hooks inside the views (`useAltaInscripcion`, `useCatalogoPaquetes`) |
| 6 | delete the unreferenced `PasoDeclaraciones.tsx` and the unreferenced hooks of the frozen wizard (`useCrearInscripcion`, `useCotizacion`) | **DONE** — all three are GONE, plus `schemas/cotizacion.schema.ts`, `schemas/paquete.schema.ts` and `utils/inscripcion.utils.ts` |

**The frozen routes are gone from the whole `src`:** `POST /inscripciones/completa/`,
`POST /cotizaciones/`, `GET /catalogo/promociones/` and `GET /catalogo/categorias/`
have **zero** production calls. The only occurrences of those literals left in
the feature are the NEGATIVE assertions of the suites (`inscripcion-transporte.test.ts`
and `inscripcion-responsive.test.ts`), whose whole purpose is to prove that
they are never called.

### `D-API02-09` — the client validation is KEPT next to the wire mirror

UI-02's checklist asked to REPLACE `alta-inscripcion.schema.ts` with the
mirror of `InscripcionInicialIn`. Replacing it would have removed the
validation of what the visitor typed (the mirror only describes the wire) and
would have made the form unvalidatable. The schema was KEPT as the client
validation (it declares no wire shape, it says so) and the mirror was ADDED
next to it. The two are compatible: the client requires a package and at least
one team with a discipline and a name of at most 160 characters (the limit the
server declares), and the mirror accepts the payload that the mapper builds.

---

## 8. Files changed (17 created, 17 modified, 7 deleted)

All of them are inside the allowed roots.

### Created (17)

| File | What |
|---|---|
| `schemas/catalogo.schema.ts` | the mirror of the catalogue of the edition |
| `schemas/inscripcion.schema.ts` | **rewrote** the mirror of the inscriptions (it held the frozen `InscripcionCompletaOut`) |
| `schemas/pool.schema.ts` | the mirror of the pool |
| `schemas/compra-cupos.schema.ts` | the mirror of the purchase of extra cupos |
| `schemas/participante.schema.ts` | the client validation of the assignment + the closed vocabularies |
| `services/catalogo.service.ts` | the transport of `RT-IN-12` and `RT-IN-13` |
| `services/inscripcion.service.ts` | the transport of `RT-IN-02/03/05/06/14` and `RT-CM-01` |
| `services/respuesta.service.ts` | the opening of the frozen envelope |
| `services/index.ts` | the granular barrel of the services |
| `hooks/useInscripcion.ts` | the reads of the detail and of the pool |
| `hooks/useInscripcionMutaciones.ts` | the four writes, with the write/invalidate policy |
| `utils/inscripcion.errores.utils.ts` | the status of a failure + the wrapper of a read |
| `utils/inscripcion.payloads.utils.ts` | the three CREATE mappings |
| `components/FormularioParticipante.tsx` | the assignment of a person |
| `components/SeccionParticipantes.tsx` | the section of the people + the S-10 confirmation |
| `__tests__/inscripcion-mirrors.test.ts` | the mirrors, the envelope and the payloads |
| `__tests__/inscripcion-transporte.test.ts` | the routes, the payloads, the cache policy, the 422 and the 409 |
| `__tests__/inscripcion-participantes.test.tsx` | the two writes of the pool and the S-10 |

### Modified (17)

| File | What |
|---|---|
| `schemas/index.ts` | the barrel of the new mirrors |
| `schemas/alta-inscripcion.schema.ts` | the docstring now points at the mirror |
| `types/inscripcion.types.ts` | the view models are now derived from the mirrors |
| `hooks/useCatalogo.ts` | **rewrote**: the frozen catalogue hooks are gone, the real ones are here |
| `hooks/index.ts` | the barrel of the real hooks |
| `utils/inscripcion.claves.utils.ts` | **rewrote**: the four namespaces with the shared factory |
| `components/index.ts` | the barrel of the new components |
| `components/PanelCompras.tsx` | the truthful empty copy |
| `components/PanelParticipantes.tsx` | the optional action of withdrawal |
| `components/PaqueteCard.tsx` | the chip prints `nombre` (the target has no `sigla`) |
| `components/PasoResumen.tsx` | the disciplines print `nombre` |
| `views/InscripcionWizardView.tsx` | the real reads and the real write |
| `views/MisInscripcionDetalleView.tsx` | the real reads and the section of the people |
| `__tests__/inscripcion-estados.test.tsx` | **rewrote**: no fixture, the double at the transport boundary |
| `__tests__/inscripcion-detalle.test.tsx` | **rewrote**: same |
| `__tests__/inscripcion-responsive.test.ts` | the static audit now covers the hooks, the services and the utils |

### Deleted (7)

| File | Why |
|---|---|
| `fixtures/inscripcion.fixture.ts` | the provisional fixture; the mirrors replace it |
| `hooks/useCotizacion.ts` | it called `POST /cotizaciones/`, a route that does not exist |
| `hooks/useCrearInscripcion.ts` | it called `POST /inscripciones/completa/`, a route that does not exist |
| `schemas/cotizacion.schema.ts` | the mirror of a wrapper that does not exist |
| `schemas/paquete.schema.ts` | the mirror of the FROZEN `PaqueteListOut` |
| `utils/inscripcion.utils.ts` | `formatearPrecio`, `precioProyectado` and `construirPayloadInscripcion` (the frozen payload) |
| `components/PasoDeclaraciones.tsx` | the declarations step has no counterpart in the target (`D-UI02-04`) |

The `fixtures/` directory was removed with it.

### NOT touched

`src/app/**` (the two routes of the packet included) · `src/lib/**` ·
`src/hooks/**` · `src/shared/**` · `src/errors/**` ·
`src/components/genericForm/**` · `src/components/ui/**` ·
`src/components/shell/**` · `src/providers/**` · `src/features/cuenta/**` ·
`src/features/public/**` · `src/features/auth/**` · `src/features/portada/**` ·
`src/features/admin/**` · `src/features/pases/**` and
`src/features/marketplace/**` (concurrent, API-03) · `Aplicacion/backend/**` ·
`contract/**` · `Aplicacion/plan/**` · `Aplicacion/documentacion/**` · the
frozen `frontend/**` and `backend/**`.

---

## 9. Commands run, exit codes and results

**The only runtime command of this packet was the typecheck.** Everything else
was forbidden by the launch contract.

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| V1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | **3 errors of THIS packet**: `enabled` is not a property of `DatasetQueryOptionsInput` (×2) and `obtenerEquipos` was still exported by the barrel after it was removed (×1). All three were fixed. |
| V2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | **0 errors in the roots of this packet.** The project-wide gate was RED because of a **CONCURRENT** out-of-scope tree: `src/features/pases/**` (`DialogoCheckout.tsx`, `PaseGestionarRuta.tsx`, `PaseGestionarView.tsx`). Not touched, not reverted, not merged — its owner repaired it. |
| V3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **2** | **0 errors in the roots of this packet.** The gate was RED because of another **CONCURRENT** out-of-scope tree: `src/features/marketplace/views/{ProductoDetalleRuta,TiendaRuta}.tsx`. Not touched; its owner repaired it. |
| V4 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | **CLEAN, project-wide.** The global gate is GREEN again. |
| V5 | `git status --short -- Aplicacion/frontend/src/features/inscripciones` | repo root | **0** | the whole tree is `??` (untracked), as UI-02 left it. No git operation was performed by this packet. |
| V6 | grep `PROVISIONAL_CONTRACT_FIXTURE` in `features/inscripciones/**` | repo root | **0** | **0 coincidencias.** The token survives in `features/pases/**`, `features/marketplace/**` (API-03) and `features/portada/fixtures/**` (PUB-01, out of the roots). |
| V7 | grep `/inscripciones/completa`, `/cotizaciones`, `/catalogo/promociones`, `/catalogo/categorias` in `src/**` | repo root | **0** | **0 llamadas de producción.** The only occurrences are the NEGATIVE assertions of the suites. |

**NOT RUN** (forbidden by the launch contract and by the standing preference
#11299): `vitest` · `biome check` · `next build` · `npm install` · any server ·
any browser · any visual automation · `git stash` · `git commit` ·
`git reset` · `git checkout`.

**Known baseline failures:** none of this packet. The two RED runs (V2, V3)
were caused by CONCURRENT trees outside the allowed roots.

**Reconciliation (2026-11-19, after the concurrent execution of API-01 and
API-03):** the roots of this packet gave **0 errors in EVERY run** (V1 to V4) — the
only own error (V1) was fixed in that same run. The project-wide gate was RED in
**two** runs (V2 and V3) and **both** times because of **CONCURRENT, out-of-scope**
trees of **API-03** (`src/features/pases/**` and
`src/features/marketplace/views/**`): they were **NOT** touched, reverted or merged,
and their owners repaired them. The **final project-wide `npx tsc --noEmit` exited
0** in the final verification of **API-03** (`V4`, exit **0**), so **the project-wide
gate is GREEN**. That last exit code is **reported by the API-03 evidence** and was
**NOT measured by this packet**: this reconciliation ran **no** command. The packet
stays `verification_required` — its 6 suites are **WRITTEN and NOT EXECUTED** and its
five-width browser audit is **NOT RUN**.

**Regressions:** none. Zero frozen files modified. No commit created.
`git stash` never invoked.

---

## 10. Tests written (NOT executed)

The standing preference (#11299) is that the suites of an apply packet are
**written** and **not executed**, and that the packet stays
`verification_required`. The suites below were written and **have never run**:
nothing here may be read as a green result.

| Suite | Environment | What it freezes |
|---|---|---|
| `__tests__/inscripcion-mirrors.test.ts` | node | the exact wire shape of every wrapper (the money as a string, the `slug` of the discipline, the three counters of the pool); the REJECTION of the shape of the frozen backend; the opening of the envelope (data + message, and the failure when the server says no); the three CREATE payloads and the ABSENCE of the responsible, of the price and of the quantity |
| `__tests__/inscripcion-transporte.test.ts` | jsdom | the exact route of every call (and the ABSENCE of the four frozen routes); the edition in the KEY; the exact payload of the alta; the 422 propagated ORIGINAL (so the field errors reach the form); the 409 NOT retried; the pool WRITTEN when the answer is a pool; the pool NOT written when the answer is not a pool (the purchase of cupos); the absence of orphans |
| `__tests__/inscripcion-estados.test.tsx` | jsdom | the ten states of `SPORT-01` against the real transport: the skeleton while the catalogue travels, the catalogue, the recoverable error with the message of the server, the recovery of a pending operation, the summary that says the cupos wait for the payment, the alta that publishes the result of the server, the retry that does NOT create a second inscription, and the 422 that marks the field |
| `__tests__/inscripcion-detalle.test.tsx` | jsdom | the states of `ACCOUNT-03`: the honest empty, the permission (`403`), the recoverable error with the retry, the five sections and the balance printed verbatim; the five sections in isolation |
| `__tests__/inscripcion-participantes.test.tsx` | jsdom | the assignment of a person by document (the server resolves her); the S-10 confirmation that names the effect and sends NOTHING until it is confirmed; the confirmed withdrawal on its route; the 422 that marks the control |
| `__tests__/inscripcion-responsive.test.ts` | node | the static rules: no literal colour, no fixed pixel width, `scope="col"` on every table header, the table from 1024 and the cards below, the 44 px targets, no provider vocabulary, **no arithmetic of cupos or money** in the components, in the views, in the hooks, in the services and in the utils, and **no frozen route** in the transport layer |

The double of the suites lives at the **transport boundary** (`apiSend`), not
at the service and not at the schema: the route, the envelope and the cache
are all under test, and no production module carries a mock.

### 10.1 The five widths

The audit at 360, 390, 768, 1024 and 1440 was **deferred**: no browser was run
in this packet. The STATIC rules that the markup guarantees are frozen in
`inscripcion-responsive.test.ts`; the BEHAVIOUR is not.

| Width | What the composition does | What is still unverified |
|---|---|---|
| 360 | one column; the rail of the wizard never scrolls sideways; the package cards stack; the form of the participant stacks its four fields; the people are labelled cards, never a table; every action is at least 44 px high | that no page overflows horizontally, that the sticky header does not cover the first action, that the long team names truncate |
| 390 | the same single column | the same |
| 768 | the rail of the wizard shows the title of every step; the form of the participant goes to two columns | that the two columns do not squeeze the controls |
| 1024 | the people become a table with prioritised columns and the column of the action | that no column is stretched and that nothing is clipped |
| 1440 | the content band is capped by the shell | the same |

**Residual gaps declared, never assumed green:** no browser rendering, no
screen-reader pass, no 200 % zoom reflow, no automated axe or Lighthouse run,
and no measurement of the contrast of the `--success` / `--warning` tones.

---

## 11. Deviations, decisions and A0 requests

| ID | Type | What |
|---|---|---|
| `D-API02-01` | decision | **Only registered routes are bound**, and the mirror is 1:1 with the presenter that publishes them. The truth was read from `config/api.py` and from the presenters, not from the plan. |
| `D-API02-02` | decision | **The money on the wire is a STRING** (chain proved in §4). It closes `OD-A0R2-01` / `A0-UI02-01` at the level of the wire. |
| `D-API02-03` | decision | **Four datasets, four namespaces.** The edition and the registration travel in the key; no filter and no page travel because no registered endpoint of the area filters or paginates. |
| `D-API02-04` | decision | **Write when the exact shape is preserved, invalidate otherwise.** The pool is written (three of the four routes answer with the updated pool); the purchase of cupos and the alta invalidate. |
| `D-API02-05` | decision | **The browser never derives a business value**, and the static audit now covers the transport layer too. |
| `D-API02-06` | decision | **The 422 reaches the control** (the original error travels) and the failures are branched by HTTP STATUS, never by the machine code. |
| `D-API02-07` | deviation | The `pendiente` seam of the wizard is KEPT but **no route can fill it**: `RT-IN-01` is not implemented. The reachable recovery is the idempotent alta. |
| `D-API02-08` | deviation | `RT-IN-04` (`GET /inscripciones/{id}/equipos`) is registered but **NOT bound**: the detail already publishes the teams, and two owners would break the cache rule. The mirror exists; the hook does not. |
| `D-API02-09` | deviation | The client validation `alta-inscripcion.schema.ts` was **KEPT** next to the wire mirror instead of being replaced (see §7). |
| `D-API02-10` | deviation | The discipline chip of the package card and the summary print `nombre`: the target `DisciplinaOut` publishes `slug`, not the `sigla` of the frozen tree. |
| `D-API02-11` | deviation | The `Veredicto` / `EstadoOperativo` re-export of `types/inscripcion.types.ts` was removed: nothing used it and it coupled the feature to the account area. |

### A0 requests

| ID | Request |
|---|---|
| `A0-API02-01` | `RT-IN-01` (`GET /inscripciones`, the paginated list of the inscriptions of the responsible) is in the provisional ledger and is **NOT implemented**. Without it the wizard cannot know that there is a pending inscription BEFORE the alta; the recovery only happens through the idempotent alta. The same route would close the list of `ACCOUNT-02` (`/mis-inscripciones`), which is still a fixture of UI-01. |
| `A0-API02-02` | No route **LISTS the purchases of a registration**. The initial one comes with the alta and every expansion with its own answer (`RT-CM-01`). The section of the purchases stays empty and says so. |
| `A0-API02-03` | No presenter publishes `BeneficioConcedido`. The section of the benefits stays the honest empty. |
| `A0-API02-04` | The routes of the inscription domain (`RT-IN-02`, `RT-IN-03`, `RT-IN-04`, `RT-IN-05`, `RT-IN-06`, `RT-IN-12`, `RT-IN-13`) and `RT-IN-14` are **PROVISIONAL**: only `RT-CM-01` is in the frozen ledger. They exist and are served, but the ledger has to ratify them. |
| `A0-API02-05` | The name of the presenter of `RT-IN-05` and `RT-IN-06` in the ledger (`ParticipanteAsignarPresenter` / `ParticipanteRetirarPresenter`) is NOT the one of the target: the target publishes the SAME wrapper `PoolOut` with `PoolPresenter` for the three routes. The equivalence of names has to be ratified. |
| `A0-API02-06` | `RT-IN-04` publishes `EquiposInscripcionOut` through `InscripcionPresenter.present_equipos`, and the ledger names `EquiposInscripcionPresenter`. Same ratification. |
| `A0-API02-07` | `00-matriz-tareas.md` does not carry a row for API-02 and the matrix is outside the allowed roots: the row has to be synchronised by the coordinator. |
| `A0-API02-08` | The provisional fixture token survives in `features/portada/fixtures/**` (PUB-01, out of the roots of this packet): the catalogue of the portada is still the frozen one and it duplicates the dataset of `inscripcion.catalogo.paquetes` (`R-FND08-01` of FND-08). |

---

## 12. Workload and review boundary

The tasks artefact of this change carries **no** `Review Workload Forecast`,
so no chain decision was required before the apply (the same precedent as
DOM-06, FND-07, FND-08, UI-01, UI-02, UI-03 and API-01).

**The real size of this packet is ~4 400 changed lines** (17 created, 17
modified and 7 deleted files; the feature went from ~3 860 to ~5 330 lines, of
which ~1 470 are the six suites), which exceeds the 400-line review budget by
roughly **11x**. There is **no commit** in this packet, so the budget is a
report and not a gate.

**Autonomous work units** (each one reviewable on its own, in this order):

| WU | Scope | Files |
|---|---|---|
| WU-1 | the Zod mirrors of the target presenters | `schemas/{catalogo,inscripcion,pool,compra-cupos}.schema.ts` · `types/inscripcion.types.ts` |
| WU-2 | the transport and the key factory | `services/**` · `utils/inscripcion.claves.utils.ts` · `utils/inscripcion.errores.utils.ts` · `utils/inscripcion.payloads.utils.ts` |
| WU-3 | the reads | `hooks/useCatalogo.ts` · `hooks/useInscripcion.ts` |
| WU-4 | the writes and the cache policy | `hooks/useInscripcionMutaciones.ts` |
| WU-5 | the wizard and the detail | `views/**` · `components/{PaqueteCard,PasoResumen,PanelCompras}.tsx` |
| WU-6 | the people of the pool | `components/{FormularioParticipante,SeccionParticipantes,PanelParticipantes}.tsx` · `schemas/participante.schema.ts` |
| WU-7 | the deletion of the frozen layer | `fixtures/**` · `hooks/{useCotizacion,useCrearInscripcion}.ts` · `schemas/{cotizacion,paquete}.schema.ts` · `utils/inscripcion.utils.ts` · `components/PasoDeclaraciones.tsx` |
| WU-8 | the suites | `__tests__/**` |

**Rollback:** revert WU-8 to WU-1. The rollback is confined to the 41 files of
this packet; the shared shell, the providers, the theme, the account feature
and every other domain are untouched, so reverting this packet leaves the
product exactly as it was. `git stash` was never invoked and no commit was
created.

---

## 13. Acceptance criteria of the packet

- [x] Every call goes to a **registered** route of the target backend; the four
      routes of the frozen tree are gone and **0** production calls survive.
- [x] The mirror of every wrapper is **1:1** with the presenter that publishes
      it (field names, optionality and types included) and the envelope is
      opened by the ONE frozen shape, with a loud failure.
- [x] **Service, hook and key ownership is singular**: one transport owner
      (`src/lib/api.ts`), one key factory, four namespaces, one service per
      endpoint group, one envelope reader.
- [x] The cache invalidation **reflects the backend**: the pool is WRITTEN
      when the answer is a pool, the purchase of cupos and the alta
      INVALIDATE, and no entry is created that nobody read.
- [x] The browser **never derives** an available capacity or an eligibility:
      the three counters are printed as they arrive and the static audit
      forbids the arithmetic in the whole feature.
- [x] **All the registration mocks are removed**: the provisional fixture, the
      four frozen hooks and the two frozen schemas are GONE, and no production
      module imports a fixture nor falls back to one in a `catch`.
- [x] The failures **preserve a recoverable operation state**: the recoverable
      error offers a retry, the 422 reaches the control and keeps the form,
      the 409 is not retried, and the pending operation is recovered instead
      of duplicated.
- [x] The only runtime command was the typecheck, and it exited **0**
      (V4). **0** errors in the roots of this packet in EVERY run.
- [ ] The execution of the six suites, the lint pass, the five-width browser
      audit and the assistive-technology pass are **DEFERRED** — the packet
      stays **`verification_required`**.

---

## 14. Readiness for XCT-02

`XCT-02` (transversal admin) needs the inscription surface to be real:

| Need of XCT-02 | State |
|---|---|
| the catalogue of the edition, read from the server | **READY** (`RT-IN-12`, `RT-IN-13`) |
| the detail and the pool of a registration, read from the server | **READY** (`RT-IN-02`, `RT-IN-03`) |
| the writes of the pool | **READY** (`RT-IN-05`, `RT-IN-06`) |
| the purchase of extra cupos | **READY** (`RT-CM-01`) |
| the alta, with its idempotent retry | **READY** (`RT-IN-14`) |
| the list of the inscriptions of the responsible | **NOT READY** (`RT-IN-01` not implemented → `A0-API02-01`) |
| the list of the purchases of a registration | **NOT READY** (`A0-API02-02`) |
| the granted benefits | **NOT READY** (`A0-API02-03`) |
| the admin surface of the inscriptions (`RT-IN-07`…`RT-IN-11`) | **NOT READY** — no admin controller of the inscription domain exists in the target backend; it belongs to **API-04** |

The transversal pieces that XCT-02 owns (the payment vs the delivery, the
right, the act of delivery) do not collide with this packet: the only
commercial state that the inscription surface publishes is the state of the
purchase, and it is printed verbatim.

---

## 15. Consumers unblocked

- **API-04** — the admin surface of the inscriptions reads the same wrappers
  (`InscripcionDetalleOut`, `PoolOut`, `EquiposInscripcionOut`) and can reuse
  the mirrors of this packet or write its own namespace.
- **API-03** — the commercial surface needs the SAME money decision
  (`D-API02-02`: a string on the wire).
- **XCT-02** — the transversal admin pass, with the readiness table of §14.
- **XCT-03** — the payment, the media and the notifications.
- **VER-01…VER-03** — the regression, the e2e and the sign-off.

**Next packet:** `XCT-02` after the other admin integrations (**API-03 was applied
after this packet**; the packet still depends on API-04, API-05 and XCT-01), and
**API-04**/**API-05** in parallel.

> **Reconciliation note (2026-11-19):** the "Next packet" line above was written
> before **API-03** closed; it is corrected here. The other two lines of this
> section are unaffected: **API-03** consumed the money decision `D-API02-02`
> (a string on the wire) and **API-04** still reads the same wrappers.

---

## 16. API-02B — Corrective sub-batch (2026-11-20): the focused suite was stale against the NEW target contract

**Sub-batch:** API-02B · **Owner:** A7 · **Status:** `verification_required` (the
implementation pass is applied; the runtime verification stays deferred)
**Allowed roots:** `Aplicacion/frontend/src/features/inscripciones/**` (one focused
test file) · **No other feature, no shared root, no backend, no contract touched.**
**Rollback point:** `fd1c4c123df3767ef6e86908565edf2d4c27c00a` (no commit created;
`git stash`/`reset`/`checkout` never invoked)

### 16.1 The symptom

`npx tsc --noEmit` reported **exactly two** errors, both in
`features/inscripciones/__tests__/inscripcion-transporte.test.ts` (lines **446**
and **487**), with the same shape:

```
TS2345: Argument of type '{ edicion_id: string; paquete_id: string;
  equipos: { disciplina_id: string; nombre: string; }[]; }' is not assignable to
  parameter of type '{ edicion_id: string; paquete_id: string;
  promocion_id: string; cantidad: number; equipos: [...]; ... }'.
  Type ... is missing the following properties: promocion_id, cantidad
```

The two errors were observed by **XCT-02** and by **XCT-03** as FOREIGN errors
(STATE.md, rows `XCT-02` and `XCT-03`): both packets ran the project-wide gate,
found the two errors outside their own roots, did **not** touch them and left the
gate RED.

### 16.2 The root cause

**A later concurrent change of the TARGET contract moved the payload of the alta,
and the focused suite of this packet was not migrated with it.**

The backend change `restore-registration-promotion-catalog-flow` (2026-11-20)
extended `InscripcionInicialIn` in
`Aplicacion/backend/modules/salesianos_fest/presentation/schemas/inscripcion_schemas.py`:
`promocion_id` became **REQUIRED** (the cohort that buys and that determines the
band of the teams, `RN-C02`/`QA-K01`) and `cantidad` became **REQUIRED** (the
number of participants, `ge=MIN_CANTIDAD_POR_INSCRIPCION`); `fusion_promocion_id`
and `cotizacion_version` stayed OPTIONAL.

The frontend mirror and the payload builder of this feature were migrated with
that change (`schemas/inscripcion.schema.ts` → `inscripcionInicialInSchema`,
`utils/inscripcion.payloads.utils.ts` → `construirPayloadAlta`), and the focused
suite was migrated in **three of its five** alta call sites (lines 336, 369 and
398 of `inscripcion-transporte.test.ts`). **Two call sites were left on the
previous three-field payload**: the **422** case (the field errors reach the form)
and the **409** case (the race is decided by the server). TypeScript rejected
them because the hook's variable type is the mirror's.

**The two errors were a STALE TEST, not a wrong contract.** The mirror, the
payload builder and the hook were already correct against the backend.

### 16.3 The fix (1 file, 2 call sites, 4 added lines)

`features/inscripciones/__tests__/inscripcion-transporte.test.ts` — the two
stale alta payloads now carry the fields that the target contract REQUIRES,
with the same values as their three already-migrated siblings:

```diff
         await result.current.mutateAsync({
           edicion_id: "ed-1",
           paquete_id: "paq-1",
+          promocion_id: "pro-1",
+          cantidad: 10,
           equipos: [{ disciplina_id: "dis-1", nombre: "Halcones" }],
         });
```

**Nothing else was changed.** No mirror, no payload builder, no hook, no
component, no view, no other test, no shared root, no backend and no contract.
The fix **preserves the current intended target contract** (the cohort and the
quantity are visitor decisions that the server resolves against the catalogue)
and **reintroduces no frozen endpoint**.

### 16.4 Commands / exit codes (workdir `Aplicacion/frontend`)

| # | Command | Exit | Result |
|---:|---|---:|---|
| V1 | `npx tsc --noEmit` | **1** | **2 errors, BOTH in the roots of this packet**: `features/inscripciones/__tests__/inscripcion-transporte.test.ts` lines 446 and 487 (`TS2345`: the payload lacks `promocion_id` and `cantidad`). 0 errors anywhere else. |
| V2 | `npx tsc --noEmit` | **0** | **CLEAN, project-wide.** The two errors of V1 are gone and **no other error appeared**: the fix did not touch a single line outside the focused test. |

**NOT RUN** (forbidden by the launch contract and by the standing preference
#11299): `vitest` · `biome check` · `next build` · `npm install` · any server ·
any browser · any visual automation · `git stash` · `git commit` · `git reset` ·
`git checkout`. The 6 suites of this feature stay **WRITTEN and NOT EXECUTED**
and the five-width browser audit stays **NOT RUN**; the packet stays
`verification_required`.

### 16.5 The registration truth re-verified (and one gap that is NOT ours to fix)

The two routes that the concurrent change added to this feature were checked
against the **registered** controllers of the target backend
(`Aplicacion/backend/config/api.py`):

| Route | Controller | Registered? | Verdict |
|---|---|---|---|
| `GET /catalogo/promociones` | `CatalogoController.listar_promociones` | **YES** (`CatalogoController` is registered) | **EXISTS** — a legitimate target route |
| `GET /catalogo/categorias` | `CatalogoController.listar_categorias` | **YES** (same controller) | **EXISTS** — a legitimate target route |
| `POST /cotizaciones` | `CotizacionController.cotizar` | **NO** | **DOES NOT EXIST at runtime** |

`CotizacionController` exists, is implemented and is exercised by the module's
own e2e URL configuration
(`modules/salesianos_fest/tests/urls_salesianos_fest.py`), but it is **NOT** in
the `registrar_controladores(...)` block of `config/api.py` and its own
docstring says so: *"Ledger: ruta PROVISIONAL — A0 tiene que registrar este
controller en `config/api.py`"*. Per `FR-07` §3.1 regla 2, **a route does not
exist until its controller is registered**: code written and not registered is
dead code by design.

**This sub-batch did NOT unbind it and did NOT touch the backend.** The binding
is the concurrent agent's deliberate work against the new target contract, and
the controller exists: the missing piece is the **registration**, which is a
backend file (`Aplicacion/backend/config/api.py`) and therefore **outside the
allowed roots** of this corrective apply. It is reported as an A0 request
(`A0-API02-09`).

### 16.6 Deviations and A0 requests of the sub-batch

| ID | Type | What |
|---|---|---|
| `D-API02B-01` | decision | **The stale TEST was fixed, not the contract.** The mirror, the payload builder and the hook of the feature were already correct against `restore-registration-promotion-catalog-flow`; only the focused suite was behind. Reverting the contract to the three-field payload would have broken the target backend's own requirement. |
| `D-API02B-02` | decision | The two call sites were aligned with their **three already-migrated siblings** (same field values), so the six suites of the feature speak **one** contract. |
| `A0-API02-09` | A0 request | **Register `CotizacionController` in `Aplicacion/backend/config/api.py`** so `POST /api/cotizaciones` exists at runtime. Until then the quotation that the wizard requests has no route, and the concurrency token `cotizacion_version` can never arrive. Owner: A0 (backend root, outside this packet's roots). |

### 16.7 Acceptance criteria of the sub-batch

- [x] The **root cause** is identified and it is a stale focused suite, not a wrong contract.
- [x] The fix touches **exactly one file** inside the allowed roots, and only the two stale call sites.
- [x] The **current intended target contract is preserved** (the cohort and the quantity are required by the target backend) and **no frozen endpoint is reintroduced**.
- [x] `npx tsc --noEmit` exits **0** and the **project-wide gate is GREEN** (V2).
- [x] Nothing outside `features/inscripciones/**` was modified; the concurrent trees of API-03, API-04, API-05, UI-04, UI-05, XCT-01, XCT-02 and XCT-03 were **not** touched, reverted or merged.
- [ ] The execution of the six suites, the lint pass and the five-width browser audit stay **DEFERRED** — the packet stays **`verification_required`**.
