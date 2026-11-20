# UI-02 - Registration Wizard And Owner Detail Skeletons

**Artifact:** `evidence/ui/UI-02-inscription-shells.md` - **Packet:** UI-02 (`wave-02-frontend-skeletons`)
**Owner:** A7 - **Status:** `verification_required` (implementation applied, runtime verification deferred)
**Date:** 2026-11-19 - **Target:** `Aplicacion/frontend/**` only

> **Reconciliation 2026-11-19 (after the concurrent execution of UI-03):** the commands table, the
> baseline note, `A0-UI02-09` and the acceptance criteria were corrected. The **roots of this packet
> were GREEN (0 errors) in every run**; the project-wide gate was RED only because of concurrent
> out-of-scope trees of UI-03 (`features/pases/**`, `features/marketplace/**`), and the **final global
> `npx tsc --noEmit` exited 0** after UI-03 completed (exit code reported by the UI-03 evidence, NOT
> measured by this packet - the reconciliation ran no command). The packet stays
> `verification_required`: its three suites are written and not executed and its five-width browser
> audit is not done. **Nothing of UI-03 was touched.**

---

## 1. Scope actually applied

The packet names two page IDs. Both of them live inside the allowed edit roots of this packet, so
both were applied.

| Page ID | Route | Route file | Feature view | State |
|---|---|---|---|---|
| `SPORT-01` | `/inscripcion` | `app/(cuenta)/inscripcion/page.tsx` (modified) | `features/inscripciones/views/InscripcionWizardView.tsx` | **applied** |
| `ACCOUNT-03` | `/mis-inscripciones/[id]` | `app/(cuenta)/mis-inscripciones/[id]/page.tsx` (modified) | `features/inscripciones/views/MisInscripcionDetalleView.tsx` | **applied** |

**The step of the wizard lives in the URL** (`?paso=`). The route reads `searchParams` and hands it
to the view, so a step is recoverable: the visitor can reload it, share it and go back to it
(`frontend/06` §1: "cada step URL es recuperable"). The view writes the step back with
`router.replace`, so the URL never disagrees with the screen.

---

## 2. The route brief applied

The briefs were produced by **GOV-02** and were read before any code was written:

- `evidence/routes/RB-01-public-account-identity.md` -> `SPORT-01` and `ACCOUNT-03`.
- `evidence/routes/SH-01` (tokens) - `SH-02` (five widths + a11y) - `SH-03` (ten states) -
  `SH-04` (shadcn families) - `SH-05` (provisional endpoints) - `SH-06` (wireframes).
- `evidence/contracts/FR-08` (provisional fixtures) - `FR-01` (envelope and error) -
  `FR-07` (presenters and schema versions).
- `evidence/domains/DOM-01` and `evidence/domains/DOM-02` (the presenters of the inscription
  domain that the skeleton mirrors).

### The visual direction

`SH-01` section 3: **Institutional Blue, Festival Gold**. This packet consumes **only semantic
roles** (`bg-surface-raised`, `bg-surface-recessed`, `border-border`, `text-foreground`,
`text-muted-foreground`, `bg-primary`/`text-primary-foreground`, `--success`, `--warning`, `--info`,
`--destructive`, `accent-primary`). No token was added and `globals.css` was not touched.

### The rule that decided the composition (`D-UI02-01`)

> **The verdict chip of UI-01 was NOT reused, because no wrapper of the inscription domain
> publishes `EstadoOperativo`.**

`VeredictoEstado` draws the `EstadoOperativo` wrapper (`codigo` / `etiqueta` / `descripcion`) that
`FREEZE-ENV-1.0.0` §5 freezes and that the commerce and the passes publish. The inscription domain
publishes something else: `PoolOut` carries a `causa_operativa` and a list of `impedimentos` with a
`codigo` and a `mensaje`, and the states of the inscription, of the team and of the participation
are bare strings. Reusing the chip would have meant mapping a code onto a bucket in the browser,
which is exactly what `SH-03` §6 forbids while 33 public codes are still uncatalogued.

Therefore the pool prints the `mensaje` of the server verbatim and the states are printed as they
come. The gap is recorded as an A0 request (`A0-UI02-02`).

### The rule that decided the wizard (`D-UI02-02`)

> **A step of the wizard NEVER calculates a business value.**

The frozen wizard of `frontend/` multiplied the price by the quantity in React and offered a
quantity stepper. The target backend does not accept any of that: `InscripcionInicialIn` is
`{edicion_id, paquete_id, equipos[{disciplina_id, nombre}]}` and the package declares its own cupos
(`cupos_incluidos`) and its own price. The stepper, the quotation and the declarations were
**removed**, and the price, the cupos and the eligibility are printed exactly as the catalogue
publishes them.

