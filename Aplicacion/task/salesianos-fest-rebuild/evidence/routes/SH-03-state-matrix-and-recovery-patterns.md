# SH-03 — State Matrix And Recovery Patterns (shared across all 38 page IDs)

**Artifact:** `evidence/routes/SH-03-state-matrix-and-recovery-patterns.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — brief only
**Date:** 2026-11-19
**Authority:** `Aplicacion/plan/salesianos-fest-rebuild/frontend/06-sistema-ux-ui.md` §3 · `Aplicacion/plan/salesianos-fest-rebuild/funcional/04-flujos-end-to-end.md` (recovery matrix) · `00-workflow-frontend-contract-first.md` §1 · `Aplicacion/documentacion/07-guia-para-ui-ux.md` §4.4, §4.5

---

## 1. The Ten Required States

`00-workflow-frontend-contract-first.md` §1 mandates exactly these ten. Each is defined once here; route briefs reference the definition and only add route-specific content.

| # | State | Definition | Component intent | Forbidden |
|---|---|---|---|---|
| S-01 | **Initial / loading** | First paint of a data-backed surface | Skeleton that mirrors the final layout (card skeleton for cards, row skeleton for tables) | A centred spinner over an empty page; a skeleton that does not match the final geometry |
| S-02 | **Empty (never had data)** | The collection is genuinely empty for this actor/edition | Explains what does not exist and offers the one relevant action | "No data"; a blank table; a disabled button |
| S-03 | **Filtered-empty** | Data exists but the active filters exclude it | Keeps the filters visible, states the filter count, offers "clear filters" | Replacing the list with an empty-state that implies there is no data |
| S-04 | **Recoverable error** | The request failed in a way the user can retry | Explains the problem in plain language + "Retry" | A raw stack trace; a bare HTTP code; a silent console error |
| S-05 | **Validation** | The submission was rejected on field data | Field-level message + summary + focus to the first invalid field | An error only at the top of the form; a message that contradicts the backend's wording |
| S-06 | **Permission** | The backend refused (401/403) | Explains that the account lacks the permission; offers the recovery that exists (sign in, request access) | Hiding the error because the button was hidden; a 403 that looks like a bug |
| S-07 | **Success** | A mutation completed | States what changed and what can be done next | A toast that says "ok"; a toast with no next action |
| S-08 | **In progress** | A mutation is running | Double-submit prevented, truthful progress, no invented duration | A spinner with a fabricated ETA; a disabled button with no explanation |
| S-09 | **Partial / indeterminate** | The operation succeeded partially or is not yet conclusive (payment verified but right not yet enabled; order paid but not delivered) | Names the exact pending thing and offers a **safe** follow-up that does not duplicate the operation | Treating it as success; auto-retrying a payment; hiding it |
| S-10 | **Irreversible confirmation** | The action cannot be undone | Names the concrete effect ("retirar libera su cupo; no genera devolución") and captures a reason where required | "Are you sure?" without naming the effect |

---

## 2. HTTP Status → Presentation Contract

The backend envelope is frozen by `FREEZE-ENV-1.0.0` (`D-06`): success `{success, data, error:null, message}`; error `{code, message, details?, field_errors[]}`. The UI reacts to the **status** and shows the backend `message` verbatim (`07-guia-para-ui-ux.md` §4.4).

| Status | Presentation | Recovery offered | Route examples |
|---|---|---|---|
| **400** | The request was malformed / signature invalid | "Reintentar" once the cause is corrected; never auto-retry | ADM-16, ADM-20, payments |
| **401** | Session absent or expired | "Iniciar sesión" — the intent is preserved where possible (`FL` recovery matrix) | All account/admin routes |
| **403** | Authenticated but not permitted | "Tu cuenta no tiene permiso para esta acción" + who to contact | Every admin action |
| **404** | The referenced resource does not exist (or the edition is not published) | Empty-state, not an error toast: "Esta edición no está publicada" | PUB-01, PUB-02, all detail routes |
| **409** | A business conflict (already paid, no cupos, team not eligible, ticket consumed) | Show the **business** reason from the backend message; offer the next legitimate action | ACCOUNT-03, ADM-07, ADM-14, ADM-16 |
| **413** | Payload too large (media) | "La imagen supera el tamaño máximo" with the limit | ADM-18, ADM-21 |
| **422** | Field validation | Field-level errors via `error.field_errors[]` → RHF `setError` | All forms |
| **5xx** | Server fault | "Reintentar" + a reference to the edition; no technical detail | All routes |

**Rule:** `field_errors[]` is the **only** per-field channel (`C-ENV-02`). `error.details` carries non-field context only. The client never parses `error.details` into fields and never invents a field mapping in a component (`07-guia-para-ui-ux.md` §4.5).

**Known debt that must not be copied:** the frozen frontend's 422 parser is documented but **not implemented** (`FE-12`), and its fallback messages are in English while the backend speaks Spanish (`FE-13`). The rebuild must implement the parser once, globally, in the API layer — never per component.

---

## 3. The Five Presentable Payment States (shared checkout component)

From `frontend/03-paginas-comerciales.md` §"Componente compartido de pago" and `FL-06`, `FL-12`. The client **never** shows provider tokens, `CAPTURED`, or "liquidación".

| Presented state | Meaning | CTA | Backend source |
|---|---|---|---|
| Pago pendiente | No money confirmation yet | Continuar pago | `estado_operativo` (pending) |
| Verificando pago | Result received, not conclusive | Consultar más tarde | `estado_operativo` (verifying) |
| Pago confirmado | Valid evidence of charge | Ver entradas / cupos / pedido | `estado_operativo` (confirmed) + `derechos_otorgados` |
| Pago no completado | Attempt failed, purchase unpaid | Reintentar de forma segura | `estado_operativo` (not completed) |
| Necesita atención | Charged but the right is not yet enabled | Contactar soporte / revisión admin | `estado_operativo` (needs attention) |

**Hard rule (all checkout routes):** closing the modal **never** deletes the purchase. Reopening the checkout queries the existing order; it does not create a new one. See `QA-C01` / `QA-C02`.

---

## 4. Common Recovery Matrix (from `funcional/04` §"Matriz de recuperación común")

| Situation | Required behaviour | Applies to |
|---|---|---|
| Browser closes the modal | Purchase persists and can be recovered | PASS-01, SHOP-02, SPORT-01 |
| Checkout reopened | Query the attempt and the order; do not create a duplicate purchase | PASS-01, SHOP-02, SPORT-01 |
| Webhook repeated | Payment and activation are idempotent (backend) | all checkout routes |
| Mail not sent | Paid purchase persists; notification is retryable | PASS-02, SHOP-03, REC-01 |
| Stock reservation expires | Release per the chosen policy; no fictitious sale | SHOP-01, ADM-19 |
| Session expired | Ask for sign-in or a secure link; preserve the intent when possible | ACCOUNT-*, ADM-* |
| No active edition | Say so clearly; never attribute operations to another edition | PUB-01, PUB-02, all catalogue |
| Ticket already used | Refuse a second consumption and show the previous record if authorised | ADM-16, ADM-20, ADM-22 |

---

## 5. Route-Specific State Addenda

| Page ID | State that is **not** generic and must be called out in the brief |
|---|---|
| PUB-01 | "Edición no publicada" (message, not an error) · "Módulo no habilitado" (hide the section, not show it empty) · catalogue load error with retry and **no invented fallback** |
| PUB-02 | Anchor navigation must land on sections that exist; no second client-side catalogue for the same packages |
| AUTH-01 | Wrong credential (specific) · account disabled · administrative account routed to the panel |
| AUTH-02 | DNI not found · external source temporarily unavailable · document already linked to an account · duplicate email |
| ACCOUNT-02 | No inscriptions · payment in verification · modification window closed · connection error |
| ACCOUNT-03 | No paid cupos · modification closed · player not eligible · cupos exhausted · duplicate person for a discipline · pending purchase |
| PASS-01 | Gateway closed · pending · confirmed · still verifying · payment failure · entries pending assignment |
| PASS-02 | Link expired · purchase of another person · wrong document · person already has an active right · assignment without a cupo · revoked pass |
| SHOP-01 | No products · empty category · out of stock · image error · edition without a store |
| SHOP-02 | Availability/price re-validated in the backend before the order is created |
| SHOP-03 | A paid order that has not been delivered must **not** read as "delivered" |
| REC-01 | Sent / pending / rate-limited / temporary error · neutral answer · a second request never reopens a purchase |
| ADM-01 | "Aún no hay inscripciones para esta edición" |
| ADM-06 | Tabbed: Resumen · Equipos · Pool y personas · Compras de cupos · Historial — each tab has its own empty state |
| ADM-07 | "6 jugadores registrados; necesita al menos 7" · "No hay cupos deportivos disponibles" · "Este jugador ya participa en la misma disciplina" — the reason comes from the backend |
| ADM-11 | "Por definir" (no participants yet) · scheduled · in progress / finished (backend vocabulary) · version conflict → reload and retry **without silently applying stale changes** |
| ADM-12 | Advance error highlights the blocking match/slot |
| ADM-14 | One understandable verdict per row · diagnosis hidden under an advanced tab by default |
| ADM-16 | Invalid / consumed / revoked / not permitted — each with a plain reason; reading a QR does **not** consume |
| ADM-19 | Stock movement with actor + reason; no purchase is created for a non-sale exit |
| ADM-22 | Audit: entry validation and payment confirmation are **different** things and must never be conflated |

---

## 6. Interaction Language (interface vocabulary)

`frontend/06` §2 — the client shows the backend's business language, never internal codes.

| Internal | Show |
|---|---|
| `settlement_status` / liquidación | "Beneficio habilitado" · "Cupos disponibles" · "Entrada activa" |
| `PENDIENTE` (no context) | "Pago pendiente" or "Pendiente de asignación", per the operation |
| `AL_LIMITE` | "Equipo completo: alcanzó máximo de jugadores" |
| `INCOMPLETO` | "Falta 1 jugador para competir" (the backend's reason) |
| `PASE_BENEFICIARIO_DUPLICADO` | "Esta persona ya tiene una entrada activa para esta edición" |
| `RESOURCE_CHANGED` | "Los datos cambiaron. Actualiza y revisa antes de guardar." |

The client **never** invents a message that contradicts a backend rule (`frontend/06` §2).

---

## 7. Copy Principles Applied To Every Brief

From `frontend-design` §"More on writing about design":

- Active voice; the CTA names exactly what happens ("Continuar al pago", not "Enviar").
- An action keeps the same name through the whole flow ("Publicar" → toast "Publicado").
- Errors do not apologise and are never vague; they name the cause and the fix.
- An empty screen is an invitation to act, not a mood.
- Plain verbs, sentence case, no filler, no emoji, no tracked-out ALL-CAPS eyebrows above every heading.
- Spanish is the interface language (the backend's public messages are Spanish); technical identifiers stay as the backend emits them.
