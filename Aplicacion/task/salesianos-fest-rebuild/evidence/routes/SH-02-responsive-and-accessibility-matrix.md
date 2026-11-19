# SH-02 — Responsive And Accessibility Matrix (shared across all 38 page IDs)

**Artifact:** `evidence/routes/SH-02-responsive-and-accessibility-matrix.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 (UI) · A9 (review) · **Status:** DRAFT FOR REVIEW — brief only
**Date:** 2026-11-19
**Authority:** `.opencode/skills/salesianos-responsive-a11y/SKILL.md` (Hard Rules 1–5, Decision Gates) · `.opencode/agents/ui-ux-reviewer.md` (finding format) · `Aplicacion/documentacion/07-guia-para-ui-ux.md` §7.5

---

## 1. Mandatory Viewport Matrix

Every one of the 38 page IDs is audited at exactly these five widths. A route is not "responsive" because it works at one of them.

| # | Width | Class | Device reference | What it must prove |
|---|---|---|---|---|
| **W1** | **360** | Small phone (Android baseline) | 360×800 | No horizontal overflow. Sticky CTA does not cover content. Tables collapse to stacked cards. Touch targets ≥ 44×44 px. Wizard steps fit without a horizontal scroll. |
| **W2** | **390** | Default phone (iPhone 14/15/16) | 390×844 | Primary flow (buy / apply / validate) completes without pinch-zoom. Bottom nav ≤ 5 items. |
| **W3** | **768** | Tablet portrait | 768×1024 | Two-column composition for content (not for dense tables). Drawer becomes a side sheet. Sidebar collapses to icon rail. |
| **W4** | **1024** | Tablet landscape / small laptop | 1024×768 | Admin list + detail can coexist (master–detail) without horizontal scroll. Filter bar wraps, does not truncate. |
| **W5** | **1440** | Desktop | 1440×900 | Maximum measure for body text ≤ 80 characters. Admin table uses the full width without stretching a single column to 600 px. Content is centred with a max width, not edge-to-edge. |

### 1.1 Per-family composition rules

| Family | 360 | 390 | 768 | 1024 | 1440 |
|---|---|---|---|---|---|
| Public marketing (PUB) | Single column; hero text 28–32 px; image below | Same, 32 px | Two-column hero (text + visual) | Two-column, generous | Two-column, max 1200 px content band, hero band full-bleed |
| Public catalogue (SHOP) | 1 product card per row | 1–2 cards | 2–3 cards | 3–4 cards | 4 cards + sticky category rail |
| Public wizard (SPORT, PASS checkout) | Full-screen step, sticky footer CTA | Same | Centred 640 px step, footer inline | Same | Centred 640 px step |
| Account (ACCOUNT) | Card list | Card list | 2-col summary | 2-col | 3-col summary + side rail |
| Admin list (ADM list pages) | Card-per-record stack (no table) | Card stack | Table with 3 priority columns | Table, 5–6 columns + filter bar | Table, full column set + column visibility toggle |
| Admin detail (ADM detail pages) | Stacked sections, tabs become a scrollable segmented control | Same | Tabs | Tabs + side summary | Tabs + 2-col (main + sticky summary) |
| QR / validation (ADM-16, ADM-20) | **Full-bleed scanner**, manual code entry always visible below | Same | Scanner + preview side by side | Same | Camera + large preview + audit list |
| Bracket (ADM-12, public bracket) | Horizontal scroll container with round indicators, card detail below | Same | Same | Same | Bracket centred, scroll only if > 8 columns |

### 1.2 Anti-patterns rejected at every width

- Horizontal page overflow (body-level scroll-x).
- Fixed pixel container widths.
- Content clipped or hidden with no alternative (an action reachable only at 1440 is a defect).
- Actions that exist only on hover.
- A dialog wider than the viewport or with no mobile variant.
- A table whose only affordance is a horizontal scrollbar with no column prioritisation.
- `user-scalable=no` / zoom disabled.

---

## 2. Accessibility Contract (per route, verified at W1–W5)

### 2.1 Global requirements

| ID | Requirement | Verification |
|---|---|---|
| A11Y-01 | Every interactive element is keyboard reachable in a logical order | Tab order walk-through per flow |
| A11Y-02 | Focus is always visible (`:focus-visible`, 2 px `--ring`, 2 px offset) — never `outline: none` without a replacement | Visual check + `T-01` ring token |
| A11Y-03 | Body text contrast ≥ 4.5:1; large text and UI borders ≥ 3:1 | Contrast check per token pair (light **and** dark) |
| A11Y-04 | Every input has a programmatically associated `<label>`; every error is associated with its field via `aria-describedby` | DOM inspection |
| A11Y-05 | Form errors are announced (`role="alert"` / `aria-live="assertive"` on the error summary) and the summary receives focus on submit | Keyboard + screen-reader pass |
| A11Y-06 | Icon-only buttons carry `aria-label`; decorative icons are `aria-hidden` | DOM inspection |
| A11Y-07 | Touch targets ≥ 44×44 px with ≥ 8 px spacing | Measured at W1/W2 |
| A11Y-08 | Dialogs trap focus, restore it to the trigger on close, and close on `Escape` | Keyboard pass per dialog |
| A11Y-09 | Modals/drawers fit the viewport at 360 and do not create a second scroll trap | Visual check at W1 |
| A11Y-10 | Current location is exposed in navigation (`aria-current="page"`) | Navigation audit |
| A11Y-11 | Status is never conveyed by colour alone — colour + icon + text | Visual check per verdict chip |
| A11Y-12 | `prefers-reduced-motion` disables all non-essential motion | Emulation check |
| A11Y-13 | Images carry descriptive `alt`; decorative images `alt=""` | Image audit per route |
| A11Y-14 | QR scanning always offers manual code entry as an alternative, and requests camera permission explicitly | Camera-permission test |
| A11Y-15 | Long content (team names, product titles, buyer names) truncates with a title/tooltip and does not break layout | Content-expansion test at W1 |
| A11Y-16 | Zoom to 200 % at W5 does not remove content or actions | Zoom test |

### 2.2 Per-surface requirements (from `salesianos-responsive-a11y` Decision Gates)

| Surface | Requirement |
|---|---|
| **Tables** | Preserve meaning. At ≤ 768 each record becomes a labelled card (label from the column header, not a generic "Field"). At ≥ 1024 a horizontally scrollable region is permitted **only** with prioritised columns visible and an explicit scroll affordance. Column header semantics must be `<th scope="col">`. |
| **Forms** | Label, description, error and focus order are preserved at every width. Inputs ≥ 44 px high at W1/W2. `autocomplete` set for identity fields. Wizard shows a visible step indicator with the current step announced. |
| **Dialogs** | Focus trapped and restored. Title associated via `aria-labelledby`. Dismiss control always reachable. At 360 a dialog is a bottom sheet or a full-height panel, never a squeezed centred box. |
| **Navigation** | Current location exposed. Compact behaviour at ≤ 768 must be a drawer/dialog (shadcn `sidebar` `offcanvas` variant) rather than a hidden hamburger with no affordance. |

### 2.3 Route-specific a11y hotspots

| Page ID | Hotspot |
|---|---|
| PUB-01 | Hero motion under reduced motion; marquee must not be the only way to reach information; decorative orbs hidden from AT. |
| AUTH-01 / AUTH-02 | Password visibility toggle must be a labelled button; password-manager hints preserved; error summary on submit. |
| SPORT-01 | Wizard step navigation announces the step; progress is not colour-only; the "next" action states what it will do. |
| ACCOUNT-03 | Pool numbers must be readable as a sentence ("6 de 8 cupos asignados"), not only as three separate numerals. |
| PASS-01 / SHOP-02 | Quantity stepper is keyboard-operable and announces the value; price change is announced. |
| PASS-02 / SHOP-03 | Token links are **not** the only gate: the page must state why access is denied without leaking whether a purchase exists. |
| ADM-05 / ADM-07 / ADM-09 | The list must remain operable at 360 without hover; the drilldown affordance is a real link/button. |
| ADM-12 | Bracket is keyboard-scrollable; each match card is a button with an accessible name including both teams. |
| ADM-14 | Verdict chips carry the backend `etiqueta` text; the technical diagnosis is in a collapsed section that is keyboard-reachable. |
| ADM-16 / ADM-20 | Scanner is an enhancement; manual entry is a first-class path. Confirming a consumption is a deliberate, non-hover action. |
| ADM-22 | Audit table exposes actor, instant, verdict and point as text. |

---

## 3. Required State Matrix Per Route

Every route must expose the ten states required by `00-workflow-frontend-contract-first.md` §1, using the shared definitions in `SH-03-state-matrix-and-recovery-patterns.md`.

| State | Required for | Minimal evidence |
|---|---|---|
| Initial / loading | All data-backed routes | Skeleton that matches the final layout (no spinner over an empty box) |
| Empty (never had data) | All list/collection routes | Explains what does not exist + one relevant action |
| Filtered-empty | All filterable list routes | Keeps filters visible + "clear filters" action |
| Recoverable error | All data-backed routes | Explains the problem + "Retry" + distinguishes 401/403/404/409/422/5xx |
| Validation | All form routes | Field-level error + summary + focus to first invalid field |
| Permission | Every admin route | 403 is explained; the action is hidden, not disabled-and-broken |
| Success | All mutating routes | States what changed + what can be done next |
| In-progress | All mutating routes | Double-submit prevented; truthful progress; no invented ETA |
| Partial / indeterminate | Payment, activation, validation | "Verified but not yet enabled" + safe follow-up that does not duplicate the operation |
| Irreversible confirmation | Revocation, removal, manual approval, delivery | Confirmation stating the concrete effect + reason capture where required |

---

## 4. Review Cadence (obligations for the next packets)

| Packet | Obligation |
|---|---|
| UI-01…UI-05 (skeletons) | Evidence file per route family listing the five widths, the ten states, the shadcn items chosen and the token roles consumed. No implementation code outside the allowed roots. |
| API-01…API-05 (integration) | Re-run the five-width audit after real envelopes replace fixtures. A fixture-driven layout that only works with fixture shapes is a defect. |
| VER-02 | Full five-width × 38-route matrix with per-route evidence, using the `ui-ux-reviewer` finding format: `[severity] file:line | route | viewport | finding | remediation`. |

---

## 5. Residual Test Gaps (must be declared, never assumed green)

| Gap | Why it cannot be closed in this packet |
|---|---|
| Real browser rendering at the five widths | This packet produces briefs only; no UI code exists yet in the target root. |
| Screen-reader pass (NVDA / VoiceOver) | Requires the implemented routes. |
| Camera-permission and QR-under-low-light behaviour | Requires a device; the manual-entry path is the guaranteed fallback. |
| 200 % zoom reflow | Requires rendered pages. |
| Automated axe / Lighthouse run | No route markup exists yet. |

These gaps are **declared**, not silently skipped, and they are the reason UI packets must produce their own evidence rather than inheriting this document.