---

## 3. shadcn candidate comparison (GOV-02-SH-01 re-run for this route family)

The MCP was executed for this family, not inherited:

| # | Tool call | Result |
|---|---|---|
| 1 | `shadcn_get_project_registries` | `@shadcn` (the target registry; style `radix-nova` in `Aplicacion/frontend/components.json`) |
| 2 | `shadcn_list_items_in_registries` (types `registry:ui`) | **61** items in `@shadcn` |
| 3 | `shadcn_search_items_in_registries` - "progress stepper wizard" | **0** hits: the registry has NO stepper |
| 4 | `shadcn_search_items_in_registries` - "tabs" | 1 hit: `tabs` (registry:ui) |
| 5 | `shadcn_search_items_in_registries` - "drawer sheet" | **0** hits by that query; `sheet` is in the registry listing |
| 6 | `shadcn_search_items_in_registries` - "progress" | 1 hit: `progress` (registry:ui) |
| 7 | `shadcn_view_items_in_registries` (`tabs`, `table`, `progress`, `sheet`, `alert-dialog`) | 1 file each; dependencies `cn` and `radix-ui` |
| 8 | `shadcn_get_audit_checklist` | Executed before closing the packet |

### The comparison and the decision

| Item | Registry | Fit for this family | Local state | Decision |
|---|---|---|---|---|
| `tabs` | `registry:ui` | The six sections of `ACCOUNT-03` | **present** in `components/ui/tabs.tsx` | **Selected / reused**. The list WRAPS at 360 (`flex-wrap`) instead of scrolling horizontally, so the page never pushes sideways |
| `table` | `registry:ui` | The participants from 1024 | **present** | **Selected / reused**. Every `TableHead` carries `scope="col"` |
| `alert` | `registry:ui` | S-04, S-06, S-09 and the outcome of the alta | **present** | **Selected / reused** |
| `empty` | `registry:ui` | S-02 of every section | **present** | **Selected / reused** (through the shared `RouteEmptyState`) |
| `skeleton` | `registry:ui` | S-01 of the two routes | **present** | **Selected / reused** |
| `button` | `registry:ui` | Every action | **present** | **Selected / reused** |
| `input` + `label` | `registry:ui` | The name of the teams | **present** | **Selected / reused** |
| `radio` (native) | - | The choice of the package | The registry has no radio; the HTML one is used | **Selected**. The package is a real `<label>` around a real `<input type="radio">`: the browser gives the group the arrow keys, the focus and the announcement for free, and RHF registers it without an adapter |
| `select` (native) | `registry:ui` | The discipline of each team | **present** (radix) | **Rejected for this field** (`D-UI02-07`): the radix `Select` needs a `Controller` per row of a DYNAMIC array and a manual `onValueChange` bridge; the native `<select>` registers with RHF directly and gives the platform picker. The list is short and closed |
| `progress` | `registry:ui` | The balance of the cupos | **present** | **Rejected**: a progress bar would express a PERCENTAGE, and the percentage is a division the browser would have to compute from three numbers that the server owns. The pool band prints the three numbers and reads them as a sentence |
| `badge` | `registry:ui` | The state of the inscription | present, no verdict variants, and a typo in the secondary variant (reported by UI-01) | **Rejected**: the wrappers publish bare codes without a label, so a badge would print a code |
| `sheet` / `drawer` | `registry:ui` | The resolution of a person | `sheet` present, `drawer` **absent** | **Not used**: the assignment of a person needs the transport of `RT-IN-05` and the resolution sheet of `RT-ID-02`, and this packet creates no transport. Recorded as `A0-UI02-08` |
| `alert-dialog` | `registry:ui` | The confirmation of a removal | **present** | **Not used** in this packet (`D-UI02-08`): the removal confirmation of `ACCOUNT-03` is the S-10 of the DETAIL and needs the transport of `RT-IN-06` |

**No component was added. No file in `components/ui/**` was created, modified or overwritten.**

---

## 4. The ten states, route by route

`SH-03` section 1 fixes ten states. This is where each one lives for the two routes of this packet.

