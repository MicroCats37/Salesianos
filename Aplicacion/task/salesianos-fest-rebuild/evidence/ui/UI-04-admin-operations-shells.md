# UI-04 - Admin Registration, Team, Participant And Payment Shells

**Artifact:** `evidence/ui/UI-04-admin-operations-shells.md` · **Packet:** UI-04 (`wave-02-frontend-skeletons`)
**Owner:** A7 · **Status:** `verification_required` (implementation applied, runtime verification deferred)
**Date:** 2026-11-19 · **Target:** `Aplicacion/frontend/**` only
**Packet:** `Aplicacion/task/salesianos-fest-rebuild/wave-02-frontend-skeletons/UI-04-admin-operations-shells.md`

---

## 1. Scope actually applied

The packet names six page IDs. All six were applied, in **FIVE NEW
domain-specific subfolders** under `src/features/admin/**` plus one shared
operational layer.

| Page ID | Route | Route file | Feature | State |
|---|---|---|---|---|
| `ADM-05` | `/administracion/inscripciones` | `app/(administracion)/administracion/inscripciones/page.tsx` (modified) | `features/admin/inscripciones/views/InscripcionesAdminView.tsx` | **applied** |
| `ADM-06` | `/administracion/inscripciones/[id]` | `app/(administracion)/administracion/inscripciones/[id]/page.tsx` (modified) | `features/admin/inscripciones/views/InscripcionAdminDetalleView.tsx` | **applied** |
| `ADM-07` | `/administracion/equipos` | `app/(administracion)/administracion/equipos/page.tsx` (modified) | `features/admin/equipos/views/EquiposAdminView.tsx` | **applied** |
| `ADM-08` | `/administracion/equipos/[id]` | `app/(administracion)/administracion/equipos/[id]/page.tsx` (modified) | `features/admin/equipos/views/EquipoAdminDetalleView.tsx` | **applied** |
| `ADM-09` | `/administracion/participantes` | `app/(administracion)/administracion/participantes/page.tsx` (modified) | `features/admin/participantes/views/ParticipantesAdminView.tsx` | **applied** |
| `ADM-14` | `/administracion/pagos` | `app/(administracion)/administracion/pagos/page.tsx` (modified) | `features/admin/pagos/views/PagosAdminView.tsx` | **applied** |

**The transversal rule that decided the composition (`D-UI04-01`).**

> **One admin list pattern, not six** (`GOV-02-RB-03a`). The six lists of the
> panel share `ListaOperativa`: one card per row at 360/390, one table from
> 768 with the priority columns, and the remaining columns from 1024.

**The rule that decided the honesty of the states (`D-UI04-02`).**

> **A provisional fixture never reaches a route.** Every route of this packet
> renders the honest state by default (`sin-datos`). The populated
> compositions are implemented, typed and exercised by the suites; they are
> the code that **API-04** binds to the real presenters.

### 1.1 The shared operational layer

`features/admin/operaciones/**` is NOT a domain: it is the **proven
cross-feature primitive** that `GOV-02-RB-03a` demands (the list pattern) plus
the verdict vocabulary of `SH-01` §3.2. It imports nothing from the four
domains; the four domains import it. The four domain folders never import
each other.

---

## 2. The route briefs applied

The briefs were produced by **GOV-02** and were read before any code was
written:

- `evidence/routes/RB-03-admin-editions-identity-inscriptions.md` ->
  `ADM-05`, `ADM-06`.
- `evidence/routes/RB-04-admin-teams-participants.md` -> `ADM-07`, `ADM-08`,
  `ADM-09`.
- `evidence/routes/RB-06-admin-payments.md` -> `ADM-14`.
- `evidence/routes/SH-01` (tokens) · `SH-02` (five widths + a11y) ·
  `SH-03` (ten states) · `SH-04` (shadcn families) · `SH-05` (provisional
  endpoint register) · `SH-06` (wireframes).
- `evidence/contracts/FR-07` (presenter/schema versions) · `FR-08`
  (provisional fixtures) · `FR-01` (envelope).
- `Aplicacion/plan/salesianos-fest-rebuild/frontend/04-panel-administrativo.md`
  (the six page briefs) · `frontend/01` (route map) ·
  `contratos/01` (the administrative presenters of the team and the payment).

### 2.1 The contract truth that was read in the TARGET backend

No endpoint of this area is registered. The **real** vocabularies that the
interfaces use were read from the target backend, not invented:

| Fact | Source in `Aplicacion/backend` | Used by |
|---|---|---|
| `EstadoInscripcion` = `CREADA`, `CANCELADA` | `modules/salesianos_fest/domain/constants.py` | filter `estado` of `ADM-05` |
| `EstadoEquipo` = `ACTIVO`, `RETIRADO` | same | filter `estado` of `ADM-07` |
| `EstadoParticipacion` = `ACTIVA`, `RETIRADA` | same | the roster of `ADM-06`/`ADM-08` |
| `RolParticipante` = `JUGADOR`, `CAPITAN`, `DELEGADO` | same | the roster of `ADM-06`/`ADM-08` |
| `EstadoOperativoPago` = 8 codes + `DESCRIPCIONES_ESTADO_OPERATIVO` | `modules/pagos/domain/constants.py` | the `estado_operativo` filter of `ADM-14` and the adapter |
| `OrigenCompra` = `INSCRIPCION`, `PASE`, `MARKETPLACE` | `modules/commerce/domain/constants.py` | filter `tipo` of `ADM-14` |
| `EstadoCompra` = `PENDIENTE`, `PAGADA`, `CANCELADA` | same | filter `estado_compra` of `ADM-14` |
| `EstadoOrdenPago` = `PENDIENTE`, `EN_VERIFICACION`, `CONFIRMADA`, `FALLIDA`, `VENCIDA` | `modules/pagos/domain/constants.py` | filter `estado_orden` of `ADM-14` |
| `OrigenPago` = `IZIPAY`, `MANUAL`, `SIN_PAGO` | same | the diagnosis of `ADM-14` |
| `IntentoPagoOut` | `modules/pagos/presentation/schemas/pago_schemas.py` | the diagnosis of `ADM-14` |
| `PoolOut` (`cupos_pagados/asignados/disponibles` + `impedimentos`) | `modules/salesianos_fest/presentation/schemas/pool_schemas.py` | the tab «Pool y personas» of `ADM-06` |

