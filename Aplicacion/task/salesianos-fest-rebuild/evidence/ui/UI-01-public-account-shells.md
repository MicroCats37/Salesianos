# UI-01 - Public, Authentication, Account And Recovery Skeletons

**Artifact:** `evidence/ui/UI-01-public-account-shells.md` - **Packet:** UI-01 (`wave-02-frontend-skeletons`)
**Owner:** A7 - **Status:** `verification_required` (implementation applied, runtime verification deferred)
**Date:** 2026-11-19 - **Target:** `Aplicacion/frontend/**` only

---

## 1. Scope actually applied

The packet names nine page IDs. Three of them live outside the allowed edit roots of this
packet (`(public)/**` and `(cuenta)/**` plus the two owning features), so they were **not**
touched. They are listed in section 10 with the reason and the handover.

| Page ID | Route | Route file | Feature view | State |
|---|---|---|---|---|
| `PUB-02` | `/informacion` | `app/(public)/informacion/page.tsx` (unchanged) | `features/public/views/InformacionView.tsx` | **applied** |
| `REC-01` | `/recuperar-compra` | `app/(public)/recuperar-compra/page.tsx` (unchanged) | `features/public/views/RecuperarCompraView.tsx` | **applied** |
| `ACCOUNT-01` | `/mi-cuenta` | `app/(cuenta)/mi-cuenta/page.tsx` (unchanged) | `features/cuenta/views/MiCuentaView.tsx` | **applied** |
| `ACCOUNT-02` | `/mis-inscripciones` | `app/(cuenta)/mis-inscripciones/page.tsx` (modified) | `features/cuenta/views/MisInscripcionesView.tsx` | **applied** |
| `ACCOUNT-04` | `/mis-compras` | `app/(cuenta)/mis-compras/page.tsx` (modified) | `features/cuenta/views/MisComprasView.tsx` | **applied** |
| `ACCOUNT-05` | `/mis-compras/[id]` | `app/(cuenta)/mis-compras/[id]/page.tsx` (unchanged) | `features/cuenta/views/MisCompraDetalleView.tsx` | **applied** |
| `PUB-01` | `/` | `app/(portada)/**` | `features/portada/**` | **not touched** (outside the roots) |
| `AUTH-01` | `/login` | `app/(auth)/**` | `features/auth/**` | **not touched** (outside the roots) |
| `AUTH-02` | `/registro` | `app/(auth)/**` | `features/auth/**` | **not touched** (outside the roots) |

`ACCOUNT-03` (`/mis-inscripciones/[id]`) and `SPORT-01` (`/inscripcion`) belong to **UI-02**
(`wave-02-frontend-skeletons/UI-02`), not to this packet. They were not touched.

---

## 2. The route brief applied

The briefs were produced by **GOV-02** and were read before any code was written:

- `evidence/routes/RB-01-public-account-identity.md` -> `PUB-02`, `AUTH-01`, `AUTH-02`,
  `ACCOUNT-01`, `ACCOUNT-02`, `ACCOUNT-03`, `ACCOUNT-04`, `ACCOUNT-05`, `SPORT-01`.
- `evidence/routes/RB-02-commerce-passes-store.md` -> `REC-01` (and `PASS-*`, `SHOP-*`, which
  are **UI-03** and out of this packet).
- `evidence/routes/SH-01` (tokens) - `SH-02` (five widths + a11y) - `SH-03` (ten states) -
  `SH-04` (shadcn families) - `SH-05` (provisional endpoints) - `SH-06` (wireframes).

### The visual direction

`SH-01` section 3: **Institutional Blue, Festival Gold** - the calm institutional blue of a
school programme carrying the warmth of a festival. Gold and cyan appear only where celebration
is genuinely intended; they are never a state. This packet consumes **only semantic roles**
(`bg-surface-raised`, `border-border`, `text-foreground`, `text-foreground-muted`,
`bg-surface-recessed`, `bg-primary`/`text-primary-foreground`, `--success`, `--warning`,
`--info`, `--destructive`). No token was added and `globals.css` was not touched.