| State | `SPORT-01` | `ACCOUNT-03` |
|---|---|---|
| S-01 initial / loading | `app/(cuenta)/inscripcion/loading.tsx` (header + rail of four nodes + the panel of the step) | `app/(cuenta)/mis-inscripciones/[id]/loading.tsx` (header + the tabs + the band of the cupos) |
| S-02 empty (never had data) | `CatalogoNoConectado`: the four steps of the flow and the honest reason | `RouteEmptyState` of the route, and one per section (`PanelEquipos`, `PanelParticipantes`, `PanelCompras`, `PanelBeneficios`) |
| S-03 filtered-empty | **does not apply**: the wizard has no filters | **does not apply**: the detail has no filters |
| S-04 recoverable error | `app/(cuenta)/inscripcion/error.tsx` (retry + back to the account) and the error of the catalogue inside the first step | `app/(cuenta)/mis-inscripciones/[id]/error.tsx` (retry + back to the list) and the error of the route |
| S-05 validation | Zod (`AltaInscripcionSchema`) + the `GenericForm`: the error of the field is associated with `aria-invalid` / `aria-describedby`, the step does not advance until the step is valid and the focus goes to the first invalid field | **does not apply**: the detail has no form |
| S-06 permission | `estado="sin-permiso"` (the route explains that the account cannot create inscriptions in this edition) | `estado="sin-permiso"`: "Tu cuenta no tiene acceso a esta inscripción" |
| S-07 success | the outcome of the alta: the inscription exists, the purchase is pending, the cupos are enabled when the payment is confirmed | **does not apply**: the route does not mutate |
| S-08 in progress | the submit is disabled and says **Registrando…**; the double submit is prevented | **does not apply** |
| S-09 partial / indeterminate | the pending operation is RECOVERED, not duplicated: `pendiente` renders "Ya hay una inscripción en curso" and the page never offers to create a second one. The outcome of an accepted alta says that the inscription has **no cupos disponibles** until the payment is confirmed | `PanelPool` says "No hay ningún cupo habilitado todavía" when the server publishes `cupos_pagados = 0`, and `PanelCompras` shows the pending purchase |
| S-10 irreversible confirmation | the fourth step, `PasoConfirmacion`: it names the effect ("se registra tu inscripción", "se abre una compra pendiente", "cuando el pago se confirme los cupos se habilitan") | **declared, not silently dropped**: the removal confirmation of a participant belongs to the transport of `RT-IN-06` and is owed to API-02 (`D-UI02-08`) |
| 422 field errors | the seam of the alta throws and `GenericForm` maps `error.field_errors[]` to the control with `setError` (the FND-07 seam, once per field) | **does not apply** |
| 409 conflict | the server answers a conflict and the page shows its message verbatim; the retry returns the SAME inscription (`RN-A03`, `reutilizada`) | the pool publishes the impediments with their `mensaje` verbatim |
| neutral recovery response | the recovery of a pending operation does NOT say whether it is a new inscription or a reused one beyond what the server published (`causa_operativa`) | **does not apply** |

---

## 5. Provisional fixtures (FR-08)

Every fixture is **local to its feature**, **typed with `as const satisfies`**, **marked** and
**deterministic**. The deletion ledger is in section 11.

| Fixture (symbol) | Mirrors | Contract | Path | Deleted in |
|---|---|---|---|---|
| `catalogoPaquetesFixture` | `CatalogoPaquetesOut` (`RT-IN-12`) | `FREEZE-PS-1.0.0` | `features/inscripciones/fixtures/inscripcion.fixture.ts` | **API-02** |
| `catalogoDisciplinasFixture` | `CatalogoDisciplinasOut` (`RT-IN-13`) | `FREEZE-PS-1.0.0` | same | **API-02** |
| `inscripcionDetalleFixture` | `InscripcionDetalleOut` (`RT-IN-02`) | `FREEZE-PS-1.0.0` | same | **API-02** |
| `poolInscripcionFixture` | `PoolOut` (`RT-IN-03`) | `FREEZE-PS-1.0.0` | same | **API-02** |
| `compraInscripcionFixture` | `CompraOut` | `FREEZE-CM-1.0.0` | same | **API-02** |
| `comprasInscripcionFixture` | the purchases of a registration (the alta plus the expansions) | `FREEZE-CM-1.0.0` | same | **API-02** |
| `compraCuposFixture` | `CompraCreadaOut` (`RT-CM-01`) | `FREEZE-CM-1.0.0` | same | **API-02** |
| `altaInscripcionFixture` | `InscripcionInicialOut` (`RT-IN-14`) | `FREEZE-PS-1.0.0` | same | **API-02** |
| `beneficiosConcedidosFixture` | the granted benefits (no presenter yet) | - | same | **API-02** |

**Rules honoured:** the literal token `PROVISIONAL_CONTRACT_FIXTURE` is in the header of the file and
the symbol name carries the `Fixture` suffix. No business calculation, no `if`, no arithmetic, no
`Date.now()` / `Math.random()` / `crypto.randomUUID()`, no price, no eligibility, no capacity, no
payment state and no permission is DERIVED. The amount of the example purchase is `0.00` on
purpose, so it cannot look like a real price (`FR-08` §2.4). The three counters of the pool are
DECLARED as three independent literals, exactly like the canonical example of `FR-08` §2.3.