### 2.2 The endpoints of this area DO NOT exist (registration truth)

`Aplicacion/backend/config/api.py` registers nine controllers. **None** of
them serves the administrative routes of this packet:

| Ledger route | Method + path | Presenter | Registered? |
|---|---|---|---|
| `RT-IN-07` | `GET /administracion/inscripciones` | `AdminInscripcionListaPresenter` | **NO** |
| `RT-IN-08` | `GET /administracion/inscripciones/{inscripcion_id}` | `AdminInscripcionDetallePresenter` | **NO** |
| `RT-IN-09` | `GET /administracion/equipos` | `AdminEquipoListaPresenter` | **NO** |
| `RT-IN-10` | `GET /administracion/equipos/{equipo_id}` | `AdminEquipoDetallePresenter` | **NO** |
| `RT-IN-11` | `GET /administracion/participantes` | `AdminParticipanteListaPresenter` | **NO** |
| `RT-PG-04` | `GET /administracion/pagos` (FROZEN) | `AdminPagoPresenter` | **NO** |
| `RT-PG-05` | `POST /administracion/pagos/{orden_pago_id}/aprobar-manual` (FROZEN) | `AdminPagoManualPresenter` | **NO** |
| `RT-PG-06` | `GET /pagos/ordenes/{orden_id}/intentos` | `PagoIntentosPresenter` | **NO** |
| `RT-PG-07` | `GET /administracion/pagos/{compra_id}` | `AdminPagoDetallePresenter` | **NO** |
| `RT-ID-07` | `GET /administracion/personas` | `AdminPersonaListaPresenter` | **NO** |
| `RT-ID-08` | `GET /administracion/personas/{persona_id}` | `AdminPersonaDetallePresenter` | **NO** |

**Consequence applied in the code:** every route renders the honest state,
every sensitive action is DISABLED with a written reason, and no endpoint,
payload or field was invented.

---

## 3. shadcn candidate comparison (the MCP was executed for this family)

| # | Tool call | Result |
|---|---|---|
| 1 | `shadcn_get_project_registries` | `@shadcn` (the target registry) |
| 2 | `shadcn_list_items_in_registries` (types `ui`) | **61** items in `registry:ui` |
| 3 | `shadcn_search_items_in_registries` — `table` | `table` (registry:ui) |
| 4 | `shadcn_search_items_in_registries` — `sheet` | `sheet` (registry:ui) |
| 5 | `shadcn_search_items_in_registries` — `tabs` | `tabs` (registry:ui) |

| Item | Registry | Fit for this family | Local state | Decision |
|---|---|---|---|---|
| `table` | `registry:ui` | The rows of the six lists | **present** (`components/ui/table.tsx`) | **Selected / reused** for the table of `ListaOperativa`. It carries `overflow-x-auto`, so the table scrolls inside its container and the page never overflows. The local `AdminDataTable` (FND-06) was NOT reused: it has no card composition for 360/390 and it is an FND root |
| `sheet` | `registry:ui` | The drawer of `ADM-08` and of the commercial detail of `ADM-14` | **present** (`components/ui/sheet.tsx`) | **Selected / reused**. Its own close button ships the English screen-reader label "Close", so it is composed with `showCloseButton={false}` and a Spanish "Cerrar" |
| `drawer` | `registry:ui` | The same drawer | **absent** | **Rejected**: `components/ui/**` is a FORBIDDEN root of this packet and the launch contract forbids an install. `sheet` is the local equivalent |
| `tabs` | `registry:ui` | The five tabs of `ADM-06` and the three groupings of `ADM-09` | **present** (`components/ui/tabs.tsx`) | **Selected / reused** |
| `collapsible` | `registry:ui` | The disclosure of the diagnosis (`ADM-14`, level 3) | **present** (`components/ui/collapsible.tsx`) | **Selected / reused**. It is a real disclosure with `aria-expanded`, which is what the third level needs |
| `accordion` | `registry:ui` | The same disclosure | **absent** | **Rejected**: forbidden root + no install. `collapsible` covers the case |
| `alert-dialog` | `registry:ui` | The S-10 confirmations | **present** (`components/ui/alert-dialog.tsx`) | **Selected / reused** through `ConfirmacionIrreversible` |
| `dialog` | `registry:ui` | The commercial detail | **present** | **Not used**: the brief asks for a drawer, and the sensitive action asks for a confirmation with a reason (`alert-dialog`) |
| `sidebar` | `registry:ui` | The admin navigation | **present** | **Not touched**: the navigation belongs to the shell (`components/shell/AdminSidebar.tsx`) and the packet declares "admin navigation changes are A0 requests" |
| `badge` | `registry:ui` | The verdict chip | **present**, but with only `default` / `secondary` / `destructive` / `outline` | **Rejected for the verdict**: the chip is **composed** in the feature layer (icon shape + the label of the backend + a semantic surface), because the local badge has no `success` / `warning` / `info` variants. **The shared primitive was not touched** |
| `item` | `registry:ui` | The row card | **present** | **Not used**: the card of an operational row is a title plus a definition list, and `ItemTitle` truncates the line. The card is composed in the feature layer |
| `pagination` | `registry:ui` | The pagination of the lists | **present** | **Selected / reused**: server-driven LINKS (`?page=N`), so the page never computes a page |
| `empty` | `registry:ui` | S-02 and S-03 | **present** | **Selected / reused** through `AdminEmptyState` (FND-06) |
| `skeleton` | `registry:ui` | S-01 | **present** | **Selected / reused** |
| `input` + `label` | `registry:ui` | The search field and the reason of the S-10 | **present** | **Selected / reused** |
| `select` | `registry:ui` | The filters | **present** | **Selected / reused**. The trigger is labelled with `aria-labelledby` (a radix trigger is a `button`, not a labelable element) |
| `field` | `registry:ui` | The form fields | **absent** | **Rejected**: `GOV-02-SH-03` — `field` must not enter the `GenericForm` wrapper path without proving there is no double render of label/error |
| `form` | `registry:ui` | The reason of the S-10 | **absent** | **Rejected**: forbidden root + no install. The reason is a plain labelled `Textarea` (see `D-UI04-08`) |

