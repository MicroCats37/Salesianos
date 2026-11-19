# SH-01 — Visual Direction And Semantic Token System

**Artifact:** `evidence/routes/SH-01-visual-direction-and-semantic-tokens.md` · **Packet:** GOV-02 (`GOV-02-route-ux-baseline`) · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 (UI) · **Status:** DRAFT FOR REVIEW — brief only, no CSS was written
**Date:** 2026-11-19
**Authority:** `contract/next-app-architecture-contract.md` §1–§12 · `Aplicacion/documentacion/07-guia-para-ui-ux.md` §2, §3.1, §6 · `.opencode/skills/salesianos-ui-ux/SKILL.md` (Hard Rules 5–6) · `.opencode/skills/salesianos-shadcn/SKILL.md` (Hard Rules 6–8)

---

## 1. Scope And Non-Scope

| | |
|---|---|
| **In scope** | The *intent* of a global, semantic, reusable visual token system for the rebuilt Salesianos FEST frontend; the mapping from the frozen legacy palette to semantic roles; the light/dark pairing; the rule set every route brief must obey. |
| **Out of scope** | Writing `globals.css`, editing `Aplicacion/frontend/**` or `frontend/**`, choosing a final font, or committing any token to code. This packet produces briefs and evidence only. |
| **Owner of the implementation** | FND-06 (`frontend-shell`) owns the token file; every UI skeleton packet consumes it. |

---

## 2. Legacy Identity That Must Survive The Rebuild

The frozen `frontend/src/app/globals.css` (841 lines) is the only **visual evidence** of the Salesianos identity. It is explicitly *not* an implementation source (`salesianos-ui-ux` Hard Rule 6). The following values are the recognisable identity and MUST survive as the source values of the new semantic tokens.

### 2.1 Core brand source values

| Legacy variable | Light value | Role it plays today | Why it is recognisable |
|---|---|---|---|
| `--primary` / `--institutional` | `#312e8e` | Institutional blue — brand spine | Appears in hero gradient, CTAs, scrollbar, focus ring, selection |
| `--institutional-dark` | `#25236f` | Pressed / deeper blue | CTA hover, gradient stop, selection text |
| `--accent` / `--gold` | `#f4c64e` | Festival gold — accent + celebration | Section glows, "FEST" title pulse, badges, highlights |
| `--brand-cyan` | `#22d3ee` | Festival cyan — energy accent | Title gradient, orb glow, discipline card |
| `--brand-deep-navy` | `#17214b` | Body ink on light | All body text, foreground |
| `--brand-deep-blue` / `-mid` / `--brand-deep-night` | `#1a1857` / `#211e70` / `#0c0c1f` | Hero gradient stops, dark surface | Hero depth; also the whole dark theme canvas |
| `--secondary` | `#6976ff` | Lighter blue | Secondary buttons, dark-mode primary |
| `--brand-cyan-soft` | `#c98a1f` | Muted gold — **misnamed** | Consumed by `text-gold-soft`; it is a warm amber, not a cyan |

### 2.2 Surface, state and structure source values

| Legacy variable | Light value | Role |
|---|---|---|
| `--background` | `#f4f6fb` | Page canvas (cool near-white) |
| `--foreground` | `#17214b` | Body ink |
| `--card` / `--popover` | `#ffffff` | Raised surface |
| `--muted` / `--muted-foreground` | `#f1f5fb` / `#626195` | Recessed surface / secondary text |
| `--border` / `--input` | `#e5e7eb` | Hairlines |
| `--ring` | `#312e8e` | Focus ring (brand blue) |
| `--success` / `--warning` / `--destructive` | `#10b981` / `#f59e0b` / `#ef4444` | Verdict states |
| `--sidebar-*` | `#f8f9fc` … `#d1d5e0` | Admin chrome |
| `--radius` | `0.75rem` (sm `.5` · md `.75` · lg `1` · xl `1.5` · 2xl `2` · 3xl `3`) | Corner language — generous, soft, **not** a zero-radius editorial style |
| `--font-sans` / `--font-heading` | Plus Jakarta Sans | Single-family humanist geometric sans (display + body) |
| `--font-mono` | Geist Mono | Technical data only |

### 2.3 What must NOT be carried over (debt, not identity)

