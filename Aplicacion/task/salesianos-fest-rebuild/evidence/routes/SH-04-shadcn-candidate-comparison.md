# SH-04 — shadcn Candidate Comparison (mandatory pre-implementation register)

**Artifact:** `evidence/routes/SH-04-shadcn-candidate-comparison.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — comparison performed via shadcn MCP; **no component was added**
**Date:** 2026-11-19
**Authority:** `.opencode/skills/salesianos-shadcn/SKILL.md` (Hard Rules 1–9, Execution Steps 1–8) · `.opencode/agents/ui-ux-designer.md` (candidate table contract) · `Aplicacion/frontend/components.json`

---

## 1. What Was Actually Executed

| Step | Tool call | Result |
|---|---|---|
| 1 | `shadcn_get_project_registries` | **Returned an EMPTY registry list.** The MCP resolves `components.json` from the current working directory; the repository root has no `components.json`. The project file lives at `Aplicacion/frontend/components.json`. |
| 2 | `shadcn_list_items_in_registries` (no type filter) | **471 items** in `@shadcn`: 66 `registry:ui`, 16 `registry:block` (sidebar) + 1 dashboard + 5 login + 5 signup + 62 chart blocks + 2 style + 1 lib + 1 hook + 9 theme + 32 font + ~270 `registry:example`. |
| 3 | `shadcn_list_items_in_registries` (types=`component`) | **0 items.** The registry index exposes components under `registry:ui`, not `registry:component`. Query by `registry:ui` or use the untyped listing. |
| 4 | `shadcn_search_items_in_registries` — "data table" | 4 hits: `dashboard-01`, `sidebar-11`, `sidebar-05`, `sidebar-02` |
| 5 | `shadcn_search_items_in_registries` — "sidebar navigation" | 2 hits: `sidebar-08`, `sidebar-01` |
| 6 | `shadcn_search_items_in_registries` — "login" | 7 hits: `login-01..05`, `sidebar-04`, `sidebar-01` |
| 7 | `shadcn_search_items_in_registries` — "dialog confirm" / "form wizard input" / "chart metrics" / "sheet drawer detail" | **0 hits for all four.** Multi-word queries are matched too narrowly; the search is lexical, not semantic. Single-word queries (`sidebar`, `login`) work. **Tooling constraint recorded for later packets.** |
| 8 | `shadcn_view_items_in_registries` — `sidebar-01`, `sidebar-02`, `sidebar-13`, `sidebar-16`, `dashboard-01` | Descriptions, file counts and dependencies (see §4) |
| 9 | `shadcn_get_item_examples_from_registries` — "data-table-demo" | Full source of the official data-table example (see §4, **critical risk R-01**) |

**Tooling findings that must reach the next packets:**
- **T-A** The MCP cannot see the project registries unless `components.json` is resolvable from the process working directory. Callers must either run from `Aplicacion/frontend` or pass `registries: ["@shadcn"]` explicitly.
- **T-B** `types: ["component"]` returns nothing; the registry exposes `registry:ui`.
- **T-C** Multi-word fuzzy queries return 0 hits. Search with single tokens and filter locally.
- **T-D** `get_project_registries` returning empty is **not** evidence that the project has no registry — cross-check `components.json` directly.

---

## 2. Registry And Style State (as read from disk)

| File | `style` | `registries` | Notes |
|---|---|---|---|
| `Aplicacion/frontend/components.json` | `radix-nova` | `{"@shadcn": "https://ui.shadcn.com/r/styles/radix-nova/{name}.json"}` | **Target root.** Currently modified in the working tree by concurrent user activity (see §6). |
| `frontend/components.json` (frozen) | `radix-nova` | `{}` (empty) | Frozen evidence. Same style, **no registry entry** — this is why the MCP's registry list is empty when it resolves the frozen root. |

**Decision:** the target registry is `@shadcn` at style `radix-nova`. The frozen root's empty `registries` map is the reason the MCP reports nothing, **not** an indication that the project is unconfigured. Do **not** reconfigure or duplicate the shadcn MCP (`salesianos-shadcn` Hard Rule 2).

---

## 3. Candidate Comparison — Route Families

The table format is fixed by `.opencode/agents/ui-ux-designer.md`: *item, registry, fit, role support, mobile behavior, customization cost, risks, recommendation*.

### 3.1 Admin shell / navigation — used by ADM-01…ADM-22

| Item | Registry | Fit | Role support | Mobile behaviour | Customisation cost | Risks | Recommendation |
|---|---|---|---|---|---|---|---|
| `sidebar` (component) | `registry:ui` | **Core.** The `sidebar` component provides `SidebarProvider`, `Sidebar`, `SidebarContent`, `SidebarGroup`, `SidebarMenu`, `SidebarInset`, `SidebarTrigger`, and the `collapsible` / `offcanvas` / `inset` variants. | Full (group, collapsible group, menu, sub, badge, action) | `offcanvas` variant = drawer; `collapsible="icon"` = rail at 768–1024 | Low — wrap, do not fork | Registry UI is generic; the legacy app already has a customised `frontend/src/components/ui/sidebar.tsx` that **must be diffed before replacing** | **Selected as the base.** Reuse the existing local `sidebar.tsx` if its customisations are intentional; otherwise add from `@shadcn/sidebar`. |
| `sidebar-01` | block | "A simple sidebar with navigation grouped by section" — maps exactly to the plan's required grouping *Deportivo / Ventas y entradas / Configuración y personas* (`frontend/04` §1) | Grouped sections, no submenu depth beyond one | Collapsible like the component | Low | Block overwrites `components/ui/sidebar.tsx`; 4 files | **Preferred block reference** for ADM-01…ADM-22 shell. Use as a *reference*, then compose the local file. |
| `sidebar-02` | block | "A sidebar with collapsible sections" | Collapsible groups | Collapses to icon rail | Low | Same overwrite risk | **Candidate.** Use only if the grouping must be collapsible on desktop too; the plan asks for "secciones desplegables". |
| `sidebar-07` | block | "A sidebar that collapses to icons" | — | Icon rail | Low | Icon-only navigation hurts discoverability of 22 destinations | **Rejected for the primary shell**; acceptable for a secondary rail. |
| `sidebar-13` | block | "A sidebar in a dialog" | — | Mobile drawer | Low | 2 files only; minimal | **Candidate for the ≤768 mobile shell.** |
| `sidebar-08` | block | "An inset sidebar with secondary navigation" | Two levels | Inset | Medium | Visual weight; the app has one nav level + contextual tabs | **Rejected.** Adds a second navigation layer the plan does not need. |
| `sidebar-16` | block | "A sidebar with a sticky site header" | — | — | Medium | 8 files | **Candidate** if the admin shell adopts a persistent header with the edition selector. |
| `sidebar-11` | block | "A sidebar with a collapsible file tree" | File tree | — | Medium | Wrong metaphor (no file tree in this product) | **Rejected.** |
| `sidebar-05` | block | "A sidebar with collapsible submenus" | Submenus | — | Medium | Depth not required | **Candidate**, lower priority than `sidebar-01`/`sidebar-02`. |
| `dashboard-01` | block | "A dashboard with sidebar, charts and data table" | Sidebar + charts + data table | — | **High** | **Depends on `@tanstack/react-table`, `@dnd-kit/*`, `@tabler/icons-react`, `zod`** — pulls a *second* table library and a *second* icon set into a project that already uses `@tanstack/react-table@^8.21.3` and Lucide. Also drags in drag-and-drop. | **Rejected as an add.** Use as a **visual reference only** for ADM-01. If any part is wanted, it must be re-composed by hand over the local primitives. |

### 3.2 Operational list — ADM-05, ADM-07, ADM-09, ADM-14, ADM-17, ADM-19, ADM-22

| Item | Registry | Fit | Role support | Mobile behaviour | Customisation cost | Risks | Recommendation |
|---|---|---|---|---|---|---|---|
| `table` | `registry:ui` | The canonical table primitives (`Table`, `TableHeader`, `TableBody`, `TableRow`, `TableHead`, `TableCell`) | Semantic markup; `scope` is the implementer's job | Horizontal scroll region | Low | None | **Selected.** |
| `data-table-demo` | `registry:example` | The canonical *behaviour* example (filter, sort, column visibility, pagination, row selection, empty row) | Full | The example has **no responsive behaviour at all** | Medium — the example is a starting point, not a component | **R-01 (critical):** the example uses the **TanStack Table v9 API** (`tableFeatures`, `createColumnHelper<typeof features, T>`, `useTable`, `filterFn_includesString`) while the project pins **`@tanstack/react-table@^8.21.3`** (v8 API: `useReactTable`, `createColumnHelper<T>`, `getFilteredRowModel`). Copying the example verbatim breaks the build. | **Selected as a behaviour reference only.** The implementation must use the v8 API already in the project, or upgrade the dependency deliberately in FND-08 (not as an implicit side effect of a UI packet). |
| `pagination` | `registry:ui` | Page navigation | — | Compact at mobile | Low | The backend envelope is `data:{items,total,page,page_size,total_pages}` (`D-06`) — the component must be driven by **server** pagination, not client-side slicing | **Selected**, server-driven mode. |
| `filter-bar` / `command` | `registry:ui` | Filters and a command palette for admins | — | Filters collapse into a sheet at ≤768 | Low | The admin filter contract is `adminParametrosConsulta(estado)` and filters live in the URL (`07-guia-para-ui-ux.md` §8) | **Selected** (`command` for the admin global search; a composed filter bar, not a registry item). |
| `dropdown-menu` | `registry:ui` | Row actions | — | Menu instead of hover | Low | The `data-table-demo` row-action pattern (a `MoreHorizontal` ghost button) is the accepted pattern; on mobile it must be the same button, not hover-only | **Selected.** |

### 3.3 Detail / confirmation surfaces

| Item | Registry | Fit | Role support | Mobile behaviour | Customisation cost | Risks | Recommendation |
|---|---|---|---|---|---|---|---|
| `dialog` | `registry:ui` | Short actions, confirmations, buyer-data capture | Focus trap + restore | Must become a bottom sheet / full-height panel at 360 | Low | A centred dialog at 360 is a defect | **Selected** for S-10 confirmations and the buyer-data form. |
| `alert-dialog` | `registry:ui` | Destructive / irreversible confirmation | Same | Same | Low | — | **Selected** for irreversible actions (revoke, remove, manual approval, delivery). |
| `drawer` | `registry:ui` | The reusable "encuentro" panel / pass management detail | — | Bottom drawer at mobile, side sheet at ≥768 | Low | — | **Selected** for `MatchDetailPanel` (`frontend/05` §3) and for the ADM-06 detail. |
| `sheet` | `registry:ui` | Side panel, filters at mobile | — | — | Low | Overlaps `drawer` | **Alternative to `drawer`.** Pick **one** in FND-06 to avoid two panel primitives. Recommendation: `drawer` (vaul-based, mobile-first). |
| `tabs` | `registry:ui` | ADM-06 "Resumen · Equipos · Pool y personas · Compras · Historial"; ADM-14's three levels | — | At ≤768 a tab strip becomes a horizontally scrollable segmented control — which is allowed **inside** a component but must not cause page overflow | Low | A 5-tab strip at 360 overflows if not handled | **Selected**, with the 360 treatment specified per route. |
| `accordion` | `registry:ui` | PUB-02 "navegación por anclas reales" and FAQ | — | Full width | Low | A TOC should be links, not an accordion | **Selected** for FAQ only; PUB-02 uses real anchor links. |
| `empty` | `registry:ui` | S-02 / S-03 empty states | — | — | Low | New in the registry; verify it exists in the local `components/ui` (it does **not** — the frozen tree has no `empty.tsx`) | **Selected** (must be added). |
| `skeleton` | `registry:ui` | S-01 loading | — | — | Low | Present locally | **Selected / reused.** |
| `alert` | `registry:ui` | S-04 recoverable error, partial/indeterminate | — | — | Low | Present locally | **Selected / reused.** |
| `badge` | `registry:ui` | Verdict chips | — | — | Low | Present locally; the verdict chip is a **composed** badge + icon + text, not a bare badge | **Selected / reused.** |
| `card` | `registry:ui` | Product/package cards, admin metric tiles | — | 1 per row at 360 | Low | Present locally. **Anti-pattern control:** `frontend-design` names the "SaaS-card kit" (identical rounded cards, one radius, same soft shadow) as a tell. The metric tiles on ADM-01 must therefore differ in emphasis from content cards. | **Selected**, with the differentiation rule in SH-01 §3.6. |
| `carousel` | `registry:ui` | SHOP-02 product gallery | — | Swipe + keyboard + thumbnails | Low | Present locally | **Selected / reused.** Keyboard-operable thumbnails are a hard requirement (`frontend/02` SHOP-02). |
| `field` | `registry:ui` | The **new** shadcn form primitive (label/description/error composition) | Full | Responsive variants exist (`field-responsive`) | Low | The project already has `GenericForm` + `GenericInput` + `FieldWrapper` (`contract/smart.md`) with a **different** contract: `GenericInput` owns the error rendering, and a `customFields` field must render its own label/error **exactly once**. `field` could double-render errors. | **⚠ Compare before adopting.** Recommendation: **do not** introduce `field` into `GenericForm`'s wrapper path without first proving there is no double-render. `field` may be used only in **new, non-GenericForm** surfaces. |
| `form` + `form-rhf-*` examples | `registry:ui` / `registry:example` | React Hook Form examples | — | — | Medium | The project mandates `GenericForm` **Mode 1 (`children`)** in production (`contract/next-app-architecture-contract.md` §5, `07-guia-para-ui-ux.md` §6). The `form-rhf-*` examples use the bare `form` primitives, which would bypass `GenericForm`. | **Rejected as an implementation base.** Use only as a source for the `Form`/`FormField`/`FormItem` visual composition. `GenericForm` remains the orchestrator. |
| `sonner` | `registry:ui` | Toasts | — | — | Low | Present locally; the project uses a **swappable toast adapter** (`errors/toast-adapter.ts`) — the toast component must not be called directly from components | **Selected / reused, through the adapter.** |
| `tooltip` | `registry:ui` | Truncated values | — | **Tooltips do not exist on touch** — truncated content must also be reachable another way | Low | — | **Selected**, with the touch caveat handled. |
| `progress` | `registry:ui` | Wizard step indicator | — | — | Low | The wizard has 4 steps (`SPORT-01`); a bar alone hides the step names | **Selected** alongside a labelled step indicator. |
| `chart` | `registry:ui` | ADM-01 metrics, competition charts | — | Charts must not be the only representation | Medium | **No chart tokens exist in the legacy theme** (SH-01 §3.3). The chart component expects `--chart-*` variables and the project has none → charts would render with undefined colours. | **Conditional.** Add only together with the `--chart-*` token set in FND-06. |
| `input-otp` | `registry:ui` | — | — | — | Low | Tempting for the "code" field of a ticket — but tickets are scanned, not typed as OTPs | **Rejected.** |
| `navigation-menu` | `registry:ui` | Public top navigation | — | — | Low | A mega-menu is not needed for 5 public destinations | **Rejected.** The public header is a composed bar. |
| `avatar` / `bubble` / `message` / `message-scroller` / `marker` / `item` | `registry:ui` | — | — | — | Low | Chat/transcript semantics; not applicable | **Rejected.** (`item` deserves a second look for the metric-tile row — see 3.4.) |

### 3.4 Cross-family blocks

| Item | Registry | Fit | Risks | Recommendation |
|---|---|---|---|---|
| `login-01` … `login-05` | block | AUTH-01 | `login-02`/`login-04` are "two column with a cover image"; the frozen login already has a bespoke split visual panel with a gold/cyan brand treatment that **is** the recognisable identity. Replacing it with a stock block erases brand identity. | **Rejected as a replacement.** Use `login-01` (simple form) only as a layout reference; keep the local brand composition and its tokens. |
| `signup-01` … `signup-05` | block | AUTH-02 | Same reasoning; AUTH-02 has a specific local→RENIEC search step that no stock block models | **Rejected as a replacement.** |
| `chart-*` (62 blocks) | block | ADM-01, ADM-11, ADM-12 | 62 near-identical chart blocks; choosing one is a brand decision, not a component decision | **Not selected in this packet.** Deferred to ADM-01/ADM-12 briefs, which specify the chart *type* (bar for counts, line for trends, none for the bracket) rather than a block. |
| `item` / `item-group` | `registry:ui` | ADM-01 metric rows; PUB-02 index | The `item` primitive is a flexible row that could replace the "identical rounded card" grid with a list that carries more information density | **Candidate for ADM-01.** FND-06 should decide between `card` (marketing) and `item` (operational). |

---

## 4. Critical Risk R-01 — TanStack Table v8 vs v9

The official `data-table-demo` example shipped by the registry uses:

```tsx
const features = tableFeatures({ columnFilteringFeature, columnVisibilityFeature, /* … */ })
const columnHelper = createColumnHelper<typeof features, Payment>()
const table = useTable({ features, data, columns, /* … */ })
```

The project pins `"@tanstack/react-table": "^8.21.3"` and the frozen tree exposes `frontend/src/components/ui/table.tsx` plus `frontend/src/components-app/tables/AppDataTable.tsx` (itself under the CAM `components-app` quarantine list from GOV-00). The v9 API is a different call shape.

**Consequences, recorded now so no packet discovers it mid-implementation:**

1. The registry example **cannot** be copied verbatim into the target root.
2. The `dashboard-01` block additionally pulls `@dnd-kit/*` and `@tabler/icons-react` — a second icon library next to Lucide.
3. The canonical admin list pattern is documented in `Aplicacion/documentacion/03b` §3.4 ("El patrón de lista operativa (compartido por 6 páginas)") — the rebuild must **reuse that documented pattern**, not re-derive it from a registry example.
4. Decision needed (recorded, not taken here): keep v8 and adapt the example, or upgrade deliberately in FND-08.

---

## 5. Obligations Issued To The Next Packets

| ID | Obligation | Owner | Blocking scope |
|---|---|---|---|
| `GOV-02-SH-01` | Before any component is added, run the shadcn MCP comparison **again for that route family** and record the candidate table in the route brief. This document covers families, not individual routes. | A7 | Every UI-0x skeleton packet |
| `GOV-02-SH-02` | Diff the local `frontend/src/components/ui/*` against the registry source before replacing anything; preserve intentional customisations (`salesianos-shadcn` Hard Rule 5). | A7 | FND-06 |
| `GOV-02-SH-03` | Never introduce `field` into the `GenericForm` wrapper path without proving there is no double-render of label/error (`contract/smart.md` §4). | A7 | FND-07, FND-08 |
| `GOV-02-SH-04` | Do not use the `data-table` example verbatim — v8 API only, or a deliberate dependency upgrade. | A7 | FND-08, ADM-05/07/09/14/17/19/22 |
| `GOV-02-SH-05` | `chart` requires the `--chart-*` token set to exist first; tokens in FND-06, chart in ADM-01. | A7 + A0 | ADM-01, ADM-11, ADM-12 |
| `GOV-02-SH-06` | Choose exactly **one** panel primitive (`drawer` **or** `sheet`) — not both. | A7 | FND-06 |
| `GOV-02-SH-07` | Add commands must use `-c Aplicacion/frontend` if the CLI is used, and must come from `get_add_command_for_items`. | A7 | FND-06+ |
| `GOV-02-SH-08` | `get_audit_checklist` must be called before any UI packet is declared complete. | A7 | Every UI-0x |

---

## 6. Concurrent Activity Observed (not touched)

`Aplicacion/frontend/components.json` is **modified in the working tree** relative to `f3df540` — this is concurrent user activity, not this packet's change. It declares the `@shadcn` → `radix-nova` registry that this document relies on. **It was read only.** It was not reverted, staged, or edited.

---

## 7. Acceptance Criteria For This Document

- [x] The shadcn MCP was actually executed; the calls and their real results are recorded.
- [x] Tooling limitations that will bite the next packets are documented.
- [x] The registry/style configuration is read from disk, not assumed.
- [x] Candidate tables carry item, registry, fit, role support, mobile behaviour, customisation cost, risks and recommendation.
- [x] Sidebar variants are compared (the plan and the skill both require it).
- [x] The one critical technical risk (TanStack Table v8 vs v9) is named with evidence.
- [x] No component was added, no `components/ui` file was created or modified, and no CLI command was executed.
