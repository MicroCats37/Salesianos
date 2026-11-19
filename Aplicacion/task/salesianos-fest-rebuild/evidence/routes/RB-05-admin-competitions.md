# RB-05 — Route Briefs: Admin Competitions, Schedule And Bracket

**Artifact:** `evidence/routes/RB-05-admin-competitions.md` · **Packet:** GOV-02 · **Original plan tasks:** `T-001`, `T-002`
**Owner:** A7 · **Status:** DRAFT FOR REVIEW — briefs only
**Date:** 2026-11-19
**Page IDs in this file (4 of 38):** `ADM-10`, `ADM-11`, `ADM-12`, `ADM-13`
**Shared references:** `SH-01` … `SH-06`

> **Base (verified):** the backend already has `Competencia`, `CompetenciaEquipo`, `Ronda`, `Encuentro` with 29 documented administrative routes (17 + 12), including propagation and bracket correction (`frontend/05` §base, source `03b` §4.9–4.12). The target UX must **not lose those verified rules**.
> **Public bracket** `/competencias/[id]` appears only in `frontend/05` §2 and has **no page ID**; it is registered as `RT-CP-10` and marked provisional (`P-04`).

---

## `ADM-10` — `/administracion/competencias` — list of competitions

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** select and administer the competitions of the edition.
- **Preconditions:** admin group; edition, discipline and category context.
- **Visible sections:** competition list · filters · create (if authorised) · open detail / agenda / bracket.
- **Key components (candidates):** `table`/card list · `input`/`select` (filters) · `button` · `badge` (state) · `empty` · `pagination`.
- **Actions:** search/filter · create · open the detail, the agenda or the bracket.
- **Navigation:** `ADM-11` (detail), `ADM-12` (bracket), `ADM-13` (agenda).
- **Data / contract dependencies (provisional):** `RT-CP-01`.
- **States:** `S-01` · `S-02` (no competitions for this edition) · `S-03` (filtered-empty) · `S-04` · `S-06`.
- **Responsive intent:** 360/390 card per competition with its discipline/category and the three entry points as buttons; 768+ table with an action column.
- **Semantic-token intent:** `bg-surface-raised`, verdict chips, `bg-primary` for "Ver detalle", `text-foreground-muted` for the discipline line.
- **Accessibility intent:** the three entry points are three distinct labelled links, not an icon menu with no accessible name; the filter bar keeps the same contract as the other admin lists (`GOV-02-RB-03b`).
- **Acceptance:** the filters of the competition list and the bracket selector stay **coherent** (`frontend/05` §7) · creating is only offered when authorised.
- **Open decisions:** `P-05` (possible merge with the admin summary).

---

## `ADM-11` — `/administracion/competencias/[id]` — operational centre

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** edit the competition, manage eligible teams, rounds, matches and indicators.
- **Preconditions:** admin group; a competition id.
- **Visible sections:** competition data · eligible teams (and the reason when a team is ineligible) · rounds · matches · indicators.
- **Key components (candidates):** `tabs` · `table`/card list (teams, rounds, matches) · `drawer` (**the single match-detail panel**, `SH-06` §5.2) · `dialog` (create round / match) · `alert` (eligibility reason) · `badge` (match state) · `alert-dialog` (irreversible corrections).
- **Actions:** edit the data · add an eligible team · create a round · create a match (empty/partial allowed) · schedule · open the match detail.
- **Navigation:** to `ADM-12` (bracket) and `ADM-13` (agenda); the match detail is a panel, **not** a route.
- **Data / contract dependencies (provisional):** `RT-CP-02`, `RT-CP-04` (match detail), plus the write routes the backend already owns for rounds/matches (not re-proposed here).
- **States:** `S-01` · `S-02` (no rounds / no teams → a **specific** CTA to add them, not a generic empty screen — `frontend/05` §5) · `S-04` · `S-06` · `S-08` · *version conflict* → "Los datos cambiaron. Actualiza y revisa antes de guardar." and **reload + retry without silently applying stale changes** · `S-09` (advance preview shows the effect before writing).
- **Responsive intent:** see `SH-06` §5. 360/390 tabs scroll, body single column, the match detail is a **bottom drawer** at 90 vh with a trapped focus; 768+ side sheet; 1024/1440 two columns (body + indicator rail).
- **Semantic-token intent:** `bg-surface-raised` panels, `bg-surface-recessed` for the round grouping, `--warning` for a partial match, `--destructive` for a blocking eligibility issue, `bg-primary` for the primary action, `border-border` between rounds.
- **Accessibility intent:** the match-detail panel is a `dialog` with `aria-labelledby`; every action states its **consequence** ("Ganador registrado: Equipo Norte", "La corrección afecta a 2 encuentros posteriores"); the version conflict never auto-applies; the panel restores focus to the trigger on close.
- **Acceptance:** the same match detail is reachable from the list, the agenda and the bracket — one editor, no divergence (`frontend/05` §7) · a version conflict informs and recovers (`QA-K05`).
- **Open decisions:** `PD-01` (BOX assignment) is adjacent to the competition domain.