**No component was added. No file in `components/ui/**` was created, modified
or overwritten. No install was executed.**

---

## 4. The ten states, route by route

| State | `ADM-05` | `ADM-06` | `ADM-07` | `ADM-08` | `ADM-09` | `ADM-14` |
|---|---|---|---|---|---|---|
| S-01 initial / loading | `EsqueletoOperativo` (cards + table) | per tab | idem | idem | idem | idem |
| S-02 empty (never had data) | "Todavía no hay inscripciones cargadas" | "No se pudo cargar esta inscripción" | "Todavía no hay equipos cargados" | "No se pudo cargar este equipo" | **"Busca a una persona para empezar"** (the PROMPT comes first) | "Todavía no hay compras cargadas" |
| S-03 filtered-empty | "No hay inscripciones para esta edición" | per tab | "No hay equipos para esta edición" | — | "Sin participaciones para esta búsqueda" | — |
| S-04 recoverable error | `ShellErrorState` with the message of the backend VERBATIM | idem | idem | idem | idem | idem |
| S-05 validation | the reason of the S-10 (required, associated, focused) | idem | idem | idem | — | idem |
| S-06 permission | `ShellPermissionDenied` — "No tienes permiso para ver esto" | idem | idem | idem | idem | idem |
| S-07 success | the list opens the detail | the tabs answer | the row opens the team | the identity answers | the rows answer | the row opens the commercial detail |
| S-08 in progress | the confirm button of the S-10 says "Ejecutando…" | idem | idem | idem | — | idem |
| S-09 partial / indeterminate | the verdict carries its cause | idem | idem | idem | idem | "Pago confirmado; el diagnóstico separa la evidencia de la entrega" (the two levels are two facts) |
| S-10 irreversible confirmation | "Retirar participante libera su cupo en esta inscripción; no genera devolución" + reason | idem | — | "Retirar a la persona libera su cupo en la inscripción de este equipo; no genera devolución" + reason | — | "Registrar 0.00 PEN de «…» habilita los derechos de esta compra y queda registrado en la auditoría" + reason |
| payment states | — | — | — | — | — | the EIGHT frozen codes of `EstadoOperativoPago`, each with the label and the description of the backend |
| paid vs delivered | — | — | — | — | — | the commercial detail and the diagnosis are TWO levels; a paid purchase is never described as delivered |

**The states that are NOT generic** (`SH-03` §5):

- `ADM-07`/`ADM-08`: "6 jugadores registrados; necesita al menos 7" — the
  cause is the `descripcion` of the backend, never a client-side inference.
- `ADM-09`: a duplicate participation in the same discipline is stated in
  words (the `mensaje` of the backend), never as a red highlight.
- `ADM-14`: one understandable verdict per row; the diagnosis is hidden under
  a disclosure by default.

---

## 5. Provisional fixtures (FR-08)

Every fixture is **local to its feature**, **typed with `as const satisfies`**,
**marked** and **exported from no production barrel**.

