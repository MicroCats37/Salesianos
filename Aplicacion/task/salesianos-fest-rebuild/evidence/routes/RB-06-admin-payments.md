# RB-06 — Route Briefs: Admin Payments

**Artifact:** `evidence/routes/RB-06-admin-payments.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only
**Date:** 2026-11-19
**Page IDs in this file (1 of 38):** `ADM-14`
**Shared references:** `SH-01` … `SH-06`

> **Redesign priority.** `frontend/04` §6: the current admin payments view mixes the purchase, the order and the provider evidence in one layer. The rebuild must separate **three levels**.
> **Frozen obligation.** The backend already exposes the `estado_operativo` filter (`F-9`); exposing it in the UI is a **contract obligation**, not an optional improvement (`RT-PG-04`, `P-06`).

---

## `ADM-14` — `/administracion/pagos`

- **Actor:** administrador. **Priority:** **Alta** (redesign priority).
- **Objective:** investigate a purchase or a payment, and act on what needs attention.
- **Preconditions:** admin group; an edition context; the `Administrador` permission.
- **Visible sections — three separated levels:**
  1. **Operational list** — Compra/orden · comprador · concepto · total · fecha · **one** understandable state. Filters: `estado_operativo`, purchase type, date, free text.
  2. **Commercial detail** — what was bought · the state of the payment · what was obtained · the next permitted action.
  3. **Diagnosis and audit** — the order, the Izipay attempts, the evidence, manual operations. **Hidden by default under an advanced tab.**
- **Key components (candidates):** `table` (level 1) · `drawer` or a dedicated detail route (level 2) · `accordion` / `collapsible` (level 3, collapsed) · `badge` (verdict chip) · `input`/`select`/`popover` (filters) · `pagination` (server-driven, 1-based, `page_size` 25/100) · `alert-dialog` (manual approval) · `alert` (partial/indeterminate) · `command` (quick search).
- **Actions:**
  - *Primary* — filter by an understandable state; open a record; review an incidence.
  - *Sensitive* — register an external payment (only when permitted); audit a cancellation or a revocation.
  - *Explicitly forbidden* — "Aprobación manual" as a ubiquitous button; cancelling a payment as a synonym for removing participants; calling a delivered benefit "liquidated".
- **Navigation:** the list → the detail (drawer at ≥768, full route at ≥1024 or as a drawer everywhere for consistency) → back to the list with the filters preserved.
- **Data / contract dependencies (all provisional except the two noted):**
  - `RT-PG-04` — **frozen in GOV-01**: `GET /administracion/pagos`, presenter `AdminPagoPresenter`, wrapper `PaginatedData[AdminPagoListItemOut]`, query `page, page_size, q, ordering, estado_operativo, estado_compra, estado_orden, tipo, desde, hasta`, error `ACTION_NOT_ALLOWED` → 403, scope path-or-`edicion_id`, permission `Administrador`, `FREEZE-ENV-1.0.0`.
  - `RT-PG-05` — **frozen in GOV-01**: `POST /administracion/pagos/{orden_pago_id}/aprobar-manual`, presenter `AdminPagoManualPresenter`, wrapper `AdminPagoAprobarManualOut`, errors `PAGO_MANUAL_APROBACION_DESHABILITADA` / `MONTO_NO_COINCIDE` / `ORDEN_YA_PAGADA_CON_IZIPAY` / `COMPRA_YA_CANCELADA` → 409, permission `Administrador` + approval capability.
  - `RT-PG-07` — **provisional (this packet)**: `GET /administracion/pagos/{compra_id}` → `AdminPagoDetallePresenter` → `AdminPagoDetalleOut` (commercial detail + diagnosis).
  - `RT-PG-06` — **provisional (this packet)**: `GET /pagos/ordenes/{orden_id}/intentos` → `PagoIntentosPresenter` → `PagoIntentosOut` (the provider attempts, visible only under diagnosis).
  - `RT-ID-06` — **provisional**: the purchase detail for the commercial level.
- **States:** `S-01` (table skeleton) · `S-02` (no purchases for this edition) · `S-03` (filtered-empty — filters preserved + "clear filters") · `S-04` (recoverable error; 403 distinguished from 5xx) · `S-06` (not an administrator) · `S-08` (manual approval in progress) · `S-09` (payment confirmed but the right not yet enabled → *"Pago confirmado; estamos resolviendo la activación de tu compra"*) · `S-10` (manual approval confirmation naming the effect).
- **Responsive intent:** see `SH-06` §3. 360/390 a filter **sheet** plus one verdict card per purchase; 768 a 3-column table with the detail in a drawer; 1024/1440 the full table with a detail panel and the diagnosis collapsed.
- **Semantic-token intent:**
  - verdict chips from `SH-01` §3.2 — `--success` confirmed · `--warning` pending/verifying · `--info` needs attention · `--muted` not completed · `--destructive` rejected/revoked · unknown codes render **neutrally**, never as an error.
  - `bg-surface-raised` rows, `bg-surface-recessed` table header, `border-border`, `text-foreground-muted` for the buyer line, `tabular-nums` for amounts, `bg-primary` for the primary action, `--destructive` for the destructive audit actions.
  - **The provider layer never inherits a colour**: provider status is text inside the collapsed diagnosis, not a verdict chip.
- **Accessibility intent:**
  - One verdict per row, rendered as **colour + icon + the backend's `etiqueta`** (`SH-03` §6) — never colour alone.
  - `<th scope="col">` on every column; the row's accessible name includes the purchase id, the concept and the verdict.
  - The filter sheet traps focus and restores it to the filter trigger (A11Y-08/09).
  - The three levels are three **keyboard-reachable** disclosures; the advanced tab is reachable without a pointer.
  - The verdict is announced in a live region when the operator filters to "needs attention".
  - Amounts use tabular numerals; a re-render never reflows the column.
- **Acceptance cases:**
  - `QA-A01` — a clear state, the operational filter and the advanced diagnosis.
  - `frontend/04` §12.3 — a payment is explainable without looking at technical records; provider details appear only under diagnosis.
  - `frontend/04` §12.5 — a backend 403 prevents execution even if the button is forced from the client.
  - `frontend/04` §12.4 — every sensitive change shows a confirmation with its effect and, where required, a reason.
  - `FL-12` — the operator sees which right was enabled or which operation needs review.
- **Open decisions:**
  - `GOV-02-BL-01` — the success envelope **must include `message`**; the frozen backend already does, and the frozen test that asserts the opposite is a baseline failure. The mirror for `AdminPagoListItemOut` must accept it.
  - `GOV-02-BL-06` — the status-code convention for the 409 family must be frozen before API integration (baseline failures #8 and #9 are exactly this question).
  - `P-11` — the query-parameter names beyond `RT-PG-04` are provisional.
  - `PD-06` — refunds/cancellations are open; the "audit a cancellation" action may not exist in the first cut.

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-06a` | The client never infers a verdict by crossing `Compra.estado`, `OrdenPago.estado` and provider messages (`contratos/01` §1.4). The presenter supplies `estado_operativo.{codigo, etiqueta, descripcion}` and `acciones_disponibles`. | A7 |
| `GOV-02-RB-06b` | `estado_operativo` is a **frozen obligation** of the admin payments UI, not a nice-to-have. | A7 + A0 |
| `GOV-02-RB-06c` | `acciones_disponibles` is a projection, not authorisation (`contratos/01` §6). The 403 remains the control. | A7 + A0 |
| `GOV-02-RB-06d` | The row key must be unique and stable — the frozen `AdminPagosLista` fixture emits a duplicate key that React reports (`GOV-02-BL-07`). | A7 |
