# FND-06 — Target Frontend Shell And Shared Providers

**Packet:** `wave-01-foundations/FND-06-frontend-shell.md` (`T-017`) · **Owner:** A0 + A7
**Date:** 2026-11-19 · **Target:** `Aplicacion/frontend/**` · **Rollback:** commit `f3df540` + the frozen tree `frontend/src/**`

---

## 1. What Was Consumed

| Source | Role in this packet |
|---|---|
| `evidence/routes/SH-01-visual-direction-and-semantic-tokens.md` | **The token system.** Wins over the parallel design brief. |
| `evidence/routes/SH-04-shadcn-candidate-comparison.md` | **The component selection.** Wins over the parallel design brief. |
| `evidence/routes/SH-02-responsive-and-accessibility-matrix.md`, `SH-03-state-matrix-and-recovery-patterns.md` | The five-width contract and the ten-state matrix. |
| `evidence/routes/GOV-02-route-brief-index.md`, `RB-01..RB-08` | The 38 page IDs, their actors and their tasks. |
| `evidence/contracts/GOV-01-contract-freeze-summary.md`, `FR-08` | The provisional fixture contract (used by UI-0x, not here). |
| `evidence/checkpoint/GOV-00-classification-and-rollback.md` | The classification of `Aplicacion/frontend/src/**` as `COPY/REBUILD` with a named rollback. |
| `contract/next-app-architecture-contract.md`, `smart.md`, `api-wrapper-presenter-contract.md` | The architecture, the form contract, the envelope. |
| `Aplicacion/plan/salesianos-fest-rebuild/frontend/01..06` | The route map and the UX system. |
| `Aplicacion/documentacion/07-guia-para-ui-ux.md` | The operational law of the UI. |