These are **defects of the legacy file**, not brand decisions. The rebuild converts them into semantic roles instead of copying them.

| Legacy artefact | Problem | Target rule |
|---|---|---|
| `hero-gradient`, `section-gradient-warm`, `surface-page-gradient`, `text-gradient-*` | Literal `rgba()`/`#hex` inside `@utility` — 15+ hardcoded colours outside any token | Gradients compose **from** semantic tokens (`from-primary` → `via-institutional-dark` → `to-surface-inverse`) |
| `card-elevated`, `card-glass`, `discipline-card`, `btn-brand-gradient` | Literal shadows and gradient stops | Shadow roles as tokens; cards consume `bg-card` + `border-border` + a shadow role |
| `text-gold-soft` → `--brand-cyan-soft` | Name/value mismatch (a gold utility reads a "cyan" variable) | One name per role: `text-accent-muted` |
| `btn-login`, `.login-bg`, `.vp-panel`, `.feature-pill`, `.carousel-dot` | A whole second token island scoped to `/login` | Fold into the global system; the auth page composes global roles |
| `--surface-form-amber`, `--shadow-gold*`, `--input-pill-*` | Page-local tokens declared in `:root` | Either promote to a named role or move next to its only consumer |
| `@utility` as the styling mechanism | Tailwind v4 `@utility` with hand-written CSS bypasses the shadcn class contract | Prefer shadcn semantic utilities; keep custom utilities only for genuine brand motion |
| `.dark` overrides only 11 tokens | Dark mode does not remap `--secondary`, `--success`, `--warning`, `--destructive`, `--sidebar-accent-foreground` consistently | Every semantic role must have a light and a dark value |

---

## 3. Direction: "Institutional Blue, Festival Gold"

One sentence: **the calm, orderly institutional blue of a Salesianos school programme carrying the warmth and noise of a festival, with gold and cyan used only where celebration or energy is genuinely intended.**

This is deliberately **not** a generic SaaS dashboard, and not a neon festival site either. The plan forbids "generic dashboard, card-grid, gradient" aesthetics (`salesianos-ui-ux` Hard Rule 5) and forbids placeholder-heavy AI layouts.

### 3.1 Colour roles (semantic, global)

| Token role | Light | Dark | Source | Used by |
|---|---|---|---|---|
| `--primary` | `#312e8e` | `#6976ff` | legacy | Primary CTA, active nav, focus |
| `--primary-foreground` | `#ffffff` | `#0c0c1f` | legacy | On primary |
| `--primary-hover` | `#25236f` | `#312e8e` | legacy `institutional-dark` | Primary CTA hover (never `transform`-only) |
| `--secondary` | `#6976ff` | `#3a43c9` (new — see §3.4) | legacy | Secondary CTA, chips |
| `--secondary-foreground` | `#ffffff` | `#ffffff` | legacy | On secondary |
| `--accent` | `#f4c64e` | `#f4c64e` | legacy | Festival accent, celebration highlights |
| `--accent-foreground` | `#17214b` | `#0c0c1f` | legacy | On accent |
| `--accent-muted` | `#c98a1f` | `#e0a83a` | legacy `brand-cyan-soft` (renamed) | Quiet gold text on light |
| `--brand-cyan` | `#22d3ee` | `#22d3ee` | legacy | Energy accent, chart series |
| `--surface` | `#f4f6fb` | `#0c0c1f` | legacy `background` | Page canvas |
| `--surface-raised` | `#ffffff` | `#16162e` | legacy `card` | Cards, panels |
| `--surface-overlay` | `#ffffff` | `#16162e` | legacy `popover` | Popover, dialog, sheet |
| `--surface-recessed` | `#f1f5fb` | `#1a1a36` | legacy `muted` | Table headers, wells |
| `--surface-inverse` | `#17214b` | `#0e1223` | legacy `brand-deep-navy` | Hero / footer band |
| `--foreground` | `#17214b` | `#f4f6fb` | legacy | Body ink |
| `--foreground-muted` | `#626195` | `#a0a3c4` | legacy `muted-foreground` | Secondary text, metadata |
| `--border` | `#e5e7eb` | `#2a2a4a` | legacy | Hairlines |
| `--border-strong` | `#d1d5e0` | `#3a3a63` | legacy `sidebar-border` | Emphasised dividers |
| `--ring` | `#312e8e` | `#6976ff` | legacy | Focus ring |
| `--success` | `#10b981` | `#10b981` | legacy | Verified / enabled |
| `--success-foreground` | `#ffffff` | `#0c0c1f` | legacy | On success |
| `--warning` | `#f59e0b` | `#f59e0b` | legacy | Needs attention |
| `--warning-foreground` | `#17214b` | `#0c0c1f` | legacy | On warning |
| `--destructive` | `#ef4444` | `#ef4444` | legacy | Rejected / irreversible |
| `--destructive-foreground` | `#ffffff` | `#ffffff` | legacy | On destructive |
| `--info` | `#1557b8` | `#38bdf8` | new (`--login-bg-end` promoted) | Informational, in-flight |

