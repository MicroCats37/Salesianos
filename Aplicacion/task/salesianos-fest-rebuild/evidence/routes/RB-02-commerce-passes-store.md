# RB-02 — Route Briefs: Passes, Store And Purchase Recovery

**Artifact:** `evidence/routes/RB-02-commerce-passes-store.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only
**Date:** 2026-11-19
**Page IDs in this file (6 of 38):** `PASS-01`, `PASS-02`, `SHOP-01`, `SHOP-02`, `SHOP-03`, `REC-01`
**Shared references:** `SH-01` … `SH-06` (see the header of `RB-01` for the reading convention)

> **Transversal concept** (`frontend/03`): each module has **its own checkout**; the visual payment component and the order state are shared. **There is no mixed cart** between registrations, passes and store products.

---

## `PASS-01` — `/pases` — buy party passes

- **Actor:** visitante (buyer may be a guest). **Priority:** **Alta**.
- **Objective:** buy individual party passes, with no sports registration and no mandatory account.
- **Preconditions:** passes enabled for the resolved edition.
- **Visible sections:** available pass + confirmed current price · quantity · summary · buyer identity (document type/number + email) via a modal/form · CTA "Continuar al pago" · an explicit note that **buyer and attendees may be different people**.
- **Key components (candidates):** `card` (pass options) · `input`/`select` (buyer) · `button` · `badge` (availability) · `dialog` or `sheet` (buyer form) · `alert` (payment states) · `empty` (no passes enabled).
- **Actions:** choose a pass and quantity · enter the buyer data · create the purchase and the order · pay · confirm · manage the beneficiaries.
- **Navigation:** to the shared checkout, then to `/pases/gestionar/[token]`.
- **Data / contract dependencies (provisional):** `RT-PS-01`, `RT-PS-02`, `RT-CM-02` (create the pass purchase — frozen in GOV-01), the payment-order route of the commerce/pagos freeze, `RT-ID-02`/`03` only if a `Persona` must be resolved.
- **States:** `S-01` · `S-05` (buyer form validation) · `S-08` (payment in progress) · `S-09` (payment pending / still verifying) · `S-04` · *gateway closed* · *payment failed* → "Reintentar de forma segura" · *entries pending assignment* (after a successful payment) · *no passes enabled for this edition* (hide the section, `S-02`).
- **Responsive intent:** see `SH-06` §6.1–6.2. 360/390 single column, sticky CTA, quantity stepper ≥ 44 px; 768 centred 480 px column; 1024/1440 two columns (options + sticky summary).
- **Semantic-token intent:** `bg-surface` page, `bg-surface-raised` pass cards, `border-primary` for the selected pass, `bg-primary`/`text-primary-foreground` CTA, `--accent` only for the "festival" framing of the pass (never for a state), `--warning` pending, `--success` confirmed, `--destructive` failed.
- **Accessibility intent:** the quantity stepper is keyboard-operable and announces its value; a price change is announced in a live region; the buyer form has associated labels and a focus-managed error summary; the "buyer ≠ attendees" note is real text, not a tooltip (tooltips do not exist on touch).
- **Acceptance:** closing the checkout does **not** delete the purchase (`QA-C01`) · beneficiaries are never assigned over an unpaid purchase · the buyer may differ from the attendees · no price is computed in the browser.
- **Open decisions:** `PD-02` (revocation/transfer) · `P-01` (the management-link token in the route).

---

## `PASS-02` — `/pases/gestionar/[token]` — guest pass management

- **Actor:** guest buyer holding a private link. **Priority:** **Alta**.
- **Objective:** assign and review passes **without creating an account**.
- **Preconditions:** a valid, non-expired private token; revalidation by email when the link has expired.
- **Visible sections:** purchase summary · quantities (acquired / assigned / pending) · the list of persons.
- **Key components (candidates):** `card` summary · the three counters · `input`/`select` (person resolution) · `button` · `alert` (error reasons) · `alert-dialog` (revocation — irreversible).
- **Actions:** resolve a person by document · assign a pass · review the state · revoke (per `PD-02`).
- **Navigation:** the receipt and the state view — no cross-link to another person's data.
- **Data / contract dependencies (provisional):** `RT-PS-03`, `RT-PS-04`, `RT-PS-05`, `RT-RT-03` (revoke a beneficiary — frozen in GOV-01), `RT-ID-01`/`02` (person resolution).
- **States:** `S-01` · `S-05` (document validation) · `S-06`/neutral denial: *link expired* · *purchase of another person* · *wrong document* · *person already has an active right* · *assignment without a cupo* · *pass revoked* · `S-08` (assignment in progress) · `S-10` (revocation confirmation).
- **Responsive intent:** see `SH-06` §6.3. 360/390 single column; 768 centred 560 px; 1024/1440 centred 640 px with the counters as a horizontal band.
- **Semantic-token intent:** `bg-surface-raised` summary, `bg-surface-recessed` for the counter band, `--success` for "entrada activa", `--warning` for "pendiente de asignación", `--destructive` for a revoked right, `bg-primary` for "Asignar".
- **Accessibility intent:** the denial message is **neutral and identical** whether or not a purchase exists (no existence oracle — `QA-U03`); the three counters are read as a sentence; errors are announced; the revocation dialog names the effect and traps focus.
- **Acceptance:** another person's purchases are **not** exposed by typing a DNI alone · assignment is refused without a cupo · a duplicate right is refused with the backend's message.
- **Open decisions:** `P-01` (token in the path vs a temporary session) · `PD-02` (revocation rules) · `GOV-01-OPEN-05` (guest-link expiry/rotation policy).

---

## `SHOP-01` — `/tienda` — store catalogue

- **Actor:** visitante. **Priority:** Media.
- **Objective:** discover Salesianos FEST's own products.
- **Preconditions:** the store module is enabled for the edition.
- **Visible sections:** optional search · category filters · product cards (main image, price/offer, availability) · CTA to the detail.
- **Key components (candidates):** `card` (product cards) · `carousel` (image strip inside a card) · `input` (search) · `select`/`tabs` (categories) · `badge` (offer, out of stock) · `empty` · `skeleton`.
- **Actions:** filter by category · search · open a product.
- **Navigation:** `/tienda/[slug]`.
- **Data / contract dependencies (provisional):** `RT-MK-01` (categories), `RT-MK-02` (products), `RT-MK-03` (detail).
- **States:** `S-01` · `S-02` no products · `S-03` category empty · *out of stock* (a state on the card, not an error) · *image error* (fallback placeholder, `alt` preserved) · *edition without a store* (the section is not rendered at all) · `S-04`.
- **Responsive intent:** 360/390 one card per row; 768 two to three cards; 1024 three to four cards + a sticky category rail; 1440 four cards, max content band 1280 px.
- **Semantic-token intent:** `bg-surface`, `bg-surface-raised` cards, `border-border`, `bg-surface-recessed` for the image well, `--destructive` for the offer badge only when the backend says the offer ended, `text-foreground-muted` for the category line.
- **Accessibility intent:** product images carry descriptive `alt` from the server description; the carousel is keyboard-operable; an out-of-stock product is **disabled with a text reason**, not dimmed only; no action depends on hover.
- **Acceptance:** the catalogue **never invents available stock** and the cards use server photos (`frontend/03` §SHOP-01 acceptance) · no mixed cart with packages or passes.
- **Open decisions:** none new.

---

## `SHOP-02` — `/tienda/[slug]` — product detail

- **Actor:** visitante. **Priority:** Media.
- **Objective:** evaluate a product and buy it.
- **Preconditions:** the product exists and is published for the edition.
- **Visible sections:** ordered `ProductoImagen` gallery · title · description · category · normal price / active offer · quantity · availability · CTA "Comprar".
- **Key components (candidates):** `carousel` + thumbnail row (keyboard-navigable, descriptive alt) · `badge` (offer, availability) · `input` (quantity) · `button` · `dialog` (buyer data) · `alert` (payment states).
- **Actions:** browse the gallery · choose a quantity · validate availability and price **in the backend** · enter buyer data · create the `Pedido` + `Compra` + `OrdenPago` · pay → "Pedido pagado / pendiente de entrega" + ticket if applicable.
- **Navigation:** the shared store checkout, then `/tienda/pedidos/[token]`.
- **Data / contract dependencies (provisional):** `RT-MK-03`, `RT-CM-03` (create the order — frozen in GOV-01), the payment-order route, `RT-ID-02`/`03` when a person must be resolved.
- **States:** `S-01` · `S-05` (quantity bounds, buyer form) · `S-08` · `S-09` (paid, awaiting delivery) · `S-04` · *price changed since the page loaded* → the backend's re-validation governs and the client shows the new price with the reason · *stock insufficient* (409 with the backend's business message).
- **Responsive intent:** 360/390 gallery first, then the title, then the price, then the CTA (sticky); 768 single column capped at 640 px; 1024/1440 gallery 60% + information 40%.
- **Semantic-token intent:** `bg-surface-raised` for the information block, `bg-surface-recessed` for the gallery well, `--success` for the offer badge, `--destructive` for a stock problem, `bg-primary` CTA, `border-border` separators.
- **Accessibility intent:** the gallery exposes a per-image accessible name and a position ("Imagen 2 de 5"); quantity is a labelled numeric input with keyboard support; the sticky CTA never covers the price; the offer badge pairs colour with the word "Oferta".
- **Acceptance:** the price and availability shown after re-validation are the backend's · the store checkout is bounded to the marketplace and never mixes passes or external cupos · a paid order shows "pagado / pendiente de entrega", not "entregado".
- **Open decisions:** `PD-05` (shared vs per-edition stock) affects the availability text.

---

## `SHOP-03` — `/tienda/pedidos/[token]` — guest order tracking

- **Actor:** guest buyer holding a private link. **Priority:** Media.
- **Objective:** follow an invited order.
- **Preconditions:** a valid private token.
- **Visible sections:** summary · products and quantities · **payment state** · **delivery state** · code/QR when applicable · the permitted consumption history.
- **Key components (candidates):** `card` summary · `badge` (payment state, delivery state) · `table`/card list (products) · `alert` (partial/indeterminate) · `sheet` (QR / code display) · `empty`.
- **Actions:** view the state · show the delivery code · consult the permitted history.
- **Navigation:** none outward beyond the order itself.
- **Data / contract dependencies (provisional):** `RT-MK-04`.
- **States:** `S-01` · neutral denial (expired / wrong link) · `S-02` (no items yet) · `S-09` (paid, not delivered) · `S-04`.
- **Responsive intent:** 360/390 single column, product lines as rows; 768+ two columns (summary + products).
- **Semantic-token intent:** `bg-surface-raised`, `--success` for "pagado", `--info` for "pendiente de entrega", `--warning` for "en verificación" — **payment state and delivery state are two different tokens and two different lines**.
- **Accessibility intent:** the two states are separate labelled rows so a screen-reader user cannot confuse them; the QR has a text alternative (the code) and a manual entry path.
- **Acceptance:** a paid order that has not been delivered **never** reads as "delivered" (`QA-M04`) · the consumption history shows only what the ticket permits.
- **Open decisions:** `P-01` (token in the path).

---

## `REC-01` — `/recuperar-compra` — recover a purchase link

- **Actor:** visitante. **Priority:** Media.
- **Objective:** recover the private management link by email.
- **Preconditions:** the mail provider is configured — **it is not** (`PD-08` deferred). The route ships with a **disabled-with-reason** state until then.
- **Visible sections:** email + minimal identifying data · a neutral answer.
- **Key components (candidates):** `input` · `button` · `alert` (neutral result) · `card`.
- **Actions:** request access.
- **Navigation:** none.
- **Data / contract dependencies (provisional):** `RT-RC-01`.
- **States:** `S-05` validation · *sent / pending* · *rate limited* · *temporary error* · `S-08` (request in progress).
- **Responsive intent:** 360/390 single centred column ≤ 480 px; 768+ same, centred.
- **Semantic-token intent:** `bg-surface`, `bg-surface-raised` card, `bg-primary` CTA, `--info` for the neutral result, `--destructive` for a temporary error with a retry.
- **Accessibility intent:** the neutral answer is announced via a live region; the field has a real label; the rate-limit message states when to retry; **no existence oracle** — the response is identical whether or not a purchase exists (`REC-01` acceptance).
- **Acceptance:** the response never reveals that a foreign DNI has entries · sending a second message never reopens a purchase.
- **Open decisions:** `PD-08` (SMTP provider) — the route is blocked functionally until a provider is chosen; the UI ships as a documented "temporarily unavailable" state.

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-02a` | **No mixed cart.** Each module keeps its own checkout; only the payment visual component and the order state are shared (`frontend/03`). | A7 |
| `GOV-02-RB-02b` | Closing the payment modal must never delete the purchase; reopening queries the existing order (`QA-C01`, `QA-C02`). | A7 + A2 |
| `GOV-02-RB-02c` | Never show `CAPTURED`, provider tokens, or "liquidación" (`contratos/01` §1.6). | A7 |
| `GOV-02-RB-02d` | The presentable payment states are exactly the five in `SH-03` §3. The client never derives a payment state from a modal close or a timeout (`contratos/01` §7). | A7 |
| `GOV-02-RB-02e` | Guest access is never granted by a DNI alone — a secure link or an authenticated session is required (`QA-U03`). | A7 + A4 |
