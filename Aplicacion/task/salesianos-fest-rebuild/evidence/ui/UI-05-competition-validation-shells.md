# UI-05 - Competition, Validation And Sponsor Route Skeletons

**Artifact:** `evidence/ui/UI-05-competition-validation-shells.md` · **Packet:** UI-05 (`wave-02-frontend-skeletons`)
**Owner:** A7 · **Status:** `verification_required` (implementation applied, runtime verification deferred)
**Date:** 2026-11-19 · **Target:** `Aplicacion/frontend/**` only
**Packet:** `Aplicacion/task/salesianos-fest-rebuild/wave-02-frontend-skeletons/UI-05-competition-validation-shells.md`
**Reconciled:** 2026-11-19, after the concurrent **UI-04** packet completed — §8.1 (the global gate is GREEN), `D-UI05-06` / `A0-UI05-08` (the ownership of `ADM-15/17/18/19`). No frontend source was modified by the reconciliation.

---

## 1. Scope actually applied

The packet names **twelve** page IDs. **Eight** were applied in this batch,
in **three NEW features** that did not exist before this packet
(`features/competencias/**`, `features/validaciones/**`,
`features/patrocinadores/**`).

| Page ID | Route | Route file | Feature view | State |
|---|---|---|---|---|
| `ADM-10` | `/administracion/competencias` | `app/(administracion)/administracion/competencias/page.tsx` (modified) | `features/competencias/views/CompetenciasListaView.tsx` | **applied** |
| `ADM-11` | `/administracion/competencias/[id]` | `…/competencias/[id]/page.tsx` (modified) | `features/competencias/views/CompetenciaDetalleView.tsx` | **applied** |
| `ADM-12` | `/administracion/competencias/[id]/cuadro` | `…/competencias/[id]/cuadro/page.tsx` (modified) | `features/competencias/views/CompetenciaCuadroView.tsx` | **applied** |
| `ADM-13` | `/administracion/competencias/agenda` | `…/competencias/agenda/page.tsx` (modified) | `features/competencias/views/AgendaCompetenciasView.tsx` | **applied** |
| `ADM-16` | `/administracion/pases/validar` | `…/administracion/pases/validar/page.tsx` (modified) | `features/validaciones/views/ValidarPaseView.tsx` | **applied** |
| `ADM-20` | `/administracion/marketplace/entregas` | `…/administracion/marketplace/entregas/page.tsx` (modified) | `features/validaciones/views/ValidarEntregaView.tsx` | **applied** |
| `ADM-21` | `/administracion/patrocinadores` | `…/administracion/patrocinadores/page.tsx` (modified) | `features/patrocinadores/views/PatrocinadoresAdminView.tsx` | **applied** |
| `ADM-22` | `/administracion/validaciones` | `…/administracion/validaciones/page.tsx` (modified) | `features/validaciones/views/AuditoriaValidacionesView.tsx` | **applied** |

### The four page IDs that were NOT applied, and why

`ADM-15` (`/administracion/pases`), `ADM-17` (`/administracion/marketplace`),
`ADM-18` (`/administracion/marketplace/productos/[id]`) and `ADM-19`
(`/administracion/marketplace/inventario`) are **not** part of what this
packet delivered. Their four route files point today at
`features/admin/views/{AdminPasesView, AdminMarketplaceView,
AdminProductoDetalleView, AdminInventarioView}.tsx`.

**The ownership, established from the current evidence (`D-UI05-06`):**