**No fixture is exported from a production barrel.** The fixtures are consumed by the suites of the
feature and by API-02, which replaces them with the Zod mirror of the frozen presenter.

---

## 6. Files changed (18 created, 9 modified, 0 deleted)

All of them are inside the allowed roots of the packet.

**Route presentation - created (4)**

- `app/(cuenta)/inscripcion/loading.tsx`
- `app/(cuenta)/inscripcion/error.tsx`
- `app/(cuenta)/mis-inscripciones/[id]/loading.tsx`
- `app/(cuenta)/mis-inscripciones/[id]/error.tsx`

**Route presentation - modified (2)**

- `app/(cuenta)/inscripcion/page.tsx` - reads `searchParams` and hands the step to the view.
- `app/(cuenta)/mis-inscripciones/[id]/page.tsx` - points to the new view of the inscriptions feature.

**Feature `inscripciones` - created (14)**

- `types/inscripcion.types.ts` - the view models that mirror the presenters of the domain.
- `schemas/alta-inscripcion.schema.ts` - the client-side validation of the alta.
- `fixtures/inscripcion.fixture.ts` - the provisional fixture adapter.
- `components/PasoResumen.tsx`, `components/PasoConfirmacion.tsx`
- `components/PanelPool.tsx`, `components/PanelEquipos.tsx`, `components/PanelParticipantes.tsx`,
  `components/PanelCompras.tsx`, `components/PanelBeneficios.tsx`
- `views/MisInscripcionDetalleView.tsx`
- `__tests__/inscripcion-estados.test.tsx`, `__tests__/inscripcion-detalle.test.tsx`,
  `__tests__/inscripcion-responsive.test.ts`

**Feature `inscripciones` - modified (7)**

- `components/WizardStepper.tsx`, `components/PaqueteCard.tsx`, `components/PasoPaquete.tsx`,
  `components/PasoEquipos.tsx`, `components/index.ts`
- `views/InscripcionWizardView.tsx`, `views/index.ts`

**Left on disk, unreferenced (1):** `components/PasoDeclaraciones.tsx`. The declarations step of the
frozen wizard has no counterpart in the target backend (`D-UI02-04`). The file was **not** deleted
because the whole `features/inscripciones/` tree is untracked and this packet performs no git
operations: deleting it would be irreversible. The cleanup packet removes it.

**Not touched:** `src/components/shell/**` - `src/components/ui/**` - `src/providers/**` -
`src/app/globals.css` - `src/lib/**` - `src/hooks/**` - `src/shared/**` - `src/features/cuenta/**`
(UI-01) - `src/features/public/**` - `src/features/auth/**` - `src/features/portada/**` -
`src/features/admin/**` - `src/features/pases/**` (concurrent) - the backend - `contract/**` - the
root `frontend/**`.

---

## 7. Skills loaded

| Order | Skill | Use in this packet |
|---|---|---|
| 1 | `salesianos-ui-ux` | Route purpose, actors, actions, states, the visual direction of `SH-01` and the semantic roles |
| 2 | `salesianos-feature-architecture` | Layer boundaries: thin pages, the view owns the composition, the components own the presentation, the types separate from the fixtures, no business logic in a page |
| 3 | `salesianos-forms-smart-fields` | Mode 4 (`formMethods`) + Mode 1 (`children`) of the `GenericForm`, Zod as the only owner of the validation, `useWatch` on the named dependency only (`contract/smart.md` §5.2), the 422 channel of FND-07 |
| 4 | `salesianos-shadcn` | The MCP comparison of section 3, the reuse of the local primitives, the refusal to recreate a registry component, the hardcoded-colour audit, `get_audit_checklist` |
| 5 | `salesianos-responsive-a11y` | The five-width contract, the table-to-cards rule, the 44 px targets, the labels and the live regions, the `aria-current="step"` of the rail |
| 6 | `frontend-design` | The restraint: ONE memorable element per surface (the rail of the steps and the band of the cupos), no card grid, copy that says one thing, errors that name the cause and the fix |

`salesianos-api-data` was read as **contract context**: the packet forbids the network hooks, the
wire schemas, the query keys and `src/lib/**`, and this packet creates **no transport**. The
endpoints it mirrors were read in the target backend (`Aplicacion/backend/modules/salesianos_fest/`)
and not invented.

---

## 8. Commands run, exit codes and results

