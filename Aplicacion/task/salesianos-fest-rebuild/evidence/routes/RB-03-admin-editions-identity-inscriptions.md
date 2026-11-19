# RB-03 — Route Briefs: Admin Overview, Editions, People, Accounts And Registrations

**Artifact:** `evidence/routes/RB-03-admin-editions-identity-inscriptions.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only
**Date:** 2026-11-19
**Page IDs in this file (6 of 38):** `ADM-01`, `ADM-02`, `ADM-03`, `ADM-04`, `ADM-05`, `ADM-06`
**Shared references:** `SH-01` … `SH-06`

> **Admin context.** The administrator is a single functional role backed by Django groups; the backend is authoritative and sensitive actions are audited (`frontend/04`). **Hiding a button is UX help, not authorisation** — the 403 is the control (`07-guia-para-ui-ux.md` §5).

---

## `ADM-01` — `/administracion` — operational summary

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** see the selected edition's operational state and reach a filtered list from a metric.
- **Preconditions:** admin group; an edition context.
- **Visible sections:** selected edition · active/pending registrations · incomplete teams · upcoming matches · pending / needs-attention purchases · passes to validate · orders to deliver · stock alerts.
- **Key components (candidates):** **`item` / `item-group`** for the metric rows — preferred over identical `card`s to avoid the "SaaS-card kit" tell (SH-01 §3.6, SH-04 §3.4) · `chart` **only after the `--chart-*` tokens exist** (`GOV-02-SH-05`) · `badge` (verdict) · `button` (quick links) · `empty` · `skeleton`.
- **Actions:** navigate to a filtered list from a metric · switch the edition.
- **Navigation:** every metric links to its filtered list (`/administracion/inscripciones?estado=…`, `/administracion/pagos?estado_operativo=…`, `/administracion/validaciones`, `/administracion/marketplace/entregas`, `/administracion/competencias/agenda`).
- **Data / contract dependencies (provisional):** `RT-ED-01`, plus the list routes of the destination pages (`RT-IN-07`, `RT-PG-04`, `RT-CP-05`, `RT-VA-01`, `RT-MK-10`, `RT-MK-08`). **No new aggregate endpoint is proposed by this packet** — the existing administrative summary surface is reused until the backend offers one.
- **States:** `S-01` · `S-02` "Aún no hay inscripciones para esta edición" · `S-04` · `S-06` · *no edition resolved* → say so clearly; never attribute the metrics to another edition.
- **Responsive intent:** 360/390 metric rows stacked, one per line, each a link; 768 two columns of metric rows; 1024 metrics in a left column with the alert list on the right; 1440 metrics row + alerts + a chart band.
- **Semantic-token intent:** `bg-surface` page, `bg-surface-raised` metric rows, `border-border` separators, `--warning` for "needs attention", `--info` for "pending", `--destructive` for stock alerts, `text-primary` for the metric value, `text-foreground-muted` for its label. Metric rows use `item`, not stacked `card`s.
- **Accessibility intent:** each metric is a link with an accessible name that includes the metric, the value and the destination ("Pagos pendientes · 7 · ver lista filtrada"); the value uses tabular numerals; the metric row is not colour-coded; charts (if any) ship a legend and a table alternative.
- **Acceptance:** from a visible problem in the summary one reaches its filtered record and a concrete action (`frontend/04` §12.1) · no dozens of irrelevant KPIs · the summary never blocks the operator.
- **Open decisions:** `GOV-02-UX-05` (whether the summary uses charts at all in the first cut — the plan warns against a generic dashboard).

---

## `ADM-02` — `/administracion/ediciones` — create and publish editions

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** create, configure, publish and close editions.
- **Preconditions:** admin group.
- **Visible sections:** list of editions with state, enabled modules, dates · create/edit form · publish/close actions.
- **Key components (candidates):** `table`/card list · `dialog` or a dedicated route form · `input`/`select` (dates, module toggles) · `switch` (module enabled) · `badge` (state) · `alert-dialog` (publish / close) · `pagination`.
- **Actions:** create · edit · publish · close.
- **Navigation:** `/administracion/ediciones` → the edition detail (the same route, selected).
- **Data / contract dependencies (provisional):** `RT-ED-03` (list), `RT-ED-04` (detail), `RT-ED-05` (create), `RT-ED-06` (publish). **Branding is deferred** (`frontend/04` §3).
- **States:** `S-01` · `S-02` no editions · `S-03` filtered-empty · `S-05` (validation: dates, module set) · `S-08` · `S-09` (published but data still separate per edition — `QA-E01`) · `S-10` (close confirmation).
- **Responsive intent:** 360/390 card per edition with the actions in an overflow menu; 768+ table with an inline action column.
- **Semantic-token intent:** `bg-surface-raised`, verdict chips for the edition state, `bg-primary` for the primary action, `--warning` for "published but modules incomplete", `border-border` on the form.
- **Accessibility intent:** date inputs expose a readable format and a machine format; the publish dialog names the effect and requires no colour to understand it; the module toggles have real labels.
- **Acceptance:** editions are separated by registration data while sharing the same people (`QA-E01`) · the editor's ambiguity is impossible: the resolution order of `D-01` is the single behaviour.
- **Open decisions:** edition lifecycle dates are still open (`GOV-01-OPEN-03`).

---

## `ADM-03` — `/administracion/personas` — find people

- **Actor:** administrador. **Priority:** Media.
- **Objective:** find a person by document and see their relations.
- **Preconditions:** admin group.
- **Visible sections:** search by document and name · result list · the person's relations (participations, passes, purchases visible by permission) · confirmation of RENIEC-found data.
- **Key components (candidates):** `input` (search) · `table`/card list · `tabs` (relations) · `badge` · `empty` · `dialog` (detail).
- **Actions:** search · open the record · confirm externally found data · **never create a duplicate**.
- **Navigation:** to the person detail; cross-links to participations and passes.
- **Data / contract dependencies (provisional):** `RT-ID-07`, `RT-ID-08`, `RT-ID-01`/`02` (document resolution).
- **States:** `S-01` · `S-02` (no search performed yet → a prompt, not an empty table) · `S-03` (no results for the query) · `S-04` · `S-06`.
- **Responsive intent:** 360/390 search field pinned at the top, results as cards; 768+ table with the relations in a right drawer.
- **Semantic-token intent:** `bg-surface-raised` cards, `text-foreground-muted` for the document line, `bg-primary` for the search action, `border-border` for the relation tabs.
- **Accessibility intent:** the search input has a visible label and announces the result count; the relation tabs are a semantic tablist; a person is identified by name **and** document in every accessible name.
- **Acceptance:** no duplicate people are created · the relations shown respect the permission.
- **Open decisions:** none new.

---

## `ADM-04` — `/administracion/usuarios` — manage accounts and groups

- **Actor:** administrador. **Priority:** Media.
- **Objective:** manage accounts and their group (Normal / Administrador), activation state and history.
- **Preconditions:** admin group; **privilege escalation is subject to explicit authorisation** — the technical superuser is not an ordinary configurable role (`frontend/04` §3).
- **Visible sections:** account list · group assignment · activate/deactivate · history.
- **Key components (candidates):** `table`/card list · `select` (group) · `switch` (active) · `badge` (group) · `alert-dialog` (deactivate, escalate) · `pagination`.
- **Actions:** assign a group · activate / deactivate · review the history.
- **Navigation:** `/administracion/usuarios` only.
- **Data / contract dependencies (provisional):** `RT-ID-09`, `RT-ID-10`.
- **States:** `S-01` · `S-02` · `S-03` · `S-05` · `S-06` (cannot escalate without the capability) · `S-10` (deactivation confirmation).
- **Responsive intent:** 360/390 card per account with the group as a select inside the card; 768+ table with the group column and a row menu.
- **Semantic-token intent:** `bg-surface-raised`, `--warning` for a deactivated account, `--destructive` for the destructive deactivate action, `bg-primary` for the save.
- **Accessibility intent:** the group select has a real label; the deactivate action is a labelled button in a row menu with `aria-haspopup`; the confirmation names the effect ("Esta cuenta perderá el acceso al panel").
- **Acceptance:** a forced client-side command is still rejected by the backend (`QA-A03`) · the group vocabulary comes from the backend catalogue, never hardcoded.
- **Open decisions:** validation-operator group policy is open (`GOV-01-OPEN-04`).

---

## `ADM-05` — `/administracion/inscripciones` — registrations list

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** manage registrations — find one, understand its state, act on an incidence.
- **Preconditions:** admin group; edition context.
- **Visible sections:** list (responsible, package, edition, teams, understandable state, cupos acquired/assigned/available, relevant payment state, alert) · filters (responsible, discipline, state, date, incidence).
- **Key components (candidates):** `table` (≥1024) / card list (≤768) · `badge` (verdict) · `input`/`select`/`popover` (filter bar) · `pagination` (server-driven) · `empty` · `command` (quick admin search).
- **Actions:** filter · open a registration · act on an alert.
- **Navigation:** `/administracion/inscripciones/[id]`.
- **Data / contract dependencies (provisional):** `RT-IN-07`.
- **States:** `S-01` · `S-02` (no registrations for this edition) · `S-03` (filtered-empty with filters preserved) · `S-04` · `S-06`.
- **Responsive intent:** 360/390 card per registration with the three cupos figures and the next action; 768 a 3-column priority table; 1024/1440 the full column set with a column-visibility toggle.
- **Semantic-token intent:** `bg-surface-raised`, `bg-surface-recessed` for the table header, verdict chips (SH-01 §3.2), `text-foreground-muted` for metadata, `tabular-nums` for the cupos figures.
- **Accessibility intent:** `<th scope="col">` on every column header; the row's accessible name includes the responsible person and the edition; the priority columns at ≤768 keep the same header names as inline labels; filters are in the URL so the view is shareable.
- **Acceptance:** the documented operational list pattern is reused (`03b` §3.4) · filters live in the URL · no action depends on hover.
- **Open decisions:** `P-11` (query-parameter names beyond the frozen `RT-PG-04` contract).

---

## `ADM-06` — `/administracion/inscripcion/[id]` — registration detail

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** operate one registration — pool, cupos purchases, teams, responsible.
- **Preconditions:** admin group; a record id.
- **Visible sections:** tabs — **Resumen · Equipos · Pool y personas · Compras de cupos · Historial**.
- **Key components (candidates):** `tabs` (5 tabs; 360 → scrollable segmented control) · `table`/card list · `drawer` (person resolution, team detail) · `alert-dialog` (destructive actions) · `badge` · `button`.
- **Actions:** inspect each tab · withdraw a participant (frees its cupo, **generates no refund**) · manage teams · open the cupos purchases.
- **Navigation:** the tabs are in-page; the previous admin route is `/dashboard/inscripcion/[id]` — **provisional** (`P-02`-adjacent).
- **Data / contract dependencies (provisional):** `RT-IN-08`, `RT-IN-03`, `RT-IN-04`, `RT-IN-07`, `RT-IN-09`.
- **States:** `S-01` (per tab) · `S-02` (per tab: no teams / no participants / no purchases) · `S-04` · `S-06` · `S-10`.
- **Responsive intent:** 360/390 tabs scroll, body single column; 768 tabs + single column; 1024 tabs + 2 columns; 1440 tabs + body + sticky summary rail (the pool trio).
- **Semantic-token intent:** `bg-surface-raised` tab panels, `bg-surface-recessed` for the pool band, verdict chips, `border-border` for the tab strip, `bg-primary` for the primary tab action, `--destructive` for the withdraw action.
- **Accessibility intent:** the tab strip is a real `tablist`/`tab`/`tabpanel` with `aria-selected` and arrow-key navigation; each tab panel has its own empty state; the withdrawal confirmation names the effect exactly ("Retirar participante libera su cupo en esta inscripción; no genera devolución") — the plan's own wording.
- **Acceptance:** every permitted administrative action explains its consequence · the 403 is enforced by the backend even if the client forces the button (`QA-A03`).
- **Open decisions:** `PD-10` (exact scope of administrative modifications).

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-03a` | The admin list pattern is **shared** by the six list pages (registrations, teams, participants, payments, products, validations) and is documented in `03b` §3.4. It must be one pattern, not six. | A7 |
| `GOV-02-RB-03b` | Admin filters live in the **URL** (`adminParametrosConsulta` is the single filter contract) — never in a component-local store. | A7 |
| `GOV-02-RB-03c` | Every state vocabulary displayed in the admin comes from the backend catalogue; no literal is hardcoded (`07-guia-para-ui-ux.md` §2). | A7 |
| `GOV-02-RB-03d` | `acciones_disponibles` is a **projection**, not authorisation (`contratos/01` §6). The UI may use it to hide affordances; the backend still decides. | A7 + A0 |