### 3.2 Verdict roles (domain-facing, derived — never a raw provider code)

`07-guia-para-ui-ux.md` §2 forbids branching on business codes in the UI, but the UI still needs a *visual* bucket. The mapping is **presentational only**; the label and the meaning always come from the backend `estado_operativo.{codigo, etiqueta, descripcion}` (frozen by `FREEZE-ENV-1.0.0` / `D-07`).

| Presentation role | Token pair | Backend source (indicative, **not authoritative**) |
|---|---|---|
| Verified / enabled | `--success` / `--success-foreground` | `estado_operativo.codigo` in the confirmed set |
| Pending / in verification | `--warning` / `--warning-foreground` | pending + verifying codes |
| Needs attention | `--info` / on-info | "needs attention" code |
| Not completed | `--muted` / `--foreground-muted` | payment not completed |
| Rejected / revoked | `--destructive` / `--destructive-foreground` | revoked, rejected |
| Unknown / neutral | `--muted` / `--foreground-muted` | fallback — the client must render unknown codes **neutrally**, never crash |

Rule: **colour never carries the meaning alone** (`ui-ux-pro-max` priority 1, `frontend/06` §6). Every verdict chip pairs colour + icon + the backend's `etiqueta` text.

### 3.3 Chart roles (mandatory, currently absent)

The frozen `globals.css` has **no chart tokens at all**. Admin summaries (ADM-01) and competition charts need them.

| Token | Value (light) | Note |
|---|---|---|
| `--chart-1` | `#312e8e` | Institutional blue — primary series |
| `--chart-2` | `#f4c64e` | Gold — second series |
| `--chart-3` | `#22d3ee` | Cyan — third series |
| `--chart-4` | `#6976ff` | Light blue — fourth series |
| `--chart-5` | `#c98a1f` | Amber — fifth series |
| `--chart-grid` | `#e5e7eb` | Axis / grid lines |
| `--chart-axis` | `#626195` | Axis labels (muted, never foreground) |

Categorical pairs must remain distinguishable in both themes; every chart ships a legend and an accessible table alternative.

### 3.4 Tokens that must be ADDED (gaps in the legacy palette)

| New role | Why it is needed | Proposal |
|---|---|---|
| `--secondary` dark value | The legacy `.dark` block never remaps `--secondary`; `#6976ff` on `#0c0c1f` is the *primary* in dark, so a "secondary" that equals the primary is meaningless | dark secondary `#3a43c9` (darker, still brand-family) |
| `--shadow-sm` / `--shadow-md` / `--shadow-lg` / `--shadow-focus` | Shadows are literal `rgba()` in 5 legacy utilities; elevation must be a token so dark mode can differ | derived from `--primary` at 6/8/12 % alpha in light, pure black at 40/50/60 % in dark |
| `--focus-ring-width` / `--focus-ring-offset` | Focus visibility is a hard a11y requirement but no token exists | `2px` / `2px` |
| `--radius-*` already exist | Keep | `.5 / .75 / 1 / 1.5 / 2 / 3 rem` |
| `--space-*` scale | Spacing is ad-hoc Tailwind utilities; a scale prevents drift between 38 pages | 4/8/12/16/24/32/48/64/96 (`--space-section` = 48 desktop, 32 mobile) |
| `--z-*` | Layering is implicit today | `--z-base 0`, `--z-sticky 10`, `--z-drawer 40`, `--z-dialog 50`, `--z-toast 60` |
| `--motion-duration-fast/base/slow` | Legacy has 4 different durations (0.2/0.3/0.7/0.8/1.0 s) with no system | `120ms / 200ms / 320ms` |
| `--motion-ease-standard` | Legacy mixes `cubic-bezier(0.4,0,0.2,1)` and `cubic-bezier(0.16,1,0.3,1)` | one standard ease; the "reveal" ease reserved for the single orchestrated page-load moment |