---

## `ADM-12` — `/administracion/competencias/[id]/cuadro` — bracket

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** view and operate the progression.
- **Preconditions:** admin group; a competition id.
- **Visible sections:** the bracket by round · a match card (teams, score, winner) · preview and confirm for the advance · corrections with impact preview.
- **Key components (candidates):** `card` (match cards) · `scroll-area` (horizontal bracket container) · `badge` (winner / state) · `drawer` (match detail) · `alert-dialog` (correction, with a reason field) · `button` · `tooltip` (round context, with a non-tooltip fallback).
- **Actions:** open a match · register a result · **preview** the advance · **confirm** the advance · correct a result (reason required).
- **Navigation:** the match detail opens as a panel from the bracket.
- **Data / contract dependencies (provisional):** `RT-CP-03` (bracket), `RT-CP-04` (match), `RT-CP-06` (register result), `RT-CP-07` (advance preview), `RT-CP-08` (advance confirm), `RT-CP-09` (correction preview).
- **States:** `S-01` · `S-02` (no rounds / no teams → specific CTA) · `S-04` · `S-06` · *advance error* → the blocking match/slot is highlighted · *version conflict* · `S-10` (correction requires a reason).
- **Responsive intent:** see `SH-06` §5.1. Desktop: bracket centred, scrolling only when it exceeds the viewport. Mobile: a **horizontal scroll container** with round indicators and the match card's detail below — **not** a desktop grid squeezed into 360 px, and **never** a page-level horizontal scroll.
- **Semantic-token intent:** `bg-surface-raised` match cards, `border-primary` on the selected card, `--success` for the confirmed winner, `--warning` for a bye, `--destructive` for a blocking error, `--chart-*` only if a chart is added (requires the tokens first — `GOV-02-SH-05`).
- **Accessibility intent:** each match card is a **button** whose accessible name includes both teams and the score ("Equipo Norte 2, Rival Sur 1"); the bracket container is keyboard-scrollable with visible focus; round indicators are text, not dots only; a correction's impact is announced.
- **Acceptance:** an ineligible team cannot be added and the reason is shown (`QA-K01`) · an overlapping schedule is rejected and the agenda is unchanged (`QA-K02`) · the result fixes the winner exactly once and is visible in the bracket (`QA-K03`) · the advance preview **does not write** while the confirm does (`QA-K04`) · a correction that affects descendants requires a reason and a confirmation (`QA-K05`).
- **Open decisions:** `P-09` — the current route is `/administracion/competencias/cuadro`; the proposed one is `/administracion/competencias/[id]/cuadro`.

---

## `ADM-13` — `/administracion/competencias/agenda` — schedule

- **Actor:** administrador. **Priority:** Alta.
- **Objective:** see the matches of a day and open one.
- **Preconditions:** admin group.
- **Visible sections:** matches grouped by day · filters (day, discipline, state) · open a match.
- **Key components (candidates):** `card` (day groups) · `table`/list (matches) · `select`/`input` (filters) · `badge` (state) · `drawer` (match detail) · `empty`.
- **Actions:** filter by day/discipline/state · open a match.
- **Navigation:** the match detail panel — the same one as `ADM-11` and `ADM-12`.
- **Data / contract dependencies (provisional):** `RT-CP-05`.
- **States:** `S-01` · `S-02` (no matches that day) · `S-03` (filtered-empty) · `S-04` · `S-06`.
- **Responsive intent:** 360/390 a vertical timeline of day groups with matches as rows (the **local time of the edition** is displayed — `frontend/05` §5); 768 two columns of day groups; 1024/1440 a single day column with a date rail.
- **Semantic-token intent:** `bg-surface-raised` day cards, `bg-surface-recessed` for the time column, verdict chips for the match state, `text-foreground-muted` for the discipline, `bg-primary` for "Abrir".
- **Accessibility intent:** the time is exposed as text with a machine-readable `datetime`; the day grouping is a heading; the match row's accessible name includes both teams and the time.
- **Acceptance:** the agenda, the bracket and the competition detail share one operational data source (`FL-11` §6) · overlapping scheduling is rejected by the backend and the agenda is not modified.
- **Open decisions:** none new.

---

## Cross-Route Obligations In This File

| ID | Obligation | Owner |
|---|---|---|
| `GOV-02-RB-05a` | **One** match-detail panel serves the list, the agenda and the bracket. Divergent editors are a defect (`frontend/05` §3). | A7 |
| `GOV-02-RB-05b` | Preview and confirm are **separate routes** and separate user actions. The preview never writes (`FREEZE-RT` principle, `QA-K04`). | A7 + A4 |
| `GOV-02-RB-05c` | The client never computes a winner from a score, never forces an advance and never invents a bye without confirmation (`frontend/05` §6). | A7 |
| `GOV-02-RB-05d` | Match states use the **backend's** vocabulary; no presentation-only enumeration is introduced (`frontend/05` §5). | A7 |
| `GOV-02-RB-05e` | The bracket is never a page-level horizontal scroll; the scroll container is the bracket itself. | A7 |
