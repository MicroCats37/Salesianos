# RB-01 — Route Briefs: Public, Identity And Sports Registration

**Artifact:** `evidence/routes/RB-01-public-account-identity.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only, no implementation code
**Date:** 2026-11-19
**Page IDs in this file (10 of 38):** `PUB-01`, `PUB-02`, `AUTH-01`, `AUTH-02`, `ACCOUNT-01`, `ACCOUNT-02`, `ACCOUNT-03`, `ACCOUNT-04`, `ACCOUNT-05`, `SPORT-01`
**Shared references:** `SH-01` (tokens) · `SH-02` (responsive + a11y) · `SH-03` (states) · `SH-04` (shadcn candidates) · `SH-05` (provisional endpoints) · `SH-06` (wireframes)

---

## Reading This File

Every route below carries the mandatory fiche fields from `frontend/01` §6: `ID`, proposed route, actor, objective, preconditions, visible sections, important components, actions, navigation, information/contracts, states, accessibility, permissions, acceptance cases and open decisions — plus the three additions this packet requires: **responsive intent**, **semantic-token intent**, and the **mandatory shadcn candidate comparison**.

**Route status:** every route in this file is **provisional**. No URL is live; see `SH-05` §0.

---

## `PUB-01` — `/` — portada de la edición

- **Actor:** visitante anónimo. **Priority:** Alta (entry point of every public journey).
- **Objective:** understand what Salesianos FEST is and reach the primary task in **≤ 2 navigations** (`frontend/02` §PUB-01 acceptance).
- **Preconditions:** a resolvable published edition (`FREEZE-ED-1.0.0` `D-01` resolution order). Modules may be disabled.
- **Visible sections:** hero (edition, dates) · enabled activities · disciplines · featured packages with CTA · passes · store (if enabled) · sponsors · FAQ · footer.
- **Key components (shadcn candidates — compare before selection):** `card` (featured packages/products — **differentiated** from the metric-card kit, SH-01 §3.6) · `accordion` (FAQ) · `carousel` (sponsor strip) · `badge` (module enabled) · `button` (primary/secondary CTA) · `skeleton` · `empty` · `alert` (catalogue error). **Comparison obligation: `GOV-02-SH-01`.**
- **Actions:** open information · start registration · buy a pass · explore the store · sign in.
- **Navigation:** `/informacion`, `/inscripcion`, `/pases`, `/tienda`, `/login`.
- **Data / contract dependencies (all provisional):** `RT-ED-01` (current edition), `RT-ED-02` (edition catalogue), `RT-IN-12` (packages), `RT-IN-13` (disciplines), `RT-PS-01` (passes), `RT-MK-02` (products), `RT-ED-07` (sponsors).
- **States:** `S-01` loading · `S-04` catalogue error with retry and **no invented fallback** (`FL-01`) · *edition not published* → a message, not an error · *module disabled* → the section is **hidden**, not shown empty.
- **Responsive intent:** 360/390 single column, hero type 28–32 px, image below the fold; 768 two-column hero; 1024/1440 two-column with a 1200 px max content band and a full-bleed hero band. No horizontal scroll at any width.
- **Semantic-token intent:** `bg-surface`, `text-foreground`, `bg-surface-raised`, `border-border`, `text-foreground-muted`, `bg-primary`/`text-primary-foreground` for the CTA, `bg-accent`/`text-accent-foreground` for festival accents only, `text-brand-cyan` for energy accents, `bg-surface-inverse` for the hero band. **No literal gradient stops** — the hero gradient composes `from-primary via-institutional-dark to-surface-inverse`.
- **Accessibility intent:** the hero motion is decorative and hidden from AT; reduced motion disables it (`SH-01` §3.7); the marquee must not be the only route to information; decorative orbs are `aria-hidden`; one `h1`; sections use real headings in order.
- **Acceptance:** ≤ 2 navigations to the primary task · no invented prices or stock · sections reflect only what the backend says is enabled.
- **Open decisions:** `GOV-02-UX-03` (do the legacy marketing gradients survive?) · `GOV-01-OPEN-02` (public edition history — not ratified).

---

## `PUB-02` — `/informacion` — detalles de la edición

- **Actor:** visitante. **Priority:** Media.
- **Objective:** reach the rules, schedule and categories **without** becoming a second visual landing page (`frontend/02` §PUB-02).
- **Preconditions:** published edition.
- **Visible sections:** a real anchor navigation (toc) · content grouped by topic · a consistent CTA.
- **Key components (candidates):** anchor link list (composed, not a registry item) · `accordion` (only for collapsible sub-topics) · `card` (category blocks) · `typography-*` (content blocks).
- **Actions:** jump to a section · start registration.
- **Navigation:** anchors within the page → `/inscripcion`.
- **Data / contract dependencies (provisional):** `RT-ED-01`, `RT-ED-02`, `RT-IN-13`.
- **States:** `S-01` · `S-04` content load error · *anchor target missing* → **must not happen**: every toc anchor must resolve to a section that exists.
- **Responsive intent:** 360/390 the toc becomes a collapsible disclosure above the content; 768 two-column (sticky toc 240 px + content); 1024/1440 same, toc sticky, content max 80 characters measure.
- **Semantic-token intent:** `text-foreground`, `text-foreground-muted` for the toc, `border-border` for the toc rail, `bg-surface-raised` for topic cards, `text-accent-muted` for the active anchor marker.
- **Accessibility intent:** the toc is a `<nav>` with a labelled list; the active anchor is `aria-current="true"`; headings form a correct hierarchy; no client-side duplicate catalogue for the same packages (plan acceptance).
- **Acceptance:** every anchor lands on an existing section · the same packages are not catalogued twice client-side.
- **Open decisions:** none new.

---

## `AUTH-01` — `/login`

- **Actor:** persona con cuenta (responsable o administrador). **Priority:** Alta.
- **Objective:** authenticate; land a normal user in the personal area and an administrator in the panel.
- **Preconditions:** none. **Never** required to buy a pass or from the store when guest purchase is enabled.
- **Visible sections:** identifier · password/credential · access recovery · specific error message · link to registration.
- **Key components (candidates):** `input` · `label` · `button` · `alert` (error) · `field` — **with the caveat of `GOV-02-SH-03`: `field` must not be introduced inside the `GenericForm` wrapper path without proving there is no double render of label/error.** The legacy login has a bespoke split visual panel whose brand treatment must be preserved (SH-04 §3.4) — the `login-01..05` blocks are **rejected as replacements**.
- **Actions:** authenticate · recover access · go to registration.
- **Navigation:** `/mi-cuenta` or `/administracion` after success; `/registro` from the page.
- **Data / contract dependencies (provisional):** authentication is a session concern owned by the auth chain; the client **must not** decide access from a Zustand store or a cookie (`07-guia-para-ui-ux.md` §3.3). No new endpoint is proposed for the credential exchange.
- **States:** `S-01` (form hydration) · `S-05` validation · `S-08` in progress (submit disabled + truthful progress) · `S-04` recoverable error with the specific reason · `S-06` permission/account-disabled.
- **Responsive intent:** 360/390 the split panel collapses to a single column with the form first; 768 the form column is centred at max 480 px; 1024/1440 the two-column split (visual panel + form) is preserved with the form column at 480 px.
- **Semantic-token intent:** `bg-surface-inverse` + `text-accent` for the brand panel, `bg-surface-raised`/`text-foreground` for the form card, `text-destructive` for the credential error, `ring` for focus.
- **Accessibility intent:** the password visibility toggle is a labelled button; password-manager hints preserved; the error summary receives focus on submit; `autocomplete="username"` / `"current-password"`.
- **Acceptance:** wrong credential yields a specific message · an administrative account reaches the panel · no forced login for pass/store purchase.
- **Open decisions:** `GOV-02-UX-03` (does the bespoke login visual survive? — default **yes**, it carries the brand).

---

## `AUTH-02` — `/registro`

- **Actor:** visitante anónimo. **Priority:** Media.
- **Objective:** create an account **when it is useful**, resolving the document first.
- **Preconditions:** none.
- **Visible sections:** document type + number · local→RENIEC search · confirmable data · contact · credentials · **real** consents.
- **Key components (candidates):** `input` · `select` (document type) · `combobox` (type + number, if the catalogue is long) · `button` · `alert` · `checkbox` (consents) · `field` (same caveat).
- **Actions:** search the document · confirm the person · create the account.
- **Navigation:** `/mi-cuenta` or `/inscripcion` on success.
- **Data / contract dependencies (provisional):** `RT-ID-01` (local exact match), `RT-ID-02` (external resolution — `FUENTE_EXTERNA_NO_DISPONIBLE` → 503), `RT-ID-03` (confirm and persist).
- **States:** `S-01` · `S-05` validation · *DNI not found* · *external source temporarily unavailable* (a **retryable** message, not a rejection) · *document already linked to an account* (409) · *invalid email* (422 `field_errors`) · *duplicate* (409) · `S-08` in progress.
- **Responsive intent:** 360/390 one field per row, inputs ≥ 44 px, the search result appears inline below the field; 768 two-column (form + summary of the found person); 1024/1440 two-column capped at 960 px total.
- **Semantic-token intent:** `border-border` + `bg-surface-raised` for the found-person card, `border-primary` for the selected match, `text-destructive` for the duplicate conflict, `bg-surface-recessed` for the "searching" well.
- **Accessibility intent:** the resolved person is announced in a live region; errors are associated to their field; the search result is focusable and reachable by keyboard; the consented checkboxes are individually labelled with the real consent text.
- **Acceptance:** no duplicate personas are created · no user is created for every sports participant (`frontend/02` §AUTH-02 acceptance) · searching does **not** by itself create a `Persona` (`FL-02` step 3).
- **Open decisions:** `PD-07` (guest flow scope) is adjacent but does not block this route.

---

## `ACCOUNT-01` — `/mi-cuenta`

- **Actor:** cuenta autenticada. **Priority:** Alta.
- **Objective:** start the personal task — **not** display every table of the system (`frontend/02` §ACCOUNT-01).
- **Preconditions:** authenticated session.
- **Visible sections:** "Mis inscripciones" · "Mis compras" · "Mis entradas" (if they exist) · a "Nueva inscripción" CTA · an empty state with actions.
- **Key components (candidates):** `card` (summary blocks — **differentiated** from the marketing card kit) · `badge` (counts) · `button` · `empty` · `skeleton`.
- **Actions:** start a registration · open inscriptions · open purchases · open entries.
- **Navigation:** `/mis-inscripciones`, `/mis-compras`, `/inscripcion`.
- **Data / contract dependencies (provisional):** `RT-ID-04` (`MiCuentaOut`).
- **States:** `S-01` · `S-02` empty (with the "Nueva inscripción" action) · `S-04` error · `S-06` session expired → sign in, preserving the intent (`FL` recovery matrix).
- **Responsive intent:** 360/390 a vertical stack of full-width cards; 768 two columns; 1024/1440 three columns plus a right rail with the primary CTA.
- **Semantic-token intent:** `bg-surface-raised`, `border-border`, `text-foreground-muted` for labels, `text-primary` for counts, `bg-primary`/`text-primary-foreground` for the CTA. **Never** Izipay terminology (`frontend/02` §ACCOUNT-01).
- **Accessibility intent:** each card is a link with an accessible name that includes the entity ("Inscripción · Fútbol 7 · 2 cupos disponibles"); counts are accompanied by their label, not colour alone.
- **Acceptance:** the personal task is reachable in one action · no provider vocabulary leaks into the page.
- **Open decisions:** `P-02` (`/mi-cuenta` replaces `/dashboard` — provisional).

---

## `ACCOUNT-02` — `/mis-inscripciones`

- **Actor:** responsable autenticado. **Priority:** Alta.
- **Objective:** list and understand the state of one's registrations and act on the next step.
- **Preconditions:** authenticated session with at least one registration.
- **Visible sections:** list of cards/rows (edition, package, promotion, teams, understandable state, available cupos, **next action**) · filters (edition, state) · local search only if useful.
- **Key components (candidates):** `table` (≥1024) / card list (≤768) · `badge` (verdict chip) · `select` + `input` (filters) · `button` · `empty` · `pagination` (server-driven, `D-06`).
- **Actions:** open a registration · start a new registration.
- **Navigation:** `/mis-inscripciones/[id]`, `/inscripcion`.
- **Data / contract dependencies (provisional):** `RT-IN-01`.
- **States:** `S-01` · `S-02` no inscriptions · `S-03` filtered-empty (filters preserved + "clear filters") · `S-04` connection error · *payment in verification* (verdict) · *modification window closed*.
- **Responsive intent:** 360/390 one card per registration, the "next action" is the card's primary button (44 px); 768 a 2-column card grid or a 3-column table; 1024/1440 a full table with the next action as a row action.
- **Semantic-token intent:** `bg-surface-raised`, `border-border`, verdict chip tokens from SH-01 §3.2 (`--success`/`--warning`/`--info`/`--destructive`), `text-foreground-muted` for metadata, `bg-primary` for the next action.
- **Accessibility intent:** the next action is a real button with a state-specific label ("Completar pago", "Asignar participantes", "Ver equipo"); the available-cupos figure is read in a sentence; the verdict chip pairs colour + icon + backend label.
- **Acceptance:** the next action is visible without opening the record · filters live in the URL (the admin filter contract is the model) · no 409-only messaging.
- **Open decisions:** none new.

---

## `ACCOUNT-03` — `/mis-inscripciones/[id]`

- **Actor:** responsable (owner) o administrador. **Priority:** **Alta** (redesign priority).
- **Objective:** manage the registration — pool, teams, participants, cupos, benefits.
- **Preconditions:** authenticated session + ownership (or admin capability).
- **Visible sections:** header (edition, package, state, operational summary, next action) · `Pool` (pagados · asignados activos · disponibles + "Agregar cupos") · `Equipos` (per discipline/category: players vs min/max + explained state) · `Participantes` (search, add, assign, move, remove with confirmation) · `Compras` (initial/expansions, state, access to a pending payment) · `Beneficios` (fixed vs per-cupo, not mixed with cupos).
- **Key components (candidates):** `tabs` (6 sections; 360 → scrollable segmented control) · `table` / card list · `drawer` (the person-resolution sheet — the single panel primitive per `GOV-02-SH-06`) · `alert-dialog` (removal) · `badge` · `progress` (pool balance) · `button`.
- **Actions (primary / recovery):** *primary* — assign, move, remove a participant; add cupos. *recovery* — re-open a pending purchase, retry a failed assignment, resolve a person by document.
- **Navigation:** internal tabs; "Agregar cupos" opens the domain checkout; team detail is a drawer, not a new route.
- **Data / contract dependencies (provisional):** `RT-IN-02`, `RT-IN-03`, `RT-IN-04`, `RT-IN-05`, `RT-IN-06`, `RT-CM-01` (buy cupos), `RT-ID-01`/`02` (person resolution).
- **States:** `S-01` · `S-02` (no cupos paid; no teams; no purchases) · `S-04` · `S-05` (422 field errors on the cupos form) · `S-06` (not the owner → 403 explained) · `S-08` · `S-09` (purchase paid, cupos not yet enabled → "Estamos habilitando tus cupos") · `S-10` (removal confirmation naming the effect).
- **Blocking states to render as business reasons, not codes:** no paid cupos · modification closed · player not eligible · cupos exhausted · duplicate person for the discipline · pending purchase.
- **Responsive intent:** see `SH-06` §2 for the full wireframes. 360/390 stacked sections, the pool band as a labelled trio plus a sentence; 768 tabs with a single-column body; 1024 tabs + two-column body; 1440 tabs + body + sticky summary rail.
- **Semantic-token intent:** `bg-surface-raised` panels, `bg-surface-recessed` for the pool band, `--success`/`--warning`/`--destructive` verdict chips, `text-foreground-muted` for metadata, `bg-primary` for the primary action, `ring` for the focused field. The pool balance is never expressed with a raw accent colour alone.
- **Accessibility intent:** the pool trio is read as a sentence ("6 de 8 cupos asignados"); removal confirmation names the effect ("libera su cupo; no genera devolución"); the participant list is a semantic table at ≥1024 and a labelled card list below; focus returns to the trigger after the drawer closes.
- **Acceptance:** after removing a player the cupos balance updates and the purchase does not disappear (`QA-I04`) · a race of assignments never exceeds the available cupos (`QA-I05`) · the modification-closed state blocks with the backend's reason.
- **Open decisions:** `PD-02` (revocation/transfer rules) affects the removal action's exact consequences.

---

## `ACCOUNT-04` — `/mis-compras`

- **Actor:** cuenta autenticada. **Priority:** Media.
- **Objective:** see the purchases associated with one's person, grouped by origin.
- **Preconditions:** authenticated session.
- **Visible sections:** list grouped by origin (inscripción / pase / tienda) with date, amount, state, what was obtained and the next action.
- **Key components (candidates):** `table` / card list · `badge` (verdict) · `accordion` (grouping by origin) · `button` · `pagination` (server-driven).
- **Actions:** open the receipt / open the detail.
- **Navigation:** `/mis-compras/[id]`, and from the detail back to the module of origin.
- **Data / contract dependencies (provisional):** `RT-ID-05`.
- **States:** `S-01` · `S-02` no purchases · `S-03` filtered-empty · `S-04` · `S-09` (payment verified, right not yet enabled).
- **Responsive intent:** 360/390 card per purchase with the origin as the card header; 768 list; 1024/1440 table with an origin column and a filter.
- **Semantic-token intent:** `bg-surface-raised`, verdict chips (SH-01 §3.2), `text-foreground-muted` for the date, `tabular-nums` for amounts.
- **Accessibility intent:** the amount uses tabular numerals so it does not reflow; the verdict chip carries text; the purchase is a link whose accessible name includes the origin and the date.
- **Acceptance:** purchases are grouped by origin · no provider vocabulary · no access to another person's purchase by typing a DNI (`QA-U03`).
- **Open decisions:** `PD-07` — whether guest purchases also appear here or only through a private link.

---

## `ACCOUNT-05` — `/mis-compras/[id]`

- **Actor:** titular (owner) o administrador. **Priority:** Media.
- **Objective:** read the state of a purchase in plain language and know where to go next.
- **Preconditions:** authenticated session + ownership.
- **Visible sections:** what was bought · the payment state in presentable form · what was obtained (rights) · the next permitted action · the link to the origin module.
- **Key components (candidates):** `card` summary · `badge` verdict · `accordion` (technical detail, collapsed) · `button` (next action) · `alert` for partial/indeterminate.
- **Actions:** consult the right · continue a pending payment · go to the module of origin.
- **Navigation:** back to `/mis-compras`, and out to `/mis-inscripciones/[id]`, `/pases/gestionar/[token]` or `/tienda/pedidos/[token]`.
- **Data / contract dependencies (provisional):** `RT-ID-06`.
- **States:** `S-01` · `S-04` · `S-06` (not the owner) · `S-09` (paid but the right is not enabled → "Pago confirmado; estamos resolviendo la activación") · `S-08`.
- **Responsive intent:** 360/390 a single column, the next action as a sticky footer CTA that does not cover content; 768+ two-column (summary + details).
- **Semantic-token intent:** `bg-surface-raised`, `--info` for the partial/indeterminate alert, `--warning` for pending, `--success` for confirmed, `bg-primary` for the next action. `settlement_status` is **never** rendered (`contratos/01` §1.6).
- **Accessibility intent:** the status is announced in a live region when it changes; the amount uses tabular numerals; the technical detail disclosure is keyboard-operable.
- **Acceptance:** the state is understandable without reading provider fields · the next action is explicit · `settlement_status`, `CAPTURED` and provider tokens never appear.
- **Open decisions:** none new.

---

## `SPORT-01` — `/inscripcion` — sports wizard

- **Actor:** responsable autenticado (the plan allows an open guest path — `PD-07`). **Priority:** **Alta**.
- **Objective:** create a registration and the initial cupos purchase.
- **Preconditions:** authenticated session; an enabled edition and package.
- **Steps (from `frontend/02` §SPORT-01):** 1 · edition/package · 2 · teams · 3 · cupos and summary · 4 · confirmation and purchase.
- **Visible sections:** step indicator · the step body · a contextual summary (desktop rail / mobile disclosure) · the sticky CTA.
- **Key components (candidates):** `progress` + a labelled step list · `card` (package options) · `input`/`select`/`combobox` (team name, discipline, category, promotion) · `button` · `alert` (eligibility reasons) · `skeleton`.
- **Actions:** choose a package · define teams · choose the initial quantity · confirm and create the registration and the purchase · continue to payment · recover a pending operation without duplicating it.
- **Navigation:** forward through the steps (each step URL is recoverable — plan `frontend/06` §1) → `/mis-inscripciones/[id]` after creation; back to `/mi-cuenta`.
- **Data / contract dependencies (provisional):** `RT-IN-12`, `RT-IN-13`, `RT-ED-02`, `RT-ID-02`/`03` (person resolution when needed), `RT-CM-01` (create the initial cupos purchase — this is the write path of the wizard's final step), plus the payment-order route of the commerce/pagos freeze.
- **States:** `S-01` · `S-05` (team validation: name, discipline, category, promotion — **clear before advancing**) · `S-06` (not authorised for this package) · `S-08` (creation in progress; **double submit prevented**) · `S-09` (payment pending / verifying) · `S-04` · *creation succeeded but payment not yet confirmed* → the registration exists with 0 enabled cupos.
- **Responsive intent:** see `SH-06` §1. 360/390 full-screen step + sticky CTA; 768 centred 640 px step; 1024/1440 step + 320 px summary rail.
- **Semantic-token intent:** `bg-surface` page, `bg-surface-raised` option cards, `border-primary` for the selected option, `text-foreground` body, `text-foreground-muted` for conditions, `--destructive` for an eligibility refusal, `bg-primary`/`text-primary-foreground` for the CTA, `ring` for focus.
- **Accessibility intent:** the step indicator announces the current step (`aria-current="step"`); each step has an `h2`; validation focuses the first invalid field and links errors to fields; the CTA states what happens; forms preserve entered work when navigating back ("preservan el trabajo al navegar cuando es razonable").
- **Acceptance:** a created registration is **not** duplicated on reload · the user knows what is missing before being able to play (`QA-I01`: 0 cupos before payment) · the roster is not demanded before payment when the approved flow allows later assignment · team validation is explained before advancing.
- **Open decisions:** `PD-07` (guest registration path) · `PD-05` (stock scope) · `P-07` (the create-registration write route is not in the frozen ledger — it is part of the 59 provisional rows).

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-01a` | No public route may require authentication to browse a catalogue or buy a pass/store item when guest purchase is enabled. | A7 |
| `GOV-02-RB-01b` | The 422 field-error parser must exist **once, globally** before any of these forms is built — the frozen parser is documented but not implemented (`FE-12`), and its fallback messages are in English against a Spanish backend (`FE-13`). | A7 + A0 |
| `GOV-02-RB-01c` | `GenericForm` Mode 1 (`children`) is mandatory in production; `buildApiPayload` lives in the mutation hook, never in `onSubmit` (`contract/next-app-architecture-contract.md` §5). | A7 |
| `GOV-02-RB-01d` | No route in this file may show a provider state, a `settlement_status` literal, or a raw UUID as primary text. | A7 |