**Merge decision (GOV-02 asked for it):** `SH-01` and `SH-04` win. The parallel brief
(`Aplicacion/frontend/doc_dev/brief-gov02-parte-a-sistema-visual-y-shell.md`) contributed its
DEFECT LIST — `ThemeProvider` never mounted, global `scroll-snap-type`, global `body{overflow-y:scroll}`,
duplicated `--color-gold` / `--radius`, font weight 900 never loaded — and none of its visual decisions.
It diverges from `SH-01` on radii (`SH-01` keeps the soft generous corners: "that softness is part of
what makes Salesianos look like Salesianos"), on the eyebrow weight (`SH-01` keeps 900) and on the
panel primitive. It stays in `doc_dev/**`, a GOV-00 `QUARANTINE` folder, and no packet consumes it.

---

## 2. Decisions Taken

| ID | Decision | Why |
|---|---|---|
| `D-FND06-01` | **`sheet` is the ONE panel primitive.** `drawer.tsx` was removed and the `vaul` dependency dropped. | `GOV-02-SH-06` demands exactly one. `sidebar.tsx` (selected by `SH-04`) imports `sheet` for its offcanvas mode, so `sheet` is unavoidable; adding `drawer` would have created two panel primitives and a second interaction for the same gesture. |
| `D-FND06-02` | **`field` is NOT installed.** | `SH-04` flags it "⚠ Compare before adopting" and `GOV-02-SH-03` forbids introducing it into the `GenericForm` wrapper path without proving there is no double render. That proof is FND-07's job. Installing it now would be an unused import. |
| `D-FND06-03` | **`cn` is normalised to `@/lib/utils`.** The `cn` npm package was removed from `dependencies`. | `contract/next-app-architecture-contract.md` §6 makes the alias canonical. The npm `cn@0.3.2` is a drop-in for `twMerge(clsx(...))` so there is no behavioural change, but two implementations of class merging is a defect waiting to happen. The shadcn CLI kept writing `from "cn"` because the package was installed. |
| `D-FND06-04` | **`globals.css` was rewritten from scratch.** | The frozen file carried 16 defects (`SH-01` §2.3, plus the defect list of the parallel brief). The new file holds the roles, not the layout (`T-02`). |
| `D-FND06-05` | **The superseded frozen presentation components were removed from the target.** `components/{portada,landing,paquetes,event}/**`, `components/AppSidebar.tsx`, `components/AppShell.tsx`, `components/{emptyState,genericPagination,confirmationDialog,breadcrumbs,branding}/**`, and the old routes `app/page.tsx`, `app/informacion/`, `app/(auth)/login/`, `app/(auth)/register/`, `app/(app)/`. | GOV-00 classifies `Aplicacion/frontend/src/**` as `COPY/REBUILD` with a named rollback (commit `f3df540` and the frozen tree). These components carried 36 broken imports to the emptied `features/**` and duplicated what the new shell owns (5 grammars of empty state, 2 page headers, 3 diverging state→colour maps). UI-0x re-derives the ones it needs from the frozen tree. |
| `D-FND06-06` | **`proxy.ts` keeps its authority and changes its route list.** Anonymous visitors now land on `/login` instead of `/`; a visitor with a credential on `/login` lands on `/mi-cuenta`. The guest links (`/pases/gestionar/*`, `/tienda/pedidos/*`) are public. | The route map changed; the gate had to follow it. The file still decides NOTHING about roles: the 403 of the backend is the control (`07-guia-para-ui-ux.md` §3.3). |
| `D-FND06-07` | **`@types/node` was raised to `^22.12.0`.** | `vitest@5.1.1` declares `peerOptional @types/node ^22 || >=24`; the project pinned `^20` and `npm install` failed with `ERESOLVE`. Blocking every dependency install. |
| `D-FND06-08` | **The admin navigation consolidates the 22 page IDs into 14 destinations + the summary.** The detail routes (ADM-06, ADM-08, ADM-11, ADM-12, ADM-13, ADM-18, ADM-20) are reached from their parent destination. | `frontend/04` §1: the 22 entries are CONCEPTUAL destinations; "evitar fragmentar navegación sin necesidad". `SH-04` rejects `sidebar-08` because the app has one navigation level plus contextual tabs. |
| `D-FND06-09` | **The social marks are the official simple-icons SVGs, inlined from the allsvgicons MCP.** | `lucide-react@1.7.0` has no brand icons. The frozen tree used hand-written inline SVG, which the brief forbids. The marks use `currentColor`, so they work in both themes from one file. |
| `D-FND06-10` | **`biome.json` gained two overrides.** The a11y rules are off for `src/components/ui/**` (vendored registry source: forking it would break `shadcn add` updates) and `noImportantStyles` is off for `globals.css` (the reduced-motion guard MUST win over any animation). | `SH-01` `T-01` and `T-08`. |

---

## 3. What Was Built

### 3.1 Token system — `src/app/globals.css` (rewritten)

- Every role of `SH-01` §3.1 with a **light and a dark value** (`T-05`): the dark block now remaps
  `--secondary`, `--popover`, `--success`, `--warning`, `--destructive`, `--info` — the 11 roles the
  legacy `.dark` never touched.
- The five `--chart-*` series plus `--chart-grid` / `--chart-axis` (`SH-01` §3.3, absent from the legacy).
- `--shadow-sm/md/lg/focus` resolve per theme (`--elevation-*` raw tokens + `@theme inline` mapping).
- `--spacing-section`, `--spacing-gutter`, `--z-*`, `--motion-duration-*`, `--motion-ease-*`.
- The brand utilities compose FROM tokens: `bg-brand-gradient`, `bg-page-gradient`, `bg-hero-gradient`,
  `bg-hero-overlay`, `bg-surface-glass`, `text-gradient-brand`, `text-gradient-gold`, `rule-gold`,
  `card-elevated`, `shadow-glow-brand`, `text-eyebrow-brand`.
- **Removed**: the legacy `@layer utilities` island, the 15+ literal colours inside `@utility`,
  `html{scroll-snap-type}`, `body{overflow-y:scroll}`, the duplicated `--color-gold` / `--radius`.
- **Added**: one `prefers-reduced-motion` block, one global focus spec (`:focus-visible` with
  `outline`, never removed).

### 3.2 Shell — `src/components/shell/**`

| File | Owns |
|---|---|
| `BrandMark.tsx` | The brand mark (crest + wordmark) with tokens only. |
| `SiteHeader.tsx` | The public bar: brand, destinations, primary action; `Sheet` below 1024. |
| `SiteFooter.tsx` | The public footer with the official social marks. |
| `AdminSidebar.tsx` | The administration navigation: summary + 3 collapsible groups, active marker = the gold rule. |
| `AccountTopbar.tsx` | The account bar: the user menu with the five account destinations. |
| `ShellState.tsx` | `ShellErrorState`, `ShellEmptyState`, `ShellPermissionDenied`, `ShellPendingState`. |
| `RoutePlaceholder.tsx` | The honest placeholder of a route whose view is not built yet. |
| `SocialIcons.tsx` | The three brand marks, inlined from the allsvgicons MCP. |

### 3.3 Providers — `src/providers/AppProviders.tsx`

`ThemeProvider` (mounted, `attribute="class"`, `defaultTheme="system"`) → `QueryClientProvider` →
`TooltipProvider` → children, with `Toaster` as a sibling. The theme was DEAD before this: `next-themes`
was installed, `sonner.tsx` called `useTheme()` and there was no provider, so `.dark` never applied.

`src/hooks/system/useReducedMotion.ts` replaces the two ad-hoc `prefers-reduced-motion` selector lists
of the frozen tree with one shared hook plus the one global rule.

### 3.4 Routes — `src/app/**`

Four route groups, 38 pages, all wired and building:

| Group | Routes | Chrome |
|---|---|---|
| `(public)` | 8 | `SiteHeader` + `SiteFooter`, skip-link |
| `(auth)` | 2 | Brand panel + form panel; one column below 1024 |
| `(cuenta)` | 6 | `AccountTopbar`, no sidebar; server-side session guard |
| `(administracion)` | 22 | `SidebarProvider` + `AdminSidebar` + sticky header; server-side session AND capability guard |

Every group has `loading.tsx` (a skeleton of the real shape), `error.tsx` (a Client Component with
`reset()`) and, where it applies, `not-found.tsx`. `app/error.tsx` and `app/not-found.tsx` are global.
The two guest-link routes (`/pases/gestionar/[token]`, `/tienda/pedidos/[token]`) carry a minimal chrome
of their own: they are a guest of the event, not an account.

`src/lib/routes.ts` holds the 38 routes in ONE constant. The plan proposes them; renaming one is a
change in one file, not a search-and-replace across the markup.

### 3.5 Navigation model — `src/features/admin/utils/admin.secciones.ts`

14 destinations + the summary, in the three groups of `frontend/04` §1, each with the capability it
requires. `adminSeccionesVisibles` fails CLOSED (no capabilities → only the destinations without one).
`adminSeccionActiva` derives the active destination from the route on every render, so a reload and the
back button always mark the right one.

### 3.6 shadcn — 11 primitives added

`alert` · `alert-dialog` · `empty` · `pagination` · `command` · `progress` · `item` · `toggle-group` ·
`toggle` · `input-group` · `spinner` (38 primitives in total).

Commands come from the official registry (`https://ui.shadcn.com/r/styles/radix-nova/{name}.json`,
`style: radix-nova`), fetched rather than copied blindly, and the local customisations of the 27
existing primitives were preserved (`GOV-02-SH-02`): the CLI had overwritten `label.tsx` and
`textarea.tsx` while resolving dependencies and both were normalised back to the project alias.
`card` was already present and was not touched.

**Not installed, on purpose:** `form` (would duplicate the `GenericForm` orchestrator of
`contract/smart.md`), `chart` (needs the `--chart-*` tokens, which now exist — but the chart belongs
to ADM-01, `GOV-02-SH-05`), `navigation-menu`, `combobox`, `drawer` (`D-FND06-01`), `field`
(`D-FND06-02`), `input-otp`, `accordion` (FAQ only, UI-01), `switch` (UI-04).

---

## 4. Commands And Results

| # | Command | Workdir | Exit | Result |
|---:|---|---|---:|---|
| 1 | `npx tsc --noEmit` | `Aplicacion/frontend` | **0** | clean — the target did NOT compile before this packet |
| 2 | `npx vitest run` | `Aplicacion/frontend` | **0** | 7 files, **162 tests passed** |
| 3 | `npx biome check .` | `Aplicacion/frontend` | 1 | **14 errors / 72 warnings** — baseline was **105 / 93**. All 14 errors are pre-existing frozen code (`components-app/**`, `genericForm/GenericForm.tsx`, `ui/{breadcrumb,carousel,sidebar}.tsx`, `hooks/callsApi/useApiUpdate.ts`). **Zero errors in the code written by this packet.** |
| 4 | `npx next build` | `Aplicacion/frontend` | **0** | 38 routes + 2 API handlers + 404 registered; proxy (middleware) active |
| 5 | `npm install cmdk` | `Aplicacion/frontend` | 0 | the only new runtime dependency |

**Baseline comparison (GOV-02, frozen tree):** `npx tsc --noEmit` → 0 (clean) · `npx vitest run` →
1 failed file / 2 failed tests · `npx biome check .` → 105 errors / 93 warnings.

**Regressions:** none. The two red tests of the baseline are in `frontend/**` (frozen) and were not
touched.

---

## 5. Viewport Audit — 360 / 390 / 768 / 1024 / 1440

**NOT PERFORMED IN A BROWSER.** No browser and no Playwright are available in this session, so the
visual and assistive-technology behaviour is **unverified**. What IS verified statically:

| Width | Verified in the source |
|---|---|
| 360 / 390 | The public navigation collapses into a `Sheet`; the menu button is `size-11` (44 px). The admin sidebar switches to offcanvas below 768 (`useIsMobile`, `MOBILE_BREAKPOINT = 768`). The account bar hides the name below `sm`. |
| 768 | The admin sidebar is the icon rail (`collapsible="icon"`). The public navigation is still in the `Sheet` (`lg:block` on the nav). |
| 1024 | The public navigation appears in the bar; the admin sidebar expands to 16rem inside a `SidebarInset` with a sticky header. |
| 1440 | The containers cap at `max-w-[1200px]` (public), `max-w-[1100px]` (account) and the admin content fills the inset. |

**Residual gap:** the five-width audit of `salesianos-responsive-a11y` must be executed with a browser
before UI-01 closes. The shell was written to the matrix of `SH-02`, but the matrix is not the audit.

---

## 6. Open Decisions Carried Forward

| ID | Question | Owner | Blocking scope |
|---|---|---|---|
| `GOV-02-UX-01` | `--secondary` dark = `#3a43c9` — adopted as proposed. | A0 | closed |
| `GOV-02-UX-02` | Does the dark theme ship in wave 1? — **YES**: the brief and the user's instruction both require light and dark. | A0 | closed |
| `GOV-02-UX-03` | Do the legacy marketing gradients survive? — the brand utilities survive, rebuilt from tokens. | A7 | closed for the shell; PUB-01 decides the composition |
| `GOV-02-UX-04` | Font hosting — `next/font` Plus Jakarta Sans + Geist Mono kept. The registry has no plus-jakarta-sans. | A7 | closed |
| `GOV-02-UX-05` | Is `--accent` interactive? — **NO**: it decorates. Gold TEXT on a light surface uses `--accent-muted`. | A7 | closed |
| `FND-06-D-01` | The vocabulary of capabilities has 11 codes and does NOT cover marketplace, patrocinadores or validaciones. The shell filters with `ADMIN_VER` for those. | A0 + backend | the real filter arrives with the frozen catalogue |
| `FND-06-D-02` | The edition scope (which modules are enabled) is not published by the backend yet. The header renders the plan's destinations. | A0 + backend | the filter enters in ONE place when the catalogue lands |

---

## 7. What FND-06 Does NOT Contain

- **No feature route implementation.** The 38 pages are shells: `RoutePlaceholder` says so on the page.
- **No service, no network hook, no wire schema, no query key.** Nothing in the target calls the API:
  the only importers of `@/lib/api` are the generic hooks of `hooks/callsApi/**` and `hooks/cache/**`,
  and nothing invokes them. `src/features/**` holds only the identity types and the navigation model.
- **No fixture.** The provisional fixtures are the job of UI-01..UI-05 (`FR-08`).
- **No change in `Aplicacion/backend/**`.** The other agent owns FND-01.
- **No change in `contract/**`, `plan/**`, `Aplicacion/documentacion/**`.**
- **No commit and no `git stash`.**

## 8. Next Packet

- `FND-07` — forms lifecycle, 422 field errors, create/update payload semantics. `GenericForm` already
  exists in the target and is the orchestrator of `contract/smart.md`; this packet fixes its known
  divergences.
- `UI-01` — public, auth, account and recovery skeletons with the provisional fixtures of `FR-08`.