### 3.5 Typography

| Role | Face | Use |
|---|---|---|
| Display / heading | Plus Jakarta Sans, weight 800, tracking `-0.025em` | Page title, hero, section titles |
| Body | Plus Jakarta Sans, weight 400/500, 16 px base, line-height 1.6, **measure ≤ 80 characters** | Everything |
| Eyebrow | Plus Jakarta Sans, weight 900, uppercase, `letter-spacing: 0.3em`, 10 px | **Only** for section labels that a human would label — the legacy `text-eyebrow-brand` is a "tell" per `frontend-design`; it must not be applied to every heading |
| Data / technical | Geist Mono, 12–13 px, tabular numerals | Order ids, codes, timestamps, amounts in tables |
| Numeric emphasis | Plus Jakarta Sans, weight 700, `font-variant-numeric: tabular-nums` | Amounts, cup counts, totals — **must not** reflow when a value changes |

Two families maximum (one sans + one mono). No third face.

### 3.6 Radius, elevation, density

| Surface | Radius | Elevation |
|---|---|---|
| Buttons / inputs | `--radius-md` (`.75rem`) | `--shadow-sm` |
| Cards / panels | `--radius-lg` (`1rem`) | `--shadow-md` |
| Dialogs / sheets | `--radius-xl` (`1.5rem`) | `--shadow-lg` |
| Hero band / marketing surfaces | `--radius-2xl` / `--radius-3xl` | `--shadow-lg` |

Legacy corners are soft and generous — **keep them**. That softness is part of what makes Salesianos look like Salesianos and not like a Stripe clone.

### 3.7 Motion

- Legacy defines 6 keyframes (`orb-float`, `orb-float-slow`, `fade-up`, `pulse-slow`, `hero-reveal`, `goldPulse`/`cyanPulse`, `shine-sweep`, `festival-ribbon-marquee`) applied across the portada. `frontend-design` explicitly calls "fade-and-slide-up entrances on each section and hover transitions on every card" the generic AI default.
- **Rule for the rebuild:** exactly **one** orchestrated page-load moment per marketing surface (the hero reveal), plus motion that answers a user action (dialog open, accordion expand, row advance). No per-section entrance animations. No `shine-sweep` on every CTA.
- `prefers-reduced-motion: reduce` must disable **all** of it — the legacy file honours this only for the animation classes, not for the `goldPulse`/`cyanPulse` inline styles (it does handle them with an attribute selector, but any new motion must be added to the same reduced-motion block).
- The legacy `orb-float` uses `15vw`/`10vh` translations — on a 360 px viewport that is 54 px of travel; verify no overflow and no scroll-jank at 360.

### 3.8 Iconography

- Library: **Lucide** (`iconLibrary: "lucide"` in `components.json`). `frontend-design` and `ui-ux-pro-max` both forbid emoji as icons.
- Icons are always decorative-with-text or labelled: an icon-only button carries `aria-label` + `sr-only` text.
- Status icons pair with the verdict chip text (never colour alone).

---

## 4. Rules Every Route Brief Must Cite

| # | Rule | Source |
|---|---|---|
| T-01 | No literal hex/RGB/HSL and no palette utilities (`bg-[#…]`, `text-red-500`) in any component. Only semantic roles. | `salesianos-shadcn` Hard Rule 8 |
| T-02 | Layout/spacing/responsive utilities stay local to the component; the global theme holds **roles**, never layout. | `salesianos-shadcn` Hard Rule 9 |
| T-03 | The frontend shows verdicts; it never derives price, eligibility, capacity, payment state, or permission. | `07-guia-para-ui-ux.md` §1, §5 |
| T-04 | A new visual role requires a global token **first**, then a consumer. No role is invented at the call site. | `salesianos-shadcn` Decision Gate |
| T-05 | Every colour token has a light **and** a dark value, and every pair meets 4.5:1 for body text / 3:1 for large text and UI borders. | `ui-ux-pro-max` priority 1 & 6 |
| T-06 | Dark mode is a first-class theme, not an inversion. | `salesianos-shadcn` Hard Rule 8 |
| T-07 | Charts use `--chart-*` roles, ship a legend, and offer a tabular alternative. | `ui-ux-pro-max` priority 10 |
| T-08 | Motion is either the single orchestrated moment or action-driven, and honours `prefers-reduced-motion`. | `frontend-design` §Restraint |

