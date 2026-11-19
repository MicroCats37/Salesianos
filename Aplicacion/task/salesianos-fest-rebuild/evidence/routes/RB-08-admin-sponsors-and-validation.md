# RB-08 — Route Briefs: Admin Sponsors And The Validation Audit

**Artifact:** `evidence/routes/RB-08-admin-sponsors-and-validation.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only
**Date:** 2026-11-19
**Page IDs in this file (2 of 38):** `ADM-21`, `ADM-22`
**Shared references:** `SH-01` … `SH-06`

---

## `ADM-21` — `/administracion/patrocinadores` — sponsors

- **Actor:** administrador. **Priority:** Media.
- **Objective:** manage sponsor records, their logo, their ordered gallery, their relation to the edition, and their visibility.
- **Preconditions:** admin group.
- **Visible sections:** sponsor list · the record (logo, ordered gallery, edition relation, visibility) · create/edit.
- **Key components (candidates):** `table`/card list · `carousel` (the ordered gallery) · `input`/`textarea`/`select` · `input-group` + file input (logo and images) · `switch` (visibility) · `badge` · `dialog` · `button`.
- **Actions:** create · edit · upload the logo · upload and order gallery images · toggle visibility · relate to an edition.
- **Navigation:** back to the admin navigation.
- **Data / contract dependencies:** `RT-MD-02` — **frozen in GOV-01**: `POST /patrocinadores`, `PatrocinadorPresenter` → `PatrocinadorOut`, `CrearPatrocinadorIn` (multipart `data` + `files`), the same media error family as `RT-MD-01`. Plus `RT-PA-01` (list) and `RT-PA-02` (detail) — **provisional (this packet)**; `RT-ED-07` (the public, edition-scoped sponsor read) — **provisional**.
- **States:** `S-01` · `S-02` (no sponsors) · `S-03` · `S-05` (validation; 422 → `field_errors`) · `S-08` (upload in progress) · `S-09` (image accepted, not yet processed) · `S-04` · *media rejected* (type / size / orphan file / unresolved token) · `S-10` (removing a sponsor record).
- **Responsive intent:** 360/390 cards with the logo and the gallery stacked; 768+ a two-column form (identity | media).
- **Semantic-token intent:** `bg-surface-raised` form surface, `bg-surface-recessed` for the gallery well, `border-border` inputs, `bg-primary` save, `--destructive` for the destructive removal, `--accent` reserved for the **public** sponsor strip on `PUB-01` (never as a state).
- **Accessibility intent:** every logo and gallery image carries a descriptive `alt`; the gallery is keyboard-operable and announces the position; the visibility switch has a real label; the file input announces the accepted types and the size limit.
- **Acceptance:** the gallery is **ordered** and persisted locally without a CDN (`QA-MEDIA01`) · there are **no monetary fields** — no contributions, no commissions (`frontend/04` §9) · the sponsor's relation to the edition and its visibility are editable.
- **Open decisions:** `GOV-01-OPEN-09` (media backup/permissions) · `GOV-01-OPEN-10` (image dimension limits).

---

## `ADM-22` — `/administracion/validaciones` — the transversal audit

- **Actor:** administrador. **Priority:** Media.
- **Objective:** audit every entry and delivery validation across the system.
- **Preconditions:** admin group.
- **Visible sections:** search by ticket/code · person · purchase/reference · right type · date · operator · verdict · point (where it happened).
- **Key components (candidates):** `input` (search) · `select` (right type, verdict, operator, point) · `table`/card list · `badge` (verdict) · `empty` · `pagination` · `drawer` (the record detail).
- **Actions:** filter on any of the eight dimensions · open a validation record · read the actor, the instant, the quantity and the result.
- **Navigation:** to the person, the purchase or the ticket.
- **Data / contract dependencies (provisional):** `RT-VA-01` — `GET /administracion/validaciones`, `AdminValidacionListaPresenter` → `PaginatedData[AdminValidacionListItemOut]`, permission `Administrador`. The **write** side of validation is already frozen as `RT-RT-01`/`RT-RT-02`.
- **States:** `S-01` · `S-02` (no validations for the filters) · `S-03` (filtered-empty with the filters preserved) · `S-04` · `S-06`.
- **Responsive intent:** 360/390 the filter opens as a sheet and the results are cards exposing actor, instant and verdict; 768+ a table with the priority columns (ticket, verdict, actor, instant).
- **Semantic-token intent:** `bg-surface-raised`, verdict chips (`--success` consumed · `--destructive` refused · `--warning` partial · `--muted` unknown), `text-foreground-muted` for the point and the reference, `tabular-nums` for the instant.
- **Accessibility intent:** the record exposes **actor, instant, result and point as text** — never a colour-only trail; the instant is a machine-readable `datetime` with a readable rendering; the filter sheet traps and restores focus; the table headers are scoped.
- **Acceptance:** entry validation and payment confirmation are **never conflated** (`frontend/04` §10) · a consumed ticket shows its previous consumption when authorised (`FL` recovery matrix) · the audit covers both the entry and the store contexts.
- **Open decisions:** none new.

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-08a` | Media uploads always use the frozen multipart protocol; the component never builds `FormData` itself (`salesianos-api-data` Hard Rule 21, `FREEZE-MD-1.0.0`). | A7 + A5 |
| `GOV-02-RB-08b` | Sponsors carry **no monetary fields** while monetary sponsorship remains out of scope (`frontend/04` §9). | A7 |
| `GOV-02-RB-08c` | The validation audit is **transversal**: it lists both entry validations and store delivery validations, and never mixes them with payment confirmations (`frontend/04` §10). | A7 + A8 |