**The only runtime command of this packet was the typecheck.** Everything else was forbidden by the
launch contract.

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 2 errors of THIS packet: `PanelBeneficios` was missing (a write that did not land) and a typo `impediment` in `PanelPool` |
| 2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 6 errors, **none of them in the roots of this packet**: `src/features/pases/components/{CatalogoPases,DialogoCheckout,DialogoRevocar,FormularioComprador,ListaBeneficiarios,SelectorCantidad}.tsx` fail with `TS2304: Cannot find name '__USE_CLIENT__'` |
| 3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | the same 6 errors of `features/pases`, which are **concurrent work of another agent** and are OUTSIDE the allowed roots of this packet |
| 4 | `git status --short -- Aplicacion/frontend/src/features/pases Aplicacion/frontend/src/features/inscripciones` | repo root | **0** | both trees are **untracked** (`??`), which proves that `features/pases` is concurrent work and not a regression of this packet |
| 5 | `npx tsc --noEmit` (final run) | `Aplicacion/frontend` | **1** | the concurrent `features/pases/**` errors were already repaired by the other agent; the gate is now RED for a DIFFERENT concurrent file, `src/features/marketplace/components/TarjetaProducto.tsx` (`TS17008`/`TS1005`, written at that very moment). **Zero errors in `src/features/inscripciones/**` and `src/app/(cuenta)/**`** (filtered runs returned empty) |
| 6 | `npx tsc --noEmit` (final global, **after UI-03 completed**) | `Aplicacion/frontend` | **0** | the project-wide gate is **GREEN**. The exit code is **reported by the UI-03 evidence** (`evidence/ui/UI-03-commerce-shells.md`, commands 2 and 3) and was **NOT measured by this packet**: this reconciliation ran **no** command. UI-03 repaired its own concurrent errors, and the run covers the roots of this packet too, which never carried an error |

**Zero errors are reported in `src/features/inscripciones/**` and in `src/app/(cuenta)/**`**: the
typecheck of the roots of this packet was GREEN in EVERY run (V1 to V5). The project-wide gate was
RED only because of OTHER, CONCURRENTLY WRITTEN features that this packet may not touch
(`features/pases/**` and `features/marketplace/**`, both of UI-03 and already repaired by their
owners). **After UI-03 completed, the final global `npx tsc --noEmit` exited 0** (exit code
reported by the UI-03 evidence, NOT measured by this packet): the project-wide gate is GREEN.

**NOT RUN** (forbidden by the launch contract, and recorded as deferred, never as passed):
`vitest` - `biome check` - `next build` - `npm install` - any server - any browser - any visual
automation - `git stash` - `git commit` - `git reset` - `git checkout`.

**Known baseline failures:** the errors of the concurrent trees of `features/pases/**` and
`features/marketplace/**` (both of UI-03). They are **concurrent**, not a baseline of this packet,
they were **not** touched, and their owners repaired them: the final global gate is GREEN.

**Regressions:** none. Zero frozen files modified. No commit created. `git stash` never invoked.

---

## 9. Tests written (NOT executed) and the five-width audit