---

## 5. External Design-System Reference Checked (and Deliberately Not Adopted)

`ui-ux-pro-max` was queried for a product-wide direction:

```
python .agents/skills/ui-ux-pro-max/scripts/search.py "sports event festival ticketing admin operations" --design-system -p "Salesianos FEST"
```

**Returned:** pattern *Event/Conference Landing*; style *Vibrant & Block-based*; palette slate `#0F172A` / `#020617` with green accent `#16A34A`; type *Bebas Neue / Source Sans 3*.

**Verdict: NOT adopted.** It conflicts with the user-approved direction ("preserve recognizable Salesianos identity") and with the frozen brand (institutional blue + festival gold + cyan). A slate-and-green generic event palette would erase the recognisable identity the rebuild is required to keep. Adopting it would also force a new font pair (Bebas Neue / Source Sans 3), breaking the Plus Jakarta Sans identity.

**What WAS adopted** — the tool's *checklist*, which is stack-agnostic and independently mandated by `ui-ux-pro-max`:

- No emoji as icons (SVG/Lucide only).
- `cursor-pointer` on every clickable element.
- Hover states with 150–300 ms transitions.
- Light-mode text contrast ≥ 4.5:1.
- Visible keyboard focus.
- `prefers-reduced-motion` respected.
- Responsive check at 375/768/1024/1440 — **extended here to the project's mandatory 360/390/768/1024/1440** (`salesianos-responsive-a11y` Hard Rule 1).
- No seat-map feedback, no hidden fees, no weak mobile — adopted directly as the ADM-01 / PASS-01 / SHOP-01 "no invented stock, no invented price" rule.

Its "AVOID" line (`No seat-map feedback + hidden fees + weak mobile`) is a precise restatement of `FL-01` and `FL-08`: the client never invents availability, prices, or stock. Recorded here so the next packet does not re-derive it.

---

## 6. Unresolved Decisions Carried Forward

| ID | Question | Owner | Blocking scope |
|---|---|---|---|
| `GOV-02-UX-01` | Is `--secondary` dark `#3a43c9` or should the dark theme simply promote `--secondary` to a distinct cyan-family role? | A7 + A0 | Token file in FND-06 |
| `GOV-02-UX-02` | Should the dark theme ship at all in the first cut, or is light-only acceptable for wave 1? The legacy `.dark` block is incomplete. | A0 + A7 | FND-06 scope |
| `GOV-02-UX-03` | Do the legacy marketing gradients (hero / ribbon / orbs) survive as brand assets on the new portada, or is the new portada a different composition? | A7 + product | PUB-01 brief |
| `GOV-02-UX-04` | Font hosting: the legacy uses `next/font` with Plus Jakarta Sans + Geist Mono — keep, or move to the shadcn `font-*` registry items (`font-geist`, `font-plus-jakarta-sans` is not in the registry list)? | A7 | FND-06 |
| `GOV-02-UX-05` | Is `--accent` (gold) an interactive colour or strictly a decorative/celebration colour? If interactive, its contrast on `--surface-raised` must be checked for text use. | A7 + a11y | All routes using accent for text |

---

## 7. Acceptance Criteria For This Document

- [x] Every legacy brand value that must survive is named with its source variable and value.
- [x] Every legacy artefact that must **not** survive is named with the reason and the target rule.
- [x] A complete semantic role table exists with light **and** dark values, including roles the legacy file lacks.
- [x] Chart roles are defined (they are entirely absent from the legacy file).
- [x] Typography, radius, elevation, motion and icon rules are stated.
- [x] The external design-system tool output is recorded with an explicit rejection rationale and an adopted checklist.
- [x] No CSS, TSX, or configuration file was created or modified by this packet.