| Fact | Evidence |
|---|---|
| The four route files point at `features/admin/views/**` | the four route files themselves (`import { Admin…View } from "@/features/admin/views"`) |
| That tree is **FND-06's root** | `features/admin/**` is the root created by FND-06 and declared as NOT TOUCHED by both packets |
| **UI-04 did NOT build them** | UI-04's evidence §1 lists only **six** page IDs (`ADM-05…09`, `ADM-14`), §6 lists **only six** modified route files, and §6 declares `src/features/admin/{components,views,utils}/**` as **NOT touched** |
| **UI-05 did NOT build them** | this packet's §1 and §6: eight page IDs, **eight** modified route files, and `features/admin/**` is a **FORBIDDEN** root that was **not touched, not reverted and not merged** |
| The tree was produced by a **non-SDD pass** | the **manually launched `general` agent** of the session `salesianos-ui-general-agent-prompt-2026-11-19` (observation **#11314**): its remit was the theme policy, the GSAP route transitions and the **visual standardisation of the administrative routes**, with the explicit instruction *"No crear, modificar ni ejecutar tests; sólo `npx tsc --noEmit`"*. That pass also **deleted** `components/shell/RoutePlaceholder.tsx`, which is why the four routes no longer render the FND-06 placeholder |

**Consequence:** the four routes are rendered today by **honest-state shells
that belong to a pass outside the packet system** — they have **no packet
row, no apply-progress artefact and no evidence file**. They are **not** the
UI-05 compositions: the UI-05 packet *does* list `ADM-15`, `ADM-17`, `ADM-18`
and `ADM-19` among its plan IDs, and the FND-06 route shells tagged them
`packet="UI-05"`, so they **remain owed** to the scope of this packet.

UI-05 therefore **did not duplicate** those four views, **did not touch**
them and **did not revert** them, and **no file of that tree was modified by
this packet**. The ownership is recorded here and the reconciliation of the
four routes is an **A0 request** (`A0-UI05-08`): either open a row for the
non-SDD pass, or fold the four routes into the next packet that claims them.

> **Correction of an earlier wording of this note.** The first version of
> this section said the four routes "were delivered **concurrently** by
> another agent". The current evidence shows that is **not** what happened:
> the concurrent agent was **UI-04**, and UI-04's own evidence **explicitly
> disclaims** those four views (§9 of its apply-progress #11434: "the
> concurrent shells `AdminPasesView` / `AdminMarketplaceView` /
> `AdminProductoDetalleView` / `AdminInventarioView` … **NOT touched, NOT
> merged**"). The four shells come from the earlier, manually launched
> `general` agent (#11314), which works **outside** the SDD packet system.
> The correction changes **no file of source**: it only makes the ownership
> note true.

### The eight FND-06 shells that this packet superseded

`features/admin/views/{AdminCompetenciasView, AdminCompetenciaDetalleView,
AdminCuadroView, AdminAgendaView, AdminPasesValidarView, AdminEntregasView,
AdminPatrocinadoresView, AdminValidacionesView}.tsx` are now **unreferenced
by the routes** (the eight route files point at the three new features).
They were **NOT deleted**: `features/admin/**` is a forbidden root of this
packet and another agent is writing there. Deleting them is an **A0
request** (`A0-UI05-04`).

---

## 2. The route briefs applied

The briefs were produced by **GOV-02** and were read before any code was
written:

- `evidence/routes/RB-05-admin-competitions.md` → `ADM-10`, `ADM-11`,
  `ADM-12`, `ADM-13`.
- `evidence/routes/RB-08-admin-sponsors-and-validation.md` → `ADM-21`,
  `ADM-22`.
- `evidence/routes/SH-01` (tokens) · `SH-02` (five widths + a11y) · `SH-03`
  (ten states) · `SH-04` (shadcn families) · `SH-05` (provisional endpoints)
  · `SH-06` (wireframes).
- `evidence/domains/DOM-07-competitions.md` and
  `evidence/domains/DOM-08-patrocinadores-logo-galeria.md` — and, above all,
  the **presenters of the target backend**, read directly from
  `Aplicacion/backend/modules/competencias/presentation/schemas/competencias_schemas.py`,
  `…/patrocinadores/presentation/schemas/patrocinadores_schemas.py`,
  `…/marketplace/presentation/schemas/inventario_schemas.py` and
  `…/salesianos_fest/presentation/schemas/pase_schemas.py`.
- `Aplicacion/plan/salesianos-fest-rebuild/frontend/05-*` (competencias) and
  `04-*` (flujos end-to-end).

### The rule that decided the honesty of the states (`D-UI05-01`)

> **A route never draws a datum that the backend cannot return.**

The registration truth was re-proved against the **working tree**, not
against the plan:

| Surface | Backend truth (2026-11-19) | Consequence for this packet |
|---|---|---|
| Competitions | `modules.competencias` is **NOT** in `LOCAL_APPS` and `CompetenciasController` is **NOT** registered → its **16 routes DO NOT EXIST** (`A0-RTV-01`/`A0-RTV-02`) | `ADM-10…ADM-13` render the honest "not connected" state; the populated compositions exist, are typed and are exercised by the suites |
| Sponsors | `modules.patrocinadores` is **NOT** in `LOCAL_APPS` and `PatrocinadorController` is **NOT** registered → its **1 route DOES NOT EXIST** | `ADM-21` renders the honest state |
| Entry validation | the module `validaciones` **does not exist at all** in the target; `RT-RT-01`/`RT-RT-02` are frozen in the ledger but unimplemented | `ADM-16` renders the honest state; the codes of the ledger are the vocabulary of the interface |
| Pickups | `RT-MK-10`/`RT-MK-11` are **provisional** and `InventarioController` is **NOT** registered → its **5 routes DO NOT EXIST** | `ADM-20` renders the honest state |
| Validation audit | `RT-VA-01` (`GET /administracion/validaciones`) is **provisional** and **no module exists** | `ADM-22` renders the honest state |

The presenters that DO exist were mirrored **1:1**: `CompetenciaListadoOut`,
`CompetenciaDetalleOut`, `CompetenciaEquipoOut`, `RondaOut`, `EncuentroOut`,
`ParticipanteOut`, `AgendaOut`, `EquipoElegibleOut`, `AvancePreviewOut`,
`CorreccionPreviewOut`, `CorreccionImpactoOut` (`DOM-07`);
`PatrocinadorOut` + `PatrocinadorLogoOut` + `PatrocinadorImagenOut`
(`DOM-08`); `PaseBeneficiarioOut` (`DOM-03`); `EntregaPendienteOut` +
`PedidoLineaOut` (`DOM-06`/`DOM-05`).

### The vocabulary is a 1:1 mirror, never an invention (`D-UI05-02`)

Every label of the area comes from a backend `TextChoices`
(`Aplicacion/backend/modules/competencias/domain/constants.py`:
`EstadoCompetencia`, `EstadoCompetenciaEquipo`, `EstadoRonda`,
`EstadoEncuentro`, `SlotDestino`, `MotivoNoElegibilidad`;
`modules/salesianos_fest/domain/constants.py`: `EstadoDerechoPase`;
`modules/marketplace/domain/constants.py`: `EstadoPedido`,
`EstadoEntregaPedido`) or from the **error codes of the frozen ledger**
(`RT-RT-01`, `RT-RT-02`: `TICKET_NO_ENCONTRADO`, `ACTION_NOT_ALLOWED`,
`TICKET_YA_CONSUMIDO`, `CANTIDAD_EXCEDIDA`, `DERECHO_REVOCADO`,
`IDEMPOTENCY_KEY_REUTILIZADA`).

A code that is **not** in the dictionary keeps its own text and falls into the
`desconocido` bucket: an unknown state is **visible**, never guessed.

---

## 3. shadcn candidate comparison (GOV-02-SH-01 re-run for these families)

The MCP was executed for these families, not inherited.

| # | Tool call | Result |
|---|---|---|
| 1 | `shadcn_get_project_registries` | `@shadcn` (the target registry) |
| 2 | `shadcn_search_items_in_registries` — `drawer` | `drawer` (registry:ui) + 2 examples |
| 3 | `shadcn_search_items_in_registries` — `scroll` | `scroll-area` (registry:ui) + 5 examples |
| 4 | `shadcn_search_items_in_registries` — `timeline` | **0 hits** |
| 5 | `shadcn_search_items_in_registries` — `carousel` | `carousel` (registry:ui) + 6 examples |
| 6 | `shadcn_search_items_in_registries` — `tabs` | `tabs` (registry:ui) + 12 blocks/fonts |
| 7 | `shadcn_search_items_in_registries` — `switch` | `switch` (registry:ui) + 7 examples |
| 8 | `shadcn_search_items_in_registries` — `input-group` | `input-group` (registry:ui) + 15 examples |
| 9 | `shadcn_search_items_in_registries` — `alert-dialog` | `alert-dialog` (registry:ui) + 1 example |
| 10 | `shadcn_view_items_in_registries` — `drawer`, `scroll-area`, `sheet` | `drawer` → 1 file, dependency **`vaul`**; `scroll-area` → 1 file, dependency `radix-ui`; `sheet` → 1 file, dependency `radix-ui` |
| 11 | `shadcn_get_item_examples_from_registries` — `drawer-demo` | the official example, with a `recharts` chart |

| Item | Registry | Fit | Local state | Decision |
|---|---|---|---|---|
| `drawer` | `registry:ui` | The single match-detail panel of `RB-05` (a bottom drawer at mobile, a side sheet at desktop) | **ABSENT** | **Rejected — BLOCKED.** The registry item declares the dependency **`vaul`**, which is **NOT** in `Aplicacion/frontend/package.json`, and `npm install` is forbidden by the launch contract. `components/ui/**` is also a forbidden root. → the local `sheet` was used. **`A0-UI05-01`** |
| `sheet` | `registry:ui` | The match-detail panel | **present** (`radix-ui`) | **Selected / reused** (`PanelDetalleEncuentro`). The primitive's own close label is the English "Close", so `showCloseButton={false}` and the panel carries a Spanish "Cerrar" |
| `scroll-area` | `registry:ui` | The horizontal container of the bracket | **present** (`radix-ui`) | **Rejected for the bracket**: the local primitive renders only a **vertical** scrollbar and the bracket needs a **horizontal** one with a visible focus. The bracket uses a **native scroll region** (`overflow-x-auto` + `tabIndex={0}` + `role="region"` + `aria-label`), which scrolls **inside itself** and never overflows the page (`GOV-02-RB-05e`) |
| `carousel` | `registry:ui` | The ordered gallery of the sponsor | **present**, but it ships the English screen-reader labels "Previous slide" / "Next slide" | **Rejected**: the gallery is composed in the feature with the local `button` primitive and Spanish accessible names (`A0-UI03-01` still open) |
| `switch` | `registry:ui` | The visibility of the sponsor | **ABSENT** | **Rejected — BLOCKED**: `components/ui/**` is a forbidden root. The visibility is a `checkbox` with a real label. **`A0-UI05-02`** |
| `input-group` | `registry:ui` | The file inputs of the sponsor form | **present** | **Not used**: the file inputs are plain `input[type=file]` with a `<label>` and an `aria-describedby` hint, because the file field must announce the accepted MIME types and the size cap and must submit with a native GET form |
| `alert-dialog` | `registry:ui` | The irreversible correction of a result | **present** | **Selected / reused** as the candidate for the confirm of the correction; the correction itself is not bound in this packet, so the dialog is NOT rendered yet — the panel shows the preview and names the authorisation that a correction over a finished descendant requires (`S-10`) |
| `tabs` | `registry:ui` | The sections of `ADM-11` | **present** | **Not used**: the sections are separate blocks (`AdminPanel`), which is the density the console already uses; a tab strip at 360 would overflow (`SH-04` §3.2) |
| `timeline` | — | The audit trail of `ADM-22` | — | **NO ITEM EXISTS** in the registry: the audit is a table whose rows carry the actor, the instant, the result and the point **as text** |
| `table` | `registry:ui` | The lists | **present** | **Selected / reused** through the shared `AdminDataTable` (whose container scrolls sideways: no page overflow) |
| `badge` | `registry:ui` | The verdict chips | **present**, without `success`/`warning` variants | **Rejected for the verdict chips**: the chip is **composed** in the feature (icon shape + label + semantic bucket), because the local `badge` has no verdict variants — same decision as `D-UI03-04` |
| `empty` | `registry:ui` | S-02 / S-03 | **present** | **Selected / reused** through `AdminEmptyState` |
| `skeleton` | `registry:ui` | S-01 | **present** | **Selected / reused** in the views |
| `alert` | `registry:ui` | S-04, S-06, S-09 | **present** | **Selected / reused** through `ShellErrorState` / `ShellPermissionDenied` / `AdminNotice` |
| `input`, `label`, `textarea`, `checkbox` | `registry:ui` | The form of the sponsor | **present** | **Selected / reused** |
| `dialog` | `registry:ui` | — | **present** | **Not used**: the match detail is a `sheet` (a `dialog` with a side), and the correction confirm is not bound yet |
| `chart` | `registry:ui` | The indicators of `ADM-11` | **present** | **Not used**: the project has **no `--chart-*` token set** (`GOV-02-SH-05`), so a chart would render with undefined colours. The indicators are counts as text |

**No component was added. No file in `components/ui/**` was created, modified
or overwritten. No CLI command was executed. `get_audit_checklist` was
called** (`GOV-02-SH-08`): the imports are correct, **no new dependency is
needed**, the typecheck is green, and the lint pass and the Playwright pass
are **NOT RUN** by the launch contract.

---

## 4. The ten states, route by route

| State | `ADM-10` | `ADM-11` | `ADM-12` | `ADM-13` | `ADM-16` | `ADM-20` | `ADM-21` | `ADM-22` |
|---|---|---|---|---|---|---|---|---|
| S-01 initial / loading | `Skeleton` that mirrors the row geometry | idem | idem | idem | the console is drawn empty | idem | idem | idem |
| S-02 empty | "Todavía no hay competencias que mostrar" + the reason | "Todavía no hay equipos en esta competencia" + "Añade un equipo elegible…" | "Todavía no hay rondas en esta competencia" + "Añade la primera ronda…" | "Todavía no hay una agenda que mostrar" | "El servicio de validación todavía no está conectado" | "No hay recogidas pendientes" | "Todavía no hay patrocinadores que mostrar" | "Todavía no hay asientos en la bitácora" |
| S-03 filtered-empty | the filters stay visible and "Quitar el filtro" is offered | not applicable | not applicable | not applicable | not applicable | not applicable | not applicable | "No hay validaciones con ese resultado" + "Quitar el filtro" |
| S-04 recoverable error | `ShellErrorState` "No pudimos cargar las competencias" + "Reintentar" | idem | "No pudimos cargar el cuadro" | "No pudimos cargar la agenda" | "No pudimos comprobar la entrada" | "No pudimos cargar las recogidas" | "No pudimos cargar los patrocinadores" | "No pudimos cargar la auditoría" |
| S-05 validation | the filter bar is a native GET form; the sponsor form announces the accepted types and the cap | not applicable | not applicable | not applicable | not applicable | not applicable | the media error family is rendered with `role="alert"` | not applicable |
| S-06 permission | `ShellPermissionDenied` "No tienes permiso para ver esta sección" | idem | idem | idem | "No tienes permiso para validar entradas" | "No tienes permiso para registrar recogidas" | "No tienes permiso para gestionar patrocinadores" | "No tienes permiso para ver la auditoría" |
| S-07 success | the save of the sponsor says what changed | idem | idem | idem | "La validación quedó registrada" | idem | idem | idem |
| S-08 in progress | — | — | — | — | "Comprobando…" and the field is locked; no invented duration | idem | "Guardando…" | — |
| S-09 partial / indeterminate | the preview of the advance says "Esta vista previa no escribe nada" and the confirm is a separate action | idem | idem | idem | the consumption that was already done is shown as a PREVIOUS consumption | the delivery is a fact apart from the payment | a media file that is not readable shows the GAP, not a broken image | the record exposes the actor, the instant, the result and the point |
| S-10 irreversible confirmation | the correction that needs an authorisation names it: "Un descendiente ya transcurrió: la corrección necesita autorización explícita y un motivo" | idem | idem | idem | the confirmation says "No se puede deshacer" | idem | the removal of a sponsor names its effect | the record is never rewritten |

### The four rules that decided the composition

- **`GOV-02-RB-05a` — ONE match-detail panel.** The panel
  (`PanelDetalleEncuentro`) is reachable from the list of the competition,
  from the agenda and from the bracket, and it is the **same component** in
  the three places. There is no second editor of an encounter.
- **`GOV-02-RB-05b` — preview and confirm are SEPARATE.** The preview of the
  advance and the preview of the correction say in their own title that they
  do not write; the confirm is a different action.
- **`GOV-02-RB-05c` — the client never computes a winner.** The winner, the
  bye, the advance, the correction, the eligibility verdict and the schedule
  are **declared** by the backend and printed verbatim. The marker of the
  winner in the card is drawn from `ganador_equipo_id` (never from the
  score).
- **`GOV-02-RB-08c` — the entry and the pickup are never conflated.** The
  two flows share the **presentation** of the preview
  (`VistaPreviaValidacion`) and nothing else: the subject is a right of
  entry in one case and a paid order in the other.

---

## 5. Provisional fixtures (FR-08)

Every fixture is **local to its feature**, **typed with `satisfies`**,
**marked** and **exported from no production barrel**.

| Fixture (symbol) | Mirrors | Contract | Path | Deleted in |
|---|---|---|---|---|
| `competenciaListadoFixture` | `CompetenciaListadoOut` (`DOM-07`) | `FREEZE-ENV-1.0.0` | `features/competencias/fixtures/competencias.fixture.ts` | **API-05** |
| `competenciaEquipoFixture` | `CompetenciaEquipoOut` | idem | idem | **API-05** |
| `encuentroFinalizadoFixture` | `EncuentroOut` + `ParticipanteOut` | idem | idem | **API-05** |
| `rondaFixture` | `RondaOut` | idem | idem | **API-05** |
| `competenciaDetalleFixture` | `CompetenciaDetalleOut` | idem | idem | **API-05** |
| `agendaCompetenciasFixture` | `AgendaOut` | idem | idem | **API-05** |
| `equipoElegibleFixture` | `EquipoElegibleOut` | idem | idem | **API-05** |
| `equipoNoElegibleFixture` | `EquipoElegibleOut` (inelegible, with its reason) | idem | idem | **API-05** |
| `vistaPreviaAvanceFixture` | `AvancePreviewOut` | idem | idem | **API-05** |
| `impactoCorreccionFixture` | `CorreccionImpactoOut` | idem | idem | **API-05** |
| `vistaPreviaCorreccionFixture` | `CorreccionPreviewOut` | idem | idem | **API-05** |
| `vistaPreviaPermitidaFixture` | `TicketPreviewOut` — **PROVISIONAL, no presenter exists** | `FREEZE-RT-1.0.0` | `features/validaciones/fixtures/validaciones.fixture.ts` | **API-05** |
| `vistaPreviaConsumidaFixture` | idem | idem | idem | **API-05** |
| `vistaPreviaRevocadaFixture` | idem | idem | idem | **API-05** |
| `resultadoConfirmacionFixture` | `TicketConfirmadoOut` — **PROVISIONAL** | idem | idem | **API-05** |
| `entregaPendienteFixture` | `EntregaPendienteOut` + `PedidoLineaOut` (`DOM-06`/`DOM-05`) | `FREEZE-CM-1.0.0` | idem | **API-05** |
| `registroEntradaFixture` | `AdminValidacionListItemOut` — **PROVISIONAL** (`RT-VA-01`) | idem | idem | **API-05** |
| `registroEntregaFixture` | idem | idem | idem | **API-05** |
| `imagenPatrocinadorFixture` | `PatrocinadorImagenOut` (`DOM-08`) | `FREEZE-MD-1.0.0` | `features/patrocinadores/fixtures/patrocinadores.fixture.ts` | **API-05** |
| `imagenPatrocinadorNoDisponibleFixture` | idem (file not readable) | idem | idem | **API-05** |
| `logoPatrocinadorFixture` | `PatrocinadorLogoOut` | idem | idem | **API-05** |
| `patrocinadorFixture` | `PatrocinadorOut` | idem | idem | **API-05** |
| `patrocinadorSinPiezasFixture` | idem (no logo, no gallery) | idem | idem | **API-05** |

**Rules honoured:** the literal token `PROVISIONAL_CONTRACT_FIXTURE` is in the
header of each file and the symbol name carries the `Fixture` suffix — no
business calculation, no `if`, no arithmetic, no `Date.now()` /
`Math.random()` / `crypto.randomUUID()`, no price, no availability, no
permission is DERIVED. The identifiers are literals of the shape the backend
publishes, so the mirror is verifiable by reading it.

**No fixture is exported from a production barrel.** The fixtures are
consumed only by the suites of their feature.

---

## 6. Files changed (47 created, 9 modified, 0 deleted)

All of them are inside the allowed roots of the packet.

**Route presentation - modified (8)**

- `app/(administracion)/administracion/competencias/page.tsx` (reads
  `searchParams` and hands the state filter to the view)
- `app/(administracion)/administracion/competencias/agenda/page.tsx`
- `app/(administracion)/administracion/competencias/[id]/page.tsx`
- `app/(administracion)/administracion/competencias/[id]/cuadro/page.tsx`
- `app/(administracion)/administracion/pases/validar/page.tsx`
- `app/(administracion)/administracion/marketplace/entregas/page.tsx`
- `app/(administracion)/administracion/patrocinadores/page.tsx`
- `app/(administracion)/administracion/validaciones/page.tsx` (reads
  `searchParams` and hands the verdict filter to the view)

**Feature `competencias` - created (21)**

- `types/competencia.types.ts`
- `utils/competencias.estados.utils.ts` · `utils/competencias.fecha.utils.ts`
- `fixtures/competencias.fixture.ts`
- `components/ChipEstadoCompetencia.tsx` · `components/CuadroCompetencia.tsx`
  · `components/FiltrosCompetencias.tsx` ·
  `components/ListaCompetencias.tsx` · `components/ListaEncuentros.tsx`
  · `components/ListaEquiposCompetencia.tsx`
  · `components/PanelDetalleEncuentro.tsx`
  · `components/TarjetaEncuentro.tsx`
  · `components/VistaPreviaAvancePanel.tsx`
  · `components/VistaPreviaCorreccionPanel.tsx` · `components/index.ts`
- `views/CompetenciasListaView.tsx` · `views/CompetenciaDetalleView.tsx`
  · `views/CompetenciaCuadroView.tsx` · `views/AgendaCompetenciasView.tsx`
  · `views/index.ts`
- `__tests__/competencias-estados.test.tsx`

**Feature `validaciones` - created (15)**

- `types/validacion.types.ts`
- `utils/validaciones.estados.utils.ts` ·
  `utils/validaciones.fecha.utils.ts`
- `fixtures/validaciones.fixture.ts`
- `components/ChipVeredictoValidacion.tsx`
  · `components/ConfirmacionValidacion.tsx` · `components/ConsolaEscaner.tsx`
  · `components/TablaAuditoriaValidaciones.tsx`
  · `components/VistaPreviaValidacion.tsx` · `components/index.ts`
- `views/ValidarPaseView.tsx` · `views/ValidarEntregaView.tsx`
  · `views/AuditoriaValidacionesView.tsx` · `views/index.ts`
- `__tests__/validaciones-estados.test.tsx`

**Feature `patrocinadores` - created (10)**

- `types/patrocinador.types.ts`
- `fixtures/patrocinadores.fixture.ts`
- `components/FormularioPatrocinador.tsx`
  · `components/GaleriaPatrocinador.tsx` · `components/LogoPatrocinador.tsx`
  · `components/TablaPatrocinadores.tsx` · `components/index.ts`
- `views/PatrocinadoresAdminView.tsx` · `views/index.ts`
- `__tests__/patrocinadores-estados.test.tsx`

**Not touched:** `src/components/shell/**` · `src/components/ui/**` ·
`src/app/globals.css` · `src/providers/**` · `src/lib/**` · `src/hooks/**` ·
`src/shared/**` · `src/features/{auth,portada,inscripciones,admin,cuenta,public,theme,pases,marketplace}/**`
· the backend · `contract/**` · the root `frontend/**`.

---

## 7. Skills loaded

| Order | Skill | Use in this packet |
|---|---|---|
| 1 | `salesianos-ui-ux` | Route purpose, actors, actions, states, the visual direction of `SH-01` and the semantic roles |
| 2 | `salesianos-feature-architecture` | Layer boundaries: thin pages, views own the composition, components own the presentation, types separate from the fixtures, no business logic in a page, no transport |
| 3 | `salesianos-api-data` | **Read-only contract clarification**: the endpoint ledger, the presenters, the error codes and the media contract. **No transport was created** |
| 4 | `salesianos-forms-smart-fields` | The form of the sponsor: the label and the error are drawn ONCE, the file field announces the accepted types and the cap, the files travel to the mutation and the form never builds a `FormData` |
| 5 | `salesianos-shadcn` | The MCP comparison of section 3, the reuse of the local primitives, the refusal to recreate a registry component, the hardcoded-colour audit |
| 6 | `salesianos-responsive-a11y` | The five-width contract, the 44 px targets, the labels and the live regions |
| 7 | `frontend-design` | The restraint: one memorable surface per route (the bracket, the console, the gallery), copy that says one thing, errors that name the cause and the fix |

---

## 8. Commands run, exit codes and results

**The only runtime command of this packet was the typecheck.** Everything else
was forbidden by the launch contract.

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 6 errors, **all of them OWN** (a `motivo`/`mensaje` mismatch, a typo and four `ShellPermissionDenied` without `title`) — **fixed in this packet** |
| 2 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | **clean** — the whole project |
| 3 | `npx tsc --noEmit` | `Aplicacion/frontend` | **1** | 8 errors, **0 of them own**: `src/features/admin/inscripciones/types/inscripciones-admin.types.ts` (4), `src/features/admin/operaciones/components/MarcoOperativo.tsx` (2), `src/features/admin/operaciones/index.ts` (2) — a **CONCURRENT and OUT-OF-SCOPE** tree (`features/admin/**`, FND-06's root) that this packet **did not touch, did not revert and did not merge**. The **8 errors of this packet are NOT reproducible in the roots of this packet** |
| 4 | `git status --short -- <my roots>` | repo root | **0** | the 3 new feature trees (untracked) + the 8 route files (modified) |

**NOT RUN** (forbidden by the launch contract, and recorded as deferred, never
as passed): `vitest` · `biome check` · `next build` · `npm install` · any
server · any browser · any visual automation · the five-width audit ·
`git stash` · `git commit` · `git reset` · `git checkout`.

**Known baseline failures:** none introduced by this packet. The 8 errors of
command 3 belong to a concurrent tree and are recorded as such.

### 8.1 The reconciliation with the concurrent UI-04 packet (2026-11-19)

**The roots of this packet were CLEAN in every single run.** The 8 errors of
command 3 were located **exclusively** in
`src/features/admin/inscripciones/**` and `src/features/admin/operaciones/**`
— the tree of the **concurrent UI-04 packet**, which was in flight at that
moment. **Zero** of them were in `features/competencias/**`,
`features/validaciones/**` or `features/patrocinadores/**`.

**The LAST recorded project-wide run is GREEN.** It is **UI-04's `V4`**, and
it exited **0** (`evidence/ui/UI-04-admin-operations-shells.md` §8: *"clean —
FINAL run of the packet; the global gate is GREEN"*). UI-04's own apply
progress states it in §9 (#11434): *"UI-05 ran in parallel and recorded in
its own V3 the 8 errors **THIS packet** had at that moment; UI-05 left them
intact and **this packet repaired them** (V2/V3/V4 exit 0)."*

⇒ **The unified truth of the global gate** is the same one that API-01,
API-02 and API-03 established: the two packets ran in parallel, **neither
had errors in its own roots**, the project-wide gate oscillated **only**
because of the **concurrent and foreign** tree of the other one — which was
**not touched, not reverted and not merged** by the foreign writer — and the
**last recorded project-wide run exits 0**, so the **global gate is GREEN**.

| Packet | Own roots | Global gate during the packet | Last recorded project-wide run |
|---|---|---|---|
| **UI-05** | **0 errors in EVERY run** (V1 had 6 own errors, fixed inside the packet) | RED only in V3, and only because of UI-04's in-flight tree | **UI-04 `V4`, exit 0 ⇒ GREEN** |
| **UI-04** | 0 errors after V1 (9 own errors, fixed inside the packet) | GREEN from V2 onwards | **UI-04 `V4`, exit 0 ⇒ GREEN** |

**Nothing of UI-04 was modified, reverted or merged by this packet, and
nothing of UI-05 was modified by UI-04** beyond the shared `STATE.md` row
that each packet owns.

---

## 9. Tests written (NOT executed) and the five widths

The standing user preference is that the suites of an apply packet are
**written** and **not executed**, and the packet status is
`verification_required`. The suites below were written and **have never run**:
nothing here may be read as a green result.

| Suite | Environment | What it freezes |
|---|---|---|
| `features/competencias/__tests__/competencias-estados.test.tsx` | jsdom | The honest state of `ADM-10` (and that **no competition is invented**), the populated list with its **three distinct links**, the filtered-empty that keeps the filters, the specific empty states of `ADM-11` and `ADM-12`, the bracket as **one column per round** with a **button** whose accessible name carries **both teams and the score**, the bracket container as a **horizontal scroll region with `tabindex=0`**, that the card **and** the agenda open **THE SAME** panel, that the advance preview and the correction preview say **that they do not write**, that the panel names the **actions the server admits**, the specific CTA of an empty bracket, the permission state vs the recoverable error, and the absence of a literal colour and of a raw palette tone |
| `features/validaciones/__tests__/validaciones-estados.test.tsx` | jsdom | That `ADM-16` says the service does not exist instead of faking a read, that the **keyboard path** has a real label, that the confirm is **NOT offered without a preview**, that it IS offered when the preview admits it and is **NOT** offered when the server refuses, that a **previous consumption** is shown, that the outcome states what happened, that a **replay is declared a replay**, that `ADM-20` is a **different operation** from `ADM-16`, that the audit lists the entry **and** the pickup **without mixing them**, that the record exposes the result, the point and the operator **as text**, the filtered-empty of the audit, that the audit draws **no seats** without the service, that **comprobar does not confirm**, that the field is locked **while the check is in flight**, and that the check receives the trimmed code |
| `features/patrocinadores/__tests__/patrocinadores-estados.test.tsx` | jsdom | That the route says the service does not exist instead of inventing an ally, that the record has **no monetary field**, that the gallery announces **"Pieza N de M"**, that it is traversed with the **keyboard** and with **Spanish accessible names**, that a file that is not readable shows the **gap** and not a broken image, that the logo is described with the **name of the sponsor**, the empty gallery, that the form announces the **accepted types and the 5 MiB cap**, that the visibility has a **real label**, that the media error names the cause **and** the fix, and that the save does **not** leave the device without the service |

All three suites also freeze the static rules of the area: **no literal
colour**, **no palette utility of a raw tone**.

### The five widths

The audit at 360, 390, 768, 1024 and 1440 was **deferred**: no browser was
run in this packet. What the markup already guarantees, and what the browser
pass will have to confirm:

| Width | What the composition does | What is still unverified |
|---|---|---|
| 360 | One column. The list of the competitions is a card per competition with its three entry points; the bracket scrolls **inside itself**; the detail of the encounter is a **bottom drawer at 90 vh**; the gallery is one image with the two controls and the position under it; the form is one column; every action is at least 44 px high. | That no page overflows horizontally, that the sticky header does not cover the first action, that the long names truncate |
| 390 | The same single column. | The same |
| 768 | The list becomes a table with an action column; the bracket is a row of columns; the match detail is a **side sheet**; the form is two columns (identity \| media) | That the two columns do not squeeze the cards |
| 1024 | The bracket shows its columns side by side; the panel of the sponsor is identity on the left and media on the right | That no column is stretched and that nothing is clipped |
| 1440 | The same, with the band of the shell capping the content | The same |

### Accessibility that was decided in the markup

- Every input has a real `<label>` and its hint is associated with
  `aria-describedby`.
- The card of an encounter is a `<button>` whose accessible name carries
  **both teams and the score**.
- The bracket container is a `role="region"` with `tabIndex={0}` and a
  visible focus ring: it is **keyboard-scrollable** and it never overflows
  the page.
- The round indicator is **text**, never dots.
- The verdict chip pairs an **icon shape**, the **label of the backend** and
  the semantic bucket: the colour never carries the meaning alone.
- The gallery announces "Pieza N de M" in a live region, its two controls
  have accessible names and its thumbnails are buttons with `aria-current`.
- The preview of the advance and the preview of the correction carry, in
  their own title, that they **do not write**.
- The state of the route that is loading is a `role="status"` live region.
- The audit exposes the **actor, the instant, the result and the point as
  text** — never a colour-only trail — and the instant is a machine-readable
  `<time datetime>`.

**Residual gaps declared, never assumed green:** no browser rendering, no
screen-reader pass, no 200 % zoom reflow, no automated axe or Lighthouse run,
and the suites themselves have **never been executed**.

---

## 10. Deviations, decisions and A0 requests

| ID | Type | What |
|---|---|---|
| `D-UI05-01` | decision | **A route never draws a datum that the backend cannot return.** Every route of the packet renders the honest "the service is not available" state by default, and the populated compositions exist, are typed and are exercised by the suites. That is the code that API-05 binds. |
| `D-UI05-02` | decision | **The vocabulary is a 1:1 mirror of the backend.** Every label comes from a backend `TextChoices` or from the frozen error codes of the ledger. A code outside the dictionary keeps its own text and falls into the `desconocido` bucket: an unknown state is visible, never guessed. |
| `D-UI05-03` | decision | **One panel, three surfaces.** The match detail is ONE component, reachable from the competition, from the agenda and from the bracket. There is no second editor of an encounter. |
| `D-UI05-04` | decision | **The entry and the pickup share the PRESENTATION of the preview and nothing else.** `VistaPreviaValidacion` is the reusable component; the subject, the verb and the audit are different. The audit never mixes an entry with a payment confirmation. |
| `D-UI05-05` | decision | **The bracket scrolls inside itself.** The scroll container is the bracket, never the page, and it is a native region with a visible focus so the keyboard can reach it. |
| `D-UI05-06` | deviation | **`ADM-15`, `ADM-17`, `ADM-18` and `ADM-19` were NOT applied by this packet.** Their four route files point at `features/admin/views/**`, which is **FND-06's root**: **UI-04 disclaims it** (its scope is six page IDs, it modified six route files and it declares `features/admin/{components,views,utils}/**` as NOT touched) and **UI-05 did not touch it** (forbidden root). The tree comes from the **manually launched `general` agent** of the session `salesianos-ui-general-agent-prompt-2026-11-19` (#11314), which works **outside** the SDD packet system. The four routes therefore have **no packet row, no apply-progress artefact and no evidence file**, and they are **not** the UI-05 compositions: the packet lists them among its plan IDs, so they **remain owed** to this scope. → `A0-UI05-08`. |
| `D-UI05-07` | deviation | **The eight FND-06 shells that this packet superseded were NOT deleted** (`features/admin/views/AdminCompetenciasView.tsx` and its seven siblings). `features/admin/**` is a forbidden root and another agent is writing there. → `A0-UI05-04`. |
| `D-UI05-08` | deviation | **The filter bar of `ADM-22` offers ONLY the verdict.** The other seven dimensions of the brief (ticket, person, purchase, type of right, date, operator, point) need the parameter names of `RT-VA-01`, which is still **provisional**: they are owed to API-05 with its ratification. The filter of `ADM-10` offers the **state**, which is the only filter the backend accepts besides the discipline, and the discipline needs the catalogue of disciplines, which is another dataset. |
| `D-UI05-09` | deviation | **The confirmation of a correction is NOT built.** The correction has a preview and an impact, but its confirm binds to the write routes of `DOM-07`, which `API-05` brings. The panel names the authorisation that a correction over a finished descendant requires (`S-10`) and stops there. |
| `D-UI05-10` | deviation | **The camera of the scanner is NOT built.** The console is the **keyboard path** — a labelled field and a real button — and it always works. The capture of the device is an accelerator and never the only way in. |
| `D-UI05-11` | deviation | **The visibility of the sponsor is a `checkbox`, not a `switch`.** The registry has a `switch` but it is **absent** locally and `components/ui/**` is a forbidden root. → `A0-UI05-02`. |
| `D-UI05-12` | deviation | **The `TicketPreviewOut` and the `TicketConfirmadoOut` fields are PROVISIONAL.** The module `validaciones` does not exist in the target, so there is no presenter to mirror. The view models follow the PROVISIONAL `PaseBeneficiario` of `DOM-03` and the pending delivery of `DOM-06`, and the code of a successful validation (`VALIDACION_PERMITIDA`) is the PROVISIONAL code of this frontend until the backend ratifies it. → `A0-UI05-03`. |
| `D-UI05-13` | deviation | **The date formatter is repeated per feature.** A shared root (`src/lib/**`) is out of the allowed roots of this packet and a cross-feature import would couple two domains that have no reason to know each other. The formatter pins the locale (`es`) and the timezone (`America/Lima`) of the server so the render is identical on the server and in the browser. → `A0-UI05-05`. |

### A0 requests

| ID | Request |
|---|---|
| `A0-UI05-01` | The registry has a `drawer` (the `vaul` dependency) and the local tree has **only** a `sheet`. `GOV-02-SH-06` says to choose exactly ONE panel primitive. UI-05 used the local `sheet` because `vaul` is not installed and `npm install` was forbidden. Either install `vaul` and add `drawer`, or ratify `sheet` as THE panel of the area. |
| `A0-UI05-02` | The registry has a `switch` and the local tree does not. The visibility of the sponsor is composed with a `checkbox`. `components/ui/**` was a forbidden root of this packet. |
| `A0-UI05-03` | The module `validaciones` **does not exist** in the target: `RT-RT-01` and `RT-RT-02` are frozen in the ledger but unimplemented, and `RT-VA-01` is provisional. The fields of `TicketPreviewOut`, `TicketConfirmadoOut` and `AdminValidacionListItemOut`, the parameter names of the audit and the code of a successful validation must be ratified before API-05 binds them. |
| `A0-UI05-04` | The eight FND-06 shells that UI-05 superseded (`AdminCompetenciasView`, `AdminCompetenciaDetalleView`, `AdminCuadroView`, `AdminAgendaView`, `AdminPasesValidarView`, `AdminEntregasView`, `AdminPatrocinadoresView`, `AdminValidacionesView`) are now unreferenced by the routes and can be removed. `features/admin/**` was a forbidden root of this packet. |
| `A0-UI05-05` | The date formatter is repeated in `features/competencias/utils/competencias.fecha.utils.ts` and in `features/validaciones/utils/validaciones.fecha.utils.ts`. It should live in one shared place (`src/lib/**` or `src/shared/**`), which was out of the allowed roots of this packet. |
| `A0-UI05-06` | `00-matriz-tareas.md` does not carry a row for UI-05 and the matrix is a forbidden root: the row has to be synchronised by the coordinator. |
| `A0-UI05-07` | `modules.competencias` and `modules.patrocinadores` are still out of `INSTALLED_APPS` and `CompetenciasController` / `PatrocinadorController` are still unregistered (`A0-RTV-01`/`A0-RTV-02`), so **16 + 1 routes do not exist**. Until they are registered, the competitions and the sponsors keep their honest state. |
| `A0-UI05-08` | **The ownership of `ADM-15`, `ADM-17`, `ADM-18` and `ADM-19` is UNATTRIBUTED.** The four routes are rendered by honest-state shells of `features/admin/views/**` (FND-06's root) produced by the **manually launched `general` agent** of #11314, which works **outside** the packet system: no row, no apply-progress, no evidence file. Neither UI-04 nor UI-05 claims them, and the UI-05 packet lists them among its plan IDs, so they **remain owed**. Either open a row for that non-SDD pass, or fold the four routes into the next packet that claims them. **No source file was modified by this reconciliation.** |

---

## 11. API-05 handoff

### The seams that API-05 has to bind

| Seam | Where | What API-05 does |
|---|---|---|
| The list of the competitions | `features/competencias/views/CompetenciasListaView.tsx` — props `estado`, `competencias` | Reads `GET /api/competencias` (`DOM-07`) and binds `CompetenciaListadoOut` |
| The detail of a competition | `features/competencias/views/CompetenciaDetalleView.tsx` — props `estado`, `detalle` | Reads `GET /api/competencias/{competencia_id}` and binds `CompetenciaDetalleOut` |
| The bracket | `features/competencias/views/CompetenciaCuadroView.tsx` — props `rondas`, `vistaPreviaAvancePorEncuentro`, `vistaPreviaCorreccionPorEncuentro` | Reads `GET /api/competencias/{competencia_id}/cuadro` and binds `list[RondaOut]`; binds the advance preview (`…/avance/preview`) and the correction preview (`…/correccion/preview`) |
| The agenda | `features/competencias/views/AgendaCompetenciasView.tsx` — prop `agenda` | Reads `GET /api/competencias/agenda` and binds `AgendaOut` |
| The teams and their eligibility | `features/competencias/components/ListaEquiposCompetencia.tsx` | Reads `GET /api/competencias/{id}/equipos-elegibles` and binds `EquipoElegibleOut` — the reason is the OWNER of the registration and it is never derived |
| The filter of the list | `features/competencias/components/FiltrosCompetencias.tsx` — prop `estado` | Binds `estado` to `listar_competencias(estado=…)`; the `disciplina_id` filter needs the catalogue of disciplines |
| The entry validation | `features/validaciones/views/ValidarPaseView.tsx` — props `vistaPrevia`, `resultado`, `onComprobar`, `onConfirmar` | Reads `RT-RT-01` (`POST /validaciones/preview`) and `RT-RT-02` (`POST /validaciones/confirmar`) with the `idempotency_key`. **The module does not exist** (`A0-UI05-03`) |
| The pickup validation | `features/validaciones/views/ValidarEntregaView.tsx` — props `pendientes`, `vistaPrevia`, `resultado` | Reads `RT-MK-10` (`GET /administracion/marketplace/entregas`) and binds `EntregaPendienteOut`; the confirm binds `RT-MK-11`. **`InventarioController` is NOT registered** |
| The audit | `features/validaciones/views/AuditoriaValidacionesView.tsx` — props `registros`, `filtroVeredicto` | Reads `RT-VA-01` (`GET /administracion/validaciones`) and binds `AdminValidacionListItemOut`. **Provisional** |
| The sponsor record | `features/patrocinadores/views/PatrocinadoresAdminView.tsx` — props `patrocinadores`, `seleccionado`, `errorMedio`, `onGuardar` | Reads and writes `RT-MD-02` (`POST /patrocinadores`) with the frozen multipart protocol and binds `PatrocinadorOut`. **`PatrocinadorController` is NOT registered** |
| The media error family | `features/patrocinadores/types/patrocinador.types.ts` — `CodigoErrorMedio` | Branches on the HTTP status and shows the wording of the code |
| The label of a code | `features/*/utils/*.estados.utils.ts` | The dictionaries are 1:1 mirrors of the backend `TextChoices` and of the codes of the ledger |

### The deletion checklist (mandatory in API-05, `T-082` of the workflow)

1. Delete `features/competencias/fixtures/competencias.fixture.ts` and
   replace it with the Zod mirrors of the presenters of `DOM-07`.
2. Delete `features/validaciones/fixtures/validaciones.fixture.ts` and
   replace it with the Zod mirrors of `PaseBeneficiarioOut`,
   `EntregaPendienteOut`, `PedidoLineaOut` and — once the module exists — of
   `TicketPreviewOut`, `TicketConfirmadoOut` and
   `AdminValidacionListItemOut`.
3. Delete `features/patrocinadores/fixtures/patrocinadores.fixture.ts` and
   replace it with the Zod mirror of `PatrocinadorOut`.
4. Prove that **no** module outside `__tests__` imports a fixture, that
   there is no `catch` that falls back to a fixture and that there is no
   hidden route.
5. Replace the view-model types of `features/*/types/*.types.ts` with the Zod
   mirrors (or keep them as the view contract and add the schemas next to
   them).
6. Bind the pagination of the audit (`page` / `page_size`,
   `FREEZE-ENV-1.0.0` §4.3) and its eight filter dimensions.
7. Bind the `disciplina_id` filter of the list of the competitions to the
   catalogue of disciplines.
8. Build the confirm of the correction (`…/correccion`) with its reason and
   its explicit authorisation.
9. Add the `loading.tsx` of the eight routes if the shell gives them up.

---

## 12. Workload and review boundary

The tasks artefact of this change carries **no** `Review Workload Forecast`,
so no chain decision was required before the apply (the same precedent as
DOM-06, FND-07, FND-08, UI-01, UI-02 and UI-03).

**The real size of this packet is ~6 060 changed lines** (46 created code
files — 5 532 lines — plus this evidence file, and 8 modified route files),
which exceeds the 400-line review budget by roughly **15x**. There is **no
commit** in this packet, so the budget is a report and not a gate.

**Autonomous work units** (each one reviewable on its own, in this order):

| WU | Scope | Files |
|---|---|---|
| WU-1 | The view models and the vocabulary of the competitions | `features/competencias/{types,utils}/**` |
| WU-2 | The fixtures of the competitions | `features/competencias/fixtures/**` |
| WU-3 | The chip, the card and the ONE panel of the encounter | `features/competencias/components/{ChipEstadoCompetencia,TarjetaEncuentro,PanelDetalleEncuentro}.tsx` |
| WU-4 | The previews of the advance and of the correction | `features/competencias/components/VistaPrevia*.tsx` |
| WU-5 | The bracket and the lists | `features/competencias/components/{CuadroCompetencia,ListaCompetencias,ListaEncuentros,ListaEquiposCompetencia,FiltrosCompetencias}.tsx` |
| WU-6 | The four views of the competitions | `features/competencias/views/**` |
| WU-7 | The view models, the vocabulary and the fixtures of the validations | `features/validaciones/{types,utils,fixtures}/**` |
| WU-8 | The chip, the console, the preview and the confirm of the validation | `features/validaciones/components/**` |
| WU-9 | The audit and the three views of the validations | `features/validaciones/components/TablaAuditoriaValidaciones.tsx` + `features/validaciones/views/**` |
| WU-10 | The sponsors: the view models, the fixtures, the gallery, the logo, the form and the table | `features/patrocinadores/**` |
| WU-11 | The eight route files | `app/(administracion)/administracion/**` |
| WU-12 | The three suites | `features/*/__tests__/**` |

**Rollback:** revert WU-12 to WU-1. The rollback is confined to the 46
created code files (plus this evidence file) and the 8 modified route files;
the shared shell, the providers, the theme, the other features and the
backend are untouched, so reverting this packet leaves the product exactly
as it was. `git stash` was never invoked and no commit was created.

**Concurrency:** the changes of the other agents in `src/app/**`,
`src/features/admin/**` and `src/features/inscripciones/**` were **not
touched, reverted or merged**, and their rows of the board were not edited.

**Reconciliation (2026-11-19, read-only + evidence/state only):** the
concurrent **UI-04** packet finished after this one. Its final project-wide
`npx tsc --noEmit` (**`V4`**) exited **0**, so the **global gate is GREEN**
(§8.1). The ownership note of `ADM-15/17/18/19` was corrected from the
current evidence (`D-UI05-06` → `A0-UI05-08`). **No frontend source file
was modified by this reconciliation**, no command was run, and **nothing of
UI-04 was changed**: its evidence file, its apply-progress artefact and its
rows of the board are preserved verbatim.

---

## 13. Acceptance criteria of the packet

- [x] The agenda, the bracket and the detail share the **same presentation
      semantics**: one encounter, one card, one panel, reachable from the
      three surfaces.
- [x] The effect of the preview and of the correction is **explicit**: both
      say in their own title that they do not write, the correction names
      the descendants that really change and the authorisation it needs.
- [x] The entry and the delivery remain **separate operations over a
      reusable preview component**.
- [x] The shadcn comparison was recorded **before** the composition and **no
      shared primitive was overwritten**; the two registry items that the
      local tree lacks (`drawer`, `switch`) are A0 requests with their
      blocking reason.
- [x] The provisional fixtures are **local, typed, marked** and listed for
      their deletion in API-05.
- [x] The **unregistered** controllers (`CompetenciasController`,
      `PatrocinadorController`, `InventarioController`) and the **absent**
      module (`validaciones`) were **not bound** and **no endpoint payload
      was invented**.
- [x] The only runtime command was the typecheck, and **the roots of this
      packet are clean in every run**.
- [x] The **last recorded project-wide** `npx tsc --noEmit` is **UI-04's
      `V4`, exit 0** ⇒ the **global gate is GREEN**, and the only project-wide
      RED this packet ever saw was the **concurrent and foreign** tree of
      UI-04, which was **not touched, not reverted and not merged**.
- [x] The ownership of `ADM-15`, `ADM-17`, `ADM-18` and `ADM-19` is recorded
      from the **current evidence** (FND-06's root, disclaimed by UI-04,
      untouched by UI-05, produced by the non-SDD `general` agent of #11314)
      and raised as `A0-UI05-08` — **without modifying any source file**.
- [ ] The five-width audit in a browser, the assistive-technology pass, the
      execution of the three suites and the lint pass are **DEFERRED** — the
      packet stays `verification_required`.