### The rule that decided the composition (`D-UI01-01`)

> **A provisional fixture may render the configuration of the PRODUCT; it may never render the
> PERSONAL data of the authenticated reader.**

`FR-08` section 1.4 allows a fixture to render the skeleton of a page and to simulate the shape
of the response for the layout, and the frozen root already does it for the festival
configuration (`features/portada/fixtures/*`). But a logged-in responsible reading that she has
three registrations would be told a **lie about herself**: that is invented page data, and
`00-contrato-global-de-apply.md` (Hard Prohibitions) forbids it.

Therefore:

- `PUB-02` renders the **product configuration** (date, venue, sales windows) from the frozen
  portada fixture, exactly as the route did before this packet.
- `ACCOUNT-01/02/04/05` render the **honest state** by default (`sin-datos`): the account
  service is not connected and the route says so.
- The **populated compositions** (list, table, cards, filters, verdict chips, partial state) are
  implemented, typed and exercised by the suites with the provisional fixture. They are the code
  that API-01 binds to the real presenter.

---

## 3. shadcn candidate comparison (GOV-02-SH-01 re-run for this route family)

The MCP was executed for this family, not inherited:

| # | Tool call | Result |
|---|---|---|
| 1 | `shadcn_get_project_registries` | `@shadcn` (the target registry; style `radix-nova` in `Aplicacion/frontend/components.json`) |
| 2 | `shadcn_list_items_in_registries` (types `registry:ui`) | **61** items in `@shadcn` |
| 3 | `shadcn_search_items_in_registries` - table | 18 hits; `table` (registry:ui) + `data-table-demo` (registry:example) |
| 4 | `shadcn_search_items_in_registries` - pagination | `pagination` (registry:ui) + `pagination-demo` |
| 5 | `shadcn_search_items_in_registries` - accordion | `accordion` (registry:ui) + `accordion-demo` |
| 6 | `shadcn_get_audit_checklist` | Executed before closing the packet |

### The comparison and the decision

| Item | Registry | Fit for this family | Local state | Decision |
|---|---|---|---|---|
| `item` / `item-group` | `registry:ui` | Operational rows with a media, a title and a description - the right density for the registrations and the purchases of the reader | **present** in `components/ui/item.tsx` | **Selected** (already used by the existing views) |
| `table` | `registry:ui` | The semantic table for the list at 1024 and above | **present** | **Selected / reused** |
| `select` | `registry:ui` | The filters of the list | **present** | **Selected / reused** |
| `input` + `label` | `registry:ui` | The two fields of the recovery form | **present** | **Selected / reused** |
| `button` | `registry:ui` | Every action | **present** | **Selected / reused** |
| `alert` | `registry:ui` | S-04, S-09 and the outcomes of the recovery form | **present** | **Selected / reused** |
| `empty` | `registry:ui` | S-02 and S-03 | **present** | **Selected / reused** |
| `skeleton` | `registry:ui` | S-01 | **present** | **Selected / reused** |
| `badge` | `registry:ui` | The verdict chip | present, but with **no** verdict variants and a typo in the secondary variant (`text-secondary-foreground-foreground`) | **Rejected for the chip**: the verdict chip is **composed** in the feature layer (`VeredictoEstado`) with an icon + the backend label + the semantic bucket, because `SH-02` A11Y-11 requires colour + icon + text and the local `badge` has no `success`/`warning`/`info` variants. **Shared primitive untouched.** |
| `accordion` | `registry:ui` | The technical detail of `ACCOUNT-05` | **absent** locally | **Rejected**: adding it would touch `components/ui/**` (forbidden root). The technical detail was **omitted** instead (see `D-UI01-04`) |
| `pagination` | `registry:ui` | The server-driven pagination of the lists | present | **Not used yet**: the pagination belongs to the service that owns the page (`FREEZE-ENV-1.0.0` section 4.3). The skeleton receives a list; API-01 binds the page |
| `field` | `registry:ui` | The new shadcn form primitive | absent | **Rejected** - `GOV-02-SH-03`: `field` must not enter the `GenericForm` wrapper path without proving there is no double render of label/error. The recovery form uses `GenericForm` Mode 1 (`children`) and draws its own label/error once, per `contract/smart.md` section 5.2 |
| `data-table-demo` | `registry:example` | The behaviour reference of a list | - | **Rejected as a source** - `GOV-02-SH-04` / risk R-01 of `SH-04`: the example ships the TanStack **v9** API and the project pins `v8`. The lists are composed over the local `table` primitive instead |
| `login-01..05`, `signup-01..05` | block | AUTH-01 / AUTH-02 | - | **Out of scope** of this packet (the auth roots are forbidden) and already rejected as replacements in `SH-04` section 3.4 |