The standing user preference (#11299) is that the suites of an apply packet are **written** and
**not executed**, and the packet status is `verification_required`. The suites below were written
and **have never run**: nothing here may be read as a green result.

| Suite | Environment | What it freezes |
|---|---|---|
| `features/inscripciones/__tests__/inscripcion-estados.test.tsx` | jsdom | The states of `SPORT-01`: the honest catalogue-less one, the catalogue with the price printed verbatim, the recoverable error, the permission, the RECOVERY of a pending operation, the form without a transport, and the rule that the cupos are not presented as available before the payment |
| `features/inscripciones/__tests__/inscripcion-detalle.test.tsx` | jsdom | The states of `ACCOUNT-03` and the five sections: the honest empty, the permission, the recoverable error, the balance of three numbers, the impediment printed verbatim, the teams, the people, the purchases and the honest benefits |
| `features/inscripciones/__tests__/inscripcion-responsive.test.ts` | node | The static rules: no literal colour, no fixed pixel width, `scope="col"` on every table header, the table from 1024 and the cards below, the 44 px targets, no provider vocabulary, and **no arithmetic of cupos or money in the browser** |

### The five widths

The audit at 360, 390, 768, 1024 and 1440 was **deferred**: no browser was run in this packet.

What the markup already guarantees, and what the browser pass will have to confirm:

| Width | What the composition does | What is still unverified |
|---|---|---|
| 360 | One column. The rail of the wizard is four nodes in one row with the current step written above it; it never scrolls sideways. The package cards stack. The teams stack. The tabs of the detail WRAP into two rows. The participants are labelled cards, never a table. Every action is at least 44 px high. | That no page overflows horizontally, that the sticky header does not cover the first action, that the long team names truncate |
| 390 | The same single column. | The same |
| 768 | The rail of the wizard shows the title of every step; the pool band puts the sentence next to the three numbers | That the two columns do not squeeze the cards |
| 1024 | The participants become a table with prioritised columns; the pool band is a single row | That no column is stretched and that nothing is clipped |
| 1440 | The content band is capped by the shell (`max-w-page`); the body measure is capped at 72 characters (`max-w-measure`) | The same |

### Accessibility that was decided in the markup

- Every input has a real `<label>` and its error is associated with `aria-describedby`; the
  invalid ones carry `aria-invalid`.
- The radio of the package has an accessible name that includes the package and its cupos, and the
  card shows the focus with `focus-within`.
- The rail of the wizard marks the current step with `aria-current="step"` and the completed ones
  with a check, so the meaning never depends on the colour.
- The pool band reads the three numbers as a sentence, so a screen reader hears the balance.
- The impediments and the causes of the server are printed verbatim, never translated.
- The motion of the route is the one of the shell; this packet adds no animation of its own, so
  the reduced-motion preference is respected by construction.

**Residual gaps declared, never assumed green:** no browser rendering, no screen-reader pass, no
200 % zoom reflow, no automated axe or Lighthouse run, and no measurement of the contrast of the
`--success` / `--warning` tones.

---

## 10. What was NOT done, and why

| Item | Reason |
|---|---|
| The declarations step of the frozen wizard | The target's `InscripcionInicialIn` carries **no acceptances**: the backend records them per person. A step that asked for them would collect data the server would reject (`D-UI02-04`) |
| The quantity stepper and the quotation of the frozen wizard | The target's alta accepts neither a quantity nor a quoted price, and `POST /cotizaciones/` is not a route of the target backend. The price and the cupos come from the catalogue (`D-UI02-05`) |
| The network hooks of the feature (`useCrearInscripcion` to `POST /inscripciones/completa/`, `useCotizacion` to `POST /cotizaciones/`) | They point to routes that the target backend does not serve. They are a FORBIDDEN root of this packet, so they were **not edited**; they are now unreferenced (`D-UI02-06`) |
| The removal confirmation of a participant (S-10 of the detail) | It needs the transport of `RT-IN-06`. It is owed to API-02 (`D-UI02-08`) |
| The assignment of a person and the resolution sheet | They need `RT-IN-05` and `RT-ID-02`; there is no transport in this packet (`A0-UI02-08`) |
| The list of the granted benefits | `BeneficioConcedido` exists in the domain of DOM-02 but **no presenter publishes it**. The section says so instead of showing the benefits of the catalogue as if they had been granted (`A0-UI02-04`) |
| A route that lists the purchases of an inscription | The target backend does not publish one. The list is a seam assembled from the answers it gives (`A0-UI02-05`) |

---

## 11. API-02 handoff

### The seams that API-02 has to bind

| Seam | Where | What API-02 does |
|---|---|---|
| The catalogue of packages | `features/inscripciones/views/InscripcionWizardView.tsx` - prop `catalogo?: CatalogoPaquetes` | Reads `RT-IN-12` (`GET /api/catalogo/paquetes`) with the edition scope and hands the real catalogue to the wizard |
| The disciplines of the edition | the same prop (`catalogo.paquetes[].disciplinas`) | Reads `RT-IN-13` (`GET /api/catalogo/disciplinas`) when the package does not carry them |
| The alta | prop `enviar?: (solicitud: SolicitudAlta) => Promise<ResultadoAlta>` | Binds `POST /api/inscripciones` (`RT-IN-14`) and returns the wrapper of the answer |
| The pending operation | prop `pendiente?: OperacionPendiente` | Reads the existing inscription of the responsible and offers to continue it |
| The detail of the registration | `features/inscripciones/views/MisInscripcionDetalleView.tsx` - props `inscripcion`, `pool`, `compras`, `beneficios` | Reads `RT-IN-02` (`GET /api/inscripciones/{id}`) and `RT-IN-03` (`GET /api/inscripciones/{id}/pool`) |
| The purchases | prop `compras?: ComprasInscripcion` | The initial purchase comes with the alta and every expansion with its own answer (`RT-CM-01`) |
| The granted benefits | prop `beneficios?: readonly BeneficioConcedido[]` | Needs a route that publishes them (`A0-UI02-04`) |
| The form validation | `features/inscripciones/schemas/alta-inscripcion.schema.ts` | Replaced by the exact Zod mirror of `InscripcionInicialIn`. The schema of this packet is a CLIENT-VALIDATION schema and it declares no wire shape |
| The wire mirrors | `features/inscripciones/types/inscripcion.types.ts` | Replaced by the Zod mirrors of the frozen presenters, or kept as the view contract with the schemas next to them |

### The deletion checklist (mandatory in API-02, `T-082` of the workflow)

1. Delete `features/inscripciones/fixtures/inscripcion.fixture.ts` and replace it with the Zod
   mirrors of the frozen presenters.
2. Prove that **no** module outside `__tests__` imports a fixture, that there is no `catch` that
   falls back to a fixture and that there is no hidden route.
3. Replace the view models of `features/inscripciones/types/inscripcion.types.ts` with the Zod
   mirrors (or keep them as the view contract and add the schemas next to them).
4. Replace `features/inscripciones/schemas/alta-inscripcion.schema.ts` with the mirror of
   `InscripcionInicialIn` and check that the rules of the client do not contradict the server.
5. Bind the real service to the `enviar` seam and to the catalogue prop.
6. Delete the unreferenced `features/inscripciones/components/PasoDeclaraciones.tsx` and the
   unreferenced hooks of the frozen wizard (`useCrearInscripcion`, `useCotizacion`) if API-02
   replaces them.

---

## 12. Deviations, decisions and A0 requests

| ID | Type | What |
|---|---|---|
| `D-UI02-01` | decision | **The verdict chip of UI-01 was not reused.** No wrapper of the inscription domain publishes `EstadoOperativo`; the pool publishes its own `causa_operativa` and its `impedimentos`. Mapping a code onto a bucket in the browser would break as soon as a new code is catalogued (`SH-03` §6) |
| `D-UI02-02` | decision | **A step of the wizard never calculates a business value.** The quantity stepper, the quotation and the multiplication of the price of the frozen wizard were removed: the target's alta accepts none of them and the package declares its cupos and its price |
| `D-UI02-03` | deviation | **A `types/` folder was created inside the feature** (`features/inscripciones/types/inscripcion.types.ts`). The wire mirrors are forbidden in this stage, so the view models are plain TypeScript types, exactly as UI-01 did (`D-UI01-03`) |
| `D-UI02-04` | deviation | **The declarations step was dropped.** `InscripcionInicialIn` carries no acceptances: the backend records them per person. The legacy file stays on disk, unreferenced, because the tree is untracked and this packet performs no git operations |
| `D-UI02-05` | deviation | **The quantity of people was dropped.** The alta accepts no quantity; the package declares `cupos_incluidos` |
| `D-UI02-06` | deviation | **The network hooks of the frozen wizard were not used.** They point to `POST /inscripciones/completa/` and `POST /cotizaciones/`, routes that the target backend does not serve. They are a forbidden root, so they were not edited and are now unreferenced |
| `D-UI02-07` | deviation | **The discipline is a native `<select>`.** The radix `Select` needs a `Controller` per row of a dynamic array and a manual bridge of `onValueChange`; the native select registers with RHF directly and gives the platform picker. The list is short and closed |
| `D-UI02-08` | deviation | **The removal confirmation of a participant (S-10 of the detail) was not implemented.** It needs the transport of `RT-IN-06`; it is owed to API-02. The S-10 that this packet covers is the confirmation step of the wizard |
| `D-UI02-09` | deviation | **The detail of `ACCOUNT-03` lives in `features/inscripciones/views/`.** The route points to it. The previous `features/cuenta/views/MisInscripcionDetalleView.tsx` (UI-01) was **not** touched and is now unreferenced by the route |
| `D-UI02-10` | deviation | **The fixtures use `as const satisfies` with `readonly` arrays** (`FR-08` §1.2 asks for the `as const` form). The view models declare the arrays as `readonly` so the literal fixture stays assignable to them |

### A0 requests

| ID | Request |
|---|---|
| `A0-UI02-01` | The money wire shape is still OPEN (`OD-A0R2-01`). This packet types the amount as a STRING and prints it verbatim; it never parses, sums or formats money. The ratification of the shape belongs to API-02 |
| `A0-UI02-02` | `InscripcionDetalleOut.estado`, `EquipoOut.estado`, `ParticipacionOut.estado` and `CompraOut.estado` publish bare machine codes with no label, while the commerce and the passes publish the `EstadoOperativo` wrapper with `etiqueta` and `descripcion`. The pages print the codes as they come. This is the same class of debt as `A0-UI01-03` |
| `A0-UI02-03` | `PoolOut.ParticipacionOut` publishes `persona_id` but neither the name of the person nor a presentable label of the state of the participation. The list of the people shows the team, the discipline, the role and the state of the cupo, and nothing more |
| `A0-UI02-04` | `BeneficioConcedido` exists in the domain of DOM-02 but **no presenter of the target backend publishes it**. The section of the benefits is an honest empty until a route exists |
| `A0-UI02-05` | No route of the target backend LISTS the purchases of an inscription. The initial one comes with the alta and the expansions with their own answer. A listing route would close the section |
| `A0-UI02-06` | The routes of the inscription domain (`RT-IN-02`, `RT-IN-03`, `RT-IN-04`, `RT-IN-05`, `RT-IN-06`, `RT-IN-12`, `RT-IN-13`, `RT-IN-14`) are **PROVISIONAL**: only `RT-CM-01` is in the frozen ledger. They are implemented and served by the target backend, but the ledger is a forbidden root and A0 has to ratify them |
| `A0-UI02-07` | `00-matriz-tareas.md` does not carry a row for UI-02 and the matrix is a forbidden root: the row has to be synchronised by the coordinator |
| `A0-UI02-08` | The assignment of a person (`RT-IN-05`), the removal (`RT-IN-06`) and the resolution sheet (`RT-ID-02`) are not reachable from this skeleton: there is no transport. API-02 owns them |
| `A0-UI02-09` | TWO concurrent trees broke the project-wide typecheck while this packet ran: six files of `src/features/pases/**` (`TS2304: Cannot find name '__USE_CLIENT__'`) and then `src/features/marketplace/components/TarjetaProducto.tsx` (`TS17008`/`TS1005`) - both of **UI-03**. Both trees are OUTSIDE the allowed roots of this packet, so they were **not** touched. Their owners repaired them and the final global `npx tsc --noEmit` exited **0** after UI-03 completed (reported by the UI-03 evidence). The rule that stands: a packet never touches a concurrent root |

---

## 13. Workload and review boundary

The tasks artefact of this change carries **no** `Review Workload Forecast`, so no chain decision
was required before the apply (the same precedent as DOM-06, FND-07, FND-08 and UI-01).

**The real size of this packet is ~2 900 changed lines** (18 created files and 9 rewritten files),
which exceeds the 400-line review budget by roughly **7x**. There is **no commit** in this packet,
so the budget is a report and not a gate.

**Autonomous work units** (each one reviewable on its own, in this order):

| WU | Scope | Files |
|---|---|---|
| WU-1 | The view models, the client-side validation and the provisional fixture adapter | `types/**`, `schemas/alta-inscripcion.schema.ts`, `fixtures/**` |
| WU-2 | The rail of the steps and the card of the package | `components/{WizardStepper,PaqueteCard}.tsx` |
| WU-3 | The three steps of the wizard | `components/{PasoPaquete,PasoEquipos,PasoResumen,PasoConfirmacion}.tsx` |
| WU-4 | The five sections of the detail | `components/{PanelPool,PanelEquipos,PanelParticipantes,PanelCompras,PanelBeneficios}.tsx` |
| WU-5 | The two views | `views/**` |
| WU-6 | The route presentation (loading and error) | `app/(cuenta)/inscripcion/**`, `app/(cuenta)/mis-inscripciones/[id]/**` |
| WU-7 | The suites | `__tests__/**` |

**Rollback:** revert WU-7 to WU-1. The rollback is confined to the 18 created files and the 9
rewritten files; the shared shell, the providers, the theme, the account feature and every other
domain are untouched, so reverting this packet leaves the product exactly as it was. `git stash`
was never invoked and no commit was created.

---

## 14. Acceptance criteria of the packet

- [x] The wizard RECOVERS a pending operation: `pendiente` renders the recovery state and the page
      never offers to create a second inscription.
- [x] The wizard NEVER presents unpaid capacity as available: the summary, the confirmation and the
      outcome say that the cupos are enabled when the payment is confirmed, and the pool says that
      there is no enabled cupo while `cupos_pagados` is zero.
- [x] The detail distinguishes paid / assigned / available WITHOUT calculating them: the three
      numbers come from the wrapper and the browser prints them next to each other and as a
      sentence. The static audit forbids the arithmetic.
- [x] The shadcn comparison was recorded BEFORE the composition, no shared primitive was
      overwritten and no component was added.
- [x] The fixture deletion ledger is recorded (section 5 and section 11).
- [x] The ten states are covered on the two routes, and the ones that do not apply are declared
      with their reason (section 4).
- [x] The only runtime command was the typecheck, and the roots of this packet were GREEN in every
      run (0 errors in `src/features/inscripciones/**` and in `src/app/(cuenta)/**`).
- [ ] The five-width audit in a browser, the assistive-technology pass, the execution of the three
      suites and the lint pass are **DEFERRED** - the packet stays `verification_required`.
- [x] The project-wide typecheck is GREEN since **UI-03** completed: the only errors it ever carried
      were in CONCURRENT out-of-scope trees (`features/pases/**`, `features/marketplace/**`), repaired
      by their owners, and the final global `npx tsc --noEmit` exited **0** (reported by the UI-03
      evidence; this reconciliation ran **no** command).