| Fixture (symbol) | Mirrors | Contract | Path | Deleted in |
|---|---|---|---|---|
| `estadoOperativoPagoPendienteFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/admin/pagos/fixtures/pagos-admin.fixture.ts` | **API-04** |
| `pagoOperativoFixture` | `PagoOperativoOut` (plan `contratos/01` §4) | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `pagoAdminDetalleFixture` | `AdminPagoDetalleOut` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `compraAdminFixture` | `CompraOut` (DOM-01) | `FREEZE-PS-1.0.0` | idem | **API-04** |
| `intentoPagoAdminFixture` | `IntentoPagoOut` (DOM-04) | `FREEZE-PS-1.0.0` | idem | **API-04** |
| `operacionManualAdminFixture` | `AdminPagoManualPresenter` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `equipoOperativoFixture` | `EquipoOperativoOut` (plan `contratos/01` §3) | `FREEZE-ENV-1.0.0` | `features/admin/equipos/fixtures/equipos-admin.fixture.ts` | **API-04** |
| `equipoAdminListaFixture` | `AdminEquipoListItemOut` (`RT-IN-09`) | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `equipoAdminDetalleFixture` | `AdminEquipoDetalleOut` (`RT-IN-10`) | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `participanteDeEquipoFixture` | `ParticipanteDeEquipoOut` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `candidatoAEquipoFixture` | `CandidatoAEquipoOut` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `estadoOperativoInscripcionCreadaFixture` / `…CanceladaFixture` | `EstadoOperativo` | `FREEZE-ENV-1.0.0` | `features/admin/inscripciones/fixtures/inscripciones-admin.fixture.ts` | **API-04** |
| `equipoDeInscripcionFixture` | `EquipoDeInscripcionOut` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `participanteDeEquipoFixture` | `ParticipanteDeEquipoOut` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `poolDeInscripcionFixture` | `PoolOut` (DOM-02) | `FREEZE-PS-1.0.0` | idem | **API-04** |
| `compraDeCuposFixture` | `CompraOut` (DOM-01) | `FREEZE-PS-1.0.0` | idem | **API-04** |
| `eventoDeHistorialFixture` | `AdminInscripcionDetallePresenter` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `inscripcionAdminListaFixture` | `AdminInscripcionListItemOut` (`RT-IN-07`) | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `inscripcionAdminDetalleFixture` | `AdminInscripcionDetalleOut` (`RT-IN-08`) | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `participacionAdminFixture` | `AdminParticipanteListItemOut` (`RT-IN-11`) | `FREEZE-ENV-1.0.0` | `features/admin/participantes/fixtures/participantes-admin.fixture.ts` | **API-04** |
| `participanteAdminFixture` | `AdminParticipanteListItemOut` | `FREEZE-ENV-1.0.0` | idem | **API-04** |
| `eventoDeHistorialAdminFixture` | `AdminParticipanteListaPresenter` | `FREEZE-ENV-1.0.0` | idem | **API-04** |

**Rules honoured:** the literal token `PROVISIONAL_CONTRACT_FIXTURE` is in the
header of every fixture and the symbol name carries the `Fixture` suffix — no
business calculation, no `if`, no arithmetic, no `Date.now()` /
`Math.random()` / `crypto.randomUUID()`, no price, no availability, no
payment state and no permission is DERIVED. The amount is `"0.00"` on
purpose (`FR-08` §2.4), so an example amount cannot look like a real price.
The three numbers of a roster and the code of a verdict appear as DECLARED
literals, which `FR-08` §1.3 permits.

**No fixture is exported from a production barrel.** The fixtures are
consumed only by the suites of their feature.

---

## 6. Files changed (48 created, 6 modified, 0 deleted)

All of them are inside the allowed roots of the packet.

**Route presentation - modified (6)**

- `app/(administracion)/administracion/inscripciones/page.tsx` - reads
  `searchParams` and hands the filters to the view.
- `app/(administracion)/administracion/inscripciones/[id]/page.tsx`
- `app/(administracion)/administracion/equipos/page.tsx` - reads
  `searchParams`.
- `app/(administracion)/administracion/equipos/[id]/page.tsx`
- `app/(administracion)/administracion/participantes/page.tsx` - reads
  `searchParams`.
- `app/(administracion)/administracion/pagos/page.tsx` - reads `searchParams`.

**Shared operational layer `features/admin/operaciones` - created (19)**

- `types/operaciones.types.ts`
- `utils/veredicto.adapter.ts` · `utils/parametros.ts`
- `components/VeredictoOperativo.tsx` · `components/ListaOperativa.tsx` ·
  `components/BarraFiltros.tsx` · `components/BusquedaOperativa.tsx` ·
  `components/MarcoOperativo.tsx` · `components/EsqueletoOperativo.tsx` ·
  `components/CifrasCupos.tsx` · `components/PaginacionOperativa.tsx` ·
  `components/ConfirmacionIrreversible.tsx` · `components/index.ts`
- `index.ts`
- `__tests__/operaciones-estados.test.tsx`

**Feature `inscripciones` - created (9)**

- `types/inscripciones-admin.types.ts`
- `fixtures/inscripciones-admin.fixture.ts`
- `components/CifrasCupos.tsx` (**moved** to the operational layer) ·
  `components/PanelPoolInscripcion.tsx` ·
  `components/DialogoRetirarParticipante.tsx`
- `views/InscripcionesAdminView.tsx` · `views/InscripcionAdminDetalleView.tsx`
  · `views/index.ts`
- `index.ts`
- `__tests__/inscripciones-admin-estados.test.tsx`

**Feature `equipos` - created (9)**

- `types/equipos-admin.types.ts`
- `fixtures/equipos-admin.fixture.ts`
- `components/PlantillaEquipo.tsx` · `components/PanelPlantillaEquipo.tsx`
- `views/EquiposAdminView.tsx` · `views/EquipoAdminDetalleView.tsx` ·
  `views/index.ts`
- `index.ts`
- `__tests__/equipos-admin-estados.test.tsx`

**Feature `participantes` - created (6)**

- `types/participantes-admin.types.ts`
- `fixtures/participantes-admin.fixture.ts`
- `views/ParticipantesAdminView.tsx` · `views/index.ts`
- `index.ts`
- `__tests__/participantes-admin-estados.test.tsx`

**Feature `pagos` - created (10)**