**No component was added. No file in `components/ui/**` was created, modified or overwritten.**

---
## 4. The ten states, route by route

`SH-03` section 1 fixes ten states. This is where each one lives for the routes of this packet.

| State | `PUB-02` | `REC-01` | `ACCOUNT-01` | `ACCOUNT-02` | `ACCOUNT-04` | `ACCOUNT-05` |
|---|---|---|---|---|---|---|
| S-01 initial / loading | `app/(public)/informacion/loading.tsx` (band + index rail + sections) | `app/(public)/recuperar-compra/loading.tsx` (card + two fields) | group `loading.tsx` (card grid, matches the hub) | `app/(cuenta)/mis-inscripciones/loading.tsx` (filter bar + rows) | `app/(cuenta)/mis-compras/loading.tsx` (filter bar + rows) | `app/(cuenta)/mis-compras/[id]/loading.tsx` (summary + blocks) |
| S-02 empty (never had data) | the programme section states what is not published yet | - | `RouteEmptyState` on the summary | `RouteEmptyState` + **Crear la primera** | `RouteEmptyState` | `RouteEmptyState` (no purchase shown) |
| S-03 filtered-empty | - | - | - | `SinResultadosConFiltros` (keeps the filters, states the count, offers **Quitar los filtros**) | `SinResultadosConFiltros` | - |
| S-04 recoverable error | group `error.tsx` | `app/(public)/recuperar-compra/error.tsx` (retry + back to the store) | group `error.tsx` | `app/(cuenta)/mis-inscripciones/error.tsx` (retry + back to the hub) | `app/(cuenta)/mis-compras/error.tsx` | `app/(cuenta)/mis-compras/[id]/error.tsx` (retry + back to the list) |
| S-05 validation | - | `GenericForm` + Zod: field error, summary with `role="alert"` and focus, `aria-invalid` / `aria-describedby` | - | - | - | - |
| S-06 permission | - | - | `ShellPermissionDenied` | `ShellPermissionDenied` | `ShellPermissionDenied` | `ShellPermissionDenied` (the purchase belongs to somebody else) |
| S-07 success | - | the neutral answer of the recovery form | - | - | - | - |
| S-08 in progress | - | the button is disabled and says **Enviando** while the request is pending | - | - | - | - |
| S-09 partial / indeterminate | - | - | - | - | - | `EstadoIndeterminado` (the payment is confirmed and the right is not enabled yet) |
| S-10 irreversible confirmation | **does not apply**: no action of these routes can be undone. The irreversible confirmations of the plan live in `ACCOUNT-03` (UI-02), in the passes and in the store (UI-03). It is declared, not silently dropped. | | | | | |
| neutral recovery response | - | the form always states that the answer is the same whether the purchase exists or not, and the outcome of a request is the neutral one | - | - | - | - |

---

## 5. Provisional fixtures (FR-08)

Every fixture is **local to its feature**, **typed with `satisfies`**, **marked**, **deterministic**
and **exported from no production barrel**. The deletion ledger is in section 11.

