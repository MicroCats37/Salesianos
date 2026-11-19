# RB-07 — Route Briefs: Admin Passes, Entry Control And Marketplace

**Artifact:** `evidence/routes/RB-07-admin-passes-marketplace.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only
**Date:** 2026-11-19
**Page IDs in this file (6 of 38):** `ADM-15`, `ADM-16`, `ADM-17`, `ADM-18`, `ADM-19`, `ADM-20`
**Shared references:** `SH-01` … `SH-06`

> **Priority:** Media for all six (plan `frontend/01` §7.2: *"marketplace producto/pedido/inventario, administración de cortesías/tickets, control de entradas"*).
> **Cross-cutting invariant:** the ticket is a **credential that references a right**, never a duplicate of it; and **reading never consumes** — consuming is a separate, deliberate action (`FL-10`).

---

## `ADM-15` — `/administracion/pases` — passes and courtesy passes

- **Actor:** administrador. **Priority:** Media.
- **Objective:** manage passes and courtesy passes.
- **Preconditions:** admin group.
- **Visible sections:** catalogue of passes · purchases · beneficiaries · pending assignments · **courtesy passes (no payment)** · audited revocations.
- **Key components (candidates):** `table`/card list · `tabs` (purchased vs courtesy vs revoked) · `badge` (origin: purchased / courtesy) · `dialog` (grant a courtesy pass) · `alert-dialog` (revoke) · `input`/`select` (filters) · `empty`.
- **Actions:** grant a courtesy pass with a **reason** · assign a beneficiary · revoke · review the history.
- **Navigation:** `ADM-16` (entry control), the pass detail.
- **Data / contract dependencies (provisional):** `RT-PS-06`, `RT-PS-07` (courtesy list), `RT-PS-08` (grant a courtesy pass), `RT-PS-05` (assign a beneficiary), `RT-RT-03` (revoke — **frozen in GOV-01**).
- **States:** `S-01` · `S-02` · `S-03` · `S-04` · `S-06` · `S-10` (revocation confirmation) · *courtesy grant rejected* — the policy error from the backend.
- **Responsive intent:** 360/390 cards with the origin badge and the pending-assignment count; 768+ a table with a tab strip.
- **Semantic-token intent:** `bg-surface-raised`, `--accent` only to mark a **courtesy** origin (a festival-flavoured, non-transactional right) — never a verdict colour; `--success` for an active right; `--destructive` for a revoked right; `text-foreground-muted` for the reason line.
- **Accessibility intent:** the origin (purchased / courtesy) is **text**, not a colour; the reason for a courtesy grant and for a revocation is real text; the revoke confirmation names the effect; revocation rows expose their audit reason.
- **Acceptance:** a courtesy pass creates a free right with a reason and **never** a fictitious payment order or transaction (`FL-07` §3, `QA-P03`) · purchased and courtesy entries are visually distinguishable by origin (`implementacion/03` §3) · tokens are never shown in listings (`frontend/04` §7).
- **Open decisions:** `PD-02` (revocation rules) · `GOV-01-OPEN-08` (pass revocation business rules).

---

## `ADM-16` — `/administracion/pases/validar` — entry control

- **Actor:** operador autenticado. **Priority:** Media.
- **Objective:** scan or type a code, see the right, and confirm the entry.
- **Preconditions:** operator authenticated; the validation capability.
- **Visible sections:** scanner (QR) **or** manual code entry (always available) · the **preview** of the right: type, holder, pending/consumed/blocked, quantity, the reason when not allowed · **confirm entry** as a separate action.
- **Key components (candidates):** the scanner (a camera surface — **no shadcn registry item provides it**; it is a project component) · `input` (manual code) · `card` (the preview) · `badge` (right state) · `button` (confirm) · `alert` (the refusal reason) · `dialog` (the confirmation) · `spinner` (in-progress).
- **Actions:** scan · type a code manually · read the preview · **confirm** the entry.
- **Navigation:** none — a dedicated, focused screen (plan `frontend/01` §1.7: *"the QR reader is reusable; entry/delivery screens are separate"*).
- **Data / contract dependencies (all frozen in GOV-01):**
  - `RT-RT-01` — `POST /validaciones/preview`, `TicketPreviewPresenter` → `TicketPreviewOut`, `PreviewTicketIn`, errors `TICKET_NO_ENCONTRADO` → 404 · `ACTION_NOT_ALLOWED` → 403.
  - `RT-RT-02` — `POST /validaciones/confirmar`, `TicketConfirmPresenter` → `TicketConfirmadoOut`, `ConfirmarTicketIn` (**includes `idempotency_key`**), errors `TICKET_YA_CONSUMIDO` / `CANTIDAD_EXCEDIDA` / `DERECHO_REVOCADO` / `IDEMPOTENCY_KEY_REUTILIZADA` → 409.
- **States:** `S-01` (camera permission pending) · `S-04` (camera denied → the manual path is promoted to primary) · `S-08` (confirming) · `S-09` (confirmed) · *refused* — invalid / consumed / revoked / not permitted, each with a plain reason · *permission missing* (S-06).
- **Responsive intent:** 360/390 **full-bleed scanner** with the manual code field directly beneath it, always visible; 768 scanner + preview side by side; 1024/1440 camera + a large preview + the recent-entries audit list.
- **Semantic-token intent:** `bg-surface-inverse` for the scanner chrome, `--success` for a confirmed entry, `--destructive` for a refusal, `--warning` for a right that exists but is blocked, `text-foreground` on the preview card, `ring` for the focus.
- **Accessibility intent:** the camera permission request is explicit and explains the purpose; **manual code entry is a first-class path, never a degraded fallback**; the scan result is announced in an assertive live region; the confirm action is a large (≥44 px) deliberate button and is **not** triggered by the scan itself; reduced-motion applies to the scan feedback animation.
- **Acceptance:** reading a QR **does not consume** (`implementacion/03` §3 "Validaciones") · the confirm is idempotent and a reused `idempotency_key` is refused (`RT-RT-02`) · a second scan of a consumed ticket is denied and audited (`QA-V01`) · simultaneous scans consume only the permitted quantity (`QA-V02`).
- **Open decisions:** none new — `RT-RT-01`/`RT-RT-02` are frozen.

---

## `ADM-17` — `/administracion/marketplace` — store administration

- **Actor:** administrador. **Priority:** Media.
- **Objective:** manage products, orders and stock.
- **Preconditions:** admin group.
- **Visible sections:** products · orders · stock, each with its own tab or panel.
- **Key components (candidates):** `tabs` · `table`/card list · `badge` (state) · `button` · `input`/`select` (filters) · `empty` · `pagination`.
- **Actions:** filter · open a product · open an order · open the inventory.
- **Navigation:** `ADM-18` (product), `ADM-19` (inventory), `ADM-20` (deliveries).
- **Data / contract dependencies (provisional):** `RT-MK-05`, `RT-MK-07`, `RT-MK-08`.
- **States:** `S-01` · `S-02` · `S-03` · `S-04` · `S-06`.
- **Responsive intent:** 360/390 the three areas become a segmented control with card lists; 768+ tabs with tables.
- **Semantic-token intent:** `bg-surface-raised`, verdict chips, `bg-primary` for the primary action.
- **Accessibility intent:** the tab strip is a semantic tablist; each panel has its own empty state; filters live in the URL (`GOV-02-RB-03b`).
- **Acceptance:** one consistent operational list pattern across products, orders and stock (`frontend/06` §1).
- **Open decisions:** `P-05` — this route may become tabs of `ADM-01` or of a "Marketplace" section.

---

## `ADM-18` — `/administracion/marketplace/productos/[id]` — edit a product

- **Actor:** administrador. **Priority:** Media.
- **Objective:** edit a product's offer and availability, and manage its image gallery.
- **Preconditions:** admin group.
- **Visible sections:** title · description · category · price / optional offer · state · image gallery (ordered).
- **Key components (candidates):** `carousel` (gallery) · `input`/`textarea`/`select` · `input-group` + file input for images · `badge` · `dialog` (image actions) · `button` (save).
- **Actions:** edit the fields · upload images · reorder · remove an image · set the state.
- **Navigation:** back to `ADM-17`.
- **Data / contract dependencies:** `RT-MD-01` — **frozen in GOV-01**: `POST /marketplace/productos`, `ProductoPresenter` → `ProductoOut`, `CrearProductoIn` (**multipart `data` + `files`**), errors `MEDIA_TIPO_NO_PERMITIDO` / `MEDIA_ARCHIVO_HUERFANO` / `MEDIA_TOKEN_NO_RESUELTO` → 400 · `MEDIA_TAMANO_EXCEDIDO` → 413. Plus `RT-MK-06` (detail, provisional).
- **States:** `S-01` · `S-05` (validation; 422 → `field_errors` → RHF `setError`) · `S-08` (upload in progress with a truthful progress indication) · `S-09` (the image was accepted but is not yet processed) · `S-04` · *media rejected* (type / size / orphan file — the backend's reason) · `S-10` (image removal).
- **Responsive intent:** 360/390 the gallery is full-width with the form below; 768 gallery + form stacked; 1024/1440 gallery 40% + form 60%.
- **Semantic-token intent:** `bg-surface-raised` form surface, `border-border` inputs, `bg-primary` save, `--destructive` for the destructive image removal, `bg-surface-recessed` for the gallery well.
- **Accessibility intent:** every image has a descriptive `alt`; the gallery is keyboard-operable; the file input has a real label and announces the accepted types and the size limit; the 413 message states the limit; upload progress is announced.
- **Acceptance:** `N` images are persisted in order, locally, without a CDN (`QA-MEDIA01`) · the multipart protocol is exactly `data` JSON + `files` parts named `<token>___<realname>` (`FREEZE-MD-1.0.0`) · an orphan file is rejected by the backend, never silently ignored.
- **Open decisions:** `GOV-01-OPEN-10` (image dimension limits) · `GOV-01-OPEN-09` (media backup/permissions).

---

## `ADM-19` — `/administracion/marketplace/inventario` — stock

- **Actor:** administrador. **Priority:** Media.
- **Objective:** see stock, record movements, and read the ledger.
- **Preconditions:** admin group.
- **Visible sections:** current stock per product · movement history · the operations: entry, wastage, internal consumption, **exit without a sale** (each with a reason).
- **Key components (candidates):** `table`/card list (movements) · `dialog` (the movement form) · `select` (movement type) · `input` (quantity, reason) · `badge` (movement type) · `alert-dialog` (confirmation of an exit) · `empty`.
- **Actions:** record an entry / an adjustment / a wastage / an internal consumption / an exit without a sale · read the ledger.
- **Navigation:** back to `ADM-17`; to the product (`ADM-18`).
- **Data / contract dependencies (provisional):** `RT-MK-08` (inventory), `RT-MK-09` (register a movement).
- **States:** `S-01` · `S-02` (no movements yet) · `S-03` · `S-05` (quantity and reason are mandatory) · `S-08` · `S-10` (an exit without a sale is confirmed with its effect) · *insufficient availability* — the backend's reason.
- **Responsive intent:** 360/390 stock as cards and movements as a reverse-chronological list; 768+ two columns (stock + ledger).
- **Semantic-token intent:** `bg-surface-raised`, `--warning` for an adjustment, `--destructive` for an exit without a sale, `text-foreground-muted` for the actor and the instant, `tabular-nums` for the quantities and the resulting stock.
- **Accessibility intent:** every movement row states the type, the signed quantity, the reason, the actor and the instant as text; a negative quantity is announced as a decrease; the reason field is mandatory and labelled.
- **Acceptance:** an administrative exit produces a movement of −5 with an actor and a reason and **no** fictitious purchase (`QA-M02`, `FL-09` §3) · the stock changes and the ledger shows it · the backend validates availability.
- **Open decisions:** `PD-05` (shared vs per-edition stock) changes the inventory key.

---

## `ADM-20` — `/administracion/marketplace/entregas` — deliveries

- **Actor:** operador autenticado. **Priority:** Media.
- **Objective:** validate a pickup and confirm the delivery.
- **Preconditions:** operator authenticated.
- **Visible sections:** scanner or manual code · the order preview (products and quantities) · **confirm delivery** as a separate action · a guard against a double redemption.
- **Key components (candidates):** the scanner (project component) · `input` (manual code) · `card` (order preview) · `table` (product lines) · `badge` (delivery state) · `button` (confirm) · `alert` (refusal reason) · `dialog`.
- **Actions:** scan · type a code · read the preview · confirm the delivery.
- **Navigation:** none — a dedicated screen, separate from the entry control (`ADM-16`), per plan principle 7.
- **Data / contract dependencies (provisional):** `RT-MK-10` (delivery list); the confirmation route is the **same shared validation service** as `RT-RT-02` with a store context — the context discriminator belongs to the presenter, not to a duplicated client.
- **States:** `S-01` · `S-04` · `S-08` · *refused* — already delivered, ticket invalid, wrong order · *partial delivery* (some lines delivered) → the remaining quantity is shown and the operation is idempotent per quantity.
- **Responsive intent:** 360/390 full-bleed scanner with manual entry beneath; 768+ scanner + preview side by side.
- **Semantic-token intent:** `bg-surface-inverse` scanner chrome, `--success` delivered, `--warning` partially delivered, `--destructive` refused, `ring` for focus.
- **Accessibility intent:** identical to `ADM-16` — manual entry is first-class, the result is announced, the confirm is deliberate and ≥44 px.
- **Acceptance:** a paid order is **not** equivalent to a delivered one (`QA-M04`) · a double redemption is prevented and audited (`QA-V01`) · delivery and entry validation remain **separate** flows (`frontend/04` §10).
- **Open decisions:** none new.

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-07a` | **Preview never consumes.** Reading a code shows the right; consuming is a separate, deliberate, idempotent action (`FL-10` §4). | A7 + A8 |
| `GOV-02-RB-07b` | A courtesy pass **never** creates a payment order or transaction (`FL-07` §3). | A7 + A4 |
| `GOV-02-RB-07c` | An administrative stock exit **never** creates a purchase (`FL-09` §3). | A7 + A5 |
| `GOV-02-RB-07d` | The media protocol is `data` + `files` with `<token>___<realname>`; the client never hand-builds an alternative (`FREEZE-MD-1.0.0`, `GOV-01-OPEN-*`). | A7 + A5 |
| `GOV-02-RB-07e` | Entry validation and delivery validation are **separate screens** and separate audit records (`frontend/04` §10). | A7 |