- `types/pagos-admin.types.ts`
- `fixtures/pagos-admin.fixture.ts`
- `components/ListaPagosOperativa.tsx` · `components/DetalleComercialPago.tsx`
  · `components/DialogoAprobarPagoManual.tsx`
- `views/PagosAdminView.tsx` · `views/index.ts`
- `index.ts`
- `__tests__/pagos-admin-estados.test.tsx`

**Not touched:** `src/components/shell/**` · `src/components/ui/**` ·
`src/app/globals.css` · `src/providers/**` · `src/lib/**` · `src/hooks/**` ·
`src/shared/**` · `src/features/admin/{components,views,utils}/**` (FND-06) ·
`src/features/{auth,portada,inscripciones,pases,marketplace,public,cuenta,theme}/**`
· the backend · `contract/**` · the root `frontend/**`.

---

## 7. Skills loaded

| Order | Skill | Use in this packet |
|---|---|---|
| 1 | `salesianos-ui-ux` | Route purpose, actors, actions, states, the visual direction of `SH-01` and the semantic roles; the decision gates of `03b`, `05a` and `07` |
| 2 | `salesianos-feature-architecture` | Layer boundaries: thin pages, views own the composition, components own the presentation, types separate from the fixtures, no business logic in a page; the reuse/create decision of the operational layer |
| 3 | `salesianos-forms-smart-fields` | The S-10 reason: a plain labelled control and NOT a `GenericForm`, because the wire schema does not exist (`D-UI04-08`); the label and the error of a field drawn ONCE |
| 4 | `salesianos-api-data` | **Read-only contract clarification** only: the ledger of the presenters, the frozen query of `RT-PG-04` and the shape of the envelope. **No transport, no client, no schema mirror, no query key was created** |
| 5 | `salesianos-shadcn` | The MCP comparison of section 3, the reuse of the local primitives, the refusal to recreate a registry component, the hardcoded-colour audit |
| 6 | `salesianos-responsive-a11y` | The five-width contract, the 44 px targets, the labels and the live regions, the focus-managed error of the S-10 |
| 7 | `frontend-design` | The restraint: one memorable element per surface, copy that says one thing, errors that name the cause and the fix |

---

## 8. Commands run, exit codes and results

**The only runtime command of this packet was the typecheck.** Everything else
was forbidden by the launch contract.

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 9 errors, ALL of them own: the type `VeredictoOperativo` collided with the component of the same name, and `ShellErrorState` / `ShellPermissionDenied` require an explicit `title` |
| 2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean, after the rename of the type to `Veredicto` and the explicit titles |
| 3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean, after the six route pages and the five suites |
| 4 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean, final run of the packet (the global gate is GREEN) |
| 5 | `git status --short -- ...` | repo root | **0** | 6 route files modified + 5 new feature trees; the other lines were already modified by concurrent agents and were NOT touched |

**NOT RUN** (forbidden by the launch contract, and recorded as deferred,
never as passed): `vitest` · `biome check` · `next build` · `npm install` ·
any server · any browser · any visual automation · `git stash` · `git commit`
· `git reset` · `git checkout`.

**Known baseline failures:** none introduced. The 9 type errors of command 1
were introduced by this packet and were fixed in this packet.

---

## 9. Tests written (NOT executed) and the five widths