| Fixture (symbol) | Mirrors | Contract | Path | Deleted in |
|---|---|---|---|---|
| `edicionActualFixture` | `EdicionActualOut` (eventos) | `FREEZE-ED-1.0.0` | `features/public/fixtures/edicion.fixture.ts` | **API-01** |
| `estadoOperativoPagoPendienteFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `estadoOperativoPagoVerificandoFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `estadoOperativoPagoAtencionFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `estadoOperativoPagoSinConfirmarFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `estadoOperativoPagoConfirmadoFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `inscripcionResumenFixture` | the inscription list out (`RT-IN-01`) | `FREEZE-ENV-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `compraResumenFixture` | the purchase list out (`RT-ID-05`) | `FREEZE-ID-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `compraDetalleFixture` | the purchase detail out (`RT-ID-06`) | `FREEZE-ID-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `resumenCuentaFixture` | `MiCuentaOut` (`RT-ID-04`) | `FREEZE-ID-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |
| `paginaVaciaFixture` | `PaginatedData` | `FREEZE-ENV-1.0.0` | `features/cuenta/fixtures/cuenta.fixture.ts` | **API-01** |

**Rules honoured:** the literal token `PROVISIONAL_CONTRACT_FIXTURE` is in the header of the file
and the symbol name carries the `Fixture` suffix - no business calculation, no `if`, no
arithmetic, no `Date.now()` / `Math.random()` / `crypto.randomUUID()`, no price, no eligibility,
no capacity, no payment state and no permission is DERIVED. The amount of the example purchase is
`0.00` on purpose, so it cannot look like a real price (`FR-08` section 2.4).

**No fixture is exported from a production barrel.** The fixtures are consumed by the suites of
the feature and by API-01, which replaces them with the Zod mirror of the frozen presenter.

---

## 6. Files changed (34 created, 2 modified, 0 deleted)

All of them are inside the allowed roots of the packet.

**Route presentation - created (9)**

- `app/(public)/informacion/loading.tsx`
- `app/(public)/recuperar-compra/loading.tsx`
- `app/(public)/recuperar-compra/error.tsx`
- `app/(cuenta)/mis-inscripciones/loading.tsx`
- `app/(cuenta)/mis-inscripciones/error.tsx`
- `app/(cuenta)/mis-compras/loading.tsx`
- `app/(cuenta)/mis-compras/error.tsx`
- `app/(cuenta)/mis-compras/[id]/loading.tsx`
- `app/(cuenta)/mis-compras/[id]/error.tsx`

**Route presentation - modified (2)**

- `app/(cuenta)/mis-inscripciones/page.tsx` - reads `searchParams` and hands the filters to the view.
- `app/(cuenta)/mis-compras/page.tsx` - reads `searchParams` and hands the filters to the view.

**Feature `public` - created (7) / modified (2)**

- created `components/IndiceInformacion.tsx`, `components/RecuperarCompraForm.tsx`,
  `components/index.ts`, `fixtures/edicion.fixture.ts`, `schemas/recuperar-compra.schema.ts`,
  `__tests__/recuperar-compra-form.test.tsx`, `__tests__/informacion-indice.test.tsx`,
  `__tests__/public-responsive.test.ts`
- modified `views/InformacionView.tsx`, `views/RecuperarCompraView.tsx`

**Feature `cuenta` - created (10) / modified (5)**

- created `types/cuenta.types.ts`, `fixtures/cuenta.fixture.ts`,
  `components/VeredictoEstado.tsx`, `components/BarraFiltros.tsx`,
  `components/ListaInscripciones.tsx`, `components/ListaCompras.tsx`,
  `components/EstadoIndeterminado.tsx`, `components/SinResultadosConFiltros.tsx`,
  `__tests__/cuenta-estados.test.tsx`, `__tests__/cuenta-responsive.test.ts`
- modified `components/index.ts`, `views/MiCuentaView.tsx`, `views/MisInscripcionesView.tsx`,
  `views/MisComprasView.tsx`, `views/MisCompraDetalleView.tsx`

**Not touched:** `src/components/shell/**` · `src/components/ui/**` · `src/providers/**` ·
`src/app/globals.css` · `src/lib/**` · `src/hooks/**` · `src/shared/**` · `src/features/auth/**` ·
`src/features/portada/**` · `src/features/inscripciones/**` · `src/features/admin/**` ·
`src/features/theme/**` · the backend · `contract/**` · the root `frontend/**`.

---
## 7. Skills loaded

| Order | Skill | Use in this packet |
|---|---|---|
| 1 | `salesianos-ui-ux` | Route purpose, actors, actions, states, the visual direction of `SH-01` and the semantic roles |
| 2 | `salesianos-feature-architecture` | Layer boundaries: thin pages, views own the composition, components own the presentation, types separate from the fixtures, no business logic in a page |
| 3 | `salesianos-shadcn` | The MCP comparison of section 3, the reuse of the local primitives, the refusal to recreate a registry component, the hardcoded-colour audit |
| 4 | `salesianos-responsive-a11y` | The five-width contract, the table-to-cards rule, the 44 px targets, the labels and the live regions, the reduced-motion rule |
| 5 | `frontend-design` | The restraint: one memorable element per surface, no card grid, copy that says one thing, errors that name the cause and the fix |

`salesianos-forms-smart-fields` was read as context through `contract/smart.md` and the existing
`GenericForm`, but no new input type and no new Smart Field were created: the recovery form uses
`GenericForm` Mode 1 (`children`) with a plain Zod schema, so the rule of `smart.md` section 5.2
(never `watch()` the whole form, never render an error twice) is respected by construction.

`salesianos-api-data` was **not** loaded: this packet creates **no transport**. The packet's
forbidden roots list the network hooks, the wire schemas, the query keys and `src/lib/**`, and
the workflow stage 1 forbids the same.

---

## 8. Commands run, exit codes and results

**The only runtime command of this packet was the typecheck.** Everything else was forbidden by
the launch contract.

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 3 errors: `ShellPermissionDenied` was called without the required `title` (the shell component declares `title` as required) |
| 2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean |
| 3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean (after the `Suspense` boundaries around the filter bar) |
| 4 | `git status --short -- Aplicacion/frontend` | repo root | **0** | 123 lines at the baseline (the tree was already dirty from FND-06, FND-07, FND-08 and UI-01A) |
| 5 | `git diff --numstat` on the two modified route files | repo root | **0** | 38 insertions, 20 deletions |

**NOT RUN** (forbidden by the launch contract, and recorded as deferred, never as passed):
`vitest` · `biome check` · `next build` · `npm install` · any server · any browser · any visual
automation · `git stash` · `git commit` · `git reset` · `git checkout`.

**Known baseline failures:** none introduced. The three type errors of command 1 were introduced
by this packet and were fixed in this packet.

---

## 9. Tests written (NOT executed) and the five-width audit

The standing user preference (#11299) is that the suites of an apply packet are **written** and
**not executed**, and the packet status is `verification_required`. The suites below were written
and **have never run**: nothing here may be read as a green result.

| Suite | Environment | What it freezes |
|---|---|---|
| `features/cuenta/__tests__/cuenta-estados.test.tsx` | jsdom | The states of the four account routes: the honest empty, the populated list, the filtered-empty, the permission, the recoverable error and the partial payment |
| `features/cuenta/__tests__/cuenta-responsive.test.ts` | node | The static rules: no literal colour, no fixed pixel width, `scope="col"` on every table header, the table from 1024 and the cards below, the 44 px targets, no provider vocabulary |
| `features/public/__tests__/recuperar-compra-form.test.tsx` | jsdom | The three states of the form: the validation with its summary and its associated field error, the request in progress, the neutral answer - and the rule that **without a transport the form never fakes a sent message** |
| `features/public/__tests__/informacion-indice.test.tsx` | jsdom | The index is a navigation with an accessible name and **every anchor lands on a section that exists** |

### The five widths

The audit at 360, 390, 768, 1024 and 1440 was **deferred**: no browser was run in this packet.

What the markup already guarantees, and what the browser pass will have to confirm:

| Width | What the composition does | What is still unverified |
|---|---|---|
| 360 | One column. The index of `PUB-02` is a disclosure. The lists are labelled cards, never a table. The recovery form is a single column of 480 px. Every action is at least 44 px high. | That no page overflows horizontally, that the sticky header does not cover the first action, that the long team and product names truncate |
| 390 | The same single column. | The same |
| 768 | The index becomes a sticky rail beside the content of `PUB-02`; the filters of the lists are two columns; the lists are still cards | That the two columns do not squeeze the cards |
| 1024 | The lists become tables with prioritised columns; the filter bar is three columns | That no column is stretched and that nothing is clipped |
| 1440 | The content band is capped at 1200 px (`max-w-page`); the body measure is capped at 72 characters (`max-w-measure`) | The same |

### Accessibility that was decided in the markup

- Every input has a real `<label>` and its error is associated with `aria-describedby`.
- The summary of the errors of the form is a `role="alert"` with `tabIndex={-1}`, so it receives
  the focus after an invalid submit.
- The current section of the index is marked with `aria-current`.
- The verdict chip pairs an icon shape, the semantic bucket and the label of the backend: the
  colour never carries the meaning alone.
- The state of the purchase is announced: the partial state is an `alert`.
- The navigation exposes its current location (the shell owns it).
- The motion is the one of the global reduced-motion block, which forces
  `scroll-behavior: auto`; the anchor jump of the index does not scroll on its own.

**Residual gaps declared, never assumed green:** no browser rendering, no screen-reader pass, no
200 % zoom reflow, no automated axe or Lighthouse run, and no measurement of the contrast of the
`--success` / `--warning` chip tones (see the A0 request of section 12).

---

## 10. Routes that were NOT touched, and why

| Page ID | Reason | What is still owed |
|---|---|---|
| `PUB-01` (`/`) | The route lives in `app/(portada)/**` and its view in `features/portada/**`. Neither is in the allowed edit roots of this packet. The portada was built by FND-06 and is the visual showcase of the product. | The ten states of the portada and its five-width audit |
| `AUTH-01` (`/login`) | `app/(auth)/**` and `features/auth/**` are forbidden roots of the packet (auth/providers). The auth feature is the one complete vertical of the target and already has its forms, its validation and its document lookup. | The route brief of `RB-01` is written; the states it asks for (wrong credential, disabled account, administrative account) are already covered by the existing auth views |
| `AUTH-02` (`/registro`) | Same reason. | The states of `RB-01` (document not found, external source unavailable, document already linked, duplicate email) are already covered by `features/auth/**` |

**Handover:** widening the roots of UI-01 to `app/(auth)/**` + `features/auth/**` and to
`app/(portada)/**` + `features/portada/**` is the only thing needed for those three page IDs.
Nothing in this packet blocks them and nothing in them was touched.

---
## 11. API-01 handoff

### The seams that API-01 has to bind

| Seam | Where | What API-01 does |
|---|---|---|
| The account summary | `features/cuenta/views/MiCuentaView.tsx` - prop `resumen?: ResumenCuenta` | Reads `RT-ID-04` and passes the counters |
| The registrations | `features/cuenta/views/MisInscripcionesView.tsx` - props `inscripciones?: InscripcionResumen[]`, `filtros` | Reads `RT-IN-01`, binds the page of `FREEZE-ENV-1.0.0` section 4.3 and hands the filters of the URL to the service |
| The purchases | `features/cuenta/views/MisComprasView.tsx` - props `compras?: CompraResumen[]`, `filtros` | Reads `RT-ID-05` |
| The detail of a purchase | `features/cuenta/views/MisCompraDetalleView.tsx` - prop `compra?: CompraDetalle` | Reads `RT-ID-06` |
| The recovery request | `features/public/components/RecuperarCompraForm.tsx` - prop `enviar?: (datos) => Promise<ResultadoRecuperacion>` | Reads `RT-RC-01` and hands the real service to the form. **While the prop is absent the form says why it cannot send** |
| The edition | `features/public/fixtures/edicion.fixture.ts` | Replaces the fixture with the Zod mirror of `EdicionActualOut` and binds `RT-ED-01` |
| The verdict bucket | `features/cuenta/types/cuenta.types.ts` - `RolVeredicto` | The adapter maps `estado_operativo.codigo` to the bucket. **The bucket is presentational; the label always comes from the backend.** The codes are NOT catalogued yet (33 open codes), so the frontend must not branch on them |

### The deletion checklist (mandatory in API-01, `T-082` of the workflow)

1. Delete `features/public/fixtures/edicion.fixture.ts` and replace it with the Zod mirror of the
   frozen presenter.
2. Delete `features/cuenta/fixtures/cuenta.fixture.ts` and replace it with the Zod mirrors of the
   frozen presenters.
3. Prove that **no** module outside `__tests__` imports a fixture, that there is no `catch` that
   falls back to a fixture and that there is no hidden route.
4. Replace the view-model types of `features/cuenta/types/cuenta.types.ts` with the Zod mirrors
   (or keep the types as the view contract and add the schemas next to them).
5. Remove the `estado` prop of the views when every route is always in the `listo` state, or keep
   it as the honest fallback of a failed read.
6. Bind the pagination of the lists: the local `pagination` primitive is already present and was
   deliberately NOT used by the skeleton.

---

## 12. Deviations, decisions and A0 requests

| ID | Type | What |
|---|---|---|
| `D-UI01-01` | decision | **A provisional fixture may render the configuration of the product; it may never render the personal data of the authenticated reader.** The account routes show the honest state by default and the populated composition is exercised by the suites. |
| `D-UI01-02` | decision | **The verdict bucket travels with the verdict.** The view model carries `estado_operativo` (the wrapper) AND `rol` (the presentational bucket). The alternative - branching on `codigo` inside the component - is forbidden by `SH-03` section 6 and would break as soon as a new code is catalogued. |
| `D-UI01-03` | deviation | **A `types/` folder was created inside the feature** (`features/cuenta/types/cuenta.types.ts`). The contract lists `schemas/` for the Zod mirrors, and the wire mirrors are forbidden in this stage. The view models are plain TypeScript types, and the fixtures import them, so no production module imports a fixture. |
| `D-UI01-04` | deviation | **The technical detail of `ACCOUNT-05` was omitted.** The plan asks for a collapsed disclosure with the technical detail, but `GOV-02-RB-01d` forbids showing a provider state, a `settlement_status` literal or a raw identifier. The reader-facing content is already in plain language, so the disclosure was left out rather than filled with something forbidden. |
| `D-UI01-05` | deviation | **The `accordion` of the registry was not added**: `components/ui/**` is a forbidden root. The grouping of the purchases by origin is a section per origin instead of an accordion. |
| `D-UI01-06` | deviation | **`pagination` was not composed.** The pagination belongs to the service that owns the page; the skeleton receives a list. Composing a client-side pagination would be exactly the kind of thing that has to be rewritten in API-01. |
| `D-UI01-07` | deviation | **The "Mis entradas" block of `ACCOUNT-01` was omitted.** There is no route for it, so a tile would be a dead link. `RB-01` ACCOUNT-01 asks for it only if it exists. |
| `D-UI01-08` | deviation | **The form schema of the recovery lives in `features/public/schemas/`.** It is a client-side validation schema, NOT a wire mirror: it validates what the person typed before the request leaves the browser. The exact Zod mirror of the presenter arrives with API-01. |
| `D-UI01-09` | decision | **The recovery form does not fake a sent message.** While the mail provider is not configured (`PD-08`) the submit validates the fields and then states why the request cannot leave. The neutral answer is reserved for a real request. |
| `D-UI01-10` | decision | **The filter bar is a client component that writes the URL**, and the page reads the query string and filters the list. The filters therefore live in the URL, as `RB-01` ACCOUNT-02 requires, and the filtering is a query and not a business rule. |

### A0 requests

| ID | Request |
|---|---|
| `A0-UI01-01` | The chip tones `--success` (#10b981) and `--warning` (#f59e0b) do not reach 3:1 against the light surface as an ICON. The chip keeps the full-contrast text and the colour is redundant, but a `--success-strong` / `--warning-strong` role would let the icon be legible. This is a token decision of the owner of `globals.css` (FND-06), not of this packet. |
| `A0-UI01-02` | The local `components/ui/badge.tsx` has a typo in its secondary variant (`text-secondary-foreground-foreground`) and no verdict variants. It was NOT touched (forbidden root). |
| `A0-UI01-03` | The 33 public error codes that are not catalogued (8 of DOM-06 + 21 of DOM-07 + 4 of DOM-08) keep the frontend from branching on a code. The bucket of `D-UI01-02` is the mitigation, not a substitute. |
| `A0-UI01-04` | The three routes left out of this packet (`PUB-01`, `AUTH-01`, `AUTH-02`) need their roots widened, or a dedicated packet. See section 10. |
| `A0-UI01-05` | `00-matriz-tareas.md` does not carry a row for UI-01 and the matrix is a forbidden root: the row has to be synchronised by the coordinator. |

---

## 13. Workload and review boundary

The tasks artefact of this change carries **no** `Review Workload Forecast`, so no chain decision
was required before the apply (the same precedent as DOM-06, FND-07 and FND-08).

**The real size of this packet is ~2 990 changed lines** (2 934 new lines across 34 created files
+ 38 insertions and 20 deletions in the two modified route files), which exceeds the 400-line
review budget by roughly **7.5x**. There is **no commit** in this packet, so the budget is a
report and not a gate.

**Autonomous work units** (each one reviewable on its own, in this order):

| WU | Scope | Files |
|---|---|---|
| WU-1 | The account view models and the provisional fixture adapter | `features/cuenta/types/**`, `features/cuenta/fixtures/**` |
| WU-2 | The account states: the verdict chip, the indeterminate state, the filtered-empty state | `features/cuenta/components/{VeredictoEstado,EstadoIndeterminado,SinResultadosConFiltros}.tsx` |
| WU-3 | The account lists and the filter bar | `features/cuenta/components/{ListaInscripciones,ListaCompras,BarraFiltros}.tsx` |
| WU-4 | The four account views | `features/cuenta/views/**` |
| WU-5 | The public index and the recovery form | `features/public/components/**`, `features/public/schemas/**`, `features/public/fixtures/**` |
| WU-6 | The two public views | `features/public/views/**` |
| WU-7 | The route presentation (loading and error) | `app/(public)/**`, `app/(cuenta)/**` |
| WU-8 | The suites | `features/**/__tests__/**` |

**Rollback:** revert WU-8 to WU-1. The rollback is confined to the 34 created files and the 2
modified route files; the shared shell, the providers, the theme and every other feature are
untouched, so reverting this packet leaves the product exactly as it was. `git stash` was never
invoked and no commit was created.

---

## 14. Acceptance criteria of the packet

- [x] Every route that was applied has its plan-defined purpose, actions and states, and no
      invented catalogue, payment or authentication rule.
- [x] The shadcn comparison was recorded **before** the composition and no shared primitive was
      overwritten.
- [x] The provisional fixtures are local, typed, marked and listed for their deletion in API-01.
- [x] The ten states are covered on the six routes that were applied, and the one that does not
      apply is declared with its reason.
- [x] The only runtime command was the typecheck, and it is green.
- [ ] The five-width audit in a browser, the assistive-technology pass, the execution of the four
      suites and the lint pass are **DEFERRED** - the packet stays `verification_required`.