The standing user preference (#11299) is that the suites of an apply packet
are **written** and **not executed**, and the packet status is
`verification_required`. The suites below were written and **have never run**:
nothing here may be read as a green result.

| Suite | Environment | What it freezes |
|---|---|---|
| `features/admin/operaciones/__tests__/operaciones-estados.test.tsx` | jsdom | The chip shows the label of the backend and NEVER the code; an unknown role paints neutrally; the adapter knows the frozen vocabulary and neutralises the unknown; the list publishes a table with `<th scope="col">` and shows the empty state INSTEAD of an empty table; the state switch distinguishes `sin-datos` / `error` (verbatim) / `sin-permiso`; the skeleton mirrors the geometry; **T-01** (no literal colour) and the **44 px** targets |
| `features/admin/inscripciones/__tests__/inscripciones-admin-estados.test.tsx` | jsdom | `ADM-05`: the honest state, the list with the state and its cause, the three cupos as three facts. `ADM-06`: the five tabs of the plan, the summary with the three cupos. The S-10: the confirmation names the effect, asks for the reason and the confirm button is **disabled**. **T-01** |
| `features/admin/equipos/__tests__/equipos-admin-estados.test.tsx` | jsdom | `ADM-07`: the honest state, the cause of the verdict ("Se necesita al menos 7 jugadores para competir"), the roster as three facts (`6 / 7–10` + the sentence for the screen reader) and the action "Ver equipo". `ADM-08`: the honest state, the eligibility with the reason of the backend, the roster with the document and the state, and the projected actions **disabled**. **T-01** and **the roster is NEVER compared with the minimum in the browser** |
| `features/admin/participantes/__tests__/participantes-admin-estados.test.tsx` | jsdom | `ADM-09`: the PROMPT comes first (no empty table), the honest state with a search, the rows with the reason of the conflict, the three groupings. **T-01** |
| `features/admin/pagos/__tests__/pagos-admin-estados.test.tsx` | jsdom | `ADM-14`: the honest state, ONE understandable verdict per row and never the machine code, the three levels (the commercial detail and the diagnosis behind a disclosure), the provider layer as TEXT and not as a verdict chip. **T-01** and **the verdict is NEVER derived by crossing the raw fields of the purchase, the order and the attempt**. **T-01** |

### The five widths

The audit at 360, 390, 768, 1024 and 1440 was **deferred**: no browser was run
in this packet. What the markup already guarantees, and what the browser pass
will have to confirm:

| Width | What the composition does | What is still unverified |
|---|---|---|
| 360 | One column. Each row of a list is a card: the title, the state with its cause and the essential facts. The filters travel in a SHEET. The detail of a payment opens a sheet from the bottom. The tab strips scroll horizontally. Every action is at least 44 px high. | That no page overflows horizontally, that the sheet fits a small viewport, that the long names truncate |
| 390 | The same single column. | The same |
| 768 | The lists become tables with the priority columns (`th scope="col"`); the filters become inline; the payment detail opens from the side | That the three priority columns do not squeeze |
| 1024 | The tables publish the columns of priority `2`; the payment sheet is a side panel | That no column is stretched and that nothing is clipped |
| 1440 | The same, with the content band capped by the shell | The same |

### Accessibility that was decided in the markup

- Every filter has a visible name and the control is associated with it
  (`aria-labelledby`, because a radix trigger is a button and not a labelable
  element).
- The search field has a real `<label>` and a `<form role="search">`.
- The table header of every list is a `<th scope="col">` and the key of a row
  is its stable identifier, never the index.
- The verdict chip pairs an icon, the label of the backend and a semantic
  surface: the colour NEVER carries the meaning alone, and the code is never
  shown.
- The roster figure is compact and the SENTENCE is complete for a screen
  reader ("6 jugadores registrados; mínimo 7; máximo 10").
- The reason of the S-10 is associated with its field and its error is
  announced with `role="alert"`.
- The diagnosis of `ADM-14` is a real disclosure with `aria-expanded`.
- When the operator filters by a verdict, the count is announced in a live
  region (`role="status"`).

**Residual gaps declared, never assumed green:** no browser rendering, no
screen-reader pass, no 200 % zoom reflow, no automated axe or Lighthouse run,
and the suites themselves have never been executed.

---

## 10. Deviations, decisions and A0 requests

| ID | Type | What |
|---|---|---|
| `D-UI04-01` | decision | **One admin list pattern, not six.** The six lists share `ListaOperativa` (`GOV-02-RB-03a`). It answers at every width with the SAME data: a card per row at 360/390 and a table from 768, with the priority columns. |
| `D-UI04-02` | decision | **A provisional fixture never reaches a route.** Every route renders the honest state by default; the populated compositions are exercised by the suites and are the code that API-04 binds. |
| `D-UI04-03` | decision | **The verdict travels with its bucket.** The view model carries `estado_operativo` (the wrapper of the backend) AND `rol` (the presentational bucket), exactly as `D-UI01-02` does. A component NEVER branches on a business code. The adapter that resolves the code into the bucket lives in `utils/veredicto.adapter.ts` and knows the EIGHT frozen codes of `EstadoOperativoPago`; an unknown code renders NEUTRALLY. |
| `D-UI04-04` | decision | **The filters live in the URL** and nowhere else (`GOV-02-RB-03b` · `D-UI01-10`). The page reads the query string; the filter bar and the search write it back. The page number travels in the URL too, so a page of the list is a link. |
| `D-UI04-05` | decision | **A filter whose option catalogue is not published is shown DISABLED with the reason**, instead of a list of invented values. |
| `D-UI04-06` | decision | **The cupos are three facts and never a balance.** `CifrasCupos` prints the three numbers the server sent and never subtracts them (`GOV-02-RB-04a`). |
| `D-UI04-07` | decision | **The roster of a team is three numbers and never a verdict.** `PlantillaEquipo` prints `6 / 7–10` and the complete sentence for the screen reader; the READINESS is the `estado_operativo` of the presenter. The browser never compares the roster with the minimum. |
| `D-UI04-08` | deviation | **The reason of the S-10 is a plain labelled `Textarea`, NOT a `GenericForm`.** The wire schema of the action does not exist and `RT-PG-05` / the administrative withdrawal are not registered, so a Zod mirror would be an INVENTED contract. API-04 binds it to `GenericForm` Mode 2/3 with the real schema. The `field` primitive was not used (`GOV-02-SH-03`). |
| `D-UI04-09` | deviation | **The "add participant" form of `ADM-08` was NOT built.** The brief asks for a drawer with the resolution of a person, but the resolution (`RT-ID-01`/`02`) and the administrative assignment are not bound and there is no schema for them. The action is shown DISABLED with a written reason. |
| `D-UI04-10` | deviation | **The pagination is composed but not exercised.** `PaginacionOperativa` publishes server-driven LINKS (`?page=N`), but the lists are not connected, so no page of data exists. It is the seam that API-04 binds to the service that owns the page. |
| `D-UI04-11` | deviation | **The `fecha` of a row of the payments is an addition to the canonical fixture of `FR-08` §2.4.** The plan requires the date in the operational list (`frontend/04` §6) and the canonical example does not carry it, so `AdminPagoListItemOut` EXTENDS `PagoOperativoOut` with `fecha` instead of changing the canonical shape. |
| `D-UI04-12` | deviation | **The drawer of `ADM-14` is a `sheet` everywhere.** The brief allows a drawer at 768 and a route at 1024; the plan declares no page ID for the detail of a payment, so the drawer is used at every width for consistency and the sub-route `RT-PG-07` stays a data seam. |
| `D-UI04-13` | deviation | **The eligibility of a team is a list of candidates with the verdict of the backend, not a form.** The browser never pre-validates anybody (`RB-04`): it reproduces the verdict. |
| `D-UI04-14` | deviation | **The `loading.tsx` of the six routes was NOT created.** S-01 is owned by the group boundary of the shell (`app/(administracion)/loading.tsx`), which is a FORBIDDEN root of this packet. The list block has its own skeleton. |

### A0 requests

| ID | Request |
|---|---|
| `A0-UI04-01` | **Register the administrative controllers.** `AdminInscripcionController` (`RT-IN-07`, `RT-IN-08`), `AdminEquipoController` (`RT-IN-09`, `RT-IN-10`), `AdminParticipanteController` (`RT-IN-11`), `AdminPagoController` (`RT-PG-04`, `RT-PG-05`, `RT-PG-07`) and `AdminPersonaController` (`RT-ID-07`, `RT-ID-08`) do NOT exist in `Aplicacion/backend/config/api.py`: their routes DO NOT EXIST, so the six routes of this packet keep their honest state. `RT-PG-04` and `RT-PG-05` are FROZEN in GOV-01 and are waiting only for the registration. |
| `A0-UI04-02` | **Publish the presenter of the team drilldown.** `EquipoOut` (DOM-01) publishes the identity of a team but NOT the roster count, the minimum, the maximum or the readiness verdict that the table of `frontend/04` §5 requires. A presenter that publishes `plantilla.{registrados,minimo,maximo}` and `estado_operativo` is needed, or the table has to be narrowed. |
| `A0-UI04-03` | **Publish the label of the administrative codes.** `EstadoOperativoPago` publishes the label and the description of the eight payment codes, but the state of a TEAM, of a REGISTRATION and of a PARTICIPATION has no published prose in the target. The interface prints what the presenter gives; today the examples of the fixtures are the only prose. |
| `A0-UI04-04` | **Publish the administrative route that withdraws a participant of ANY registration.** The registered `DELETE /inscripciones/{id}/participantes/{pid}` belongs to the RESPONSIBLE of his own inscription (`RT-IN-06`), not to the administrator. The S-10 of `ADM-06` and `ADM-08` names its effect but has no endpoint. |
| `A0-UI04-05` | **The `catalogo/disciplinas` route exists but the administrative filter does not.** The filter of `ADM-05` and `ADM-07` by discipline is shown disabled with the reason: the option catalogue of the administrative list is not published. |
| `A0-UI04-06` | **`00-matriz-tareas.md` does not carry a row for UI-04** and the matrix is a forbidden root: the row has to be synchronised by the coordinator. |
| `A0-UI04-07` | **The shared primitive of the verdict chip.** The verdict chip is composed FOUR times (one per domain) because the local `badge` has no `success` / `warning` / `info` variants and `components/ui/**` is a forbidden root. A shared verdict primitive in the shell would remove the duplication. |

---

## 11. API-04 handoff

### The seams that API-04 has to bind

| Seam | Where | What API-04 does |
|---|---|---|
| The list of the registrations | `features/admin/inscripciones/views/InscripcionesAdminView.tsx` — prop `estado?: EstadoListaInscripcionesAdmin` | Reads `RT-IN-07` (`GET /administracion/inscripciones`) and binds `AdminInscripcionListItemOut` |
| The detail of a registration | `features/admin/inscripciones/views/InscripcionAdminDetalleView.tsx` — prop `estado?: EstadoDetalleInscripcionAdmin` | Reads `RT-IN-08` (`GET /administracion/inscripciones/{id}`) and binds `AdminInscripcionDetalleOut` |
| The pool of a registration | `features/admin/inscripciones/components/PanelPoolInscripcion.tsx` — props `pool`, `personas` | Reads `RT-IN-03` (`GET /inscripciones/{id}/pool`) for the counts and the causes; the roster comes from the admin presenter |
| The withdrawal of a participant | `features/admin/inscripciones/components/DialogoRetirarParticipante.tsx` — prop `deshabilitado` of `ConfirmacionIrreversible` | Reads the administrative withdrawal route (see `A0-UI04-04`) and binds the reason to the real payload |
| The list of the teams | `features/admin/equipos/views/EquiposAdminView.tsx` — prop `estado?: EstadoListaEquiposAdmin` | Reads `RT-IN-09` (`GET /administracion/equipos`) and binds `AdminEquipoListItemOut` |
| The detail of a team | `features/admin/equipos/views/EquipoAdminDetalleView.tsx` — prop `estado?: EstadoDetalleEquipoAdmin` | Reads `RT-IN-10` (`GET /administracion/equipos/{id}`) and binds `AdminEquipoDetalleOut` |
| The actions of a team | `features/admin/equipos/views/EquipoAdminDetalleView.tsx` — the constant `ACCIONES` | Keeps the vocabulary of the interface; the CODES are the ones of `acciones_disponibles` |
| The search of participants | `features/admin/participantes/views/ParticipantesAdminView.tsx` — prop `estado?: EstadoParticipantesAdmin` | Reads `RT-IN-11` (`GET /administracion/participantes`) and `RT-ID-07`/`08` |
| The operational list of the payments | `features/admin/pagos/views/PagosAdminView.tsx` — prop `estado?: EstadoPagosAdmin` | Reads `RT-PG-04` (`GET /administracion/pagos`) with the FROZEN query `page, page_size, q, ordering, estado_operativo, estado_compra, estado_orden, tipo, desde, hasta` |
| The commercial detail of a payment | `features/admin/pagos/components/DetalleComercialPago.tsx` — prop `detalle?: AdminPagoDetalleOut` | Reads `RT-PG-07` (`GET /administracion/pagos/{compra_id}`) |
| The diagnosis of a payment | the same component, the disclosure | Reads `RT-PG-06` (`GET /pagos/ordenes/{orden_id}/intentos`) |
| The manual approval | `features/admin/pagos/components/DialogoAprobarPagoManual.tsx` | Reads `RT-PG-05` (`POST /administracion/pagos/{orden_pago_id}/aprobar-manual`), with the four 409 codes of the ledger |
| The bucket of a verdict | `features/admin/operaciones/utils/veredicto.adapter.ts` — `rolOperativoDesdeCodigo` | Completes the map with the codes of the administrative presenters when they freeze |
| The label of the parameters | `features/admin/operaciones/utils/parametros.ts` | Nothing: the shape of the query string is already the one of the ledger |

### The deletion checklist (mandatory in API-04, `T-082` of the workflow)

1. Delete `features/admin/pagos/fixtures/pagos-admin.fixture.ts` and replace
   it with the Zod mirror of `AdminPagoListItemOut`, `AdminPagoDetalleOut`
   and `PagoIntentosOut`.
2. Delete `features/admin/equipos/fixtures/equipos-admin.fixture.ts` and
   replace it with the Zod mirror of `AdminEquipoListItemOut` and
   `AdminEquipoDetalleOut`.
3. Delete `features/admin/inscripciones/fixtures/inscripciones-admin.fixture.ts`
   and replace it with the Zod mirror of `AdminInscripcionListItemOut` and
   `AdminInscripcionDetalleOut`.
4. Delete `features/admin/participantes/fixtures/participantes-admin.fixture.ts`
   and replace it with the Zod mirror of `AdminParticipanteListItemOut`.
5. Prove that **no** module outside `__tests__` imports a fixture, that there
   is no `catch` that falls back to a fixture and that there is no hidden
   route.
6. Replace the view-model types of `features/admin/*/types/*.types.ts` with
   the Zod mirrors (or keep them as the view contract and add the schemas
   next to them).
7. Bind the pagination of the six lists to the ONE shape of the envelope
   (`items/total/page/page_size/total_pages`).
8. Replace the reason of the S-10 by the `GenericForm` Mode 2/3 with the real
   Zod schema, and bind the 422 `field_errors` to it.
9. Enable the actions that have a registered route and keep the disabled
   state ONLY for the ones that do not.

---

## 12. Workload and review boundary

The tasks artefact of this change carries **no** `Review Workload Forecast**,
so no chain decision was required before the apply (the same precedent as
DOM-06, FND-07, FND-08, UI-01, UI-02, UI-03, API-01, API-02 and API-03).

**The real size of this packet is ~5 400 changed lines** (48 created files
and 6 modified route files), which exceeds the 400-line review budget by
roughly **13x**. There is **no commit** in this packet, so the budget is a
report and not a gate.

**Autonomous work units** (each one reviewable on its own, in this order):

| WU | Scope | Files |
|---|---|---|
| WU-1 | The view models, the adapter and the shared operational primitives | `features/admin/operaciones/{types,utils,components}/**` |
| WU-2 | The registrations: types, fixtures, the pool panel, the S-10 and the two views | `features/admin/inscripciones/**` |
| WU-3 | The teams: types, fixtures, the roster, the eligibility and the two views | `features/admin/equipos/**` |
| WU-4 | The participants: types, fixtures and the view | `features/admin/participantes/**` |
| WU-5 | The payments: types, fixtures, the three levels, the S-10 and the view | `features/admin/pagos/**` |
| WU-6 | The six route files | `app/(administracion)/administracion/{inscripciones,equipos,participantes,pagos}/**/page.tsx` |
| WU-7 | The five suites | `features/admin/*/__tests__/**` |

**Rollback:** revert WU-7 to WU-1. The rollback is confined to the 48 created
files and the 6 modified route files; the shared shell, the providers, the
theme, the other features and the backend are untouched, so reverting this
packet leaves the product exactly as it was. `git stash` was never invoked
and no commit was created.

**Concurrency:** the changes of the other agents in `src/app/**`,
`src/features/**` (notably `features/admin/{components,views,utils}/**`,
owned by FND-06) and `src/components/**` were **not touched, reverted or
merged**, and their rows of the board were not edited.

---

## 13. Acceptance criteria of the packet

- [x] The team detail explains the eligibility and the roster state **from
      the presenter fixtures**: the roster is `6 / 7–10` (plus the complete
      sentence for the screen reader) and the readiness is the
      `estado_operativo` of the presenter, with its label and its cause.
- [x] The payment UI **never derives a verdict from the raw order or attempt
      fields**: the only source is `estado_operativo.{codigo,etiqueta,descripcion}`
      and the provider layer is TEXT inside the collapsed diagnosis. The
      suite freezes the rule statically.
- [x] The candidate comparison, the route states and the fixture-removal
      ledger are **complete**: section 3 (the MCP record), section 4 (the ten
      states) and section 11 (the deletion checklist).
- [x] No endpoint, payload, field or business rule was invented; every
      vocabulary comes from the target backend or from the plan.
- [x] The only runtime command was the typecheck, and it is green.
- [ ] The five-width audit in a browser, the assistive-technology pass, the
      execution of the five suites and the lint pass are **DEFERRED** - the
      packet stays `verification_required`.
